<script setup>
import { Map as MapLibre, Marker, setWorkerUrl } from 'maplibre-gl'
import workerUrl from 'maplibre-gl/dist/maplibre-gl-worker.mjs?worker&url'
import 'maplibre-gl/dist/maplibre-gl.css'
import { onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { circle } from '@/lib/geo'
import { URGENCY } from '@/lib/triage'

const props = defineProps({
  data: { type: Object, required: true },
  selectedId: { type: String, default: null },
  layer: { type: String, default: 'pins' },
  userPosition: { type: Object, default: null },
  dropping: { type: Object, default: null },
  area: { type: Object, default: null },
  dark: { type: Boolean, default: false },
})
const emit = defineEmits(['select', 'area', 'dropped'])

const areaData = () => ({
  type: 'FeatureCollection',
  features: props.area ? [{ type: 'Feature', geometry: circle(props.area.center, props.area.radius) }] : [],
})

setWorkerUrl(workerUrl)

const INK = '#11161d'
const TAP_TOLERANCE = 16
const PLATE_OFFSET = 26
const styleUrl = () => `https://tiles.openfreemap.org/styles/${props.dark ? 'dark' : 'positron'}`
const areaColor = () => (props.dark ? '#ffb21e' : INK)
const container = ref(null)
let map
let userMarker

function drawFlag(fill, stroke = '#ffffff') {
  const canvas = document.createElement('canvas')
  canvas.width = 56
  canvas.height = 80
  const ctx = canvas.getContext('2d')
  ctx.scale(2, 2)
  ctx.fillStyle = INK
  ctx.fillRect(13, 24, 2, 13)
  ctx.beginPath()
  ctx.arc(14, 37, 2.5, 0, Math.PI * 2)
  ctx.fill()
  ctx.shadowColor = 'rgba(17, 22, 29, 0.3)'
  ctx.shadowBlur = 3
  ctx.shadowOffsetY = 1
  ctx.beginPath()
  ctx.roundRect(3, 3, 22, 22, 5)
  ctx.fillStyle = fill
  ctx.fill()
  ctx.shadowColor = 'transparent'
  ctx.lineWidth = 2.5
  ctx.strokeStyle = stroke
  ctx.stroke()
  return canvas
}

const flagFor = (urgency) => (urgency >= 0 ? drawFlag(URGENCY[urgency].color) : drawFlag('#ffffff', INK))

const isSelected = () => ['==', ['get', 'id'], props.selectedId ?? '']

const selectionLayout = () => ({
  'icon-size': ['case', isSelected(), 1.3, 1],
  'symbol-sort-key': ['case', isSelected(), 10, ['get', 'urgency']],
  'text-size': ['case', isSelected(), 14, 12],
  'text-offset': ['case', isSelected(), ['literal', [0, -2.4]], ['literal', [0, -2.15]]],
})

function addLayers() {
  for (const u of [-1, 0, 1, 2]) {
    if (map.hasImage(`flag-${u}`)) continue
    const canvas = flagFor(u)
    map.addImage(`flag-${u}`, canvas.getContext('2d').getImageData(0, 0, canvas.width, canvas.height), {
      pixelRatio: 2,
    })
  }
  map.addSource('reports', { type: 'geojson', data: props.data })
  map.addLayer({
    id: 'reports-heat',
    type: 'heatmap',
    source: 'reports',
    layout: { visibility: props.layer === 'heat' ? 'visible' : 'none' },
    paint: {
      'heatmap-weight': ['/', ['*', ['+', 1, ['max', ['get', 'urgency'], 0]], ['get', 'count']], 6],
      'heatmap-intensity': ['interpolate', ['linear'], ['zoom'], 10, 0.8, 15, 2],
      'heatmap-radius': ['interpolate', ['linear'], ['zoom'], 10, 20, 15, 50],
      'heatmap-color': [
        'interpolate',
        ['linear'],
        ['heatmap-density'],
        0,
        'rgba(91, 107, 122, 0)',
        0.25,
        'rgba(91, 107, 122, 0.4)',
        0.5,
        '#ffb21e',
        0.85,
        '#e2412b',
        1,
        '#a82614',
      ],
      'heatmap-opacity': 0.85,
    },
  })
  map.addSource('area', { type: 'geojson', data: areaData() })
  map.addLayer({
    id: 'area-fill',
    type: 'fill',
    source: 'area',
    paint: { 'fill-color': areaColor(), 'fill-opacity': 0.08 },
  })
  map.addLayer({
    id: 'area-line',
    type: 'line',
    source: 'area',
    paint: { 'line-color': areaColor(), 'line-width': 2, 'line-dasharray': [2, 1.5] },
  })
  map.addLayer({
    id: 'reports-pins',
    type: 'symbol',
    source: 'reports',
    layout: {
      visibility: props.layer === 'pins' ? 'visible' : 'none',
      'icon-image': ['concat', 'flag-', ['to-string', ['get', 'urgency']]],
      'icon-anchor': 'bottom',
      'icon-allow-overlap': true,
      'icon-ignore-placement': true,
      'text-field': ['to-string', ['get', 'count']],
      'text-font': ['Noto Sans Bold'],
      'text-allow-overlap': true,
      'text-ignore-placement': true,
      ...selectionLayout(),
    },
    paint: {
      'text-color': ['match', ['get', 'urgency'], [-1, 1], INK, '#ffffff'],
    },
  })
}

function userDot() {
  const el = document.createElement('div')
  el.className = 'relative size-4'
  el.innerHTML =
    '<span class="absolute inset-0 rounded-full bg-panel animate-pulse-ring"></span>' +
    '<span class="absolute inset-0 rounded-full border-[3px] border-white bg-panel shadow-float"></span>'
  return el
}

onMounted(() => {
  map = new MapLibre({
    container: container.value,
    style: styleUrl(),
    center: [-6.2603, 53.3498],
    zoom: 12.8,
    minZoom: 10,
    maxBounds: [
      [-6.75, 53.1],
      [-5.85, 53.65],
    ],
    attributionControl: { compact: true },
  })
  map.on('style.load', addLayers)
  map.touchZoomRotate.disableRotation()
  map.touchPitch.disable()
  map.dragRotate.disable()
  map.on('click', (e) => {
    if (props.layer === 'heat') return emit('area', [e.lngLat.lng, e.lngLat.lat])
    const { x, y } = e.point
    const hits = map.queryRenderedFeatures(
      [
        [x - TAP_TOLERANCE, y - TAP_TOLERANCE],
        [x + TAP_TOLERANCE, y + TAP_TOLERANCE],
      ],
      { layers: ['reports-pins'] },
    )
    const distance = (feature) => {
      const pin = map.project(feature.geometry.coordinates)
      return Math.hypot(pin.x - x, pin.y - PLATE_OFFSET - y)
    }
    const nearest = hits.sort((a, b) => distance(a) - distance(b))[0]
    emit('select', nearest?.properties.id ?? null)
  })
  map.on('mouseenter', 'reports-pins', () => (map.getCanvas().style.cursor = 'pointer'))
  map.on('mouseleave', 'reports-pins', () => (map.getCanvas().style.cursor = ''))
})

watch(
  () => props.dark,
  () => map?.setStyle(styleUrl(), { diff: false }),
)

onBeforeUnmount(() => map?.remove())

watch(
  () => props.data,
  (data) => map?.getSource('reports')?.setData(data),
)

watch(
  () => props.area,
  () => map?.getSource('area')?.setData(areaData()),
)

watch(
  () => props.selectedId,
  () => {
    if (!map?.getLayer('reports-pins')) return
    for (const [key, value] of Object.entries(selectionLayout())) map.setLayoutProperty('reports-pins', key, value)
  },
)

watch(
  () => props.layer,
  (layer) => {
    if (!map?.getLayer('reports-pins')) return
    map.setLayoutProperty('reports-pins', 'visibility', layer === 'pins' ? 'visible' : 'none')
    map.setLayoutProperty('reports-heat', 'visibility', layer === 'heat' ? 'visible' : 'none')
    map.getCanvas().style.cursor = layer === 'heat' ? 'crosshair' : ''
  },
)

watch(
  () => props.userPosition,
  (pos) => {
    if (!pos) return
    userMarker ??= new Marker({ element: userDot() })
    userMarker.setLngLat([pos.lng, pos.lat]).addTo(map)
  },
)

watch(
  () => props.dropping,
  (report) => {
    if (!report) return
    const flag = flagFor(report.triage?.urgency.value ?? -1)
    flag.className = 'h-10 w-7 animate-flag-drop'
    const el = document.createElement('div')
    el.appendChild(flag)
    const marker = new Marker({ element: el, anchor: 'bottom' })
      .setLngLat(report.location.coordinates)
      .addTo(map)
    flag.addEventListener(
      'animationend',
      () => {
        marker.remove()
        emit('dropped')
      },
      { once: true },
    )
  },
)

function flyTo(center, zoom = 15) {
  map.flyTo({ center, zoom: Math.max(map.getZoom(), zoom), essential: true })
}

function getCenter() {
  const { lat, lng } = map.getCenter()
  return { lat, lng }
}

defineExpose({ flyTo, getCenter })
</script>

<template>
  <div role="region" aria-label="Map of reported problems in Dublin">
    <div ref="container" class="size-full" />
  </div>
</template>