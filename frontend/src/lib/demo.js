const DEPARTMENTS = {
  road_damage: 'Roads Maintenance',
  dirt: 'Street Cleaning',
  litter: 'Waste Management',
  water_drainage: 'Drainage and Water',
  unsafe_area: 'Community Safety',
  other: 'General Enquiries',
}

const commons = (file, license) => ({
  photoUrl: `https://commons.wikimedia.org/wiki/Special:FilePath/${encodeURIComponent(file)}?width=960`,
  photoCredit: {
    author: 'Wikimedia Commons',
    license,
    source: `https://commons.wikimedia.org/wiki/File:${encodeURIComponent(file.replaceAll(' ', '_'))}`,
  },
})

const SEED = [
  [
    'Deep pothole outside the school gates, cars swerving round it',
    -6.2655,
    53.3605,
    'road_damage',
    1.9,
    0.82,
    0.93,
    commons('Pothole on local Road in County Monaghan.jpg', 'CC0'),
  ],
  [
    'Street light out on the corner, very dark at night',
    -6.2489,
    53.3385,
    'other',
    1.1,
    0.3,
    0.71,
    commons(
      'Broken Street Light Stevenage (The White Way Lamppost 26) - geograph.org.uk - 8268947.jpg',
      'CC BY-SA 2.0',
    ),
  ],
  [
    'Pedestrian signal stuck on red at the junction',
    -6.2603,
    53.3478,
    'other',
    1.8,
    0.66,
    0.64,
    commons('Wien, Philharmonikerstraße, Ampel -- 2018 -- 3076.jpg', 'CC BY-SA 4.0'),
  ],
  [
    'Overflowing public bin, rubbish blowing onto the road',
    -6.2672,
    53.3434,
    'litter',
    0.4,
    0.04,
    0.95,
    commons('Overflowing bin, Mortonhall Park View - geograph.org.uk - 7601569.jpg', 'CC BY-SA 2.0'),
  ],
  [
    'Water leaking from the footpath for two days',
    -6.2817,
    53.3424,
    'water_drainage',
    1.2,
    0.21,
    0.9,
    commons('A photo of a water leak on Camberwell Place 2022-10-08 9.jpg', 'CC BY-SA 4.0'),
  ],
  [
    'Broken glass across the cycle lane',
    -6.2395,
    53.3442,
    'litter',
    1.7,
    0.71,
    0.82,
    commons('2015 broken glass on cycleway.jpg', 'CC BY-SA 3.0'),
  ],
  ['Graffiti all over the bus shelter', -6.2958, 53.3542, 'other', 0.2, 0.02, 0.77, null],
  ['Mud and wet leaves all over the footpath by the canal', -6.2577, 53.3313, 'dirt', 0.6, 0.3, 0.88, null],
  [
    'Dumped mattress and bags in the lane',
    -6.2747,
    53.3567,
    'litter',
    1.0,
    0.09,
    0.97,
    commons('A fly-tipped mattress - geograph.org.uk - 4239871.jpg', 'CC BY-SA 2.0'),
  ],
  ['Manhole cover rattling and slightly raised', -6.2295, 53.3392, 'road_damage', 1.2, 0.38, 0.86, null],
  [
    'People dealing in the lane every night, feels unsafe walking home',
    -6.2245,
    53.3655,
    'unsafe_area',
    1.6,
    0.7,
    0.52,
    null,
  ],
  [
    'Blocked drain, big puddle across the road after rain',
    -6.2862,
    53.3329,
    'water_drainage',
    0.4,
    0.15,
    0.91,
    commons('A blocked drain - geograph.org.uk - 768217.jpg', 'CC BY-SA 2.0'),
  ],
]

const RULES = [
  ['unsafe_area', /unsafe|drug|dealing|harass|threat|fight|anti-social/],
  ['water_drainage', /water|leak|flood|drain|pipe|puddle/],
  ['dirt', /mud|dirt|spill|stain|dust|leaves/],
  ['litter', /bin|rubbish|litter|dump|bags?\b|mattress|glass/],
  ['road_damage', /pothole|road|footpath|pavement|crack|manhole/],
]

function objectId(date = new Date()) {
  const seconds = Math.floor(date / 1000)
    .toString(16)
    .padStart(8, '0')
  const random = Array.from({ length: 16 }, () => Math.floor(Math.random() * 16).toString(16)).join('')
  return seconds + random
}

function document(text, [lng, lat], answers, extra = {}, date) {
  return {
    _id: objectId(date),
    text,
    photoUrl: null,
    location: { type: 'Point', coordinates: [lng, lat] },
    ...answers,
    ...extra,
  }
}

function classify(text) {
  const t = text.toLowerCase()
  const category = RULES.find(([, pattern]) => pattern.test(t))?.[0] ?? 'other'
  const hazard = /school|child|deep|danger|fell|injur|spark|flood|glass|swerv|unsafe/.test(t)
  return {
    category,
    department: DEPARTMENTS[category],
    urgency: hazard ? 1.8 : /week|days|broken|blocked/.test(t) ? 1.1 : 0.4,
    safetyHazard: hazard ? 0.77 : 0.08,
    confidence: { category: category === 'other' ? 0.41 : 0.88, urgency: hazard ? 0.81 : 0.64 },
  }
}

let reports = SEED.map(([text, lng, lat, category, urgency, safetyHazard, confidence, photo], i) =>
  document(
    text,
    [lng, lat],
    {
      category,
      department: DEPARTMENTS[category],
      urgency,
      safetyHazard,
      confidence: { category: confidence, urgency: 0.8 },
    },
    photo ?? {},
    new Date(Date.now() - (i + 1) * 47 * 60000),
  ),
)

const listeners = new Set()
const wait = (ms) => new Promise((resolve) => setTimeout(resolve, ms))

function insert(text, coordinates, photo) {
  const report = document(text, coordinates, classify(text), photo ? { photoUrl: URL.createObjectURL(photo) } : {})
  reports = [...reports, report]
  listeners.forEach((listener) => listener(report))
  return report
}

export async function listReports() {
  await wait(300)
  return reports
}

export async function createReport({ text, photo, lat, lng }) {
  await wait(900)
  return insert(text, [lng, lat], photo)
}

const INCOMING = [
  'Pothole getting deeper near the bus stop',
  'Mud spilled all over the footpath from the building site',
  'Bins overflowing after the weekend',
  'Water bubbling up through the road',
  'Group harassing people at the bus stop, feels unsafe',
  'Loose paving slab, someone nearly tripped',
]

export function subscribe(onReport) {
  listeners.add(onReport)
  const timer = setInterval(() => {
    const text = INCOMING[Math.floor(Math.random() * INCOMING.length)]
    insert(text, [-6.2603 + (Math.random() - 0.5) * 0.09, 53.3498 + (Math.random() - 0.5) * 0.05])
  }, 20000)
  return () => {
    clearInterval(timer)
    listeners.delete(onReport)
  }
}
