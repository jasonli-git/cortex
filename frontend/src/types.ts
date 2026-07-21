// API types, mirroring the backend's Pydantic models.

export type ResourceStatus = 'pending' | 'processing' | 'ready' | 'failed'
export type KnowledgeObjectType =
  | 'concept'
  | 'person'
  | 'organization'
  | 'place'
  | 'event'
  | 'summary'

export interface Resource {
  id: string
  type: 'pdf' | 'markdown' | 'text' | 'note'
  title: string
  status: ResourceStatus
  relationship: 'active_learning' | 'reference'
  error: string | null
  created_at: string
  updated_at: string
}

export interface ResourceChunk {
  id: string
  resource_id: string
  ordinal: number
  structure_path: string | null
  text: string
  token_count: number | null
}

export interface Job {
  id: string
  type: string
  status: 'queued' | 'running' | 'done' | 'failed'
  attempts: number
  error: string | null
}

export interface ResourceStatusOut {
  resource: Resource
  jobs: Job[]
}

export interface IngestResult {
  resource: Resource
  created: boolean
}

export interface KnowledgeObject {
  id: string
  type: KnowledgeObjectType
  name: string
  description: string
  aliases: string[]
  metadata: Record<string, unknown>
  version: number
  created_at: string
  updated_at: string
}

export interface Relationship {
  id: string
  from_id: string
  to_id: string
  type: string
  confidence: number
  created_by: string
}

export interface Provenance {
  id: string
  resource_id: string
  chunk_id: string | null
  quote: string | null
}

export interface KnowledgeObjectDetail {
  object: KnowledgeObject
  relationships: Relationship[]
  provenance: Provenance[]
}

export interface KnowledgeVersion {
  version: number
  operation: 'created' | 'updated' | 'deleted'
  changed_by: string
  created_at: string
}

export interface GraphOut {
  nodes: KnowledgeObject[]
  edges: Relationship[]
}

export interface SearchResponse {
  query: string
  knowledge: { score: number; object: KnowledgeObject }[]
  chunks: {
    score: number
    chunk: ResourceChunk
    resource_id: string
    resource_title: string
  }[]
}

export interface Segment {
  text: string
  source: 'pks' | 'model'
  source_numbers: number[]
}

export interface Citation {
  number: number
  kind: 'chunk' | 'knowledge_object'
  id: string
  title: string
  resource_id: string | null
  structure_path: string | null
  excerpt: string | null
}

export interface Message {
  id: string
  conversation_id: string
  role: 'user' | 'assistant'
  content: string
  segments: Segment[]
  citations: Citation[]
  created_at: string
}

export interface Conversation {
  id: string
  workspace_id: string | null
  title: string
  updated_at: string
}

export interface ChatResult {
  conversation: Conversation
  user_message: Message
  assistant_message: Message
}

export interface Workspace {
  id: string
  name: string
  description: string
}

export interface WorkspaceDetail {
  workspace: Workspace
  resources: Resource[]
  knowledge_objects: KnowledgeObject[]
  conversations: Conversation[]
}

export interface Health {
  status: string
  version: string
  ai_enabled: boolean
}
