// Renderizador de Markdown mínimo e seguro (sem innerHTML):
// suporta ###/##/# títulos, listas "- ", **negrito** e *itálico*.

function inline(text, keyBase) {
  const parts = []
  const regex = /(\*\*[^*]+\*\*|\*[^*]+\*)/g
  let last = 0
  let match
  let i = 0
  while ((match = regex.exec(text)) !== null) {
    if (match.index > last) parts.push(text.slice(last, match.index))
    const token = match[0]
    if (token.startsWith('**')) parts.push(<strong key={`${keyBase}-b${i++}`}>{token.slice(2, -2)}</strong>)
    else parts.push(<em key={`${keyBase}-i${i++}`}>{token.slice(1, -1)}</em>)
    last = match.index + token.length
  }
  if (last < text.length) parts.push(text.slice(last))
  return parts
}

export default function Markdown({ text }) {
  if (!text) return null
  const lines = text.split('\n')
  const out = []
  let list = []

  const flushList = (key) => {
    if (list.length) {
      out.push(<ul key={`ul-${key}`} className="md-list">{list}</ul>)
      list = []
    }
  }

  lines.forEach((raw, idx) => {
    const line = raw.trimEnd()
    const bullet = line.match(/^\s*[-*•]\s+(.*)$/)
    if (bullet) {
      list.push(<li key={`li-${idx}`}>{inline(bullet[1], idx)}</li>)
      return
    }
    flushList(idx)
    const heading = line.match(/^(#{1,4})\s+(.*)$/)
    if (heading) out.push(<h4 key={idx} className="md-heading">{inline(heading[2], idx)}</h4>)
    else if (line.trim()) out.push(<p key={idx} className="md-p">{inline(line, idx)}</p>)
  })
  flushList('end')
  return <div className="md">{out}</div>
}
