"""Tests for the chat service and API (fake provider/embedder)."""

import time

import pytest
from fastapi.testclient import TestClient

from pks.api.app import create_app
from pks.chat.service import ChatService
from pks.config import Settings
from pks.core import KnowledgeEngine
from pks.core.errors import NotFoundError, ValidationError
from pks.core.store import SqliteStore
from pks.events import JobQueue, Worker
from pks.ingestion import intake
from pks.pipeline import build_pipeline
from tests.fakes import ROME_MD, FakeEmbedder, FakeProvider


@pytest.fixture
def settings(tmp_path):
    return Settings(_env_file=None, data_dir=tmp_path / "data", anthropic_api_key=None)


@pytest.fixture
def store(settings):
    store = SqliteStore(settings.db_path)
    yield store
    store.close()


@pytest.fixture
def embedder():
    return FakeEmbedder()


@pytest.fixture
def ingested(settings, store, embedder):
    """A knowledge base with the Rome document fully processed."""
    registry = build_pipeline(FakeProvider(), embedder)
    engine = KnowledgeEngine(store)
    queue = JobQueue(store)
    intake.save_upload(engine, settings, registry, queue, filename="rome.md", content=ROME_MD)
    worker = Worker(settings, registry)
    worker.drain()
    worker.close()


def make_service(store, settings, embedder, provider):
    return ChatService(store, provider, embedder, settings)


# ----------------------------------------------------------------------
# Service
# ----------------------------------------------------------------------


def test_ask_creates_conversation_and_cites_sources(settings, store, embedder, ingested):
    provider = FakeProvider()
    service = make_service(store, settings, embedder, provider)

    result = service.ask("When did the Roman Republic begin?")

    assert result.conversation.title.startswith("When did the Roman Republic")
    assert result.user_message.role.value == "user"
    assistant = result.assistant_message
    assert assistant.role.value == "assistant"
    assert "From your notes: yes." in assistant.content

    # Segment labels survive; the pks segment's citation resolves to source 1.
    assert [s.source for s in assistant.segments] == ["pks", "model"]
    [citation] = assistant.citations
    assert citation.number == 1
    assert citation.kind in ("chunk", "knowledge_object")
    assert citation.excerpt

    # The fast tier answered, and retrieval put the Republic chunk in sources.
    assert provider.chat_tiers == ["fast"]
    assert "Roman Republic began in 509 BC" in provider.chat_prompts[0]


def test_history_is_included_on_followups(settings, store, embedder, ingested):
    provider = FakeProvider()
    service = make_service(store, settings, embedder, provider)

    first = service.ask("When did the Roman Republic begin?")
    service.ask("And when did it end?", conversation_id=first.conversation.id)

    followup_prompt = provider.chat_prompts[1]
    assert "When did the Roman Republic begin?" in followup_prompt  # prior user turn
    assert "From your notes: yes." in followup_prompt  # prior assistant turn
    assert len(service.list_messages(first.conversation.id)) == 4


def test_unbacked_pks_claim_is_downgraded_to_model(settings, store, embedder, ingested):
    provider = FakeProvider(
        chat={
            "segments": [
                {"text": "Backed claim.", "source": "pks", "source_numbers": [1]},
                {"text": "Fabricated citation.", "source": "pks", "source_numbers": [99]},
            ]
        }
    )
    service = make_service(store, settings, embedder, provider)
    assistant = service.ask("Tell me things").assistant_message

    assert [s.source for s in assistant.segments] == ["pks", "model"]
    assert assistant.segments[1].source_numbers == []
    assert [c.number for c in assistant.citations] == [1]


def test_chat_without_provider_rejected(settings, store, embedder):
    service = make_service(store, settings, embedder, provider=None)
    with pytest.raises(ValidationError, match="AI provider"):
        service.ask("hello")


def test_conversation_lifecycle(settings, store, embedder, ingested):
    service = make_service(store, settings, embedder, FakeProvider())
    result = service.ask("Question one")

    assert [c.id for c in service.list_conversations()] == [result.conversation.id]
    service.delete_conversation(result.conversation.id)
    assert service.list_conversations() == []
    with pytest.raises(NotFoundError):
        service.get_conversation(result.conversation.id)


def test_empty_message_rejected(settings, store, embedder, ingested):
    service = make_service(store, settings, embedder, FakeProvider())
    with pytest.raises(ValidationError):
        service.ask("   ")


# ----------------------------------------------------------------------
# API
# ----------------------------------------------------------------------


def test_chat_api_end_to_end(tmp_path):
    settings = Settings(
        _env_file=None,
        data_dir=tmp_path / "data",
        worker_poll_interval=0.02,
        anthropic_api_key=None,
    )
    app = create_app(settings=settings, provider=FakeProvider(), embedder=FakeEmbedder())
    with TestClient(app) as client:
        resource = client.post(
            "/api/resources/upload", files={"file": ("rome.md", ROME_MD)}
        ).json()["resource"]
        deadline = time.monotonic() + 15
        while time.monotonic() < deadline:
            if client.get(f"/api/resources/{resource['id']}").json()["status"] in (
                "ready",
                "failed",
            ):
                break
            time.sleep(0.02)

        body = client.post("/api/chat", json={"content": "When did the Republic begin?"}).json()
        conversation_id = body["conversation"]["id"]
        assert body["assistant_message"]["segments"][0]["source"] == "pks"
        assert body["assistant_message"]["citations"]

        followup = client.post(
            "/api/chat", json={"content": "More", "conversation_id": conversation_id}
        ).json()
        assert followup["conversation"]["id"] == conversation_id

        detail = client.get(f"/api/chat/conversations/{conversation_id}").json()
        assert len(detail["messages"]) == 4
        assert len(client.get("/api/chat/conversations").json()) == 1

        assert client.delete(f"/api/chat/conversations/{conversation_id}").status_code == 204
        assert client.get(f"/api/chat/conversations/{conversation_id}").status_code == 404
