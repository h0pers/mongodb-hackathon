<script setup>
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useDark } from '@vueuse/core'
import { Check, LocateFixed, Plus, X } from '@lucide/vue'
import { toast } from 'vue-sonner'
import AppHeader from '@/app/components/AppHeader.vue'
import AreaCard from '@/app/components/AreaCard.vue'
import ReportDialog from '@/app/components/ReportDialog.vue'
import ReportMap from '@/app/components/ReportMap.vue'
import ReportCard from '@/app/components/ReportCard.vue'
import { useGeolocation } from '@/app/composables/useGeolocation'
import { useReportsStore } from '@/app/stores/reports'
import { Button } from '@/components/ui/button'
import { Spinner } from '@/components/ui/spinner'
import { Tooltip, TooltipContent, TooltipTrigger } from '@/components/ui/tooltip'
import { CATEGORIES, URGENCY } from '@/lib/triage'

const store = useReportsStore()
const { position, status, locate } = useGeolocation()
const map = ref(null)
const layer = ref('pins')
const dark = useDark({ storageKey: 'dublin-fix:theme' })
const reporting = ref(false)
const picking = ref(false)
let disconnect

const dropping = computed(() => store.reports.find((r) => r.id === store.droppingId) ?? null)

onMounted(async () => {
  await store.load().catch(() => toast.error("Couldn't load reports. Check your connection."))
  disconnect = store.connect()
})

onBeforeUnmount(() => disconnect?.())

watch(layer, (value) => value === 'pins' && store.selectArea(null))

function select(id) {
  store.select(id)
  if (store.selected) map.value.flyTo(store.selected.location.coordinates)
}

async function locateMe() {
  const pos = await locate()
  if (pos) map.value.flyTo([pos.lng, pos.lat], 16)
  else if (status.value === 'denied') toast.error('Location access is blocked. Allow it in your browser settings.')
  else toast.error("Couldn't find your location. Try again outdoors.")
}

function startPicking() {
  reporting.value = false
  picking.value = true
  const loc = store.draft.location ?? position.value
  if (loc) map.value.flyTo([loc.lng, loc.lat], 17)
}

function finishPicking(confirmed) {
  if (confirmed) store.draft.location = { ...map.value.getCenter(), source: 'map' }
  picking.value = false
  reporting.value = true
}

function onSubmitted({ report, merged }) {
  map.value.flyTo(report.location.coordinates, 16)
  const t = report.triage
  const sorted = t ? `${URGENCY[t.urgency.value].label} · ${CATEGORIES[t.category.value]}` : 'Waiting to be sorted'
  if (merged) {
    toast.success('Added to an existing report', {
      description: `${report.report_count} people have reported this. ${sorted}.`,
    })
  } else {
    toast.success('Report sent', {
      description: report.needs_review ? `${sorted}. A person will double-check the sorting.` : `${sorted}.`,
    })
  }
}
</script>

<template>
  <div class="relative h-dvh overflow-hidden">
    <ReportMap
      ref="map"
      class="absolute inset-0"
      :data="store.geojson"
      :selected-id="store.selectedId"
      :layer="layer"
      :user-position="position"
      :dropping="dropping"
      :area="layer === 'heat' ? store.area : null"
      :dark="dark"
      @select="select"
      @area="store.selectArea"
      @dropped="store.droppingId = null"
    />

    <AppHeader v-model:layer="layer" v-model:dark="dark" class="absolute inset-x-0 top-0 z-10" />

    <p
      v-if="layer === 'heat' && !store.area && !store.selected"
      class="pointer-events-none absolute top-[calc(var(--header-height)+0.75rem)] left-1/2 z-10 -translate-x-1/2 rounded-md bg-panel px-3 py-2 text-sm font-bold whitespace-nowrap text-led shadow-float"
    >
      Tap the map to see problems nearby
    </p>

    <div v-if="picking" class="pointer-events-none absolute inset-0 z-10 grid place-items-center">
      <p class="absolute top-[calc(var(--header-height)+0.75rem)] rounded-md bg-panel px-3 py-2 text-sm font-bold text-led shadow-float">
        Move the map to place the pin
      </p>
      <svg width="28" height="40" viewBox="0 0 28 40" class="-translate-y-1/2" aria-hidden="true">
        <rect x="13" y="24" width="2" height="13" fill="#11161d" />
        <circle cx="14" cy="37" r="2.5" fill="#11161d" />
        <rect x="3" y="3" width="22" height="22" rx="5" fill="#11161d" stroke="#ffffff" stroke-width="2.5" />
      </svg>
    </div>

    <div
      class="absolute inset-x-0 bottom-0 z-10 grid gap-3 p-3 pb-[max(0.75rem,env(safe-area-inset-bottom))] md:left-1/2 md:w-120 md:-translate-x-1/2"
    >
      <ReportCard v-if="store.selected && !picking" :report="store.selected" @close="store.select(null)" />
      <AreaCard
        v-else-if="layer === 'heat' && store.area && !picking"
        :reports="store.areaReports"
        v-model:radius="store.areaRadius"
        @select="select"
        @close="store.selectArea(null)"
      />

      <div v-if="picking" class="flex gap-3">
        <Button variant="outline" class="h-14 bg-card px-5 text-base shadow-float" @click="finishPicking(false)">
          <X />
          Cancel
        </Button>
        <Button class="h-14 flex-1 text-base font-bold shadow-float" @click="finishPicking(true)">
          <Check />
          Set location here
        </Button>
      </div>

      <div v-else class="flex gap-1.5">
        <Tooltip>
          <TooltipTrigger as-child>
            <Button
              variant="outline"
              class="size-14 shrink-0 bg-card shadow-float"
              aria-label="Show my location"
              @click="locateMe"
            >
              <Spinner v-if="status === 'locating'" class="size-5" />
              <LocateFixed v-else class="size-5" />
            </Button>
          </TooltipTrigger>
          <TooltipContent>Show my location</TooltipContent>
        </Tooltip>
        <Button class="h-14 flex-1 text-base font-bold shadow-float" @click="reporting = true">
          <Plus class="size-5" />
          Report a problem
        </Button>
      </div>
    </div>

    <ReportDialog v-model:open="reporting" @pick="startPicking" @submitted="onSubmitted" />
  </div>
</template>
