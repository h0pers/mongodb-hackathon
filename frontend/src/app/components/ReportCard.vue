<script setup>
import { computed, ref, watch } from 'vue'
import { Play, ShieldQuestion, X } from '@lucide/vue'
import MediaViewer from '@/app/components/MediaViewer.vue'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Button } from '@/components/ui/button'
import { Card, CardAction, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Separator } from '@/components/ui/separator'
import { Skeleton } from '@/components/ui/skeleton'
import { getReportMedia } from '@/lib/api'
import { CATEGORIES, DEPARTMENTS, URGENCY, timeAgo } from '@/lib/triage'

const props = defineProps({ report: { type: Object, required: true } })
const emit = defineEmits(['close'])

const media = ref([])
const loading = ref(false)
const viewerOpen = ref(false)
const viewerStart = ref(0)

const triage = computed(() => props.report.triage)
const urgency = computed(() => URGENCY[triage.value?.urgency.value])
const hazard = computed(() => {
  const answer = triage.value?.safety_hazard
  return answer ? `${answer.value ? 'Likely' : 'Unlikely'} ${Math.round(answer.p * 100)}%` : '—'
})

watch(
  () => [props.report.id, props.report.media_count],
  async ([id], [previousId] = []) => {
    if (id !== previousId) media.value = []
    if (!props.report.media_count) return
    loading.value = true
    try {
      const items = await getReportMedia(id)
      if (props.report.id === id) media.value = items
    } catch {
      media.value = []
    } finally {
      loading.value = false
    }
  },
  { immediate: true },
)

function view(index) {
  viewerStart.value = index
  viewerOpen.value = true
}
</script>

<template>
  <Card class="max-h-[50dvh] gap-3 overflow-y-auto border-0 py-4 shadow-float" aria-live="polite">
    <CardHeader class="px-4">
      <CardTitle class="flex items-center gap-2">
        <span
          class="size-3.5 shrink-0 rounded-[3px] ring-1 ring-border"
          :style="{ background: urgency?.color ?? '#ffffff' }"
        />
        {{ urgency ? `${urgency.label} · ${CATEGORIES[triage.category.value]}` : 'Being sorted' }}
      </CardTitle>
      <CardDescription v-if="triage">{{ DEPARTMENTS[triage.department.value] }}</CardDescription>
      <CardAction>
        <Button variant="ghost" size="icon-sm" aria-label="Close" class="-mt-1 -mr-2" @click="emit('close')">
          <X />
        </Button>
      </CardAction>
    </CardHeader>

    <CardContent class="grid gap-3 px-4">
      <p class="text-[15px] leading-snug">{{ report.description }}</p>

      <div v-if="loading && !media.length" class="flex gap-2">
        <Skeleton v-for="n in Math.min(report.media_count, 3)" :key="n" class="size-20 shrink-0 rounded-md" />
      </div>
      <ul
        v-else-if="media.length"
        class="-mx-4 flex snap-x gap-2 overflow-x-auto px-4 [scrollbar-width:none]"
        aria-label="Photos and videos"
      >
        <li v-for="(item, index) in media" :key="item.id" class="shrink-0 snap-start">
          <button
            type="button"
            class="relative block size-20 overflow-hidden rounded-md bg-muted focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
            :aria-label="`Open ${item.type} ${index + 1} of ${media.length}`"
            @click="view(index)"
          >
            <template v-if="item.type === 'video'">
              <video :src="item.url" muted preload="metadata" class="size-full object-cover" />
              <span class="absolute inset-0 grid place-items-center bg-black/25">
                <Play class="size-5 fill-white text-white" />
              </span>
            </template>
            <img v-else :src="item.url" alt="" loading="lazy" class="size-full object-cover" />
          </button>
        </li>
      </ul>

      <Separator />
      <dl class="grid grid-cols-3 gap-2 text-sm">
        <div>
          <dt class="text-muted-foreground">Reported</dt>
          <dd class="font-bold tabular-nums">{{ report.report_count }}×</dd>
        </div>
        <div>
          <dt class="text-muted-foreground">Safety hazard</dt>
          <dd class="font-bold tabular-nums">{{ hazard }}</dd>
        </div>
        <div>
          <dt class="text-muted-foreground">First report</dt>
          <dd class="font-bold tabular-nums">{{ timeAgo(report.created_at) }}</dd>
        </div>
      </dl>

      <Alert v-if="report.needs_review" class="bg-muted">
        <ShieldQuestion />
        <AlertDescription>The model wasn't sure about this one, so a person will check the sorting.</AlertDescription>
      </Alert>
    </CardContent>
  </Card>

  <MediaViewer v-model:open="viewerOpen" :items="media" :start="viewerStart" />
</template>
