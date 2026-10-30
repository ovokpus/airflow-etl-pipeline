export type Task = { task_id: string; state: string | null; duration: number | null; try_number: number }
export type Run = {
  run_id: string; run_type: string; state: string; logical_date: string
  start_date: string | null; end_date: string | null; tasks: Task[]
}
export type Summary = {
  books: number; stocks_rows: number; tickers: number; first_date?: string; last_date?: string
  last_load: { run_id: string; loaded_at: string; books_rows: number; stocks_rows: number } | null
}
export type StockRow = { ticker_name: string; date: string; open: number; high: number; low: number; close: number; volume: number }
export type Book = { id: string; title: string | null; subtitle: string | null; number_of_pages: number | null; publish_date: string | null; publishers: string | null; collect_date: string }
export type LakeZone = { zone: string; files: number; bytes: number; latest: string | null }
export type DagInfo = { dag_id: string; description: string; is_paused: boolean; schedule: string | null; next_run: string | null; tasks: { task_id: string; downstream: string[] }[] }

export async function get<T>(path: string): Promise<T> {
  const r = await fetch(path)
  if (!r.ok) throw new Error(`${path}: ${r.status} ${await r.text()}`)
  return r.json()
}

export async function triggerRun(): Promise<{ run_id: string }> {
  const r = await fetch('/api/runs', { method: 'POST' })
  if (!r.ok) throw new Error(`trigger failed: ${r.status}`)
  return r.json()
}
