import cytoscape from 'cytoscape'
import { useEffect, useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { api } from '../api'
import { TYPE_COLORS } from '../components/ui'
import type { GraphOut } from '../types'

export default function GraphPage() {
  const container = useRef<HTMLDivElement>(null)
  const navigate = useNavigate()
  const [graph, setGraph] = useState<GraphOut | null>(null)

  useEffect(() => {
    api.graph().then(setGraph).catch(() => setGraph({ nodes: [], edges: [] }))
  }, [])

  useEffect(() => {
    if (!graph || !container.current) return
    const cy = cytoscape({
      container: container.current,
      elements: [
        ...graph.nodes.map((node) => ({
          data: { id: node.id, label: node.name, type: node.type },
        })),
        ...graph.edges.map((edge) => ({
          data: {
            id: edge.id,
            source: edge.from_id,
            target: edge.to_id,
            label: edge.type,
          },
        })),
      ],
      style: [
        {
          selector: 'node',
          style: {
            label: 'data(label)',
            'background-color': (el: cytoscape.NodeSingular) =>
              TYPE_COLORS[el.data('type') as keyof typeof TYPE_COLORS] ?? '#57534e',
            color: '#1c1917',
            'font-size': '11px',
            'text-valign': 'bottom',
            'text-margin-y': 4,
            width: 24,
            height: 24,
          },
        },
        {
          selector: 'edge',
          style: {
            label: 'data(label)',
            'font-size': '8px',
            color: '#78716c',
            'text-rotation': 'autorotate',
            width: 1.5,
            'line-color': '#d6d3d1',
            'target-arrow-shape': 'triangle',
            'target-arrow-color': '#d6d3d1',
            'curve-style': 'bezier',
          },
        },
      ],
      layout: { name: 'cose', animate: false, padding: 40 },
    })
    cy.on('tap', 'node', (event) => navigate(`/knowledge/${event.target.id()}`))
    return () => cy.destroy()
  }, [graph, navigate])

  return (
    <div className="flex h-[calc(100vh-3rem)] flex-col">
      <div className="mb-2 flex items-baseline justify-between">
        <h1 className="text-xl font-bold">Knowledge graph</h1>
        {graph && (
          <span className="text-sm text-stone-500">
            {graph.nodes.length} objects · {graph.edges.length} relationships — click a node to
            inspect it
          </span>
        )}
      </div>
      <div
        ref={container}
        className="min-h-0 flex-1 rounded-lg border border-stone-200 bg-white shadow-sm"
      />
    </div>
  )
}
