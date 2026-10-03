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
import { shrinkPhoto } from '@/lib/photo'

const open = defineModel('open', { type: Boolean, default: false })
const emit = defineEmits(['pick', 'submitted'])

const store = useReportsStore()
const { status, locate } = useGeolocation()
const desktop = useMediaQuery('(min-width: 768px)')
const photoUrl = useObjectUrl(() => store.draft.photo)
const fileInput = ref(null)
const sending = ref(false)
const error = ref('')

const ui = computed(() =>
  desktop.value
    ? { Root: Dialog, Content: DialogContent, Header: DialogHeader, Title: DialogTitle, Description: DialogDescription }
    : {
        Root: Drawer,
        Content: DrawerContent,
        Header: DrawerHeader,
        Title: DrawerTitle,
        Description: DrawerDescription,
      },
)

const location = computed(() => store.draft.location)
const canSend = computed(
  () => store.draft.description.trim().length >= 5 && store.draft.photo && location.value && !sending.value,
)

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

function revealField(event) {
  if (desktop.value || !event.target.matches('textarea, input')) return
  setTimeout(() => event.target.scrollIntoView({ block: 'center', behavior: 'smooth' }), 300)
}

async function onPhoto(event) {
  const file = event.target.files[0]
  event.target.value = ''
  if (!file) return
  try {
    store.draft.photo = await shrinkPhoto(file)
  } catch {
    error.value = "Couldn't read that photo. Try another one."
  }
}

async function send() {
  sending.value = true
  error.value = ''
  try {
    const result = await store.submit()
    open.value = false
    emit('submitted', result)
  } catch (e) {
    error.value = e instanceof TypeError ? "Couldn't reach the server. Check your connection and try again." : e.message
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

      <form
        class="grid min-w-0 gap-5 overflow-x-hidden overflow-y-auto px-4 md:px-0"
        @submit.prevent="send"
        @focusin="revealField"
      >
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
          <Label>Photo</Label>
          <div v-if="photoUrl" class="relative w-fit">
            <img :src="photoUrl" alt="Selected photo" class="h-24 rounded-md object-cover" />
            <Button
              type="button"
              variant="secondary"
              size="icon-sm"
              class="absolute -top-3 -right-3 size-10 rounded-full border md:-top-2 md:-right-2 md:size-8"
              aria-label="Remove photo"
              @click="store.draft.photo = null"
            >
              <X />
            </Button>
          </div>
          <Button v-else type="button" variant="outline" class="h-11 justify-start" @click="fileInput.click()">
            <Camera />
            Add a photo
          </Button>
          <input ref="fileInput" type="file" accept="image/*" class="hidden" @change="onPhoto" />
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
            <Button type="button" variant="outline" size="sm" class="h-10 md:h-8" @click="emit('pick')">
              {{ location ? 'Move pin' : 'Pick on map' }}
            </Button>
          </div>
          <Button
            v-if="location?.source === 'map'"
            type="button"
            variant="link"
            class="h-auto min-h-11 justify-start p-0 md:min-h-0"
            @click="useMyLocation"
          >
            <LocateFixed />
            Use my current location
          </Button>
        </div>

        <p v-if="error" role="alert" class="text-sm text-destructive">{{ error }}</p>

        <div
          class="sticky bottom-0 -mx-4 bg-background px-4 pt-2 pb-[max(1rem,env(safe-area-inset-bottom))] md:static md:mx-0 md:p-0"
        >
          <Button type="submit" class="h-12 w-full text-base font-bold" :disabled="!canSend">
            <Spinner v-if="sending" />
            {{ sending ? 'Sending…' : 'Send report' }}
          </Button>
        </div>
      </form>
    </component>
  </component>
</template>
