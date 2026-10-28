const n = (v, d = 2) => (typeof v === 'number' ? v.toFixed(d) : '—')

function Waterfall({ inp, b }) {
  const stages = [
    { label: 'TX Potência', val: inp.tx_power_dbm, type: 'start', unit: 'dBm' },
    { label: 'Perdas TX', val: -inp.tx_cable_loss_db, type: 'loss', unit: 'dB' },
    { label: 'Ganho Ant. TX', val: inp.tx_antenna_gain_dbi, type: 'gain', unit: 'dBi' },
    { label: 'PIRE (EIRP)', val: b.eirp_dbm, type: 'subtotal', unit: 'dBm' },
    { label: 'Espaço Livre', val: -b.fspl_db, type: 'loss', unit: 'dB' },
    { label: 'Chuva & Gases', val: -(b.rain_loss_db + b.gas_loss_db), type: 'loss', unit: 'dB' },
    { label: 'Perdas Extras', val: -b.misc_losses_db, type: 'loss', unit: 'dB' },
    { label: 'Ganho Ant. RX', val: inp.rx_antenna_gain_dbi, type: 'gain', unit: 'dBi' },
    { label: 'Perdas RX', val: -inp.rx_cable_loss_db, type: 'loss', unit: 'dB' },
    { label: 'RSL Recebido', val: b.rsl_dbm, type: 'final', unit: 'dBm' },
    { label: 'Sensibilidade', val: b.rx_sensitivity_dbm, type: 'ref', unit: 'dBm' },
    { label: 'Margem Líquida', val: b.fade_margin_db, type: 'margin', unit: 'dB' },
  ]
  const cls = (s) => {
    if (s.type === 'gain') return 'wf-gain'
    if (s.type === 'loss') return 'wf-loss'
    if (s.type === 'subtotal' || s.type === 'final') return 'wf-total'
    if (s.type === 'margin') return s.val >= 15 ? 'wf-gain wf-strong' : 'wf-warn wf-strong'
    return ''
  }
  return (
    <div className="waterfall">
      {stages.map((s) => (
        <div className="wf-row" key={s.label}>
          <span className="wf-label">{s.label}</span>
          <span className={`wf-value ${cls(s)}`}>
            {(s.type === 'gain' || s.type === 'margin') && s.val > 0 ? '+' : ''}{s.val.toFixed(1)} {s.unit}
          </span>
        </div>
      ))}
    </div>
  )
}

export default function BudgetTab({ data }) {
  const bd = data?.budget_data
  if (!bd) return <p className="muted-xs">Calculando...</p>
  const { budget: b, inputs: inp, reliability: rel, fresnel } = bd

  const rows = [
    ['Frequência de Operação', 'Banda Nominal', `${inp.frequency_mhz} MHz (${inp.frequency_ghz} GHz)`],
    ['Distância do Enlace', 'Linha de Visada Direta', `${inp.distance_km} km`],
    ['Potência Conduzida (TX)', 'Saída do Rádio', `+${inp.tx_power_dbm} dBm`],
    ['Perdas de Cabos/Jumper (TX)', 'Atenuação de Conectores', `-${inp.tx_cable_loss_db} dB`],
    ['Ganho da Antena (TX)', 'Antena Direcional', `+${inp.tx_antenna_gain_dbi} dBi`],
    ['PIRE / EIRP', 'Potência Radiada Equivalente', `+${n(b.eirp_dbm)} dBm`, 'row-indigo'],
    ['Perda em Espaço Livre (FSPL)', 'Equação de Friis', `-${n(b.fspl_db)} dB`, '', 'c-rose'],
    ['Atenuação por Chuva', 'ITU-R P.838 / P.530', `-${n(b.rain_loss_db)} dB`, '', 'c-rose'],
    ['Absorção por Gases Atmosféricos', 'ITU-R P.676 (O₂ + H₂O)', `-${n(b.gas_loss_db)} dB`, '', 'c-rose'],
    ['Atenuação Total de Percurso', 'Soma das perdas', `-${n(b.total_path_loss_db)} dB`, 'row-rose', 'c-rose'],
    ['Ganho da Antena (RX)', 'Antena Receptora', `+${inp.rx_antenna_gain_dbi} dBi`],
    ['Perdas de Cabos/Jumper (RX)', 'Atenuação de linha RX', `-${inp.rx_cable_loss_db} dB`],
    ['Potência Recebida (RSL)', 'Nível no receptor', `${n(b.rsl_dbm)} dBm`, 'row-cyan', 'c-cyan'],
    ['Sensibilidade do Rádio', 'Limiar de modulação', `${n(b.rx_sensitivity_dbm)} dBm`],
    ['Margem de Desvanecimento', 'RSL − Sensibilidade', `${b.fade_margin_db > 0 ? '+' : ''}${n(b.fade_margin_db)} dB`, 'row-emerald', 'c-emerald'],
    ['Raio da 1ª Zona de Fresnel (meio)', 'Fórmula de Fresnel', `${n(fresnel.midpoint_radius_r1_m)} m`],
    ['Folga Mínima 60% de Fresnel', '0.6 × R1 (ITU-R P.526)', `${n(fresnel.midpoint_clearance_60_m)} m`],
    [`Abaulamento da Terra (K=${n(inp.k_factor)})`, '(d1·d2)/(12.74·K)', `${n(fresnel.earth_bulge_midpoint_m)} m`],
    ['Disponibilidade Anual', 'Vigants-Barnett & ITU-R P.530', `${rel.availability_percent}%`, '', 'c-emerald'],
    ['Tempo Estimado de Queda Anual', 'Outage projetado', `${rel.downtime_minutes_year} min/ano`],
  ]

  return (
    <div className="budget-layout">
      <div>
        <h3 className="section-h3">Fluxo de Níveis de Potência</h3>
        <Waterfall inp={inp} b={b} />
      </div>
      <div>
        <h3 className="section-h3">Memorial Técnico das Equações</h3>
        <div style={{ overflowX: 'auto' }}>
          <table className="tech-table">
            <thead><tr><th>Parâmetro de RF</th><th>Norma / Modelo</th><th>Valor</th></tr></thead>
            <tbody>
              {rows.map(([label, norm, value, rowCls = '', valCls = '']) => (
                <tr key={label} className={rowCls}>
                  <td>{rowCls ? <strong>{label}</strong> : label}</td>
                  <td>{norm}</td>
                  <td className={`mono-cell ${valCls}`}>{value}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}
