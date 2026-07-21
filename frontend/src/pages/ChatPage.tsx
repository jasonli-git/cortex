import { useEffect, useRef, useState } from 'react'
import { api } from '../api'
import { ErrorNote, Spinner } from '../components/ui'
import type { Citation, Conversation, Message, Workspace } from '../types'

export default function ChatPage() {
  const [conversations, setConversations] = useState<Conversation[]>([])
  const [workspaces, setWorkspaces] = useState<Workspace[]>([])
  const [activeId, setActiveId] = useState<string | null>(null)
  const [messages, setMessages] = useState<Message[]>([])
  const [draft, setDraft] = useState('')
  const [workspaceId, setWorkspaceId] = useState('')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const bottom = useRef<HTMLDivElement>(null)

  useEffect(() => {
    api.listConversations().then(setConversations).catch(() => {})
    api.listWorkspaces().then(setWorkspaces).catch(() => {})
  }, [])

  useEffect(() => {
    if (!activeId) {
      setMessages([])
      return
    }
    api
      .conversation(activeId)
      .then((d) => setMessages(d.messages))
      .catch((e) => setError(e.message))
  }, [activeId])

  useEffect(() => {
    bottom.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const send = async () => {
    const content = draft.trim()
    if (!content || busy) return
    setBusy(true)
    setError(null)
    setDraft('')
    try {
      const result = await api.chat(
        content,
        activeId ?? undefined,
        activeId ? undefined : workspaceId || undefined,
      )
      setMessages((prev) => [...prev, result.user_message, result.assistant_message])
      if (!activeId) {
        setActiveId(result.conversation.id)
        setConversations((prev) => [result.conversation, ...prev])
      }
    } catch (e) {
      setError((e as Error).message)
      setDraft(content)
    } finally {
      setBusy(false)
    }
  }

  const remove = async (id: string) => {
    await api.deleteConversation(id)
    setConversations((prev) => prev.filter((c) => c.id !== id))
    if (activeId === id) setActiveId(null)
  }

  return (
    <div className="flex h-[calc(100vh-3rem)] gap-4">
      <aside className="flex w-64 shrink-0 flex-col gap-2 overflow-y-auto">
        <button
          onClick={() => setActiveId(null)}
          className="rounded-md bg-stone-900 px-3 py-2 text-sm font-medium text-white hover:bg-stone-700"
        >
          New conversation
        </button>
        {conversations.map((conversation) => (
          <div
            key={conversation.id}
            className={`group flex items-center rounded-md border px-3 py-2 ${
              activeId === conversation.id
                ? 'border-stone-900 bg-white'
                : 'border-stone-200 bg-white hover:border-stone-400'
            }`}
          >
            <button
              onClick={() => setActiveId(conversation.id)}
              className="min-w-0 flex-1 truncate text-left text-sm"
            >
              {conversation.title}
            </button>
            <button
              onClick={() => remove(conversation.id)}
              className="ml-2 hidden text-xs text-stone-400 group-hover:block hover:text-red-600"
              title="Delete conversation"
            >
              ✕
            </button>
          </div>
        ))}
      </aside>

      <div className="flex min-w-0 flex-1 flex-col rounded-lg border border-stone-200 bg-white shadow-sm">
        <div className="min-h-0 flex-1 overflow-y-auto p-4">
          {messages.length === 0 && (
            <div className="mt-12 text-center text-sm text-stone-400">
              Ask anything — answers are grounded in your knowledge base, and every claim is
              labeled with where it came from.
            </div>
          )}
          <div className="flex flex-col gap-4">
            {messages.map((message) =>
              message.role === 'user' ? (
                <div key={message.id} className="self-end rounded-lg bg-stone-900 px-4 py-2 text-sm text-white">
                  {message.content}
                </div>
              ) : (
                <AssistantMessage key={message.id} message={message} />
              ),
            )}
          </div>
          <div ref={bottom} />
        </div>
        <div className="border-t border-stone-200 p-3">
          <ErrorNote error={error} />
          {!activeId && workspaces.length > 0 && (
            <div className="mb-2 flex items-center gap-2 text-xs text-stone-500">
              Scope to workspace:
              <select
                value={workspaceId}
                onChange={(e) => setWorkspaceId(e.target.value)}
                className="rounded-md border border-stone-300 px-2 py-1"
              >
                <option value="">All knowledge</option>
                {workspaces.map((workspace) => (
                  <option key={workspace.id} value={workspace.id}>
                    {workspace.name}
                  </option>
                ))}
              </select>
            </div>
          )}
          <div className="flex gap-2">
            <input
              value={draft}
              onChange={(e) => setDraft(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && send()}
              placeholder="Ask your knowledge base…"
              className="flex-1 rounded-md border border-stone-300 px-3 py-2 text-sm"
            />
            <button
              onClick={send}
              disabled={busy || !draft.trim()}
              className="rounded-md bg-stone-900 px-4 py-2 text-sm font-medium text-white disabled:opacity-40"
            >
              {busy ? <Spinner /> : 'Send'}
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}

function AssistantMessage({ message }: { message: Message }) {
  return (
    <div className="max-w-[85%] self-start rounded-lg border border-stone-200 bg-stone-50 px-4 py-3">
      <div className="text-sm leading-relaxed">
        {message.segments.length > 0
          ? message.segments.map((segment, index) => (
              <span
                key={index}
                className={
                  segment.source === 'pks'
                    ? 'rounded bg-emerald-100/70 box-decoration-clone px-0.5'
                    : ''
                }
                title={
                  segment.source === 'pks'
                    ? `From your knowledge (sources ${segment.source_numbers.join(', ')})`
                    : 'From general model knowledge'
                }
              >
                {segment.text}
                {segment.source === 'pks' && (
                  <sup className="ml-0.5 text-[10px] font-semibold text-emerald-700">
                    {segment.source_numbers.join(',')}
                  </sup>
                )}{' '}
              </span>
            ))
          : message.content}
      </div>
      {message.citations.length > 0 && <Citations citations={message.citations} />}
      <div className="mt-2 flex items-center gap-3 text-[10px] text-stone-400">
        <span>
          <span className="mr-1 inline-block h-2 w-2 rounded-sm bg-emerald-200" />
          your knowledge
        </span>
        <span>
          <span className="mr-1 inline-block h-2 w-2 rounded-sm bg-stone-200" />
          model knowledge
        </span>
      </div>
    </div>
  )
}

function Citations({ citations }: { citations: Citation[] }) {
  return (
    <div className="mt-2 border-t border-stone-200 pt-2">
      {citations.map((citation) => (
        <div key={citation.number} className="text-xs text-stone-500">
          <span className="font-semibold text-emerald-700">[{citation.number}]</span>{' '}
          {citation.kind === 'chunk' ? 'passage from ' : 'knowledge: '}
          <span className="font-medium text-stone-700">{citation.title}</span>
          {citation.structure_path ? ` · ${citation.structure_path}` : ''}
        </div>
      ))}
    </div>
  )
}
