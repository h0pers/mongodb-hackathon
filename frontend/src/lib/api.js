import * as demo from './demo'

const base = import.meta.env.VITE_API_URL?.replace(/\/$/, '')

export const isDemo = !base

async function request(path, options) {
  const res = await fetch(`${base}${path}`, options)
  if (!res.ok) throw new Error(`Request failed (${res.status})`)
  return res.json()
}

export function listReports() {
  return isDemo ? demo.listReports() : request('/api/reports')
}

export function getReportMedia(id) {
  return isDemo ? demo.getReportMedia(id) : request(`/api/reports/${id}/media`)
}

export function subscribeReports(onReport) {
  if (isDemo) return demo.subscribe(onReport)
  const source = new EventSource(`${base}/api/reports/stream`)
  source.addEventListener('report', (event) => onReport(JSON.parse(event.data)))
  return () => source.close()
}

export function createReport({ description, media, lat, lng }) {
  if (isDemo) return demo.createReport({ description, media, lat, lng })
  const body = new FormData()
  body.append('description', description)
  body.append('lat', lat)
  body.append('lng', lng)
  if (media) body.append('media', media)
  return request('/api/reports', { method: 'POST', body })
}
