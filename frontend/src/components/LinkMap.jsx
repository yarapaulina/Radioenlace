import { useEffect, useRef, useState } from 'react'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'
import { Icon } from './Icons'

// Camadas de Mapa Gratuitas de Alta Fidelidade (Satélite, Terreno, Dark e Ruas)
const TILE_LAYERS = {
  satellite: {
    name: 'Satélite HD',
    url: 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
    attribution: '&copy; Esri, Maxar, Earthstar Geographics'
  },
  dark: {
    name: 'Tema Escuro (CartoDB)',
    url: 'https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png',
    attribution: '&copy; OpenStreetMap, &copy; CARTO'
  },
  topo: {
    name: 'Topográfico / Relevo',
    url: 'https://{s}.tile.opentopomap.org/{z}/{x}/{y}.png',
    attribution: '&copy; OpenStreetMap, &copy; OpenTopoMap'
  },
  street: {
    name: 'OpenStreetMap Ruas',
    url: 'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',
    attribution: '&copy; OpenStreetMap contributors'
  }
}

// Criação de Ícones SVG de Torre em Alta Resolução com Efeito Pulsante
function createTowerIcon(label, color, glowColor) {
  return L.divIcon({
    className: 'custom-map-marker',
    html: `
      <div style="position: relative; display: flex; flex-direction: column; align-items: center; transform: translate(-50%, -100%);">
        <div style="
          background: rgba(15, 23, 42, 0.92);
          border: 1.5px solid ${color};
          color: #f1f5f9;
          font-family: 'Plus Jakarta Sans', sans-serif;
          font-size: 11px;
          font-weight: 700;
          padding: 2px 7px;
          border-radius: 999px;
          white-space: nowrap;
          box-shadow: 0 0 10px ${glowColor};
          margin-bottom: 3px;
        ">${label}</div>
        <div style="
          width: 32px;
          height: 32px;
          border-radius: 50%;
          background: radial-gradient(circle, ${color} 0%, rgba(15, 23, 42, 0.95) 75%);
          border: 2px solid ${color};
          display: flex;
          align-items: center;
          justify-content: center;
          color: #ffffff;
          box-shadow: 0 0 14px ${glowColor};
        ">
          <svg width="18" height="18" fill="none" stroke="currentColor" stroke-width="2.2" viewBox="0 0 24 24">
            <path d="M4.9 19.1C1 15.2 1 8.8 4.9 4.9"/>
            <path d="M7.8 16.2c-2.3-2.3-2.3-6.1 0-8.5"/>
            <circle cx="12" cy="12" r="2"/>
            <path d="M16.2 7.8c2.3 2.3 2.3 6.1 0 8.5"/>
            <path d="M19.1 4.9C23 8.8 23 15.1 19.1 19"/>
          </svg>
        </div>
        <div style="
          width: 2px;
          height: 10px;
          background: ${color};
        "></div>
      </div>
    `,
    iconSize: [32, 48],
    iconAnchor: [16, 48]
  })
}

