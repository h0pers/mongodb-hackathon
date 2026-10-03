<script setup>
import { nextTick, ref, watch } from 'vue'
import { ChevronLeft, ChevronRight } from '@lucide/vue'
import { Button } from '@/components/ui/button'
import { Dialog, DialogContent, DialogDescription, DialogTitle } from '@/components/ui/dialog'

const props = defineProps({
  items: { type: Array, required: true },
  start: { type: Number, default: 0 },
})
const open = defineModel('open', { type: Boolean, default: false })

const track = ref(null)
const current = ref(0)
const navClass = 'size-11 text-white hover:bg-white/10 hover:text-white'

function go(index) {
  const next = Math.min(Math.max(index, 0), props.items.length - 1)
  track.value?.scrollTo({ left: next * track.value.clientWidth, behavior: 'smooth' })
}

function onScroll() {
  current.value = Math.round(track.value.scrollLeft / track.value.clientWidth)
}

watch(open, async (isOpen) => {
  if (!isOpen) return
  current.value = props.start
  await nextTick()
  track.value?.scrollTo({ left: props.start * track.value.clientWidth })
})
</script>

<template>
  <Dialog v-model:open="open">
    <DialogContent
      class="max-w-[calc(100%-1rem)] gap-0 overflow-hidden border-0 bg-panel p-0 text-white sm:max-w-4xl [&>[data-slot=dialog-close]]:text-white"
      @keydown.left.prevent="go(current - 1)"
      @keydown.right.prevent="go(current + 1)"
    >
      <DialogTitle class="sr-only">Attached media</DialogTitle>
      <DialogDescription class="sr-only">Swipe or use the arrow keys to browse.</DialogDescription>
      <div ref="track" class="flex snap-x snap-mandatory overflow-x-auto [scrollbar-width:none]" @scroll.passive="onScroll">
        <figure v-for="item in items" :key="item.id" class="relative grid h-[75dvh] w-full shrink-0 snap-center place-items-center">
          <video v-if="item.type === 'video'" :src="item.url" controls playsinline class="max-h-full max-w-full" />
          <img v-else :src="item.url" alt="Photo attached to the report" class="max-h-full max-w-full object-contain" />
          <figcaption v-if="item.credit" class="absolute right-2 bottom-2 rounded bg-black/60 px-2 py-0.5 text-xs">
            <a :href="item.credit.href" target="_blank" rel="noopener" class="underline-offset-2 hover:underline">
              {{ item.credit.label }}
            </a>
          </figcaption>
        </figure>
      </div>
      <div v-if="items.length > 1" class="flex items-center justify-between gap-3 px-3 py-2">
        <Button variant="ghost" size="icon" :class="navClass" aria-label="Previous" :disabled="current === 0" @click="go(current - 1)">
          <ChevronLeft />
        </Button>
        <span class="text-sm tabular-nums">{{ current + 1 }} / {{ items.length }}</span>
        <Button
          variant="ghost"
          size="icon"
          :class="navClass"
          aria-label="Next"
          :disabled="current === items.length - 1"
          @click="go(current + 1)"
        >
          <ChevronRight />
        </Button>
      </div>
    </DialogContent>
  </Dialog>
</template>
