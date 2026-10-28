import { useEffect, useRef, useState } from 'react'

// Perfil longitudinal do enlace em Canvas 2D: terreno com curvatura da Terra,
// torres, linha de visada (LOS), 1ª zona de Fresnel, linha de 60% e obstáculos.
const PAD = { left: 65, right: 35, top: 40, bottom: 45 }

function drawTower(ctx, x, yBase, yTop, label) {
  ctx.strokeStyle = '#94a3b8'
  ctx.lineWidth = 1.5
  const w = 12
  ctx.beginPath()
  ctx.moveTo(x - w / 2, yBase); ctx.lineTo(x - 2, yTop); ctx.lineTo(x + 2, yTop); ctx.lineTo(x + w / 2, yBase)
  ctx.stroke()
  for (let i = 1; i < 4; i++) {
    const f = i / 4
    const y = yBase - f * (yBase - yTop)
    const ww = w * (1 - f * 0.7)
    ctx.beginPath(); ctx.moveTo(x - ww / 2, y); ctx.lineTo(x + ww / 2, y); ctx.stroke()
  }
  ctx.fillStyle = '#6366f1'
  ctx.beginPath(); ctx.arc(x, yTop, 6, 0, Math.PI * 2); ctx.fill()
  ctx.strokeStyle = '#38bdf8'; ctx.lineWidth = 2
  ctx.beginPath(); ctx.arc(x, yTop, 9, -Math.PI / 3, Math.PI / 3); ctx.stroke()
  ctx.fillStyle = '#f1f5f9'
  ctx.font = 'bold 11px "Plus Jakarta Sans", sans-serif'
  ctx.textAlign = 'center'
  ctx.fillText(label, x, yTop - 14)
}

function linePath(ctx, points, mapX, mapY, key) {
  ctx.beginPath()
  points.forEach((pt, i) => {
    const x = mapX(pt.distance_km)
    const y = mapY(pt[key])
    if (i === 0) ctx.moveTo(x, y); else ctx.lineTo(x, y)
  })
}

