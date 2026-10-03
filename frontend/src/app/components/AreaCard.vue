<script setup>
import { computed } from 'vue'
import { ChevronRight, X } from '@lucide/vue'
import { Button } from '@/components/ui/button'
import { Card, CardAction, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Slider } from '@/components/ui/slider'
import { CATEGORIES, URGENCY, timeAgo, urgencyOf } from '@/lib/triage'

const props = defineProps({ reports: { type: Array, required: true } })
const radius = defineModel('radius', { type: Number, required: true })
const emit = defineEmits(['select', 'close'])

const distance = computed(() => (radius.value >= 1000 ? `${radius.value / 1000} km` : `${radius.value} m`))
const today = computed(() => props.reports.filter((r) => urgencyOf(r) === 2).length)
const summary = computed(() => {
  const count = props.reports.length
  if (!count) return `Nothing reported within ${distance.value}`
  return `${count} ${count === 1 ? 'problem' : 'problems'} within ${distance.value}`
})
</script>

<template>
  <Card class="max-h-[50dvh] gap-2 overflow-x-hidden overflow-y-auto border-0 py-4 shadow-float" aria-live="polite">
    <CardHeader class="px-4">
      <CardTitle>{{ summary }}</CardTitle>
      <CardDescription>
        {{ reports.length ? `${today} need fixing today` : 'Tap somewhere else on the heatmap to look around.' }}
      </CardDescription>
      <CardAction>
        <Button
          variant="ghost"
          size="icon-sm"
          aria-label="Close"
          class="-mt-2 -mr-3 size-11 md:-mt-1 md:-mr-2 md:size-8"
          @click="emit('close')"
        >
          <X />
        </Button>
      </CardAction>
    </CardHeader>

    <CardContent class="flex items-center gap-3 px-4 pt-1 pb-2">
      <span class="text-sm text-muted-foreground">Range</span>
      <Slider
        :model-value="[radius]"
        :min="100"
        :max="1000"
        :step="50"
        aria-label="Search range"
        class="flex-1"
        @update:model-value="([value]) => (radius = value)"
      />
      <span class="w-14 text-right text-sm font-bold tabular-nums">{{ distance }}</span>
    </CardContent>

    <CardContent v-if="reports.length" class="min-w-0 px-2">
      <ul class="grid grid-cols-[minmax(0,1fr)]">
        <li v-for="report in reports" :key="report.id" class="min-w-0">
          <button
            type="button"
            class="block w-full overflow-hidden rounded-md px-2 py-2 text-left hover:bg-muted focus-visible:bg-muted focus-visible:outline-none"
            @click="emit('select', report.id)"
          >
            <span class="grid grid-cols-[0.75rem_minmax(0,1fr)_auto_1rem] items-center gap-3">
              <span
                class="size-3 rounded-[3px] ring-1 ring-border"
                :style="{ background: URGENCY[urgencyOf(report)]?.color ?? '#ffffff' }"
              />
              <span class="min-w-0 overflow-hidden">
                <span class="block truncate text-sm font-bold">
                  {{ URGENCY[urgencyOf(report)]?.label ?? 'Being sorted' }}
                  · {{ CATEGORIES[report.triage?.category.value] ?? 'New report' }}
                </span>
                <span class="block truncate text-sm text-muted-foreground">{{ report.description }}</span>
              </span>
              <span class="text-right text-xs whitespace-nowrap text-muted-foreground tabular-nums">
                <span class="block font-bold text-foreground">{{ report.report_count }}×</span>
                {{ timeAgo(report.created_at) }}
              </span>
              <ChevronRight class="size-4 text-muted-foreground" />
            </span>
          </button>
        </li>
      </ul>
    </CardContent>
  </Card>
</template>
