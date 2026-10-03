export const URGENCY = [
  { label: 'Can wait', color: '#5b6b7a' },
  { label: 'This week', color: '#ffb21e' },
  { label: 'Today', color: '#e2412b' },
]

export const CATEGORIES = {
  road_damage: 'Road damage',
  dirt: 'Dirt',
  litter: 'Litter',
  water_drainage: 'Water drainage',
  unsafe_area: 'Unsafe area',
  other: 'Other',
}

export const categoryLabel = (value) => CATEGORIES[value] ?? value

export const urgencyOf = (report) => report.triage?.urgency.value ?? -1

export function timeAgo(date) {
  const minutes = Math.round((Date.now() - new Date(date)) / 60000)
  if (minutes < 1) return 'now'
  if (minutes < 60) return `${minutes} min`
  if (minutes < 1440) return `${Math.round(minutes / 60)} h`
  return `${Math.round(minutes / 1440)} d`
}