function render(ctx, width, height, profile, hover) {
  ctx.clearRect(0, 0, width, height)
  const points = profile?.points
  if (!points?.length) {
    ctx.fillStyle = '#64748b'
    ctx.font = '14px "Plus Jakarta Sans", sans-serif'
    ctx.textAlign = 'center'
    ctx.fillText('Aguardando cálculo do enlace...', width / 2, height / 2)
    return null
  }

  const totalDist = points[points.length - 1].distance_km
  let minAlt = Infinity, maxAlt = -Infinity
  points.forEach((p) => {
    minAlt = Math.min(minAlt, p.terrain_m)
    maxAlt = Math.max(maxAlt, p.fresnel_top_m, p.ground_with_obstacles_m)
  })
  minAlt = Math.max(0, minAlt - 15)
  maxAlt += 25
  const range = maxAlt - minAlt || 1
  const gW = width - PAD.left - PAD.right
  const gH = height - PAD.top - PAD.bottom
  const mapX = (km) => PAD.left + (km / totalDist) * gW
  const mapY = (alt) => PAD.top + gH - ((alt - minAlt) / range) * gH

  // Grade
  ctx.strokeStyle = 'rgba(255,255,255,0.05)'
  ctx.lineWidth = 1
  ctx.font = '10px "JetBrains Mono", monospace'
  ctx.fillStyle = '#64748b'
  for (let i = 0; i <= 5; i++) {
    const alt = minAlt + (i / 5) * range
    const y = mapY(alt)
    ctx.beginPath(); ctx.moveTo(PAD.left, y); ctx.lineTo(width - PAD.right, y); ctx.stroke()
    ctx.textAlign = 'right'; ctx.fillText(`${Math.round(alt)}m`, PAD.left - 8, y + 3)
  }
  const steps = Math.min(8, Math.max(4, Math.floor(totalDist)))
  for (let i = 0; i <= steps; i++) {
    const km = (i / steps) * totalDist
    const x = mapX(km)
    ctx.beginPath(); ctx.moveTo(x, PAD.top); ctx.lineTo(x, height - PAD.bottom); ctx.stroke()
    ctx.textAlign = 'center'; ctx.fillText(`${km.toFixed(1)} km`, x, height - PAD.bottom + 18)
  }

  // Terreno
  ctx.beginPath()
  ctx.moveTo(mapX(0), mapY(minAlt))
  points.forEach((p) => ctx.lineTo(mapX(p.distance_km), mapY(p.terrain_m)))
  ctx.lineTo(mapX(totalDist), mapY(minAlt))
  ctx.closePath()
  const tg = ctx.createLinearGradient(0, PAD.top, 0, height - PAD.bottom)
  tg.addColorStop(0, 'rgba(30,41,59,0.9)'); tg.addColorStop(1, 'rgba(15,23,42,0.95)')
  ctx.fillStyle = tg; ctx.fill()
  ctx.strokeStyle = '#475569'; ctx.lineWidth = 2
  linePath(ctx, points, mapX, mapY, 'terrain_m'); ctx.stroke()

  // Obstáculos
  points.forEach((p) => {
    if (p.ground_with_obstacles_m > p.terrain_m + 0.5) {
      const x = mapX(p.distance_km)
      const violated = p.ground_with_obstacles_m >= p.fresnel_60_bottom_m
      ctx.strokeStyle = violated ? '#f43f5e' : '#f59e0b'
      ctx.fillStyle = violated ? 'rgba(244,63,94,0.6)' : 'rgba(245,158,11,0.6)'
      ctx.lineWidth = 6
      ctx.beginPath(); ctx.moveTo(x, mapY(p.terrain_m)); ctx.lineTo(x, mapY(p.ground_with_obstacles_m)); ctx.stroke()
      ctx.beginPath(); ctx.arc(x, mapY(p.ground_with_obstacles_m), 4, 0, Math.PI * 2); ctx.fill()
    }
  })

  // Elipsóide de Fresnel
  ctx.beginPath()
  points.forEach((p, i) => { const x = mapX(p.distance_km), y = mapY(p.fresnel_top_m); if (i === 0) ctx.moveTo(x, y); else ctx.lineTo(x, y) })
  for (let i = points.length - 1; i >= 0; i--) ctx.lineTo(mapX(points[i].distance_km), mapY(points[i].fresnel_bottom_m))
  ctx.closePath()
  const fg = ctx.createLinearGradient(0, PAD.top, 0, height - PAD.bottom)
  fg.addColorStop(0, 'rgba(6,182,212,0.14)'); fg.addColorStop(1, 'rgba(99,102,241,0.08)')
  ctx.fillStyle = fg; ctx.fill()
  ctx.strokeStyle = 'rgba(6,182,212,0.45)'; ctx.lineWidth = 1.5; ctx.stroke()

  // Linha de 60%
  ctx.setLineDash([4, 4]); ctx.strokeStyle = '#f59e0b'; ctx.lineWidth = 1.2
  linePath(ctx, points, mapX, mapY, 'fresnel_60_bottom_m'); ctx.stroke()
  ctx.setLineDash([])

  // LOS
  ctx.strokeStyle = '#38bdf8'; ctx.lineWidth = 2.5
  ctx.shadowColor = 'rgba(56,189,248,0.6)'; ctx.shadowBlur = 8
  linePath(ctx, points, mapX, mapY, 'los_m'); ctx.stroke()
  ctx.shadowBlur = 0

  drawTower(ctx, mapX(0), mapY(points[0].terrain_m), mapY(points[0].los_m), 'TX')
  const last = points[points.length - 1]
  drawTower(ctx, mapX(totalDist), mapY(last.terrain_m), mapY(last.los_m), 'RX')

  // Crosshair
  if (hover) {
    const p = hover
    const x = mapX(p.distance_km)
    const yLOS = mapY(p.los_m)
    ctx.strokeStyle = 'rgba(255,255,255,0.4)'; ctx.setLineDash([2, 2])
    ctx.beginPath(); ctx.moveTo(x, PAD.top); ctx.lineTo(x, height - PAD.bottom); ctx.stroke()
    ctx.setLineDash([])
    ctx.fillStyle = '#38bdf8'; ctx.beginPath(); ctx.arc(x, yLOS, 4, 0, Math.PI * 2); ctx.fill()

    const tw = 190, th = 95
    let tx = x + 15
    if (tx + tw > width - 10) tx = x - tw - 15
    const ty = Math.max(PAD.top + 5, Math.min(yLOS - 30, height - PAD.bottom - th - 5))
    ctx.fillStyle = 'rgba(15,23,42,0.94)'; ctx.strokeStyle = 'rgba(99,102,241,0.4)'; ctx.lineWidth = 1
    ctx.beginPath(); ctx.roundRect(tx, ty, tw, th, 6); ctx.fill(); ctx.stroke()
    ctx.textAlign = 'left'
    ctx.fillStyle = '#38bdf8'; ctx.font = 'bold 11px "Plus Jakarta Sans", sans-serif'
    ctx.fillText(`Distância: ${p.distance_km.toFixed(2)} km`, tx + 10, ty + 18)
    ctx.fillStyle = '#cbd5e1'; ctx.font = '10px "JetBrains Mono", monospace'
    ctx.fillText(`Raio Fresnel R1: ${p.r1_radius_m.toFixed(1)} m`, tx + 10, ty + 36)
    ctx.fillText(`Folga 60%: ${(p.r1_radius_m * 0.6).toFixed(1)} m`, tx + 10, ty + 52)
    ctx.fillText(`Cota LOS: ${p.los_m.toFixed(1)} m`, tx + 10, ty + 68)
    const clearance = p.los_m - p.ground_with_obstacles_m
    const ok = clearance >= p.r1_radius_m * 0.6
    ctx.fillStyle = ok ? '#34d399' : '#fb7185'; ctx.font = 'bold 10px "JetBrains Mono", monospace'
    ctx.fillText(`Folga Real: ${clearance.toFixed(1)} m (${ok ? 'Livre' : 'Crítico'})`, tx + 10, ty + 84)
  }
  return { totalDist, gW }
}

