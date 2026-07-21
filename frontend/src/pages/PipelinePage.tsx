import { useCallback, useEffect, useState } from 'react'
import { api } from '../api'
import { Card, SectionTitle } from '../components/ui'
import type { Job } from '../types'

export default function PipelinePage() {
  const [counts, setCounts] = useState<Record<string, number>>({})
  const [jobs, setJobs] = useState<Job[]>([])

  const refresh = useCallback(() => {
    api
      .jobs()
      .then((d) => {
        setCounts(d.counts)
        setJobs(d.jobs)
      })
      .catch(() => {})
  }, [])

  useEffect(() => {
    refresh()
    const timer = setInterval(refresh, 2000)
    return () => clearInterval(timer)
  }, [refresh])

  return (
    <div className="mx-auto max-w-4xl">
      <h1 className="mb-4 text-xl font-bold">Pipeline</h1>
      <div className="mb-4 grid grid-cols-4 gap-3">
        {(['queued', 'running', 'done', 'failed'] as const).map((status) => (
          <Card key={status} className="text-center">
            <div
              className={`text-2xl font-bold ${
                status === 'failed' && (counts[status] ?? 0) > 0
                  ? 'text-red-700'
                  : 'text-stone-900'
              }`}
            >
              {counts[status] ?? 0}
            </div>
            <div className="text-xs text-stone-500 uppercase">{status}</div>
          </Card>
        ))}
      </div>
      <Card>
        <SectionTitle>Recent jobs</SectionTitle>
        <table className="w-full text-sm">
          <thead>
            <tr className="text-left text-xs text-stone-500">
              <th className="py-1 pr-4 font-medium">stage</th>
              <th className="py-1 pr-4 font-medium">status</th>
              <th className="py-1 pr-4 font-medium">attempts</th>
              <th className="py-1 font-medium">updated</th>
            </tr>
          </thead>
          <tbody>
            {jobs.map((job) => (
              <tr key={job.id} className="border-t border-stone-100">
                <td className="py-1.5 pr-4 font-mono text-xs">{job.type}</td>
                <td
                  className={`py-1.5 pr-4 ${
                    job.status === 'done'
                      ? 'text-emerald-700'
                      : job.status === 'failed'
                        ? 'text-red-700'
                        : 'text-amber-700'
                  }`}
                >
                  {job.status}
                  {job.error && (
                    <span className="ml-2 text-xs text-red-600">{job.error.slice(0, 80)}</span>
                  )}
                </td>
                <td className="py-1.5 pr-4">{job.attempts}</td>
                <td className="py-1.5 text-xs text-stone-500">
                  {new Date(job.updated_at).toLocaleString()}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {jobs.length === 0 && <div className="text-sm text-stone-500">No jobs yet.</div>}
      </Card>
    </div>
  )
}
