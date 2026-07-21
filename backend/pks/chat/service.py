"""Chat service: retrieval-augmented conversation over the knowledge base.

The heavy lifting happened at ingestion; here the fast tier answers using
hybrid-search retrieval (spec principle 8). Every answer segment is labeled
pks (with validated citations) or model — a pks segment whose citations don't
check out is downgraded to model rather than presenting unbacked claims as
the user's knowledge (spec principle 7).
"""

from __future__ import annotations

from pks.chat import prompts
from pks.chat.models import ChatResult, Citation, Conversation, Message, MessageRole, Segment
from pks.chat.store import ChatStore, new_message
from pks.config import Settings
from pks.core.engine import KnowledgeEngine
from pks.core.errors import NotFoundError, ValidationError
from pks.core.models import WorkspaceRefType
from pks.core.store.sqlite import SqliteStore
from pks.embeddings.base import EmbeddingProvider
from pks.providers.base import CompletionProvider
from pks.search.service import SearchService

_EXCERPT_CHARS = 1200
_TITLE_CHARS = 60


class ChatService:
    def __init__(
        self,
        store: SqliteStore,
        provider: CompletionProvider | None,
        embedder: EmbeddingProvider,
        settings: Settings,
    ):
        self._chat = ChatStore(store)
        self._search = SearchService(store, embedder)
        self._engine = KnowledgeEngine(store)
        self._provider = provider
        self._settings = settings

    # ------------------------------------------------------------------
    # Conversations
    # ------------------------------------------------------------------

    def get_conversation(self, conversation_id: str) -> Conversation:
        conversation = self._chat.get_conversation(conversation_id)
        if conversation is None:
            raise NotFoundError(f"conversation {conversation_id!r} not found")
        return conversation

    def list_conversations(self) -> list[Conversation]:
        return self._chat.list_conversations()

    def list_messages(self, conversation_id: str) -> list[Message]:
        self.get_conversation(conversation_id)
        return self._chat.list_messages(conversation_id)

    def delete_conversation(self, conversation_id: str) -> None:
        if not self._chat.delete_conversation(conversation_id):
            raise NotFoundError(f"conversation {conversation_id!r} not found")

    # ------------------------------------------------------------------
    # Asking
    # ------------------------------------------------------------------

    def ask(
        self,
        content: str,
        *,
        conversation_id: str | None = None,
        workspace_id: str | None = None,
    ) -> ChatResult:
        if self._provider is None:
            raise ValidationError(
                "chat requires an AI provider — set ANTHROPIC_API_KEY and restart"
            )
        content = content.strip()
        if not content:
            raise ValidationError("message must not be empty")

        if conversation_id is None:
            if workspace_id is not None:
                self._engine.get_workspace(workspace_id)
            title = content[:_TITLE_CHARS] + ("…" if len(content) > _TITLE_CHARS else "")
            conversation = self._chat.create_conversation(
                title=title, workspace_id=workspace_id
            )
        else:
            conversation = self.get_conversation(conversation_id)

        history = self._chat.list_messages(conversation.id)
        user_message = new_message(conversation.id, MessageRole.USER, content)
        self._chat.add_message(user_message)

        sources = self._retrieve(content, workspace_id=conversation.workspace_id)
        raw = self._provider.extract_structured(
            prompt=prompts.chat_prompt(
                self._render_sources(sources),
                self._render_history(history),
                content,
            ),
            schema=prompts.CHAT_SCHEMA,
            system=prompts.CHAT_SYSTEM,
            tier="fast",
            max_tokens=2048,
        )
        segments, citations = self._validate(raw, sources)

        assistant_message = new_message(
            conversation.id,
            MessageRole.ASSISTANT,
            " ".join(segment.text.strip() for segment in segments if segment.text.strip()),
            segments=segments,
            citations=citations,
        )
        self._chat.add_message(assistant_message)
        self._chat.touch_conversation(conversation.id)
        conversation = self.get_conversation(conversation.id)
        return ChatResult(
            conversation=conversation,
            user_message=user_message,
            assistant_message=assistant_message,
        )

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def _retrieve(self, query: str, *, workspace_id: str | None = None) -> list[Citation]:
        """Hybrid retrieval, flattened into numbered candidate citations.

        In a workspace conversation, retrieval is scoped to the workspace's
        referenced resources and the knowledge extracted from them (an empty
        workspace falls back to unscoped retrieval).
        """
        resource_filter: set[str] | None = None
        ko_filter: set[str] | None = None
        if workspace_id is not None:
            resource_ids = set(
                self._engine.workspace_object_ids(workspace_id, WorkspaceRefType.RESOURCE)
            )
            ko_ids = set(
                self._engine.workspace_object_ids(
                    workspace_id, WorkspaceRefType.KNOWLEDGE_OBJECT
                )
            )
            for resource_id in resource_ids:
                ko_ids.update(self._engine.knowledge_object_ids_for_resource(resource_id))
            if resource_ids or ko_ids:
                resource_filter = resource_ids
                ko_filter = ko_ids

        limit = max(self._settings.chat_context_chunks, self._settings.chat_context_objects)
        result = self._search.search(
            query,
            limit=limit,
            resource_ids=resource_filter,
            knowledge_object_ids=ko_filter,
        )
        sources: list[Citation] = []
        for hit in result.chunks[: self._settings.chat_context_chunks]:
            sources.append(
                Citation(
                    number=len(sources) + 1,
                    kind="chunk",
                    id=hit.chunk.id,
                    title=hit.resource_title,
                    resource_id=hit.resource_id,
                    structure_path=hit.chunk.structure_path,
                    excerpt=hit.chunk.text[:_EXCERPT_CHARS],
                )
            )
        for hit in result.knowledge[: self._settings.chat_context_objects]:
            ko = hit.object
            sources.append(
                Citation(
                    number=len(sources) + 1,
                    kind="knowledge_object",
                    id=ko.id,
                    title=ko.name,
                    excerpt=ko.description[:_EXCERPT_CHARS] or None,
                )
            )
        return sources

    @staticmethod
    def _render_sources(sources: list[Citation]) -> str:
        blocks = []
        for source in sources:
            if source.kind == "chunk":
                where = f' ({source.structure_path})' if source.structure_path else ""
                header = f'[{source.number}] Excerpt from "{source.title}"{where}:'
            else:
                header = f"[{source.number}] Knowledge object: {source.title}"
            blocks.append(f"{header}\n{source.excerpt or ''}".strip())
        return "\n\n".join(blocks)

    def _render_history(self, history: list[Message]) -> str:
        recent = history[-self._settings.chat_history_limit :]
        return "\n\n".join(f"{message.role.value}: {message.content}" for message in recent)

    @staticmethod
    def _validate(raw: dict, sources: list[Citation]) -> tuple[list[Segment], list[Citation]]:
        by_number = {source.number: source for source in sources}
        segments: list[Segment] = []
        used: set[int] = set()
        for item in raw.get("segments", []):
            segment = Segment.model_validate(item)
            valid_numbers = [n for n in segment.source_numbers if n in by_number]
            if segment.source == "pks" and not valid_numbers:
                # A pks claim without verifiable backing is a model claim.
                segment = segment.model_copy(update={"source": "model", "source_numbers": []})
            else:
                segment = segment.model_copy(update={"source_numbers": valid_numbers})
            used.update(segment.source_numbers)
            segments.append(segment)
        if not segments:
            raise ValidationError("chat model returned no answer segments")
        citations = [by_number[n] for n in sorted(used)]
        return segments, citations
