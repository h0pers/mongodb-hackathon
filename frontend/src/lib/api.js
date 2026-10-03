import * as demo from './demo'

const base = import.meta.env.VITE_API_URL?.replace(/\/$/, '') ?? ''
const REVIEW_THRESHOLD = 0.6

export const isDemo = !base

async function request(path, options) {
  const res = await fetch(`${base}${path}`, options)
  if (!res.ok) {
    const body = await res.json().catch(() => null)
    const detail = typeof body?.detail === 'string' ? body.detail : null
    throw new Error(detail ?? `Request failed (${res.status})`)
  }
  return res.json()
}

const mediaUrl = (path) => (/^(https?:|blob:)/.test(path) ? path : `${base}${path}`)
const createdAt = (id) => new Date(parseInt(id.slice(0, 8), 16) * 1000).toISOString()

function creditOf(doc) {
  const credit = doc.photoCredit
  if (credit) return { label: [credit.author, credit.license].filter(Boolean).join(' · '), href: credit.source }
  const file = doc.photoUrl?.match(/commons\.wikimedia\.org\/wiki\/Special:FilePath\/([^?]+)/)?.[1]
  return file ? { label: 'Wikimedia Commons', href: `https://commons.wikimedia.org/wiki/File:${file}` } : undefined
}

export function fromApi(doc) {
  const classified = doc.category != null
  const confidence = doc.confidence ?? {}
  return {
    id: doc._id,
    description: doc.text,
    location: doc.location,
    created_at: createdAt(doc._id),
    report_count: doc.reportCount ?? 1,
    needs_review: classified && Object.values(confidence).some((p) => p < REVIEW_THRESHOLD),
    media: doc.photoUrl
      ? [{ id: doc.photoUrl, type: 'image', url: mediaUrl(doc.photoUrl), credit: creditOf(doc) }]
      : [],
    triage: classified
      ? {
          category: { value: doc.category, p: confidence.category ?? 1 },
          urgency: { value: Math.min(2, Math.max(0, Math.round(doc.urgency ?? 0))), p: confidence.urgency ?? 1 },
          safety_hazard: { value: (doc.safetyHazard ?? 0) >= 0.5, p: doc.safetyHazard ?? 0 },
          department: { value: doc.department },
        }
      : null,
  }
}

export async function listReports() {
  const docs = isDemo ? await demo.listReports() : await request('/reports')
  return docs.map(fromApi)
}

export async function createReport({ text, photo, lat, lng }) {
  if (isDemo) return fromApi(await demo.createReport({ text, photo, lat, lng }))
  const body = new FormData()
  body.append('text', text)
  body.append('lng', lng)
  body.append('lat', lat)
  if (photo) body.append('photo', photo)
  return fromApi(await request('/reports', { method: 'POST', body }))
}

export function subscribeReports(onReport, onReconnect) {
  if (isDemo) return demo.subscribe((doc) => onReport(fromApi(doc)))
  const source = new EventSource(`${base}/events`)
  let opened = false
  source.onopen = () => {
    if (opened) onReconnect?.()
    opened = true
  }
  source.onmessage = (event) => onReport(fromApi(JSON.parse(event.data)))
  return () => source.close()
}
