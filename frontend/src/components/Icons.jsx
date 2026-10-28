// Ícones SVG inline (estilo traço) usados na interface.
const base = { fill: 'none', stroke: 'currentColor', strokeWidth: 2, strokeLinecap: 'round', strokeLinejoin: 'round', 'aria-hidden': true }

export const Icon = {
  Radio: (p) => (
    <svg width="24" height="24" viewBox="0 0 24 24" {...base} strokeWidth={2.2} {...p}>
      <path d="M4.9 19.1C1 15.2 1 8.8 4.9 4.9" /><path d="M7.8 16.2c-2.3-2.3-2.3-6.1 0-8.5" />
      <circle cx="12" cy="12" r="2" /><path d="M16.2 7.8c2.3 2.3 2.3 6.1 0 8.5" /><path d="M19.1 4.9C23 8.8 23 15.1 19.1 19" />
    </svg>
  ),
  Key: (p) => (<svg width="15" height="15" viewBox="0 0 24 24" {...base} {...p}><path d="M15 7h1a2 2 0 0 1 2 2m4 0a6 6 0 0 1-7.743 5.743L11 17H9v2H7v2H4a1 1 0 0 1-1-1v-2.586a1 1 0 0 1 .293-.707l5.964-5.964A6 6 0 1 1 21 9Z" /></svg>),
  File: (p) => (<svg width="15" height="15" viewBox="0 0 24 24" {...base} {...p}><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" /><polyline points="14 2 14 8 20 8" /></svg>),
  Download: (p) => (<svg width="15" height="15" viewBox="0 0 24 24" {...base} {...p}><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" /><polyline points="7 10 12 15 17 10" /><line x1="12" y1="15" x2="12" y2="3" /></svg>),
  Sun: (p) => (<svg width="16" height="16" viewBox="0 0 24 24" {...base} {...p}><circle cx="12" cy="12" r="5" /><path d="M12 1v2M12 21v2M4.22 4.22l1.42 1.42M18.36 18.36l1.42 1.42M1 12h2M21 12h2M4.22 19.78l1.42-1.42M18.36 5.64l1.42-1.42" /></svg>),
  Moon: (p) => (<svg width="16" height="16" viewBox="0 0 24 24" {...base} {...p}><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z" /></svg>),
  Star: (p) => (<svg width="16" height="16" viewBox="0 0 24 24" {...base} {...p}><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2" /></svg>),
  Globe: (p) => (<svg width="16" height="16" viewBox="0 0 24 24" {...base} {...p}><circle cx="12" cy="12" r="10" /><line x1="2" y1="12" x2="22" y2="12" /><path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z" /></svg>),
  ArrowRight: (p) => (<svg width="16" height="16" viewBox="0 0 24 24" {...base} {...p}><path d="M5 12h14" /><path d="m12 5 7 7-7 7" /></svg>),
  ArrowLeft: (p) => (<svg width="16" height="16" viewBox="0 0 24 24" {...base} {...p}><path d="M19 12H5" /><path d="m12 19-7-7 7-7" /></svg>),
  Cloud: (p) => (<svg width="16" height="16" viewBox="0 0 24 24" {...base} {...p}><path d="M17.5 19H9a7 7 0 1 1 6.71-9h1.79a4.5 4.5 0 1 1 0 9Z" /></svg>),
  Map: (p) => (<svg width="16" height="16" viewBox="0 0 24 24" {...base} {...p}><polygon points="1 6 1 22 8 18 16 22 23 18 23 2 16 6 8 2 1 6" /><line x1="8" y1="2" x2="8" y2="18" /><line x1="16" y1="6" x2="16" y2="22" /></svg>),
  Sparkle: (p) => (<svg width="16" height="16" viewBox="0 0 24 24" {...base} {...p}><path d="m12 3-1.912 5.813a2 2 0 0 1-1.275 1.275L3 12l5.813 1.912a2 2 0 0 1 1.275 1.275L12 21l1.912-5.813a2 2 0 0 1 1.275-1.275L21 12l-5.813-1.912a2 2 0 0 1-1.275-1.275L12 3Z" /></svg>),
  Bars: (p) => (<svg width="16" height="16" viewBox="0 0 24 24" {...base} {...p}><line x1="18" y1="20" x2="18" y2="10" /><line x1="12" y1="20" x2="12" y2="4" /><line x1="6" y1="20" x2="6" y2="14" /></svg>),
  Chat: (p) => (<svg width="16" height="16" viewBox="0 0 24 24" {...base} {...p}><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" /></svg>),
  Shield: (p) => (<svg width="18" height="18" viewBox="0 0 24 24" {...base} {...p}><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" /></svg>),
  Check: (p) => (<svg width="16" height="16" viewBox="0 0 24 24" {...base} {...p}><polyline points="20 6 9 17 4 12" /></svg>),
  Info: (p) => (<svg width="16" height="16" viewBox="0 0 24 24" {...base} {...p}><circle cx="12" cy="12" r="10" /><line x1="12" y1="16" x2="12" y2="12" /><line x1="12" y1="8" x2="12.01" y2="8" /></svg>),
  X: (p) => (<svg width="14" height="14" viewBox="0 0 24 24" {...base} {...p}><line x1="18" y1="6" x2="6" y2="18" /><line x1="6" y1="6" x2="18" y2="18" /></svg>),
}
