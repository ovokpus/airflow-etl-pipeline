import { useCallback, useEffect, useMemo, useState } from 'react'
import { get, triggerRun, type Book, type DagInfo, type LakeZone, type Run, type StockRow, type Summary } from './api'

const AIRFLOW_UI = `${location.protocol}//${location.hostname}:8080`
const TASK_ORDER = ['dummy_task', 'collect_raw_books', 'refine_books', 'collect_raw_stocks', 'refine_stocks', 'load_warehouse']

const fmtDate = (s?: string | null) => (s ? new Date(s).toLocaleString() : '—')
const fmtDay = (s: string) => s.slice(0, 10)
const fmtBytes = (b: number) => (b > 1024 * 1024 ? `${(b / 1048576).toFixed(1)} MB` : `${(b / 1024).toFixed(1)} KB`)
const duration = (r: Run) =>
  r.start_date && r.end_date ? `${((+new Date(r.end_date) - +new Date(r.start_date)) / 1000).toFixed(0)} s` : r.start_date ? 'running…' : '—'

function Pill({ state }: { state: string | null }) {
  return <span className={`pill ${state ?? 'none'}`}>{state ?? 'no status'}</span>
}

function Sparkline({ rows }: { rows: StockRow[] }) {
  const w = 220, h = 48
  const closes = rows.map(r => r.close)
  const lo = Math.min(...closes), hi = Math.max(...closes)
  const pts = closes.map((c, i) => `${(i / Math.max(1, closes.length - 1)) * w},${h - ((c - lo) / (hi - lo || 1)) * (h - 6) - 3}`).join(' ')
  const up = closes[closes.length - 1] >= closes[0]
  return (
    <svg width={w} height={h} className="spark">
      <polyline points={pts} fill="none" stroke={up ? '#16a34a' : '#dc2626'} strokeWidth={2} />
      {closes.map((c, i) => (
        <circle key={i} r={2.5} fill={up ? '#16a34a' : '#dc2626'}
          cx={(i / Math.max(1, closes.length - 1)) * w} cy={h - ((c - lo) / (hi - lo || 1)) * (h - 6) - 3} />
      ))}
    </svg>
  )
}

