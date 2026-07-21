import { TYPE_COLORS } from '../colors'
import type { KnowledgeObjectType, ResourceStatus } from '../types'

export function StatusBadge({ status }: { status: ResourceStatus }) {
  const styles: Record<ResourceStatus, string> = {
    pending: 'bg-stone-200 text-stone-600',
    processing: 'bg-amber-100 text-amber-800',
    ready: 'bg-emerald-100 text-emerald-800',
    failed: 'bg-red-100 text-red-800',
  }
  return (
    <span className={`rounded-full px-2 py-0.5 text-xs font-medium ${styles[status]}`}>
      {status}
    </span>
  )
}

export function TypeBadge({ type }: { type: KnowledgeObjectType }) {
  return (
    <span
      className="rounded-full px-2 py-0.5 text-xs font-medium text-white"
      style={{ backgroundColor: TYPE_COLORS[type] }}
    >
      {type}
    </span>
  )
}

export function Card({ children, className = '' }: { children: React.ReactNode; className?: string }) {
  return (
    <div className={`rounded-lg border border-stone-200 bg-white p-4 shadow-sm ${className}`}>
      {children}
    </div>
  )
}

export function SectionTitle({ children }: { children: React.ReactNode }) {
  return (
    <h2 className="mb-2 text-xs font-semibold tracking-wide text-stone-500 uppercase">
      {children}
    </h2>
  )
}

export function ErrorNote({ error }: { error: string | null }) {
  if (!error) return null
  return (
    <div className="rounded-md border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-800">
      {error}
    </div>
  )
}

export function Spinner() {
  return (
    <div className="h-4 w-4 animate-spin rounded-full border-2 border-stone-300 border-t-stone-700" />
  )
}
