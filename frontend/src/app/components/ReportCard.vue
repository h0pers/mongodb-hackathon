<script setup>
import { computed, ref, watch } from 'vue'
import { Play, ShieldQuestion, X } from '@lucide/vue'
import MediaViewer from '@/app/components/MediaViewer.vue'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Button } from '@/components/ui/button'
import { Card, CardAction, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Separator } from '@/components/ui/separator'
import { URGENCY, categoryLabel, timeAgo } from '@/lib/triage'

const props = defineProps({ report: { type: Object, required: true } })
const emit = defineEmits(['close'])

const media = computed(() => props.report.media)
const viewerOpen = ref(false)
const viewerStart = ref(0)
const text = ref(null)
const expanded = ref(false)
const clamped = ref(false)

watch(
  () => props.report.description,
  () => {
    expanded.value = false
    clamped.value = text.value ? text.value.scrollHeight > text.value.clientHeight + 1 : false
  },
  { immediate: true, flush: 'post' },
)

const triage = computed(() => props.report.triage)
const urgency = computed(() => URGENCY[triage.value?.urgency.value])
const hazard = computed(() => {
  const answer = triage.value?.safety_hazard
  return answer ? `${answer.value ? 'Likely' : 'Unlikely'} ${Math.round(answer.p * 100)}%` : '—'
})

function view(index) {
  viewerStart.value = index
  viewerOpen.value = true
}
</script>

<template>
  <Card class="max-h-[50dvh] gap-3 overflow-x-hidden overflow-y-auto border-0 py-4 shadow-float" aria-live="polite">
    <CardHeader class="px-4">
      <CardTitle class="flex items-center gap-2">
        <span
          class="size-3.5 shrink-0 rounded-[3px] ring-1 ring-border"
          :style="{ background: urgency?.color ?? '#ffffff' }"
        />
        {{ urgency ? `${urgency.label} · ${categoryLabel(triage.category.value)}` : 'Being sorted' }}
      </CardTitle>
      <CardDescription v-if="triage?.department.value">{{ triage.department.value }}</CardDescription>
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

    <CardContent class="grid gap-3 px-4">
      <div>
        <p
          ref="text"
          class="text-[15px] leading-snug wrap-anywhere"
          :class="{ 'line-clamp-4': !expanded }"
          :title="report.description"
        >
          {{ report.description }}
        </p>
        <button
          v-if="clamped"
          type="button"
          class="-mx-1 mt-0.5 min-h-11 px-1 text-sm font-bold underline-offset-4 hover:underline md:min-h-0"
          :aria-expanded="expanded"
          @click="expanded = !expanded"
        >
          {{ expanded ? 'Show less' : 'Show more' }}
        </button>
      </div>

      <ul v-if="media.length" class="grid grid-cols-4 gap-2" aria-label="Photos">
        <li v-for="(item, index) in media" :key="item.id">
          <button
            type="button"
            class="relative block aspect-square w-full overflow-hidden rounded-md bg-muted focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
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