export default function LinkMap({
  siteA,
  siteB,
  geodesic,
  onUpdateSiteA,
  onUpdateSiteB,
  onFetchElevation,
  fetchingElevation,
  elevationSource
}) {
  const mapContainerRef = useRef(null)
  const mapInstanceRef = useRef(null)
  const tileLayerRef = useRef(null)
  const markerARef = useRef(null)
  const markerBRef = useRef(null)
  const polylineRef = useRef(null)

  const [activeLayer, setActiveLayer] = useState('dark')
  const [clickMode, setClickMode] = useState('none') // 'none' | 'setA' | 'setB'
  const [searchQuery, setSearchQuery] = useState('')
  const [isSearching, setIsSearching] = useState(false)

  // 1. Inicializar o Mapa Leaflet
  useEffect(() => {
    if (!mapContainerRef.current || mapInstanceRef.current) return

    const initialLat = (siteA.lat + siteB.lat) / 2 || -23.55
    const initialLon = (siteA.lon + siteB.lon) / 2 || -46.65

    const map = L.map(mapContainerRef.current, {
      center: [initialLat, initialLon],
      zoom: 11,
      zoomControl: false
    })

    L.control.zoom({ position: 'topright' }).addTo(map)

    const layerConfig = TILE_LAYERS[activeLayer]
    const tileLayer = L.tileLayer(layerConfig.url, {
      attribution: layerConfig.attribution,
      maxZoom: 19
    }).addTo(map)

    tileLayerRef.current = tileLayer
    mapInstanceRef.current = map

    // Evento de clique para posicionar Site A ou Site B
    map.on('click', (e) => {
      const { lat, lng } = e.latlng
      const newLat = parseFloat(lat.toFixed(6))
      const newLon = parseFloat(lng.toFixed(6))

      if (window.__currentClickMode === 'setA') {
        onUpdateSiteA({ lat: newLat, lon: newLon })
        setClickMode('none')
      } else if (window.__currentClickMode === 'setB') {
        onUpdateSiteB({ lat: newLat, lon: newLon })
        setClickMode('none')
      }
    })

    return () => {
      map.remove()
      mapInstanceRef.current = null
    }
  }, [])

  // Sincronizar variável de clique com window para os callbacks do Leaflet
  useEffect(() => {
    window.__currentClickMode = clickMode
  }, [clickMode])

  // 2. Troca de Camada do Mapa
  const handleLayerChange = (layerKey) => {
    setActiveLayer(layerKey)
    const map = mapInstanceRef.current
    if (!map) return

    if (tileLayerRef.current) {
      map.removeLayer(tileLayerRef.current)
    }

    const cfg = TILE_LAYERS[layerKey]
    tileLayerRef.current = L.tileLayer(cfg.url, {
      attribution: cfg.attribution,
      maxZoom: 19
    }).addTo(map)
  }

  // 3. Atualizar Marcadores e Linha Geodésica
  useEffect(() => {
    const map = mapInstanceRef.current
    if (!map) return

    const posA = [siteA.lat, siteA.lon]
    const posB = [siteB.lat, siteB.lon]

    // Marcador Site A (TX)
    if (!markerARef.current) {
      const markerA = L.marker(posA, {
        draggable: true,
        icon: createTowerIcon(siteA.name || 'Site A (TX)', '#38bdf8', 'rgba(56, 189, 248, 0.4)')
      }).addTo(map)

      markerA.on('dragend', (e) => {
        const { lat, lng } = e.target.getLatLng()
        onUpdateSiteA({ lat: parseFloat(lat.toFixed(6)), lon: parseFloat(lng.toFixed(6)) })
      })

      markerARef.current = markerA
    } else {
      markerARef.current.setLatLng(posA)
      markerARef.current.setIcon(createTowerIcon(siteA.name || 'Site A (TX)', '#38bdf8', 'rgba(56, 189, 248, 0.4)'))
    }

    // Marcador Site B (RX)
    if (!markerBRef.current) {
      const markerB = L.marker(posB, {
        draggable: true,
        icon: createTowerIcon(siteB.name || 'Site B (RX)', '#34d399', 'rgba(52, 211, 153, 0.4)')
      }).addTo(map)

      markerB.on('dragend', (e) => {
        const { lat, lng } = e.target.getLatLng()
        onUpdateSiteB({ lat: parseFloat(lat.toFixed(6)), lon: parseFloat(lng.toFixed(6)) })
      })

      markerBRef.current = markerB
    } else {
      markerBRef.current.setLatLng(posB)
      markerBRef.current.setIcon(createTowerIcon(siteB.name || 'Site B (RX)', '#34d399', 'rgba(52, 211, 153, 0.4)'))
    }

    // Linha de Visada do Enlace (Polyline)
    if (!polylineRef.current) {
      const line = L.polyline([posA, posB], {
        color: '#38bdf8',
        weight: 3.5,
        opacity: 0.9,
        dashArray: '8, 8'
      }).addTo(map)
      polylineRef.current = line
    } else {
      polylineRef.current.setLatLngs([posA, posB])
    }
  }, [siteA, siteB])

  // Ajustar o zoom do mapa para enquadrar ambas as torres
  const fitBoundsToLink = () => {
    const map = mapInstanceRef.current
    if (!map) return
    const bounds = L.latLngBounds([[siteA.lat, siteA.lon], [siteB.lat, siteB.lon]])
    map.fitBounds(bounds, { padding: [60, 60] })
  }

  // Buscar Cidade/Endereço
  const handleSearch = async (e) => {
    e.preventDefault()
    if (!searchQuery.trim() || isSearching) return
    setIsSearching(true)
    try {
      const res = await fetch('/api/geocode', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: searchQuery.trim() })
      })
      if (res.ok) {
        const data = await res.json()
        if (data.results && data.results.length > 0) {
          const item = data.results[0]
          const map = mapInstanceRef.current
          if (map) {
            map.flyTo([item.lat, item.lon], 13, { duration: 1.5 })
          }
        } else {
          alert('Local não encontrado. Tente digitar nome de cidade ou coordenadas (ex: -23.55, -46.63).')
        }
      }
    } catch (err) {
      console.error(err)
    } finally {
      setIsSearching(false)
    }
  }

  // Pegar Localização Atual do Usuário
  const handleUseMyLocation = () => {
    if (!navigator.geolocation) {
      alert('Geolocalização não suportada no seu navegador.')
      return
    }
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        const lat = parseFloat(pos.coords.latitude.toFixed(6))
        const lon = parseFloat(pos.coords.longitude.toFixed(6))
        onUpdateSiteA({ lat, lon, name: 'Minha Localização (TX)' })
        const map = mapInstanceRef.current
        if (map) map.flyTo([lat, lon], 13)
      },
      (err) => alert('Não foi possível obter sua localização: ' + err.message)
    )
  }

  return (
    <div className="map-view-card">
      {/* Barra Superior de Ferramentas do Mapa (Estilo LINKPlanner) */}
      <div className="map-toolbar">
        <div className="map-tools-left">
          <form onSubmit={handleSearch} className="map-search-form">
            <input
              type="text"
              placeholder="Buscar cidade ou coordenadas..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="map-search-input"
            />
            <button type="submit" className="btn btn-secondary btn-xs" disabled={isSearching}>
              {isSearching ? '...' : 'Buscar'}
            </button>
          </form>

          <button
            type="button"
            className={`btn btn-xs ${clickMode === 'setA' ? 'btn-primary' : 'btn-secondary'}`}
            onClick={() => setClickMode(clickMode === 'setA' ? 'none' : 'setA')}
            title="Clique no mapa para posicionar o Site A"
          >
            🎯 Posicionar Site A
          </button>

          <button
            type="button"
            className={`btn btn-xs ${clickMode === 'setB' ? 'btn-primary' : 'btn-secondary'}`}
            onClick={() => setClickMode(clickMode === 'setB' ? 'none' : 'setB')}
            title="Clique no mapa para posicionar o Site B"
          >
            🎯 Posicionar Site B
          </button>

          <button
            type="button"
            className="btn btn-secondary btn-xs"
            onClick={fitBoundsToLink}
            title="Centralizar enlace na tela"
          >
            🔍 Enquadrar Enlace
          </button>

          <button
            type="button"
            className="btn btn-secondary btn-xs"
            onClick={handleUseMyLocation}
            title="Definir Site A com meu GPS"
          >
            📍 Meu GPS
          </button>
        </div>

        <div className="map-tools-right">
          {/* Botão de Extração de Relevo SRTM */}
          <button
            type="button"
            className="btn btn-ai btn-xs"
            onClick={onFetchElevation}
            disabled={fetchingElevation}
            title="Consultar altitudes reais de terreno via Open-Meteo SRTM DEM"
          >
            <Icon.Sparkle /> {fetchingElevation ? 'Extraindo Relevo...' : '⚡ Capturar Relevo Real SRTM'}
          </button>

          {/* Seletor de Camadas */}
          <div className="layer-picker">
            {Object.keys(TILE_LAYERS).map((key) => (
              <button
                type="button"
                key={key}
                className={`layer-chip ${activeLayer === key ? 'active' : ''}`}
                onClick={() => handleLayerChange(key)}
              >
                {TILE_LAYERS[key].name}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Container do Mapa Leaflet */}
      <div className="leaflet-map-wrapper">
        <div ref={mapContainerRef} className="leaflet-map-container" />

        {/* Overlay Flutuante com Métricas Geodésicas de LINKPlanner */}
        <div className="map-geodesic-overlay">
          <div className="overlay-badge">
            <span className="badge-label">Site A (TX):</span>
            <span className="badge-val">{siteA.name} ({siteA.lat.toFixed(4)}°, {siteA.lon.toFixed(4)}°)</span>
            <span className="badge-sub">Alt: {siteA.altitude}m | Torre: {siteA.towerHeight}m</span>
          </div>

          <div className="overlay-badge">
            <span className="badge-label">Site B (RX):</span>
            <span className="badge-val">{siteB.name} ({siteB.lat.toFixed(4)}°, {siteB.lon.toFixed(4)}°)</span>
            <span className="badge-sub">Alt: {siteB.altitude}m | Torre: {siteB.towerHeight}m</span>
          </div>

          <div className="overlay-badge highlight">
            <span className="badge-label">Geometria do Enlace:</span>
            <span className="badge-val">Azimute A→B: {geodesic?.bearing_ab_deg ?? '—'}° | B→A: {geodesic?.bearing_ba_deg ?? '—'}°</span>
            <span className="badge-sub">Inclinação (Tilt): {geodesic?.tilt_ab_deg ?? '0.0'}°</span>
          </div>

          {elevationSource && (
            <div className="overlay-badge srtm">
              <span className="badge-label">Fonte de Relevo:</span>
              <span className="badge-val">{elevationSource}</span>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
