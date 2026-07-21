import type {
  ChatResult,
  Conversation,
  GraphOut,
  Health,
  IngestResult,
  Job,
  KnowledgeObjectDetail,
  KnowledgeVersion,
  Message,
  Resource,
  ResourceChunk,
  ResourceStatusOut,
  SearchResponse,
  Workspace,
  WorkspaceDetail,
} from './types'

async function request<T>(url: string, init?: RequestInit): Promise<T> {
  const response = await fetch(url, init)
  if (!response.ok) {
    let detail = response.statusText
    try {
      detail = (await response.json()).detail ?? detail
    } catch {
      /* non-JSON error body */
    }
    throw new Error(detail)
  }
  if (response.status === 204) return undefined as T
  return response.json()
}

const json = (body: unknown): RequestInit => ({
  method: 'POST',
  headers: { 'content-type': 'application/json' },
  body: JSON.stringify(body),
})

export const api = {
  health: () => request<Health>('/api/health'),

  // Resources
  listResources: () => request<Resource[]>('/api/resources'),
  resourceStatus: (id: string) => request<ResourceStatusOut>(`/api/resources/${id}/status`),
  resourceChunks: (id: string) => request<ResourceChunk[]>(`/api/resources/${id}/chunks`),
  upload: (file: File, workspaceId?: string) => {
    const form = new FormData()
    form.append('file', file)
    if (workspaceId) form.append('workspace_id', workspaceId)
    return request<IngestResult>('/api/resources/upload', { method: 'POST', body: form })
  },
  createNote: (title: string, content: string, workspaceId?: string) =>
    request<IngestResult>(
      '/api/resources/notes',
      json({ title, content, workspace_id: workspaceId ?? null }),
    ),
  reprocess: (id: string) =>
    request<Resource>(`/api/resources/${id}/reprocess`, { method: 'POST' }),
  jobs: () => request<{ counts: Record<string, number>; jobs: Job[] }>('/api/jobs'),

  // Knowledge
  knowledgeDetail: (id: string) => request<KnowledgeObjectDetail>(`/api/knowledge/${id}`),
  knowledgeHistory: (id: string) => request<KnowledgeVersion[]>(`/api/knowledge/${id}/history`),
  graph: () => request<GraphOut>('/api/knowledge/graph'),
  neighborhood: (id: string, depth = 1) =>
    request<GraphOut>(`/api/knowledge/${id}/graph?depth=${depth}`),

  // Search
  search: (q: string, workspaceId?: string) => {
    const params = new URLSearchParams({ q })
    if (workspaceId) params.set('workspace_id', workspaceId)
    return request<SearchResponse>(`/api/search?${params}`)
  },

  // Chat
  chat: (content: string, conversationId?: string, workspaceId?: string) =>
    request<ChatResult>(
      '/api/chat',
      json({
        content,
        conversation_id: conversationId ?? null,
        workspace_id: workspaceId ?? null,
      }),
    ),
  listConversations: () => request<Conversation[]>('/api/chat/conversations'),
  conversation: (id: string) =>
    request<{ conversation: Conversation; messages: Message[] }>(`/api/chat/conversations/${id}`),
  deleteConversation: (id: string) =>
    request<void>(`/api/chat/conversations/${id}`, { method: 'DELETE' }),

  // Workspaces
  listWorkspaces: () => request<Workspace[]>('/api/workspaces'),
  createWorkspace: (name: string, description: string) =>
    request<Workspace>('/api/workspaces', json({ name, description })),
  workspaceDetail: (id: string) => request<WorkspaceDetail>(`/api/workspaces/${id}`),
  deleteWorkspace: (id: string) => request<void>(`/api/workspaces/${id}`, { method: 'DELETE' }),
  detachRef: (workspaceId: string, objectType: string, objectId: string) =>
    request<void>(`/api/workspaces/${workspaceId}/refs/${objectType}/${objectId}`, {
      method: 'DELETE',
    }),
}
