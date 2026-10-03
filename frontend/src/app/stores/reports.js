import { computed, reactive, ref } from 'vue'
import { defineStore } from 'pinia'
import { createReport, listReports, subscribeReports } from '@/lib/api'
import { metres } from '@/lib/geo'
import { urgencyOf } from '@/lib/triage'

export const useReportsStore = defineStore('reports', () => {
  const reports = ref([])
  const selectedId = ref(null)
  const droppingId = ref(null)
  const draft = reactive({ description: '', media: null, location: null })

  const areaCenter = ref(null)
  const areaRadius = ref(300)

  const area = computed(() => (areaCenter.value ? { center: areaCenter.value, radius: areaRadius.value } : null))

  const selected = computed(() => reports.value.find((r) => r.id === selectedId.value) ?? null)

  const areaReports = computed(() => {
    if (!area.value) return []
    return reports.value
      .filter((r) => metres(r.location.coordinates, area.value.center) <= area.value.radius)
      .sort((a, b) => urgencyOf(b) - urgencyOf(a) || b.report_count - a.report_count)
  })

  const geojson = computed(() => ({
    type: 'FeatureCollection',
    features: reports.value
      .filter((r) => r.id !== droppingId.value)
      .map((r) => ({
        type: 'Feature',
        id: r.id,
        geometry: r.location,
        properties: { id: r.id, urgency: urgencyOf(r), count: r.report_count },
      })),
  }))

  async function load() {
    reports.value = await listReports()
  }

  function upsert(report) {
    const index = reports.value.findIndex((r) => r.id === report.id)
    if (index === -1) {
      reports.value.push(report)
      droppingId.value = report.id
    } else {
      reports.value[index] = report
    }
  }

  function connect() {
    return subscribeReports(upsert)
  }

  async function submit() {
    const { location, description, media } = draft
    const result = await createReport({ description, media, lat: location.lat, lng: location.lng })
    upsert(result.report)
    selectedId.value = result.report.id
    Object.assign(draft, { description: '', media: null, location: null })
    return result
  }

  function select(id) {
    selectedId.value = id
  }

  function selectArea(center) {
    areaCenter.value = center
    selectedId.value = null
  }

  return {
    reports,
    selectedId,
    selected,
    droppingId,
    draft,
    area,
    areaRadius,
    areaReports,
    geojson,
    load,
    connect,
    submit,
    select,
    selectArea,
  }
})
