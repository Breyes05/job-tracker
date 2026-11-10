import { useEffect } from 'react'

// A short confirmation at the bottom of the screen ("Added Google").
export default function Toast({ message, onDone }) {
  useEffect(() => {
    if (!message) return
    const timer = setTimeout(onDone, 4000)
    return () => clearTimeout(timer)
  }, [message, onDone])

  if (!message) return null
  return (
    <div className={`toast${message.isError ? ' toast-error' : ''}`} role="status">
      {message.text}
    </div>
  )
}
