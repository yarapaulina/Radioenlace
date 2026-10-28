import { useCallback, useEffect, useState } from 'react'

// Alternador de tema em dois estados (sistema ↔ oposto do sistema),
// refletido no <meta name="color-scheme"> e persistido em localStorage.
const meta = () => document.querySelector('meta[name="color-scheme"]')
const systemDark = () => window.matchMedia('(prefers-color-scheme: dark)').matches

function renderedScheme() {
  const value = meta()?.content ?? 'light dark'
  if (value === 'light' || value === 'dark') return value
  return systemDark() ? 'dark' : 'light'
}

export function useTheme() {
  const [scheme, setScheme] = useState(renderedScheme)

  useEffect(() => {
    const mq = window.matchMedia('(prefers-color-scheme: dark)')
    const sync = () => setScheme(renderedScheme())
    const onStorage = (e) => {
      if (e.key !== 'color-scheme') return
      meta().content = e.newValue ?? 'light dark'
      sync()
    }
    mq.addEventListener('change', sync)
    window.addEventListener('storage', onStorage)
    return () => {
      mq.removeEventListener('change', sync)
      window.removeEventListener('storage', onStorage)
    }
  }, [])

  const toggle = useCallback(() => {
    const target = renderedScheme() === 'dark' ? 'light' : 'dark'
    const sysScheme = systemDark() ? 'dark' : 'light'
    try {
      if (target === sysScheme) localStorage.removeItem('color-scheme')
      else localStorage.setItem('color-scheme', target)
    } catch { /* armazenamento bloqueado: aplica sem persistir */ }
    meta().content = target === sysScheme ? 'light dark' : target
    setScheme(target)
  }, [])

  return { scheme, toggle }
}
