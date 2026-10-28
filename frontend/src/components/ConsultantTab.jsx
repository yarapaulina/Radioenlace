import { useEffect, useRef, useState } from 'react'
import Markdown from './Markdown'
import { api } from '../lib/api'

const QUICK = [
  ['Riscos & Mitigações', 'Quais os principais riscos de degradação deste enlace e como mitigá-los?'],
  ['Altura Mínima de Torres', 'Qual a altura mínima de torre recomendada considerando a curvatura da terra e o raio de Fresnel?'],
  ['Chuva & Polarização', 'Como a chuva afeta este enlace e qual polarização devo escolher?'],
  ['Tamanho de Antenas', 'Qual antena comercial (diâmetro em metros) é recomendada para este enlace?'],
]

export default function ConsultantTab({ params, apiKey }) {
  const [messages, setMessages] = useState([
    { role: 'assistant', text: '**Engenheiro de RF Virtual:** Olá! Pergunte sobre viabilidade, antenas, normas da ANATEL, multipercurso — ou use uma pergunta rápida acima.' },
  ])
  const [input, setInput] = useState('')
  const [busy, setBusy] = useState(false)
  const listRef = useRef(null)

  useEffect(() => {
    if (listRef.current) listRef.current.scrollTop = listRef.current.scrollHeight
  }, [messages, busy])

  const send = async (query) => {
    const q = query.trim()
    if (!q || busy) return
    setMessages((m) => [...m, { role: 'user', text: q }])
    setInput('')
    setBusy(true)
    try {
      const res = await api.consult(params, q, apiKey)
      setMessages((m) => [...m, { role: 'assistant', text: res.response, source: res.model }])
    } catch (err) {
      setMessages((m) => [...m, { role: 'assistant', text: `*Erro ao consultar a IA:* ${err.message}` }])
    } finally {
      setBusy(false)
    }
  }

  return (
    <div>
      <div className="chips-row" style={{ marginBottom: '0.75rem' }}>
        <span className="muted-xs">Perguntas rápidas:</span>
        {QUICK.map(([label, prompt]) => (
          <button type="button" key={label} className="preset-chip" onClick={() => send(prompt)} disabled={busy}>{label}</button>
        ))}
      </div>

      <div className="ai-chat-box">
        <div className="chat-messages" ref={listRef} aria-live="polite">
          {messages.map((m, i) => (
            <div key={i} className={`chat-bubble ${m.role}`}>
              {m.role === 'user' ? m.text : <Markdown text={m.text} />}
              {m.source && <div className="chat-source">Fonte: {m.source}</div>}
            </div>
          ))}
          {busy && (
            <div className="chat-bubble assistant typing">
              <span className="pulse-dot" /> Consultando IA especialista...
            </div>
          )}
        </div>
        <form className="chat-input-bar" onSubmit={(e) => { e.preventDefault(); send(input) }}>
          <input
            id="chatInput"
            type="text"
            aria-label="Pergunta para o consultor de IA"
            placeholder="Faça uma pergunta sobre o projeto de rádio enlace..."
            autoComplete="off"
            value={input}
            onChange={(e) => setInput(e.target.value)}
          />
          <button type="submit" id="sendChatBtn" className="btn btn-primary" disabled={busy || !input.trim()}>Enviar</button>
        </form>
      </div>
    </div>
  )
}
