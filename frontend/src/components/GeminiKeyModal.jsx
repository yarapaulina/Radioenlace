import { useEffect, useRef, useState } from 'react'

// Modal nativo (<dialog>) para configurar a chave opcional da API Gemini.
export default function GeminiKeyModal({ open, initialKey, onSave, onClose }) {
  const ref = useRef(null)
  const [value, setValue] = useState(initialKey || '')

  useEffect(() => {
    const dlg = ref.current
    if (!dlg) return
    if (open && !dlg.open) {
      setValue(initialKey || '')
      dlg.showModal()
    } else if (!open && dlg.open) {
      dlg.close()
    }
  }, [open, initialKey])

  return (
    <dialog ref={ref} className="modal-dialog" onClose={onClose} aria-labelledby="geminiModalTitle">
      <form method="dialog" onSubmit={() => onSave(value.trim())}>
        <h3 id="geminiModalTitle" className="modal-title">Configuração da API Gemini (Opcional)</h3>
        <p className="modal-text">
          A aplicação já tem um <strong>motor especialista de RF offline</strong>. Com uma chave da Google Gemini API,
          o consultor passa a usar o <strong>Gemini 3.8 Flash</strong>. A chave fica salva apenas neste navegador.
        </p>
        <div className="input-group">
          <label className="input-label" htmlFor="geminiApiKeyInput">Chave de API do Google Gemini</label>
          <input id="geminiApiKeyInput" type="password" className="input-control" placeholder="AIza..." value={value}
            onChange={(e) => setValue(e.target.value)} autoComplete="off" />
        </div>
        <div className="modal-actions">
          <button type="button" className="btn btn-secondary" onClick={onClose}>Cancelar</button>
          <button type="submit" className="btn btn-primary">Salvar Chave</button>
        </div>
      </form>
    </dialog>
  )
}
