import { useEffect, useState } from 'react'
import { subscribeToSlowRequests } from '../api.js'

// Render's free tier sleeps when idle, so the first request can take up to a
// minute. Without this, a slow first load looks like a broken app.
export default function SlowServerNotice() {
  const [isSlow, setIsSlow] = useState(false)

  useEffect(() => subscribeToSlowRequests(setIsSlow), [])

  if (!isSlow) return null
  return (
    <div className="slow-notice" role="status">
      Waking up the server. This can take up to a minute.
    </div>
  )
}
