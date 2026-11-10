// The four statuses the API accepts (the `Status` enum in app/models.py).
export const STATUSES = [
  { value: 'applied', label: 'Applied' },
  { value: 'interviewing', label: 'Interviewing' },
  { value: 'offer', label: 'Offer' },
  { value: 'rejected', label: 'Rejected' },
]

export const STATUS_LABELS = Object.fromEntries(STATUSES.map((s) => [s.value, s.label]))
