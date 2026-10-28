import { useState } from 'react'
import { Icon } from './Icons'

function NumberField({ id, label, unit, value, onChange, step = 0.1, min, max }) {
  return (
    <div className="input-group">
      <label className="input-label" htmlFor={id}>
        <span>{label}</span>
        <span className="input-unit">{unit}</span>
      </label>
      <input
        id={id}
        type="number"
        className="input-control"
        value={value}
        step={step}
        min={min}
        max={max}
        onChange={(e) => onChange(id, e.target.value === '' ? '' : Number(e.target.value))}
      />
    </div>
  )
}

function SectionTitle({ icon, children, style }) {
  return <div className="card-title" style={style}>{icon}{children}</div>
}

function ObstacleEditor({ obstacles, onChange, maxDistance }) {
  const [draft, setDraft] = useState({ distance_km: '', height_m: '', description: '' })
  const [open, setOpen] = useState(false)

  const add = (e) => {
    e.preventDefault()
    const d = Number(draft.distance_km)
    const h = Number(draft.height_m)
    if (Number.isNaN(d) || Number.isNaN(h) || d < 0 || h < 0 || d > maxDistance) return
    onChange([...obstacles, { distance_km: d, height_m: h, description: draft.description || 'Obstáculo' }])
    setDraft({ distance_km: '', height_m: '', description: '' })
    setOpen(false)
  }

  return (
    <>
      <div className="card-title" style={{ marginTop: '1rem', justifyContent: 'space-between' }}>
        <span style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}><Icon.Map /> Obstáculos no Trajeto</span>
        <button type="button" id="btnAddObstacle" className="btn btn-secondary btn-xs" onClick={() => setOpen((o) => !o)}>
          {open ? 'Cancelar' : '+ Adicionar'}
        </button>
      </div>

      {open && (
        <div className="obstacle-form">
          <div className="form-grid-3">
            <input aria-label="Distância do TX (km)" className="input-control" type="number" step="0.1" placeholder="km" value={draft.distance_km}
              onChange={(e) => setDraft({ ...draft, distance_km: e.target.value })} />
            <input aria-label="Altura (m)" className="input-control" type="number" step="1" placeholder="altura m" value={draft.height_m}
              onChange={(e) => setDraft({ ...draft, height_m: e.target.value })} />
            <button type="button" className="btn btn-primary btn-xs" onClick={add}>Salvar</button>
          </div>
          <input aria-label="Descrição" className="input-control" style={{ marginTop: '0.45rem' }} placeholder="Descrição (ex: Morro, Edifício)" value={draft.description}
            onChange={(e) => setDraft({ ...draft, description: e.target.value })} />
        </div>
      )}

      <div className="obstacle-list">
        {obstacles.length === 0 && <span className="muted-xs">Nenhum obstáculo cadastrado.</span>}
        {obstacles.map((obs, idx) => (
          <div className="obstacle-item" key={`${obs.distance_km}-${idx}`}>
            <div>
              <span className="obstacle-km">{obs.distance_km} km:</span> <span>+{obs.height_m} m</span>{' '}
              <span className="muted-xs">({obs.description || 'Obstáculo'})</span>
            </div>
            <button type="button" className="obstacle-remove" aria-label={`Remover obstáculo em ${obs.distance_km} km`}
              onClick={() => onChange(obstacles.filter((_, i) => i !== idx))}>
              <Icon.X />
            </button>
          </div>
        ))}
      </div>
    </>
  )
}

function TextField({ id, label, value, onChange, placeholder }) {
  return (
    <div className="input-group">
      <label className="input-label" htmlFor={id}>
        <span>{label}</span>
      </label>
      <input
        id={id}
        type="text"
        className="input-control"
        placeholder={placeholder}
        value={value || ''}
        onChange={(e) => onChange(id, e.target.value)}
      />
    </div>
  )
}

