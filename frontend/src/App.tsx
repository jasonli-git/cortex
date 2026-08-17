import { useEffect, useState } from 'react'
import { NavLink, Route, Routes } from 'react-router-dom'
import { api } from './api'
import type { Health } from './types'
import ChatPage from './pages/ChatPage'
import GraphPage from './pages/GraphPage'
import KnowledgePage from './pages/KnowledgePage'
import LibraryPage from './pages/LibraryPage'
import PipelinePage from './pages/PipelinePage'
import SearchPage from './pages/SearchPage'
import WorkspacesPage from './pages/WorkspacesPage'

const NAV = [
  { to: '/', label: 'Library' },
  { to: '/search', label: 'Search' },
  { to: '/graph', label: 'Graph' },
  { to: '/chat', label: 'Chat' },
  { to: '/workspaces', label: 'Workspaces' },
  { to: '/pipeline', label: 'Pipeline' },
]

export default function App() {
  const [health, setHealth] = useState<Health | null>(null)
  useEffect(() => {
    api.health().then(setHealth).catch(() => setHealth(null))
  }, [])

  return (
    <div className="flex min-h-screen">
      <aside className="flex w-52 shrink-0 flex-col border-r border-stone-200 bg-white px-4 py-6">
        <div className="mb-8">
          <div className="text-lg font-bold">Cortex</div>
          <div className="text-xs text-stone-500">AI personal knowledge system</div>
        </div>
        <nav className="flex flex-col gap-1">
          {NAV.map(({ to, label }) => (
            <NavLink
              key={to}
              to={to}
              end={to === '/'}
              className={({ isActive }) =>
                `rounded-md px-3 py-2 text-sm font-medium ${
                  isActive ? 'bg-stone-900 text-white' : 'text-stone-600 hover:bg-stone-100'
                }`
              }
            >
              {label}
            </NavLink>
          ))}
        </nav>
        <div className="mt-auto pt-6 text-xs text-stone-400">
          {health ? (
            <>
              v{health.version} · AI {health.ai_enabled ? 'on' : 'off'}
            </>
          ) : (
            'backend unreachable'
          )}
        </div>
      </aside>
      <main className="min-w-0 flex-1 p-6">
        <Routes>
          <Route path="/" element={<LibraryPage />} />
          <Route path="/search" element={<SearchPage />} />
          <Route path="/graph" element={<GraphPage />} />
          <Route path="/knowledge/:id" element={<KnowledgePage />} />
          <Route path="/chat" element={<ChatPage />} />
          <Route path="/workspaces" element={<WorkspacesPage />} />
          <Route path="/pipeline" element={<PipelinePage />} />
        </Routes>
      </main>
    </div>
  )
}