export default function App() {
  const [dag, setDag] = useState<DagInfo | null>(null)
  const [runs, setRuns] = useState<Run[]>([])
  const [summary, setSummary] = useState<Summary | null>(null)
  const [stocks, setStocks] = useState<StockRow[]>([])
  const [books, setBooks] = useState<Book[]>([])
  const [lake, setLake] = useState<LakeZone[]>([])
  const [error, setError] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)

  const load = useCallback(async () => {
    try {
      const [d, r, s, st, b, l] = await Promise.all([
        get<DagInfo>('/api/dag'), get<Run[]>('/api/runs'), get<Summary>('/api/summary'),
        get<StockRow[]>('/api/stocks'), get<Book[]>('/api/books'), get<LakeZone[]>('/api/lake'),
      ])
      setDag(d); setRuns(r); setSummary(s); setStocks(st); setBooks(b); setLake(l); setError(null)
    } catch (e) {
      setError(String(e))
    }
  }, [])

  useEffect(() => {
    load()
    const t = setInterval(load, 10000)
    return () => clearInterval(t)
  }, [load])

  const byTicker = useMemo(() => {
    const m = new Map<string, StockRow[]>()
    for (const r of stocks) m.set(r.ticker_name, [...(m.get(r.ticker_name) ?? []), r])
    return [...m.entries()].sort(([a], [b]) => a.localeCompare(b))
  }, [stocks])

  const onTrigger = async () => {
    setBusy(true)
    try { await triggerRun(); await load() } catch (e) { setError(String(e)) } finally { setBusy(false) }
  }

  const latest = runs[0]

  return (
    <div className="page">
      <header>
        <div>
          <h1>📦 ETL Pipeline Viewer</h1>
          <p className="sub">Open Library books + Yahoo Finance stocks → data lake → Postgres warehouse, orchestrated by Airflow</p>
        </div>
        <div className="actions">
          <a className="btn ghost" href={AIRFLOW_UI} target="_blank" rel="noreferrer">Open Airflow UI ↗</a>
          <button className="btn" onClick={onTrigger} disabled={busy}>{busy ? 'Triggering…' : '▶ Trigger run'}</button>
        </div>
      </header>

      {error && <div className="error">⚠️ {error}</div>}

      <section className="tiles">
        <div className="tile"><span>DAG</span><b>{dag?.dag_id ?? '—'}</b><small>{dag ? `${dag.schedule ?? 'manual'} · ${dag.is_paused ? 'paused' : 'active'}` : ''}</small></div>
        <div className="tile"><span>Latest run</span><b>{latest ? <Pill state={latest.state} /> : '—'}</b><small>{latest ? fmtDate(latest.start_date) : 'no runs yet'}</small></div>
        <div className="tile"><span>Warehouse: books</span><b>{summary?.books ?? 0}</b><small>distinct editions</small></div>
        <div className="tile"><span>Warehouse: stock bars</span><b>{summary?.stocks_rows ?? 0}</b><small>{summary?.tickers ?? 0} tickers{summary?.first_date ? ` · ${fmtDay(summary.first_date)} → ${fmtDay(summary.last_date!)}` : ''}</small></div>
        <div className="tile"><span>Last load</span><b>{summary?.last_load ? fmtDate(summary.last_load.loaded_at) : '—'}</b><small>{summary?.last_load?.run_id ?? ''}</small></div>
      </section>

      <section className="card">
        <h2>Recent DAG runs</h2>
        {runs.length === 0 ? <p className="muted">No runs yet. Click “Trigger run”.</p> : (
          <table>
            <thead><tr><th>Run</th><th>State</th><th>Started</th><th>Duration</th>{TASK_ORDER.map(t => <th key={t} className="task-h">{t.replace(/_/g, ' ')}</th>)}</tr></thead>
            <tbody>
              {runs.map(r => {
                const ts = new Map(r.tasks.map(t => [t.task_id, t]))
                return (
                  <tr key={r.run_id}>
                    <td className="mono">{r.run_id.replace(/\+00:00$/, '')}</td>
                    <td><Pill state={r.state} /></td>
                    <td>{fmtDate(r.start_date)}</td>
                    <td>{duration(r)}</td>
                    {TASK_ORDER.map(t => <td key={t}><span className={`dot ${ts.get(t)?.state ?? 'none'}`} title={`${t}: ${ts.get(t)?.state ?? 'no status'}`} /></td>)}
                  </tr>
                )
              })}
            </tbody>
          </table>
        )}
      </section>

      <div className="grid2">
        <section className="card">
          <h2>Stocks in the warehouse</h2>
          {byTicker.length === 0 ? <p className="muted">No stock data loaded yet.</p> : (
            <table>
              <thead><tr><th>Ticker</th><th>Bars</th><th>Last date</th><th>Last close</th><th>Trend</th></tr></thead>
              <tbody>
                {byTicker.map(([t, rows]) => (
                  <tr key={t}>
                    <td><b>{t}</b></td><td>{rows.length}</td><td>{fmtDay(rows[rows.length - 1].date)}</td>
                    <td>${rows[rows.length - 1].close.toFixed(2)}</td><td><Sparkline rows={rows} /></td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </section>

        <section className="card">
          <h2>Data lake</h2>
          <table>
            <thead><tr><th>Zone</th><th>Files</th><th>Size</th><th>Latest file</th></tr></thead>
            <tbody>{lake.map(z => <tr key={z.zone}><td className="mono">{z.zone}</td><td>{z.files}</td><td>{fmtBytes(z.bytes)}</td><td className="mono small">{z.latest ?? '—'}</td></tr>)}</tbody>
          </table>
          <h2 style={{ marginTop: 20 }}>DAG tasks</h2>
          <div className="flow">{dag?.tasks.map(t => <span key={t.task_id} className="node">{t.task_id}{t.downstream.length ? ` → ${t.downstream.join(', ')}` : ''}</span>)}</div>
        </section>
      </div>

      <section className="card">
        <h2>Books in the warehouse</h2>
        {books.length === 0 ? <p className="muted">No book data loaded yet.</p> : (
          <table>
            <thead><tr><th>Open Library ID</th><th>Title</th><th>Pages</th><th>Published</th><th>Publisher</th><th title="Earliest collection; books first collected over 12 months ago are not re-fetched">First collected</th></tr></thead>
            <tbody>{books.map(b => (
              <tr key={b.id}>
                <td className="mono"><a href={`https://openlibrary.org/books/${b.id}`} target="_blank" rel="noreferrer">{b.id}</a></td>
                <td>{b.title}{b.subtitle ? <span className="muted">: {b.subtitle}</span> : null}</td>
                <td>{b.number_of_pages ?? '—'}</td><td>{b.publish_date ?? '—'}</td>
                <td>{b.publishers?.replace(/\|/g, ', ') ?? '—'}</td><td>{fmtDay(b.collect_date)}</td>
              </tr>
            ))}</tbody>
          </table>
        )}
      </section>
      <footer>Data refreshes every 10 s · API docs at <a href={`${location.protocol}//${location.hostname}:8000/docs`}>:8000/docs</a></footer>
    </div>
  )
}
