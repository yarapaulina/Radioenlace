function marginClass(m) {
  if (m >= 25) return 'kpi-success'
  if (m >= 15) return 'kpi-cyan'
  if (m >= 10) return 'kpi-warning'
  return 'kpi-danger'
}

const fmt = (v, d = 1) => (typeof v === 'number' ? v.toFixed(d) : '—')
const signed = (v, d = 1) => (typeof v === 'number' ? `${v > 0 ? '+' : ''}${v.toFixed(d)}` : '—')

export default function KpiGrid({ data }) {
  const b = data?.budget_data?.budget
  const rel = data?.budget_data?.reliability

  return (
    <div className="kpi-grid">
      <div className={`kpi-card ${b ? marginClass(b.fade_margin_db) : ''}`}>
        <div className="kpi-label">Margem de Desvanecimento</div>
        <div className="kpi-value">{signed(b?.fade_margin_db)} dB</div>
        <div className="kpi-subtext">Limiar seguro: ≥ 20 a 30 dB</div>
      </div>
      <div className="kpi-card kpi-cyan">
        <div className="kpi-label">Nível de Sinal Recebido (RSL)</div>
        <div className="kpi-value">{fmt(b?.rsl_dbm)} dBm</div>
        <div className="kpi-subtext">Sensibilidade: {fmt(b?.rx_sensitivity_dbm)} dBm</div>
      </div>
      <div className="kpi-card">
        <div className="kpi-label">PIRE / EIRP Efetivo</div>
        <div className="kpi-value">{signed(b?.eirp_dbm)} dBm</div>
        <div className="kpi-subtext">Potência isotrópica radiada</div>
      </div>
      <div className={`kpi-card ${rel && rel.availability_percent >= 99.99 ? 'kpi-success' : 'kpi-warning'}`}>
        <div className="kpi-label">Disponibilidade Anual</div>
        <div className="kpi-value">{fmt(rel?.availability_percent, 4)}%</div>
        <div className="kpi-subtext">Queda: ~{fmt(rel?.downtime_minutes_year)} min/ano</div>
      </div>
    </div>
  )
}
