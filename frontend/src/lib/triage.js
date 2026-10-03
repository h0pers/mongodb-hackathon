export const URGENCY = [
  { label: 'Can wait', color: '#5b6b7a' },
  { label: 'This week', color: '#ffb21e' },
  { label: 'Today', color: '#e2412b' },
]

export const CATEGORIES = {
  road: 'Road',
  lighting: 'Lighting',
  traffic_signal: 'Traffic signal',
  waste: 'Waste',
  water: 'Water',
  other: 'Other',
}

export const DEPARTMENTS = {
  roads: 'Roads',
  public_lighting: 'Public lighting',
  waste_management: 'Waste management',
  water_services: 'Water services',
}

export const urgencyOf = (report) => report.triage?.urgency.value ?? -1

export function timeAgo(date) {
  const minutes = Math.round((Date.now() - new Date(date)) / 60000)
  if (minutes < 1) return 'now'
  if (minutes < 60) return `${minutes} min`
  if (minutes < 1440) return `${Math.round(minutes / 60)} h`
  return `${Math.round(minutes / 1440)} d`
}
