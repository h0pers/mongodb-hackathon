const EARTH_RADIUS = 6371000
const RAD = Math.PI / 180

export function metres([lng1, lat1], [lng2, lat2]) {
  const x = (lng2 - lng1) * RAD * Math.cos(((lat1 + lat2) / 2) * RAD)
  const y = (lat2 - lat1) * RAD
  return Math.hypot(x, y) * EARTH_RADIUS
}

export function circle([lng, lat], radius, steps = 64) {
  const dLat = radius / EARTH_RADIUS / RAD
  const dLng = dLat / Math.cos(lat * RAD)
  const ring = Array.from({ length: steps + 1 }, (_, i) => {
    const angle = (i / steps) * 2 * Math.PI
    return [lng + dLng * Math.cos(angle), lat + dLat * Math.sin(angle)]
  })
  return { type: 'Polygon', coordinates: [ring] }
}
