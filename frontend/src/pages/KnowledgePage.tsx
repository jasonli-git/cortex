import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { api } from '../api'
import { Card, ErrorNote, SectionTitle, TypeBadge } from '../components/ui'
import type {
  KnowledgeObject,
  KnowledgeObjectDetail,
  KnowledgeVersion,
  Resource,
} from '../types'

export default function KnowledgePage() {
  const { id } = useParams<{ id: string }>()
  const [detail, setDetail] = useState<KnowledgeObjectDetail | null>(null)
  const [history, setHistory] = useState<KnowledgeVersion[]>([])
  const [neighbors, setNeighbors] = useState<Map<string, KnowledgeObject>>(new Map())
  const [resources, setResources] = useState<Map<string, Resource>>(new Map())
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!id) return
    setError(null)
    api
      .knowledgeDetail(id)
      .then(async (d) => {
        setDetail(d)
        const graph = await api.neighborhood(id, 1)
        setNeighbors(new Map(graph.nodes.map((n) => [n.id, n])))
        const all = await api.listResources()
        setResources(new Map(all.map((r) => [r.id, r])))
      })
      .catch((e) => setError(e.message))
    api.knowledgeHistory(id).then(setHistory).catch(() => setHistory([]))
  }, [id])

  if (error) return <ErrorNote error={error} />
  if (!detail || !id) return null
  const { object, relationships, provenance } = detail

  return (
    <div className="mx-auto max-w-3xl">
      <div className="mb-1 flex items-center gap-2">
        <TypeBadge type={object.type} />
        <h1 className="text-xl font-bold">{object.name}</h1>
        <span className="text-xs text-stone-400">v{object.version}</span>
      </div>
      {object.aliases.length > 0 && (
        <div className="mb-2 text-sm text-stone-500">Also known as: {object.aliases.join(', ')}</div>
      )}
      {object.description && <p className="mb-4 text-stone-700">{object.description}</p>}

      <div className="flex flex-col gap-4">
        <Card>
          <SectionTitle>Relationships ({relationships.length})</SectionTitle>
          <div className="flex flex-col gap-1">
            {relationships.map((rel) => {
              const outgoing = rel.from_id === id
              const otherId = outgoing ? rel.to_id : rel.from_id
              const other = neighbors.get(otherId)
              return (
                <div key={rel.id} className="flex items-center gap-2 text-sm">
                  <span className="rounded bg-stone-100 px-1.5 py-0.5 font-mono text-xs text-stone-600">
                    {outgoing ? `${rel.type} →` : `← ${rel.type}`}
                  </span>
                  <Link to={`/knowledge/${otherId}`} className="font-medium hover:underline">
                    {other?.name ?? otherId}
                  </Link>
                  <span className="text-xs text-stone-400">
                    {(rel.confidence * 100).toFixed(0)}%
                  </span>
                </div>
              )
            })}
            {relationships.length === 0 && (
              <div className="text-sm text-stone-500">No relationships yet.</div>
            )}
          </div>
        </Card>

        <Card>
          <SectionTitle>Evidence ({provenance.length})</SectionTitle>
          <div className="flex flex-col gap-2">
            {provenance.map((prov) => (
              <div key={prov.id} className="border-l-2 border-emerald-300 pl-3 text-sm">
                {prov.quote ? (
                  <span className="text-stone-700">“{prov.quote}”</span>
                ) : (
                  <span className="text-stone-500">Whole resource</span>
                )}
                <span className="ml-2 text-xs text-stone-400">
                  — {resources.get(prov.resource_id)?.title ?? prov.resource_id}
                </span>
              </div>
            ))}
            {provenance.length === 0 && (
              <div className="text-sm text-stone-500">No recorded evidence.</div>
            )}
          </div>
        </Card>

        <Card>
          <SectionTitle>History</SectionTitle>
          <div className="flex flex-col gap-1">
            {history.map((version) => (
              <div key={`${version.version}-${version.operation}`} className="text-sm">
                <span className="font-mono text-xs text-stone-500">v{version.version}</span>{' '}
                {version.operation} by <span className="font-medium">{version.changed_by}</span>{' '}
                <span className="text-xs text-stone-400">
                  {new Date(version.created_at).toLocaleString()}
                </span>
              </div>
            ))}
          </div>
        </Card>
      </div>
    </div>
  )
}
