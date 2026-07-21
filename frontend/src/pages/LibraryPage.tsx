import { useCallback, useEffect, useRef, useState } from 'react'
import { api } from '../api'
import { Card, ErrorNote, SectionTitle, StatusBadge } from '../components/ui'
import type { Resource, ResourceChunk, ResourceStatusOut, Workspace } from '../types'

export default function LibraryPage() {
  const [resources, setResources] = useState<Resource[]>([])
  const [workspaces, setWorkspaces] = useState<Workspace[]>([])
  const [workspaceId, setWorkspaceId] = useState('')
  const [selected, setSelected] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [noteOpen, setNoteOpen] = useState(false)
  const fileInput = useRef<HTMLInputElement>(null)

  const refresh = useCallback(() => {
    api.listResources().then(setResources).catch((e) => setError(e.message))
  }, [])

  useEffect(() => {
    refresh()
    api.listWorkspaces().then(setWorkspaces).catch(() => {})
  }, [refresh])

  // Poll while anything is still being processed.
  const busy = resources.some((r) => r.status === 'pending' || r.status === 'processing')
  useEffect(() => {
    if (!busy) return
    const timer = setInterval(refresh, 1500)
    return () => clearInterval(timer)
  }, [busy, refresh])

  const onUpload = async (files: FileList | null) => {
    if (!files?.length) return
    setError(null)
    try {
      for (const file of Array.from(files)) await api.upload(file, workspaceId || undefined)
      refresh()
    } catch (e) {
      setError((e as Error).message)
    }
  }

  return (
    <div className="mx-auto flex max-w-5xl gap-6">
      <div className="min-w-0 flex-1">
        <div className="mb-4 flex items-center justify-between">
          <h1 className="text-xl font-bold">Library</h1>
          <div className="flex items-center gap-2">
            {workspaces.length > 0 && (
              <label className="flex items-center gap-1 text-xs text-stone-500">
                into
                <select
                  value={workspaceId}
                  onChange={(e) => setWorkspaceId(e.target.value)}
                  className="rounded-md border border-stone-300 bg-white px-2 py-1.5 text-xs"
                >
                  <option value="">no workspace</option>
                  {workspaces.map((workspace) => (
                    <option key={workspace.id} value={workspace.id}>
                      {workspace.name}
                    </option>
                  ))}
                </select>
              </label>
            )}
            <button
              onClick={() => setNoteOpen((v) => !v)}
              className="rounded-md border border-stone-300 bg-white px-3 py-1.5 text-sm font-medium hover:bg-stone-50"
            >
              New note
            </button>
            <button
              onClick={() => fileInput.current?.click()}
              className="rounded-md bg-stone-900 px-3 py-1.5 text-sm font-medium text-white hover:bg-stone-700"
            >
              Upload
            </button>
            <input
              ref={fileInput}
              type="file"
              multiple
              accept=".pdf,.md,.markdown,.txt"
              className="hidden"
              onChange={(e) => onUpload(e.target.files)}
            />
          </div>
        </div>
        <ErrorNote error={error} />
        {noteOpen && (
          <NoteForm
            workspaceId={workspaceId || undefined}
            onDone={() => (setNoteOpen(false), refresh())}
          />
        )}
        <div className="mt-3 flex flex-col gap-2">
          {resources.length === 0 && (
            <Card className="text-sm text-stone-500">
              Nothing here yet — upload a PDF, Markdown, or text file to start building your
              knowledge base.
            </Card>
          )}
          {resources.map((resource) => (
            <button
              key={resource.id}
              onClick={() => setSelected(selected === resource.id ? null : resource.id)}
              className={`rounded-lg border bg-white px-4 py-3 text-left shadow-sm hover:border-stone-400 ${
                selected === resource.id ? 'border-stone-900' : 'border-stone-200'
              }`}
            >
              <div className="flex items-center justify-between">
                <div className="min-w-0">
                  <div className="truncate font-medium">{resource.title}</div>
                  <div className="text-xs text-stone-500">
                    {resource.type} · {resource.relationship.replace('_', ' ')} ·{' '}
                    {new Date(resource.created_at).toLocaleString()}
                  </div>
                </div>
                <StatusBadge status={resource.status} />
              </div>
              {resource.error && (
                <div className="mt-1 text-xs text-red-700">{resource.error}</div>
              )}
            </button>
          ))}
        </div>
      </div>
      {selected && <ResourceDetail id={selected} onReprocessed={refresh} />}
    </div>
  )
}

