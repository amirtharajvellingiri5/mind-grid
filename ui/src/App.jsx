import { useEffect, useState } from 'react'

const API = import.meta.env.VITE_API_URL ?? '/api'
const eurlex = (celex) => `https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:${celex}`

// turn "... [2] ..." into text with clickable source links
function AnswerText({ text }) {
  return text.split(/(\[\d+\])/).map((part, i) => {
    const m = part.match(/^\[(\d+)\]$/)
    return m ? <a key={i} href={`#src-${m[1]}`} className="cite">{part}</a> : part
  })
}

export default function App() {
  const [health, setHealth] = useState(null)
  const [question, setQuestion] = useState('')
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    fetch(`${API}/health`).then((r) => r.json()).then(setHealth).catch(() => setHealth(false))
  }, [])

  async function ask(e) {
    e.preventDefault()
    if (question.trim().length < 3) return
    setLoading(true)
    setError('')
    try {
      const r = await fetch(`${API}/ask`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question: question.trim() }),
      })
      if (!r.ok) throw new Error(`${r.status} ${await r.text()}`)
      setResult(await r.json())
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  const cited = new Set(result?.citations.map((c) => c.marker))

  return (
    <main>
      <header>
        <h1>GridMind</h1>
        <span className="muted">
          {health === null ? 'connecting…' : health ? `${health.documents} docs · ${health.chunks} chunks` : 'API unreachable'}
        </span>
      </header>

      <form onSubmit={ask}>
        <textarea
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && (e.metaKey || e.ctrlKey) && ask(e)}
          placeholder="Ask about EU energy-market regulation, e.g. What is insider information under REMIT?"
          rows={3}
          maxLength={2000}
        />
        <button disabled={loading || question.trim().length < 3}>{loading ? 'Thinking…' : 'Ask'}</button>
      </form>

      {error && <p className="error">{error}</p>}

      {result && (
        <>
          <section className="answer">
            <p><AnswerText text={result.answer} /></p>
            <p className="muted small">{result.model} · {result.latency_ms} ms</p>
          </section>

          <h2>Sources</h2>
          <ol className="sources">
            {result.retrieved.map((c, i) => (
              <li key={c.id} id={`src-${i + 1}`} className={cited.has(i + 1) ? 'cited' : ''}>
                <details>
                  <summary>
                    <b>[{i + 1}]</b> <a href={eurlex(c.document_id)} target="_blank" rel="noreferrer">{c.document_id}</a>
                    <span className="muted"> · chunk {c.seq} · score {c.score.toFixed(3)}</span>
                  </summary>
                  <pre>{c.text}</pre>
                </details>
              </li>
            ))}
          </ol>
        </>
      )}
    </main>
  )
}