export default function ProfileChart({ profile }) {
  const wrapRef = useRef(null)
  const canvasRef = useRef(null)
  const [size, setSize] = useState({ w: 0, h: 0 })
  const [hover, setHover] = useState(null)

  useEffect(() => {
    const el = wrapRef.current
    if (!el) return
    const ro = new ResizeObserver(([entry]) => {
      const { width, height } = entry.contentRect
      setSize({ w: width, h: height })
    })
    ro.observe(el)
    return () => ro.disconnect()
  }, [])

  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas || !size.w) return
    const dpr = window.devicePixelRatio || 1
    canvas.width = size.w * dpr
    canvas.height = size.h * dpr
    const ctx = canvas.getContext('2d')
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0)
    render(ctx, size.w, size.h, profile, hover)
  }, [profile, hover, size])

  const onMove = (e) => {
    const points = profile?.points
    if (!points?.length) return
    const rect = canvasRef.current.getBoundingClientRect()
    const mx = e.clientX - rect.left
    const gW = size.w - PAD.left - PAD.right
    if (mx < PAD.left || mx > PAD.left + gW) { setHover(null); return }
    const target = ((mx - PAD.left) / gW) * points[points.length - 1].distance_km
    let closest = points[0]
    for (const p of points) if (Math.abs(p.distance_km - target) < Math.abs(closest.distance_km - target)) closest = p
    setHover(closest)
  }

  return (
    <div className="canvas-container" ref={wrapRef}>
      <canvas
        ref={canvasRef}
        id="profileCanvas"
        role="img"
        aria-label="Perfil longitudinal do enlace com terreno, linha de visada e zona de Fresnel"
        onMouseMove={onMove}
        onMouseLeave={() => setHover(null)}
      />
    </div>
  )
}
