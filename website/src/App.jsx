import { useEffect, useMemo, useState } from 'react'

const DEFAULT_DATASET = 'production'
const DEFAULT_TYPE = 'post'

function parseDeliveryResponse(json) {
  if (Array.isArray(json)) return json
  if (Array.isArray(json?.result)) return json.result
  if (Array.isArray(json?.data)) return json.data.map((entry) => ({
    _id: entry.id,
    _createdAt: entry.createdAt,
    _updatedAt: entry.updatedAt,
    ...entry.data,
  }))
  return []
}

function App() {
  const [dataset, setDataset] = useState(DEFAULT_DATASET)
  const [contentType, setContentType] = useState(DEFAULT_TYPE)
  const [queryMode, setQueryMode] = useState(false)
  const [query, setQuery] = useState('*[_type=="post"]{title,slug,summary}')
  const [deliveryToken, setDeliveryToken] = useState('')
  const [items, setItems] = useState([])
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const endpoint = useMemo(() => {
    if (queryMode) {
      const encoded = encodeURIComponent(query)
      return `/api/delivery/query?dataset=${encodeURIComponent(dataset)}&query=${encoded}`
    }
    return `/api/delivery/${encodeURIComponent(dataset)}/${encodeURIComponent(contentType)}`
  }, [dataset, contentType, queryMode, query])

  async function fetchContent() {
    setLoading(true)
    setError('')
    try {
      const response = await fetch(endpoint, {
        headers: deliveryToken ? { Authorization: `Bearer ${deliveryToken}` } : {},
      })

      const json = await response.json()
      if (!response.ok) {
        throw new Error(json?.error || `Request failed (${response.status})`)
      }

      setItems(parseDeliveryResponse(json))
    } catch (err) {
      setError(err.message)
      setItems([])
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchContent()
  }, [])

  return (
    <main style={{ maxWidth: 960, margin: '0 auto', padding: 16 }}>
      <header style={{ marginBottom: 16 }}>
        <h1 style={{ margin: 0 }}>CMS Test Website</h1>
        <p style={{ color: '#475569' }}>
          This demo website consumes your headless CMS delivery API. Update content in admin and click Refresh.
        </p>
      </header>

      <section style={{ background: '#fff', border: '1px solid #e2e8f0', borderRadius: 8, padding: 12, marginBottom: 16 }}>
        <h2 style={{ marginTop: 0 }}>Content source</h2>
        <div style={{ display: 'grid', gap: 8, gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))' }}>
          <label>
            Dataset
            <input value={dataset} onChange={(e) => setDataset(e.target.value)} style={{ width: '100%' }} />
          </label>
          <label>
            Content type
            <input value={contentType} onChange={(e) => setContentType(e.target.value)} style={{ width: '100%' }} disabled={queryMode} />
          </label>
          <label>
            Mode
            <select value={queryMode ? 'query' : 'list'} onChange={(e) => setQueryMode(e.target.value === 'query')} style={{ width: '100%' }}>
              <option value="list">List endpoint</option>
              <option value="query">Sanity-like query</option>
            </select>
          </label>
          <label>
            Delivery token (optional)
            <input value={deliveryToken} onChange={(e) => setDeliveryToken(e.target.value)} style={{ width: '100%' }} placeholder="cms_xxx..." />
          </label>
        </div>

        {queryMode && (
          <label style={{ display: 'block', marginTop: 8 }}>
            Query
            <input value={query} onChange={(e) => setQuery(e.target.value)} style={{ width: '100%' }} />
          </label>
        )}

        <p style={{ marginTop: 8, fontSize: 12, color: '#64748b' }}>
          Endpoint: <code>{endpoint}</code>
        </p>

        <button onClick={fetchContent} disabled={loading} style={{ padding: '8px 12px', borderRadius: 6, border: 0, background: '#0f172a', color: '#fff' }}>
          {loading ? 'Loading...' : 'Refresh from CMS'}
        </button>
      </section>

      {error && (
        <p style={{ background: '#fef2f2', color: '#b91c1c', border: '1px solid #fecaca', borderRadius: 8, padding: 10 }}>
          {error}
        </p>
      )}

      <section style={{ display: 'grid', gap: 12 }}>
        {items.length === 0 && !loading && !error && (
          <article style={{ background: '#fff', border: '1px solid #e2e8f0', borderRadius: 8, padding: 16 }}>
            <h3 style={{ marginTop: 0 }}>No entries found</h3>
            <p>Create/publish entries in admin for this dataset and type, then refresh.</p>
          </article>
        )}

        {items.map((item, index) => (
          <article key={item._id || index} style={{ background: '#fff', border: '1px solid #e2e8f0', borderRadius: 8, padding: 16 }}>
            <h3 style={{ marginTop: 0 }}>{item.title || item.name || item.slug || item._id || `Entry ${index + 1}`}</h3>
            {item.summary && <p style={{ color: '#334155' }}>{item.summary}</p>}
            <pre style={{ marginTop: 8, background: '#f8fafc', padding: 10, borderRadius: 6, overflow: 'auto', fontSize: 12 }}>
              {JSON.stringify(item, null, 2)}
            </pre>
          </article>
        ))}
      </section>
    </main>
  )
}

export default App
