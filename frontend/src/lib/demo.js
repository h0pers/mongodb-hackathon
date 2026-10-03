import { metres } from './geo'

const SEED = [
  ['Deep pothole outside the school gates, cars swerving round it', -6.2655, 53.3605, 'road', 2, 'roads', 0.82, 4],
  ['Street light out on the corner, very dark at night', -6.2489, 53.3385, 'lighting', 1, 'public_lighting', 0.12, 2],
  ['Pedestrian signal stuck on red at the junction', -6.2603, 53.3478, 'traffic_signal', 2, 'roads', 0.66, 3],
  ['Overflowing public bin, rubbish blowing onto the road', -6.2672, 53.3434, 'waste', 0, 'waste_management', 0.04, 1],
  ['Water leaking from the footpath for two days', -6.2817, 53.3424, 'water', 1, 'water_services', 0.21, 1],
  ['Broken glass across the cycle lane', -6.2395, 53.3442, 'road', 2, 'roads', 0.71, 2],
  ['Graffiti all over the bus shelter', -6.2958, 53.3542, 'other', 0, 'waste_management', 0.02, 1],
  ['Two street lights flickering along the canal', -6.2577, 53.3313, 'lighting', 0, 'public_lighting', 0.08, 1],
  ['Dumped mattress and bags in the lane', -6.2747, 53.3567, 'waste', 1, 'waste_management', 0.09, 2],
  ['Manhole cover rattling and slightly raised', -6.2295, 53.3392, 'road', 1, 'roads', 0.38, 1],
  ['Traffic lights out at the crossroads', -6.2245, 53.3655, 'traffic_signal', 2, 'roads', 0.88, 5],
  ['Blocked drain, big puddle across the road after rain', -6.2862, 53.3329, 'water', 0, 'water_services', 0.15, 1],
]

const RULES = [
  ['traffic_signal', 'roads', /signal|traffic light|crossing/],
  ['lighting', 'public_lighting', /light|lamp|dark/],
  ['water', 'water_services', /water|leak|flood|drain|pipe/],
  ['waste', 'waste_management', /bin|rubbish|litter|dump|bags?\b|waste/],
  ['road', 'roads', /pothole|road|footpath|pavement|cycle|crack|manhole/],
]

const COMMONS = {
  'demo-1': [
    ['Pothole on local Road in County Monaghan.jpg', 'CC0'],
    ['Pothole in Villeray, Montréal.jpg', 'Public domain'],
  ],
  'demo-2': [
    ['Broken Street Light Stevenage (The White Way Lamppost 26) - geograph.org.uk - 8268947.jpg', 'CC BY-SA 2.0'],
  ],
  'demo-3': [['Wien, Philharmonikerstraße, Ampel -- 2018 -- 3076.jpg', 'CC BY-SA 4.0']],
  'demo-4': [
    ['Overflowing bin, Mortonhall Park View - geograph.org.uk - 7601569.jpg', 'CC BY-SA 2.0'],
    ['Litter bin rubbish Lordship Lane Tottenham, London, England 1.jpg', 'CC BY-SA 4.0'],
  ],
  'demo-5': [['A photo of a water leak on Camberwell Place 2022-10-08 9.jpg', 'CC BY-SA 4.0']],
  'demo-6': [
    ['2015 broken glass on cycleway.jpg', 'CC BY-SA 3.0'],
    ['Broken glass on the road.JPG', 'CC0'],
  ],
  'demo-9': [['A fly-tipped mattress - geograph.org.uk - 4239871.jpg', 'CC BY-SA 2.0']],
  'demo-12': [['A blocked drain - geograph.org.uk - 768217.jpg', 'CC BY-SA 2.0']],
}

const media = Object.fromEntries(
  Object.entries(COMMONS).map(([id, files]) => [
    id,
    files.map(([file, license]) => ({
      id: file,
      type: 'image',
      url: `https://commons.wikimedia.org/wiki/Special:FilePath/${encodeURIComponent(file)}?width=960`,
      created_at: new Date().toISOString(),
      credit: {
        label: `Wikimedia Commons · ${license}`,
        href: `https://commons.wikimedia.org/wiki/File:${encodeURIComponent(file.replaceAll(' ', '_'))}`,
      },
    })),
  ]),
)