export default function LinkForm({
  params,
  onField,
  onObstacles,
  onOptimize,
  optimizing,
  geodesic,
  onFetchElevation,
  fetchingElevation
}) {
  const [showSites, setShowSites] = useState(true)

  return (
    <form className="glass-card" onSubmit={(e) => e.preventDefault()}>
      {/* Seção LINKPlanner: Coordenadas e Sites */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <SectionTitle icon={<Icon.Map />}>Estações & Coordenadas (GPS)</SectionTitle>
        <button
          type="button"
          className="btn btn-secondary btn-xs"
          onClick={() => setShowSites((s) => !s)}
        >
          {showSites ? 'Recolher' : 'Expandir'}
        </button>
      </div>

      {geodesic && (
        <div className="geodesic-summary-bar">
          <div>
            <strong>Azimute:</strong> {geodesic.bearing_ab_deg ?? '—'}° (A→B) / {geodesic.bearing_ba_deg ?? '—'}° (B→A)
          </div>
          <div>
            <strong>Tilt:</strong> {geodesic.tilt_ab_deg ?? '0.0'}°
          </div>
        </div>
      )}

      {showSites && (
        <>
          <div className="site-box">
            <div className="site-header">
              <span className="site-badge tx">Estação A (TX)</span>
            </div>
            <TextField id="site_a_name" label="Identificação / Nome" value={params.site_a_name} onChange={onField} placeholder="Ex: Torre Central" />
            <div className="form-grid-2" style={{ marginTop: '0.4rem' }}>
              <NumberField id="site_a_lat" label="Latitude" unit="°" value={params.site_a_lat} onChange={onField} step={0.0001} min={-90} max={90} />
              <NumberField id="site_a_lon" label="Longitude" unit="°" value={params.site_a_lon} onChange={onField} step={0.0001} min={-180} max={180} />
            </div>
          </div>

          <div className="site-box">
            <div className="site-header">
              <span className="site-badge rx">Estação B (RX)</span>
            </div>
            <TextField id="site_b_name" label="Identificação / Nome" value={params.site_b_name} onChange={onField} placeholder="Ex: POP Clientes" />
            <div className="form-grid-2" style={{ marginTop: '0.4rem' }}>
              <NumberField id="site_b_lat" label="Latitude" unit="°" value={params.site_b_lat} onChange={onField} step={0.0001} min={-90} max={90} />
              <NumberField id="site_b_lon" label="Longitude" unit="°" value={params.site_b_lon} onChange={onField} step={0.0001} min={-180} max={180} />
            </div>
          </div>

          {onFetchElevation && (
            <button
              type="button"
              className="btn btn-secondary btn-xs"
              style={{ width: '100%', marginTop: '0.5rem' }}
              onClick={onFetchElevation}
              disabled={fetchingElevation}
              title="Obtém elevação real de relevo via Open-Meteo SRTM para o trajeto"
            >
              <Icon.Sparkle /> {fetchingElevation ? 'Capturando Relevo...' : 'Extrair Altitudes de Terreno (SRTM)'}
            </button>
          )}
        </>
      )}

      <SectionTitle icon={<Icon.Globe />} style={{ marginTop: '1rem' }}>Frequência & Geometria</SectionTitle>
      <div className="form-grid-2">
        <NumberField id="frequency_mhz" label="Frequência" unit="MHz" value={params.frequency_mhz} onChange={onField} step={10} min={100} max={100000} />
        <NumberField id="distance_km" label="Distância" unit="km" value={params.distance_km} onChange={onField} step={0.1} min={0.1} max={200} />
      </div>

      <SectionTitle icon={<Icon.ArrowRight />} style={{ marginTop: '0.75rem' }}>Transmissor (TX)</SectionTitle>
      <div className="form-grid-2">
        <NumberField id="tx_power_dbm" label="Potência TX" unit="dBm" value={params.tx_power_dbm} onChange={onField} step={0.5} />
        <NumberField id="tx_antenna_gain_dbi" label="Ganho Antena" unit="dBi" value={params.tx_antenna_gain_dbi} onChange={onField} step={0.5} />
        <NumberField id="tx_cable_loss_db" label="Perdas Cabo TX" unit="dB" value={params.tx_cable_loss_db} onChange={onField} />
        <NumberField id="tx_tower_height_m" label="Altura Torre" unit="m" value={params.tx_tower_height_m} onChange={onField} step={1} />
      </div>
      <NumberField id="tx_terrain_altitude_m" label="Altitude Terreno TX (nível do mar)" unit="m" value={params.tx_terrain_altitude_m} onChange={onField} step={1} />

      <SectionTitle icon={<Icon.ArrowLeft />} style={{ marginTop: '0.75rem' }}>Receptor (RX)</SectionTitle>
      <div className="form-grid-2">
        <NumberField id="rx_antenna_gain_dbi" label="Ganho Antena" unit="dBi" value={params.rx_antenna_gain_dbi} onChange={onField} step={0.5} />
        <NumberField id="rx_sensitivity_dbm" label="Sensibilidade" unit="dBm" value={params.rx_sensitivity_dbm} onChange={onField} step={0.5} />
        <NumberField id="rx_cable_loss_db" label="Perdas Cabo RX" unit="dB" value={params.rx_cable_loss_db} onChange={onField} />
        <NumberField id="rx_tower_height_m" label="Altura Torre" unit="m" value={params.rx_tower_height_m} onChange={onField} step={1} />
      </div>
      <NumberField id="rx_terrain_altitude_m" label="Altitude Terreno RX (nível do mar)" unit="m" value={params.rx_terrain_altitude_m} onChange={onField} step={1} />

      <SectionTitle icon={<Icon.Cloud />} style={{ marginTop: '0.75rem' }}>Fatores Ambientais & ITU-R</SectionTitle>
      <div className="form-grid-2">
        <NumberField id="k_factor" label="Fator K (Terra)" unit="4/3 = 1.33" value={params.k_factor} onChange={onField} step={0.05} />
        <div className="input-group">
          <label className="input-label" htmlFor="polarization"><span>Polarização</span><span className="input-unit">H / V</span></label>
          <select id="polarization" className="input-control" value={params.polarization} onChange={(e) => onField('polarization', e.target.value)}>
            <option value="H">Horizontal (H)</option>
            <option value="V">Vertical (V)</option>
          </select>
        </div>
        <NumberField id="rain_rate_mmh" label="Chuva R0.01" unit="mm/h" value={params.rain_rate_mmh} onChange={onField} step={5} />
        <NumberField id="misc_losses_db" label="Perdas Extras" unit="dB" value={params.misc_losses_db} onChange={onField} step={0.5} />
      </div>
      <div style={{ display: 'flex', gap: '1rem', marginTop: '0.35rem' }}>
        <label className="checkbox-group">
          <input type="checkbox" id="enable_rain" checked={params.enable_rain} onChange={(e) => onField('enable_rain', e.target.checked)} />
          <span>Atenuação Chuva (P.838)</span>
        </label>
        <label className="checkbox-group">
          <input type="checkbox" id="enable_gas" checked={params.enable_gas} onChange={(e) => onField('enable_gas', e.target.checked)} />
          <span>Gases (P.676)</span>
        </label>
      </div>

      <ObstacleEditor obstacles={params.obstacles} onChange={onObstacles} maxDistance={Number(params.distance_km) || 0} />

      <button type="button" id="btnOptimizeAI" className="btn btn-ai" style={{ width: '100%', marginTop: '0.75rem', padding: '0.75rem' }}
        onClick={onOptimize} disabled={optimizing}>
        <Icon.Sparkle /> {optimizing ? 'Otimizando com IA...' : 'Otimizar Enlace com IA'}
      </button>
    </form>
  )
}
