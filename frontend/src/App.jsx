import { useCallback, useEffect, useRef, useState } from 'react'
import Header from './components/Header'
import LinkForm from './components/LinkForm'
import LinkMap from './components/LinkMap'
import KpiGrid from './components/KpiGrid'
import ProfileChart from './components/ProfileChart'
import BudgetTab from './components/BudgetTab'
import OptimizationTab from './components/OptimizationTab'
import ConsultantTab from './components/ConsultantTab'
import GeminiKeyModal from './components/GeminiKeyModal'
import { Icon } from './components/Icons'
import { api } from './lib/api'
import { useTheme } from './hooks/useTheme'

// Cálculo rápido Haversine no cliente para atualizar distância ao arrastar pinos no mapa
function calcHaversine(lat1, lon1, lat2, lon2) {
  const R = 6371.0
  const dLat = (lat2 - lat1) * (Math.PI / 180)
  const dLon = (lon2 - lon1) * (Math.PI / 180)
  const a =
    Math.sin(dLat / 2) ** 2 +
    Math.cos(lat1 * (Math.PI / 180)) * Math.cos(lat2 * (Math.PI / 180)) * Math.sin(dLon / 2) ** 2
  return 2 * R * Math.asin(Math.sqrt(a))
}

const DEFAULT_PARAMS = {
  site_a_name: 'Torre Bela Vista (TX)',
  site_a_lat: -23.5615,
  site_a_lon: -46.6559,
  site_b_name: 'Repetidora Serra da Cantareira (RX)',
  site_b_lat: -23.4285,
  site_b_lon: -46.6200,
  frequency_mhz: 5800,
  distance_km: 15.2,
  tx_power_dbm: 22,
  tx_cable_loss_db: 1.5,
  tx_antenna_gain_dbi: 30,
  tx_tower_height_m: 25,
  tx_terrain_altitude_m: 780,
  rx_antenna_gain_dbi: 30,
  rx_cable_loss_db: 1.5,
  rx_sensitivity_dbm: -74,
  rx_tower_height_m: 20,
  rx_terrain_altitude_m: 950,
  misc_losses_db: 0.5,
  k_factor: 1.33333,
  rain_rate_mmh: 42,
  polarization: 'H',
  enable_rain: true,
  enable_gas: true,
  obstacles: [{ distance_km: 7.5, height_m: 12, description: 'Vegetação de copa alta / Morro intermediário' }],
  terrain_elevations: null
}

const TABS = [
  { id: 'budget', label: 'Balanço de Potência', icon: <Icon.Bars /> },
  { id: 'optimization', label: 'Otimização com IA', icon: <Icon.Sparkle /> },
  { id: 'consultant', label: 'Consultor Especialista IA', icon: <Icon.Chat /> },
]

// Campos vazios (usuário apagando o número) não são enviados à API.
const isComplete = (p) => Object.values(p).every((v) => v !== '' && !(typeof v === 'number' && Number.isNaN(v)))

const readKey = () => { try { return localStorage.getItem('gemini_api_key') || '' } catch { return '' } }

