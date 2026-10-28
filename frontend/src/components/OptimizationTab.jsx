import { Icon } from './Icons'

export default function OptimizationTab({ optimization, onApply, onOptimize, optimizing }) {
  if (!optimization) {
    return (
      <div className="empty-state">
        <Icon.Sparkle width="28" height="28" />
        <p>Execute a otimização para ver o comparativo e as recomendações de antenas, torres e conformidade.</p>
        <button type="button" className="btn btn-ai" onClick={onOptimize} disabled={optimizing}>
          <Icon.Sparkle /> {optimizing ? 'Otimizando...' : 'Otimizar Enlace com IA'}
        </button>
      </div>
    )
  }

  const { original_summary: o, optimized_summary: p, recommendations: rec } = optimization
  const rows = [
    ['Margem de Desvanecimento', `${o.fade_margin_db.toFixed(1)} dB`, `${p.fade_margin_db.toFixed(1)} dB`, 'c-emerald'],
    ['Disponibilidade Anual', `${o.availability_percent.toFixed(4)}%`, `${p.availability_percent.toFixed(4)}%`, 'c-emerald'],
    ['Tempo de Queda Projetado', `${o.downtime_minutes_year.toFixed(1)} min/ano`, `${p.downtime_minutes_year.toFixed(1)} min/ano`, ''],
    ['Potência Recebida (RSL)', `${o.rsl_dbm.toFixed(1)} dBm`, `${p.rsl_dbm.toFixed(1)} dBm`, ''],
    ['PIRE / EIRP', `${o.eirp_dbm.toFixed(1)} dBm`, `${p.eirp_dbm.toFixed(1)} dBm`, ''],
    ['Folga Mínima de Fresnel', `${o.min_clearance_percent.toFixed(1)}%`, `${p.min_clearance_percent.toFixed(1)}%`, 'c-cyan'],
  ]
  const changes = [
    ['Ganho antena TX/RX', `${rec.tx_antenna_gain_dbi} / ${rec.rx_antenna_gain_dbi} dBi`],
    ['Potência TX', `${rec.tx_power_dbm} dBm`],
    ['Torres TX/RX', `${rec.tx_tower_height_m} / ${rec.rx_tower_height_m} m`],
    ['Polarização', rec.polarization],
  ]

  return (
    <div className="ai-optimizer-panel">
      <div>
        <h3 className="section-h3 c-cyan">Comparativo: Atual vs. Otimizado</h3>
        <table className="tech-table">
          <thead><tr><th>Métrica</th><th>Antes</th><th>Depois</th></tr></thead>
          <tbody>
            {rows.map(([label, before, after, cls]) => (
              <tr key={label}><td>{label}</td><td className="mono-cell">{before}</td><td className={`mono-cell ${cls}`}>{after}</td></tr>
            ))}
          </tbody>
        </table>
        <div className="chips-row" style={{ marginTop: '0.9rem' }}>
          {changes.map(([k, v]) => (
            <span className="param-chip" key={k}><span className="muted-xs">{k}:</span> <strong>{v}</strong></span>
          ))}
        </div>
        <button type="button" id="btnApplyOptimized" className="btn btn-primary" style={{ width: '100%', marginTop: '1rem' }} onClick={onApply}>
          <Icon.Check /> Carregar Parâmetros Otimizados no Projeto
        </button>
      </div>

      <div className="ai-recommendation-box">
        <h4><Icon.Shield /> Recomendações Técnicas</h4>
        <ul className="checklist-items">
          {rec.action_items.map((item) => (
            <li key={item}><Icon.Check className="c-emerald" /><span>{item}</span></li>
          ))}
          {rec.obstruction_notes.map((note) => (
            <li key={note}><Icon.Info className="c-cyan" /><span>{note}</span></li>
          ))}
        </ul>
        <div className="anatel-box">
          <span className="anatel-title">Conformidade Regulatória (ANATEL):</span>
          <p>{rec.anatel_compliance}</p>
        </div>
      </div>
    </div>
  )
}
