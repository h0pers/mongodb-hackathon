<script setup>
import { computed, ref, watch } from 'vue'
import { useMediaQuery, useObjectUrl } from '@vueuse/core'
import { Camera, LocateFixed, MapPin, X } from '@lucide/vue'
import { Button } from '@/components/ui/button'
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { Drawer, DrawerContent, DrawerDescription, DrawerHeader, DrawerTitle } from '@/components/ui/drawer'
import { Label } from '@/components/ui/label'
import { Spinner } from '@/components/ui/spinner'
import { Textarea } from '@/components/ui/textarea'
import { useGeolocation } from '@/app/composables/useGeolocation'
import { useReportsStore } from '@/app/stores/reports'

const open = defineModel('open', { type: Boolean, default: false })
const emit = defineEmits(['pick', 'submitted'])

const store = useReportsStore()
const { status, locate } = useGeolocation()
const desktop = useMediaQuery('(min-width: 768px)')
const mediaUrl = useObjectUrl(() => store.draft.media)
const fileInput = ref(null)
const sending = ref(false)
const error = ref('')

const ui = computed(() =>
  desktop.value
    ? { Root: Dialog, Content: DialogContent, Header: DialogHeader, Title: DialogTitle, Description: DialogDescription }
    : { Root: Drawer, Content: DrawerContent, Header: DrawerHeader, Title: DrawerTitle, Description: DrawerDescription },
)

const location = computed(() => store.draft.location)
const canSend = computed(() => store.draft.description.trim().length >= 5 && location.value && !sending.value)

const locationTitle = computed(() => {
  if (location.value) return location.value.source === 'map' ? 'Pinned on the map' : 'Your current location'
  if (status.value === 'locating') return 'Finding your location…'
  if (status.value === 'denied') return 'Location access is off'
  return "Couldn't find your location"
})

const locationDetail = computed(() => {
  const loc = location.value
  if (!loc) return status.value === 'locating' ? 'This takes a few seconds' : 'Pick the spot on the map instead'
  const accuracy = loc.accuracy ? ` · ±${Math.round(loc.accuracy)} m` : ''
  return `${loc.lat.toFixed(5)}, ${loc.lng.toFixed(5)}${accuracy}`
})

async function useMyLocation() {
  const position = await locate()
  if (position) store.draft.location = { ...position, source: 'gps' }
}

watch(open, (isOpen) => {
  error.value = ''
  if (isOpen && !location.value) useMyLocation()
})

function onMedia(event) {
  store.draft.media = event.target.files[0] ?? null
  event.target.value = ''
}

async function send() {
  sending.value = true
  error.value = ''
  try {
    const result = await store.submit()
    open.value = false
    emit('submitted', result)
  } catch (e) {
    error.value = `${e.message}. Check your connection and try again.`
  } finally {
    sending.value = false
  }
}
</script>

<template>
  <component :is="ui.Root" v-model:open="open">
    <component :is="ui.Content" class="max-h-[92dvh] md:max-w-md">
      <component :is="ui.Header" class="text-left">
        <component :is="ui.Title" class="text-xl font-extrabold">Report a problem</component>
        <component :is="ui.Description">
          Say what's wrong. It gets sorted by urgency and sent to the right council team.
        </component>
      </component>

      <form class="grid gap-5 overflow-y-auto px-4 pb-6 md:px-0 md:pb-0" @submit.prevent="send">
        <div class="grid gap-2">
          <Label for="description">What's the problem?</Label>
          <Textarea
            id="description"
            v-model="store.draft.description"
            maxlength="1000"
            placeholder="e.g. Deep pothole outside the school gates on Dorset Street"
            class="min-h-28 text-base"
            required
          />
        </div>

        <div class="grid gap-2">
          <Label>Photo or video <span class="font-normal text-muted-foreground">(optional)</span></Label>
          <div v-if="mediaUrl" class="relative w-fit">
            <video
              v-if="store.draft.media.type.startsWith('video/')"
              :src="mediaUrl"
              muted
              class="h-24 rounded-md object-cover"
            />
            <img v-else :src="mediaUrl" alt="Selected photo" class="h-24 rounded-md object-cover" />
            <Button
              type="button"
              variant="secondary"
              size="icon-sm"
              class="absolute -top-2 -right-2 rounded-full border"
              aria-label="Remove attachment"
              @click="store.draft.media = null"
            >
              <X />
            </Button>
          </div>
          <Button v-else type="button" variant="outline" class="h-11 justify-start" @click="fileInput.click()">
            <Camera />
            Add a photo or video
          </Button>
          <input ref="fileInput" type="file" accept="image/*,video/*" class="hidden" @change="onMedia" />
        </div>

        <div class="grid gap-2">
          <Label>Location</Label>
          <div class="flex items-center gap-3 rounded-md border bg-background p-3">
            <Spinner v-if="status === 'locating' && !location" class="size-5 shrink-0" />
            <MapPin v-else class="size-5 shrink-0" />
            <div class="min-w-0 flex-1 text-sm">
              <p class="font-bold">{{ locationTitle }}</p>
              <p class="truncate text-muted-foreground tabular-nums">{{ locationDetail }}</p>
            </div>
            <Button type="button" variant="outline" size="sm" @click="emit('pick')">
              {{ location ? 'Move pin' : 'Pick on map' }}
            </Button>
          </div>
          <Button
            v-if="location?.source === 'map'"
            type="button"
            variant="link"
            class="h-auto justify-start p-0"
            @click="useMyLocation"
          >
            <LocateFixed />
            Use my current location
          </Button>
        </div>

        <p v-if="error" role="alert" class="text-sm text-destructive">{{ error }}</p>

        <Button type="submit" class="h-12 text-base font-bold" :disabled="!canSend">
          <Spinner v-if="sending" />
          {{ sending ? 'Sending…' : 'Send report' }}
        </Button>
      </form>
    </component>
  </component>
</template>
