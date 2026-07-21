import { useState } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../api'
import { Card, ErrorNote, SectionTitle, Spinner, TypeBadge } from '../components/ui'
import type { SearchResponse } from '../types'

export default function SearchPage() {
  const [query, setQuery] = useState('')
  const [result, setResult] = useState<SearchResponse | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const run = async () => {
    if (!query.trim()) return
    setLoading(true)
    setError(null)
    try {
      setResult(await api.search(query))
    } catch (e) {
      setError((e as Error).message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="mx-auto max-w-4xl">
      <h1 className="mb-4 text-xl font-bold">Search</h1>
      <div className="mb-4 flex gap-2">
        <input
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && run()}
          placeholder="Search your knowledge — by meaning or by keyword"
          className="flex-1 rounded-md border border-stone-300 bg-white px-4 py-2.5 text-sm"
        />
        <button
          onClick={run}
          className="rounded-md bg-stone-900 px-4 py-2 text-sm font-medium text-white hover:bg-stone-700"
        >
          {loading ? <Spinner /> : 'Search'}
        </button>
      </div>
      <ErrorNote error={error} />
      {result && (
        <div className="flex flex-col gap-6">
          <section>
            <SectionTitle>Knowledge ({result.knowledge.length})</SectionTitle>
            <div className="flex flex-col gap-2">
              {result.knowledge.map(({ object }) => (
                <Link key={object.id} to={`/knowledge/${object.id}`}>
                  <Card className="hover:border-stone-400">
                    <div className="flex items-center gap-2">
                      <TypeBadge type={object.type} />
                      <span className="font-medium">{object.name}</span>
                      {object.aliases.length > 0 && (
                        <span className="text-xs text-stone-400">
                          aka {object.aliases.join(', ')}
                        </span>
                      )}
                    </div>
                    {object.description && (
                      <p className="mt-1 text-sm text-stone-600">{object.description}</p>
                    )}
                  </Card>
                </Link>
              ))}
              {result.knowledge.length === 0 && (
                <div className="text-sm text-stone-500">No knowledge objects matched.</div>
              )}
            </div>
          </section>
          <section>
            <SectionTitle>Passages ({result.chunks.length})</SectionTitle>
            <div className="flex flex-col gap-2">
              {result.chunks.map(({ chunk, resource_title }) => (
                <Card key={chunk.id}>
                  <div className="mb-1 text-xs font-medium text-stone-500">
                    {resource_title}
                    {chunk.structure_path ? ` · ${chunk.structure_path}` : ''}
                  </div>
                  <p className="text-sm text-stone-700">
                    {chunk.text.length > 500 ? `${chunk.text.slice(0, 500)}…` : chunk.text}
                  </p>
                </Card>
              ))}
              {result.chunks.length === 0 && (
                <div className="text-sm text-stone-500">No passages matched.</div>
              )}
            </div>
          </section>
        </div>
      )}
    </div>
  )
}
