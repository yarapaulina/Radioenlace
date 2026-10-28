// Cliente HTTP para a API FastAPI do RadioLink Pro.

async function postJSON(url, body) {
  const res = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
  if (!res.ok) throw new Error(`Erro na API (${res.status})`)
  return res.json()
}

async function postDownload(url, body, filename) {
  const res = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
  if (!res.ok) throw new Error(`Falha ao exportar (${res.status})`)
  const blob = await res.blob()
  const href = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = href
  a.download = filename
  document.body.appendChild(a)
  a.click()
  a.remove()
  URL.revokeObjectURL(href)
}

export const api = {
  presets: async () => {
    const res = await fetch('/api/presets')
    if (!res.ok) throw new Error(`Erro na API (${res.status})`)
    return res.json()
  },
  calculate: (params) => postJSON('/api/calculate', params),
  optimize: (params, targetMargin = 25, targetAvailability = 99.999) =>
    postJSON('/api/optimize', {
      link_params: params,
      target_fade_margin_db: targetMargin,
      target_availability_pct: targetAvailability,
    }),
  consult: (params, query, apiKey) =>
    postJSON('/api/ai-consulting', { link_params: params, user_query: query, api_key: apiKey || null }),
  elevationProfile: (arg1, lon1, lat2, lon2, numPoints = 50) => {
    if (typeof arg1 === 'object' && arg1 !== null) {
      return postJSON('/api/elevation-profile', {
        lat1: arg1.lat1,
        lon1: arg1.lon1,
        lat2: arg1.lat2,
        lon2: arg1.lon2,
        num_points: arg1.num_points ?? arg1.numPoints ?? 50,
      })
    }
    return postJSON('/api/elevation-profile', { lat1: arg1, lon1, lat2, lon2, num_points: numPoints })
  },
  geocode: (query) => postJSON('/api/geocode', { query }),
  exportPDF: (params) => postDownload('/api/export/pdf', params, `memorial_radio_enlace_${params.distance_km}km.pdf`),
  exportCSV: (params) => postDownload('/api/export/csv', params, `dados_radio_enlace_${params.distance_km}km.csv`),
}
