import { useEffect, useRef } from 'react'

// A modal built on the browser's <dialog> element, which handles focus,
// the Escape key, and keeping the rest of the page from being clicked.
export default function Dialog({ title, onClose, children, size = 'md' }) {
  const ref = useRef(null)

  useEffect(() => {
    const dialog = ref.current
    if (!dialog.open) dialog.showModal()
    return () => dialog.close()
  }, [])

  function handleCancel(event) {
    // Escape key: let React decide when to close, so state stays in sync.
    event.preventDefault()
    onClose()
  }

  function handleClick(event) {
    // A click on the backdrop lands on the <dialog> itself, not its contents.
    if (event.target === ref.current) onClose()
  }

  return (
    <dialog
      ref={ref}
      className={`dialog dialog-${size}`}
      aria-labelledby="dialog-title"
      onCancel={handleCancel}
      onClick={handleClick}
    >
      <div className="dialog-body">
        <div className="dialog-header">
          <h2 id="dialog-title">{title}</h2>
          <button type="button" className="icon-button" aria-label="Close" onClick={onClose}>
            ×
          </button>
        </div>
        {children}
      </div>
    </dialog>
  )
}