export default function App() {
  const { scheme, toggle } = useTheme()
  const [presets, setPresets] = useState([])
  const [activePreset, setActivePreset] = useState('wifi_5ghz_15km')
  const [params, setParams] = useState(DEFAULT_PARAMS)
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [optimization, setOptimization] = useState(null)
  const [optimizing, setOptimizing] = useState(false)
  const [tab, setTab] = useState('budget')
  const [geminiOpen, setGeminiOpen] = useState(false)
  const [apiKey, setApiKey] = useState(readKey)
  
  // Visualização LINKPlanner: 'split' (lado a lado), 'map' (mapa completo), 'chart' (perfil Fresnel)
  const [viewMode, setViewMode] = useState('split')
  const [fetchingElevation, setFetchingElevation] = useState(false)
  const [elevationSource, setElevationSource] = useState(null)

  const abortRef = useRef(null)

  useEffect(() => {
    api.presets().then(setPresets).catch(() => setPresets([]))
  }, [])

  // Recalcula com debounce sempre que os parâmetros mudam
  useEffect(() => {
    if (!isComplete(params)) return
    const t = setTimeout(async () => {
      abortRef.current?.abort()
      const ctrl = new AbortController()
      abortRef.current = ctrl
      setLoading(true)
      try {
        const res = await fetch('/api/calculate', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(params),
          signal: ctrl.signal,
        })
        if (!res.ok) throw new Error(`Parâmetros inválidos (${res.status})`)
        const data = await res.json()
        setResult(data)
        setError('')
      } catch (err) {
        if (err.name !== 'AbortError') setError(err.message)
      } finally {
        if (abortRef.current === ctrl) setLoading(false)
      }
    }, 300)
    return () => clearTimeout(t)
  }, [params])

  const onField = useCallback((id, value) => {
    setParams((p) => {
      const next = { ...p, [id]: value }
      // Se lat/lon foram alterados no formulário, recalcula distância geodésica
      if (['site_a_lat', 'site_a_lon', 'site_b_lat', 'site_b_lon'].includes(id)) {
        if (next.site_a_lat && next.site_a_lon && next.site_b_lat && next.site_b_lon) {
          const d = calcHaversine(next.site_a_lat, next.site_a_lon, next.site_b_lat, next.site_b_lon)
          next.distance_km = parseFloat(d.toFixed(2))
        }
      }
      return next
    })
    setActivePreset(null)
  }, [])

  const onObstacles = useCallback((obstacles) => setParams((p) => ({ ...p, obstacles })), [])

  const loadPreset = (preset) => {
    setActivePreset(preset.id)
    setParams({
      ...preset.params,
      obstacles: [...(preset.params.obstacles || [])],
      terrain_elevations: null
    })
    setElevationSource(null)
    setOptimization(null)
  }

  // Atualização interativa a partir do Mapa LINKPlanner
  const handleUpdateSiteA = useCallback((newCoords) => {
    setParams((p) => {
      const lat = newCoords.lat ?? p.site_a_lat
      const lon = newCoords.lon ?? p.site_a_lon
      const name = newCoords.name ?? p.site_a_name
      const dist = calcHaversine(lat, lon, p.site_b_lat, p.site_b_lon)
      return {
        ...p,
        site_a_lat: lat,
        site_a_lon: lon,
        site_a_name: name,
        distance_km: parseFloat(dist.toFixed(2)),
        terrain_elevations: null // Invalida relevo amostrado anterior até novo clique em Capturar Relevo
      }
    })
    setElevationSource(null)
    setActivePreset(null)
  }, [])

  const handleUpdateSiteB = useCallback((newCoords) => {
    setParams((p) => {
      const lat = newCoords.lat ?? p.site_b_lat
      const lon = newCoords.lon ?? p.site_b_lon
      const name = newCoords.name ?? p.site_b_name
      const dist = calcHaversine(p.site_a_lat, p.site_a_lon, lat, lon)
      return {
        ...p,
        site_b_lat: lat,
        site_b_lon: lon,
        site_b_name: name,
        distance_km: parseFloat(dist.toFixed(2)),
        terrain_elevations: null
      }
    })
    setElevationSource(null)
    setActivePreset(null)
  }, [])

  // Capturar Perfil de Relevo Real SRTM via Open-Meteo DEM
  const handleFetchElevation = async () => {
    if (!params.site_a_lat || !params.site_a_lon || !params.site_b_lat || !params.site_b_lon) {
      setError('Defina as coordenadas do Site A e Site B para capturar o relevo.')
      return
    }
    setFetchingElevation(true)
    setError('')
    try {
      const data = await api.elevationProfile({
        lat1: params.site_a_lat,
        lon1: params.site_a_lon,
        lat2: params.site_b_lat,
        lon2: params.site_b_lon,
        num_points: 60
      })

      setParams((p) => ({
        ...p,
        tx_terrain_altitude_m: data.site_a_altitude_m ?? p.tx_terrain_altitude_m,
        rx_terrain_altitude_m: data.site_b_altitude_m ?? p.rx_terrain_altitude_m,
        distance_km: data.distance_km ?? p.distance_km,
        terrain_elevations: data.elevations_m
      }))
      setElevationSource(`DEM SRTM Open-Meteo (${data.elevations_m.length} amostras)`)
    } catch (err) {
      setError(`Erro ao capturar relevo: ${err.message}`)
    } finally {
      setFetchingElevation(false)
    }
  }

  const runOptimization = async () => {
    if (!isComplete(params)) return
    setOptimizing(true)
    try {
      setOptimization(await api.optimize(params))
      setTab('optimization')
    } catch (err) {
      setError(`Falha na otimização: ${err.message}`)
    } finally {
      setOptimizing(false)
    }
  }

  const applyOptimized = () => {
    if (!optimization) return
    const o = optimization.optimized_params
    setParams((p) => ({
      ...p,
      tx_antenna_gain_dbi: o.tx_antenna_gain_dbi,
      rx_antenna_gain_dbi: o.rx_antenna_gain_dbi,
      tx_power_dbm: o.tx_power_dbm,
      tx_tower_height_m: o.tx_tower_height_m,
      rx_tower_height_m: o.rx_tower_height_m,
      polarization: o.polarization ?? p.polarization,
    }))
    setActivePreset(null)
    setTab('budget')
  }

  const saveKey = (key) => {
    try {
      if (key) localStorage.setItem('gemini_api_key', key)
      else localStorage.removeItem('gemini_api_key')
    } catch { /* ignore */ }
    setApiKey(key)
    setGeminiOpen(false)
  }

  const exportFile = async (fn) => {
    try { await fn(params) } catch (err) { setError(err.message) }
  }

  const profile = result?.profile_data
  const clearance = profile?.min_clearance_percent
  const geodesic = result?.geodesic

  // Objetos formatados para o componente LinkMap
  const siteAObj = {
    name: params.site_a_name || 'Site A (TX)',
    lat: params.site_a_lat || -23.5505,
    lon: params.site_a_lon || -46.6333,
    altitude: params.tx_terrain_altitude_m,
    towerHeight: params.tx_tower_height_m
  }

  const siteBObj = {
    name: params.site_b_name || 'Site B (RX)',
    lat: params.site_b_lat || -23.6300,
    lon: params.site_b_lon || -46.7200,
    altitude: params.rx_terrain_altitude_m,
    towerHeight: params.rx_tower_height_m
  }

  const renderProfileChartCard = () => (
    <div className="glass-card">
      <div className="profile-card-header">
        <div>
          <h2 className="card-h2">Perfil Longitudinal do Enlace & Elipsóide de Fresnel</h2>
          <p className="muted-sm">
            Curvatura da Terra (fator K={params.k_factor}), 1ª Zona de Fresnel, folga crítica 60% e terreno {elevationSource ? `(${elevationSource})` : 'estimado'}.
          </p>
        </div>
        <div style={{ textAlign: 'right' }}>
          <span className="muted-xs mono">Folga mínima: </span>
          <span className={`clearance-value ${clearance >= 60 ? 'c-emerald' : 'c-rose'}`}>
            {typeof clearance === 'number' ? `${clearance.toFixed(1)}%` : '—'}
          </span>
        </div>
      </div>
      <ProfileChart profile={profile} />
      <div className="canvas-legend">
        <div className="legend-item"><div className="legend-color" style={{ background: '#38bdf8' }} />Linha de Visada (LOS)</div>
        <div className="legend-item"><div className="legend-color" style={{ background: 'rgba(6,182,212,0.4)' }} />1ª Zona de Fresnel</div>
        <div className="legend-item"><div className="legend-color" style={{ background: '#f59e0b' }} />Folga Crítica 60%</div>
        <div className="legend-item"><div className="legend-color" style={{ background: '#475569' }} />Terreno & Curvatura</div>
        <div className="legend-item"><div className="legend-color" style={{ background: '#f43f5e' }} />Obstrução</div>
      </div>
    </div>
  )

  const renderMapCard = () => (
    <LinkMap
      siteA={siteAObj}
      siteB={siteBObj}
      geodesic={geodesic}
      onUpdateSiteA={handleUpdateSiteA}
      onUpdateSiteB={handleUpdateSiteB}
      onFetchElevation={handleFetchElevation}
      fetchingElevation={fetchingElevation}
      elevationSource={elevationSource}
    />
  )

  return (
    <>
      <Header
        budget={result?.budget_data?.budget}
        loading={loading}
        scheme={scheme}
        onToggleTheme={toggle}
        onOpenGemini={() => setGeminiOpen(true)}
        onExportPDF={() => exportFile(api.exportPDF)}
        onExportCSV={() => exportFile(api.exportCSV)}
      />

      <main className="main-container">
        <aside className="sidebar-panel">
          <div className="glass-card">
            <div className="card-title"><Icon.Star /> Cenários Pré-configurados</div>
            <div className="presets-group">
              {presets.map((p) => (
                <button
                  type="button"
                  key={p.id}
                  title={p.description}
                  className={`preset-chip ${activePreset === p.id ? 'active' : ''}`}
                  onClick={() => loadPreset(p)}
                >
                  {p.name}
                </button>
              ))}
            </div>
          </div>

          <LinkForm
            params={params}
            onField={onField}
            onObstacles={onObstacles}
            onOptimize={runOptimization}
            optimizing={optimizing}
            geodesic={geodesic}
            onFetchElevation={handleFetchElevation}
            fetchingElevation={fetchingElevation}
          />
        </aside>

        <section className="content-area">
          {error && (
            <div className="error-banner" role="alert">
              <span>{error}</span>
              <button type="button" aria-label="Fechar aviso" onClick={() => setError('')}><Icon.X /></button>
            </div>
          )}

          <KpiGrid data={result} />

          {/* Barra de Seleção de Modo Visual LINKPlanner */}
          <div className="view-switch-bar">
            <div className="view-switch-group">
              <button
                type="button"
                className={`view-switch-btn ${viewMode === 'split' ? 'active' : ''}`}
                onClick={() => setViewMode('split')}
                title="Visualização simultânea de Mapa de Rádio e Perfil de Fresnel"
              >
                ⚡ Visão Dividida (Lado a Lado)
              </button>
              <button
                type="button"
                className={`view-switch-btn ${viewMode === 'map' ? 'active' : ''}`}
                onClick={() => setViewMode('map')}
                title="Mapa de geolocalização e captura de pontos"
              >
                🗺️ Mapa LINKPlanner
              </button>
              <button
                type="button"
                className={`view-switch-btn ${viewMode === 'chart' ? 'active' : ''}`}
                onClick={() => setViewMode('chart')}
                title="Gráfico longitudinal da 1ª Zona de Fresnel e Terreno"
              >
                📡 Perfil de Fresnel & Terreno
              </button>
            </div>

            <div className="muted-xs mono" style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
              <span>Distância: <strong>{params.distance_km} km</strong></span>
              {geodesic?.bearing_ab_deg && (
                <span>| Azimute: <strong>{geodesic.bearing_ab_deg}°</strong></span>
              )}
            </div>
          </div>

          {/* Renderização de Acordo com o Modo Visual */}
          {viewMode === 'split' && (
            <div className="split-view-container">
              {renderMapCard()}
              {renderProfileChartCard()}
            </div>
          )}

          {viewMode === 'map' && renderMapCard()}

          {viewMode === 'chart' && renderProfileChartCard()}

          {/* Abas Técnicas: Balanço de Potência, Otimização IA, Consultor IA */}
          <div className="glass-card">
            <div className="tabs-container" role="tablist">
              {TABS.map((t) => (
                <button
                  type="button"
                  key={t.id}
                  role="tab"
                  aria-selected={tab === t.id}
                  className={`tab-btn ${tab === t.id ? 'active' : ''}`}
                  onClick={() => setTab(t.id)}
                >
                  {t.icon} {t.label}
                </button>
              ))}
            </div>
            <div className="tab-content active" role="tabpanel">
              {tab === 'budget' && <BudgetTab data={result} />}
              {tab === 'optimization' && (
                <OptimizationTab
                  optimization={optimization}
                  onApply={applyOptimized}
                  onOptimize={runOptimization}
                  optimizing={optimizing}
                />
              )}
              {tab === 'consultant' && <ConsultantTab params={params} apiKey={apiKey} />}
            </div>
          </div>
        </section>
      </main>

      <GeminiKeyModal open={geminiOpen} initialKey={apiKey} onSave={saveKey} onClose={() => setGeminiOpen(false)} />
    </>
  )
}