const answer = (value, p) => ({ value, p })

let reports = SEED.map(([description, lng, lat, category, urgency, department, hazard, count], i) => ({
  id: `demo-${i + 1}`,
  description,
  location: { type: 'Point', coordinates: [lng, lat] },
  created_at: new Date(Date.now() - (i + 1) * 47 * 60000).toISOString(),
  report_count: count,
  media_count: media[`demo-${i + 1}`]?.length ?? 0,
  needs_review: false,
  triage: {
    category: answer(category, 0.91),
    urgency: answer(urgency, 0.84),
    safety_hazard: answer(hazard > 0.5, hazard),
    department: answer(department, 0.9),
  },
}))

function classify(text) {
  const t = text.toLowerCase()
  const rule = RULES.find(([, , pattern]) => pattern.test(t))
  const hazard = /school|child|deep|danger|fell|injur|spark|flood|glass|swerv|out\b/.test(t)
  const urgency = hazard ? 2 : /week|days|broken|blocked/.test(t) ? 1 : 0
  const confidence = rule ? 0.88 : 0.41
  return {
    needs_review: confidence < 0.6,
    triage: {
      category: answer(rule?.[0] ?? 'other', confidence),
      urgency: answer(urgency, hazard ? 0.81 : 0.64),
      safety_hazard: answer(hazard, hazard ? 0.77 : 0.08),
      department: answer(rule?.[1] ?? 'roads', confidence - 0.05),
    },
  }
}

const wait = (ms) => new Promise((resolve) => setTimeout(resolve, ms))

export async function listReports() {
  await wait(300)
  return reports.map((r) => ({ ...r }))
}

const listeners = new Set()

function attach(report, file) {
  if (!file) return
  media[report.id] = [
    ...(media[report.id] ?? []),
    {
      id: `media-${Date.now()}`,
      type: file.type.startsWith('video/') ? 'video' : 'image',
      url: URL.createObjectURL(file),
      created_at: new Date().toISOString(),
    },
  ]
  report.media_count = media[report.id].length
}

function addReport(description, coordinates, file) {
  const { triage, needs_review } = classify(description)
  const existing = reports.find(
    (r) => r.triage?.category.value === triage.category.value && metres(r.location.coordinates, coordinates) <= 150,
  )
  let result
  if (existing) {
    existing.report_count += 1
    attach(existing, file)
    result = { report: { ...existing }, merged: true }
  } else {
    const report = {
      id: `demo-${Date.now()}`,
      description,
      location: { type: 'Point', coordinates },
      created_at: new Date().toISOString(),
      report_count: 1,
      media_count: 0,
      needs_review,
      triage,
    }
    attach(report, file)
    reports = [...reports, report]
    result = { report: { ...report }, merged: false }
  }
  listeners.forEach((listener) => listener(result.report))
  return result
}

export async function createReport({ description, media: file, lat, lng }) {
  await wait(900)
  return addReport(description, [lng, lat], file)
}

export async function getReportMedia(id) {
  await wait(400)
  return media[id] ?? []
}

const INCOMING = [
  'Pothole getting deeper near the bus stop',
  'Street lamp out, whole stretch is dark',
  'Bins overflowing after the weekend',
  'Water bubbling up through the road',
  'Pedestrian lights not changing',
  'Loose paving slab, someone nearly tripped',
]

export function subscribe(onReport) {
  listeners.add(onReport)
  const timer = setInterval(() => {
    const description = INCOMING[Math.floor(Math.random() * INCOMING.length)]
    const coordinates = [-6.2603 + (Math.random() - 0.5) * 0.09, 53.3498 + (Math.random() - 0.5) * 0.05]
    addReport(description, coordinates)
  }, 20000)
  return () => {
    clearInterval(timer)
    listeners.delete(onReport)
  }
}
