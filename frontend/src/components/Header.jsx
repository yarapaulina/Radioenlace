import { Icon } from './Icons'

export default function Header({ budget, loading, scheme, onToggleTheme, onOpenGemini, onExportPDF, onExportCSV }) {
  const pillClass = budget ? budget.verdict_color : 'info'
  const pillText = loading && !budget ? 'Calculando enlace...' : budget?.verdict ?? 'Aguardando parâmetros'

  return (
    <header className="app-header">
      <div className="brand-wrapper">
        <div className="brand-logo-icon"><Icon.Radio /></div>
        <div className="brand-text">
          <h1>RadioLink Pro <span className="brand-badge">IA ENGINE</span></h1>
          <p className="brand-tagline">Cálculo de Rádio Enlace • Zonas de Fresnel • ITU-R P.530 / P.838 • Otimização Inteligente</p>
        </div>
      </div>

      <div className="header-controls">
        <div className={`status-pill ${pillClass}`} role="status" aria-live="polite">
          <span className="pulse-dot" /> {pillText}
        </div>
        <button type="button" id="btnConfigGeminiKey" className="btn btn-secondary" onClick={onOpenGemini}>
          <Icon.Key /> Gemini IA
        </button>
        <button type="button" id="btnExportPDF" className="btn btn-secondary" onClick={onExportPDF}>
          <Icon.File /> PDF
        </button>
        <button type="button" id="btnExportCSV" className="btn btn-secondary" onClick={onExportCSV}>
          <Icon.Download /> CSV
        </button>
        <button
          type="button"
          id="themeToggleBtn"
          className="btn-icon"
          onClick={onToggleTheme}
          aria-label={scheme === 'dark' ? 'Mudar para tema claro' : 'Mudar para tema escuro'}
          title={scheme === 'dark' ? 'Mudar para tema claro' : 'Mudar para tema escuro'}
        >
          {scheme === 'dark' ? <Icon.Sun /> : <Icon.Moon />}
        </button>
      </div>
    </header>
  )
}