function NoteForm({ workspaceId, onDone }: { workspaceId?: string; onDone: () => void }) {
  const [title, setTitle] = useState('')
  const [content, setContent] = useState('')
  const [error, setError] = useState<string | null>(null)

  const submit = async () => {
    try {
      await api.createNote(title, content, workspaceId)
      onDone()
    } catch (e) {
      setError((e as Error).message)
    }
  }

  return (
    <Card className="mb-3">
      <SectionTitle>New note (Markdown)</SectionTitle>
      <input
        value={title}
        onChange={(e) => setTitle(e.target.value)}
        placeholder="Title"
        className="mb-2 w-full rounded-md border border-stone-300 px-3 py-2 text-sm"
      />
      <textarea
        value={content}
        onChange={(e) => setContent(e.target.value)}
        placeholder="# Heading&#10;&#10;Your note…"
        rows={5}
        className="mb-2 w-full rounded-md border border-stone-300 px-3 py-2 font-mono text-sm"
      />
      <ErrorNote error={error} />
      <button
        onClick={submit}
        disabled={!title.trim() || !content.trim()}
        className="rounded-md bg-stone-900 px-3 py-1.5 text-sm font-medium text-white disabled:opacity-40"
      >
        Save note
      </button>
    </Card>
  )
}

function ResourceDetail({ id, onReprocessed }: { id: string; onReprocessed: () => void }) {
  const [status, setStatus] = useState<ResourceStatusOut | null>(null)
  const [chunks, setChunks] = useState<ResourceChunk[]>([])
  const [error, setError] = useState<string | null>(null)

  const load = useCallback(() => {
    api.resourceStatus(id).then(setStatus).catch(() => setStatus(null))
    api.resourceChunks(id).then(setChunks).catch(() => setChunks([]))
  }, [id])
  useEffect(load, [load])

  const reprocess = async () => {
    setError(null)
    try {
      await api.reprocess(id)
      onReprocessed()
      load()
    } catch (e) {
      setError((e as Error).message)
    }
  }

  if (!status) return null
  return (
    <div className="w-96 shrink-0">
      <Card>
        <div className="flex items-center justify-between">
          <SectionTitle>Pipeline</SectionTitle>
          <button
            onClick={reprocess}
            className="mb-2 rounded-md border border-stone-300 px-2 py-1 text-xs font-medium hover:bg-stone-50"
            title="Re-run the full pipeline from the stored original"
          >
            Reprocess
          </button>
        </div>
        <ErrorNote error={error} />
        <div className="flex flex-col gap-1">
          {status.jobs.map((job) => (
            <div key={job.id} className="flex items-center justify-between text-sm">
              <span className="font-mono text-xs">{job.type}</span>
              <span
                className={
                  job.status === 'done'
                    ? 'text-emerald-700'
                    : job.status === 'failed'
                      ? 'text-red-700'
                      : 'text-amber-700'
                }
              >
                {job.status}
                {job.attempts > 1 ? ` (${job.attempts}×)` : ''}
              </span>
            </div>
          ))}
          {status.jobs.length === 0 && (
            <div className="text-sm text-stone-500">No pipeline activity yet.</div>
          )}
        </div>
      </Card>
      <Card className="mt-3 max-h-[60vh] overflow-y-auto">
        <SectionTitle>Chunks ({chunks.length})</SectionTitle>
        <div className="flex flex-col gap-3">
          {chunks.map((chunk) => (
            <div key={chunk.id} className="border-l-2 border-stone-200 pl-3">
              {chunk.structure_path && (
                <div className="text-xs font-medium text-stone-500">{chunk.structure_path}</div>
              )}
              <div className="text-sm whitespace-pre-wrap text-stone-700">
                {chunk.text.length > 400 ? `${chunk.text.slice(0, 400)}…` : chunk.text}
              </div>
            </div>
          ))}
        </div>
      </Card>
    </div>
  )
}
