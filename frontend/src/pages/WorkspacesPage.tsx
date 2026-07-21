import { useCallback, useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../api'
import { Card, ErrorNote, SectionTitle, StatusBadge, TypeBadge } from '../components/ui'
import type { Workspace, WorkspaceDetail } from '../types'

export default function WorkspacesPage() {
  const [workspaces, setWorkspaces] = useState<Workspace[]>([])
  const [selected, setSelected] = useState<string | null>(null)
  const [name, setName] = useState('')
  const [description, setDescription] = useState('')
  const [error, setError] = useState<string | null>(null)

  const refresh = useCallback(() => {
    api.listWorkspaces().then(setWorkspaces).catch((e) => setError(e.message))
  }, [])
  useEffect(refresh, [refresh])

  const create = async () => {
    setError(null)
    try {
      const workspace = await api.createWorkspace(name.trim(), description.trim())
      setName('')
      setDescription('')
      refresh()
      setSelected(workspace.id)
    } catch (e) {
      setError((e as Error).message)
    }
  }

  const remove = async (id: string) => {
    await api.deleteWorkspace(id)
    if (selected === id) setSelected(null)
    refresh()
  }

  return (
    <div className="mx-auto flex max-w-5xl gap-6">
      <div className="w-80 shrink-0">
        <h1 className="mb-4 text-xl font-bold">Workspaces</h1>
        <Card className="mb-4">
          <SectionTitle>New workspace</SectionTitle>
          <input
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="Name (e.g. American History)"
            className="mb-2 w-full rounded-md border border-stone-300 px-3 py-2 text-sm"
          />
          <input
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            placeholder="Description (optional)"
            className="mb-2 w-full rounded-md border border-stone-300 px-3 py-2 text-sm"
          />
          <ErrorNote error={error} />
          <button
            onClick={create}
            disabled={!name.trim()}
            className="rounded-md bg-stone-900 px-3 py-1.5 text-sm font-medium text-white disabled:opacity-40"
          >
            Create
          </button>
        </Card>
        <div className="flex flex-col gap-2">
          {workspaces.map((workspace) => (
            <div
              key={workspace.id}
              className={`group flex items-center rounded-lg border bg-white px-4 py-3 shadow-sm ${
                selected === workspace.id ? 'border-stone-900' : 'border-stone-200'
              }`}
            >
              <button
                onClick={() => setSelected(workspace.id)}
                className="min-w-0 flex-1 text-left"
              >
                <div className="truncate font-medium">{workspace.name}</div>
                {workspace.description && (
                  <div className="truncate text-xs text-stone-500">{workspace.description}</div>
                )}
              </button>
              <button
                onClick={() => remove(workspace.id)}
                className="ml-2 hidden text-xs text-stone-400 group-hover:block hover:text-red-600"
                title="Delete workspace (knowledge is kept)"
              >
                ✕
              </button>
            </div>
          ))}
        </div>
      </div>
      {selected && <WorkspaceContents id={selected} />}
    </div>
  )
}

function WorkspaceContents({ id }: { id: string }) {
  const [detail, setDetail] = useState<WorkspaceDetail | null>(null)

  const refresh = useCallback(() => {
    api.workspaceDetail(id).then(setDetail).catch(() => setDetail(null))
  }, [id])
  useEffect(refresh, [refresh])

  if (!detail) return null

  const detach = async (objectType: string, objectId: string) => {
    await api.detachRef(id, objectType, objectId)
    refresh()
  }

  return (
    <div className="min-w-0 flex-1">
      <h2 className="mb-1 text-lg font-bold">{detail.workspace.name}</h2>
      <p className="mb-4 text-sm text-stone-500">
        A workspace references knowledge — it never owns it. Removing something here never
        deletes it.
      </p>
      <div className="flex flex-col gap-4">
        <Card>
          <SectionTitle>Resources ({detail.resources.length})</SectionTitle>
          {detail.resources.map((resource) => (
            <div key={resource.id} className="flex items-center justify-between py-1 text-sm">
              <span className="min-w-0 truncate">{resource.title}</span>
              <span className="flex items-center gap-2">
                <StatusBadge status={resource.status} />
                <button
                  onClick={() => detach('resource', resource.id)}
                  className="text-xs text-stone-400 hover:text-red-600"
                >
                  remove
                </button>
              </span>
            </div>
          ))}
          {detail.resources.length === 0 && (
            <div className="text-sm text-stone-500">
              None yet — upload into this workspace from the Library, or via the API.
            </div>
          )}
        </Card>
        <Card>
          <SectionTitle>Knowledge objects ({detail.knowledge_objects.length})</SectionTitle>
          {detail.knowledge_objects.map((object) => (
            <div key={object.id} className="flex items-center justify-between py-1 text-sm">
              <Link
                to={`/knowledge/${object.id}`}
                className="flex min-w-0 items-center gap-2 hover:underline"
              >
                <TypeBadge type={object.type} />
                <span className="truncate">{object.name}</span>
              </Link>
              <button
                onClick={() => detach('knowledge_object', object.id)}
                className="text-xs text-stone-400 hover:text-red-600"
              >
                remove
              </button>
            </div>
          ))}
          {detail.knowledge_objects.length === 0 && (
            <div className="text-sm text-stone-500">No knowledge objects referenced.</div>
          )}
        </Card>
        <Card>
          <SectionTitle>Conversations ({detail.conversations.length})</SectionTitle>
          {detail.conversations.map((conversation) => (
            <div key={conversation.id} className="flex items-center justify-between py-1 text-sm">
              <span className="min-w-0 truncate">{conversation.title}</span>
              <button
                onClick={() => detach('conversation', conversation.id)}
                className="text-xs text-stone-400 hover:text-red-600"
              >
                remove
              </button>
            </div>
          ))}
          {detail.conversations.length === 0 && (
            <div className="text-sm text-stone-500">No conversations referenced.</div>
          )}
        </Card>
      </div>
    </div>
  )
}
