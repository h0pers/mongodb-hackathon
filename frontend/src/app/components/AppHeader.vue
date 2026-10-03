<script setup>
import { Flame, MapPin, Moon, Sun } from '@lucide/vue'
import { Button } from '@/components/ui/button'
import { ToggleGroup, ToggleGroupItem } from '@/components/ui/toggle-group'
import { Tooltip, TooltipContent, TooltipTrigger } from '@/components/ui/tooltip'

const layer = defineModel('layer', { type: String, required: true })
const dark = defineModel('dark', { type: Boolean, required: true })
const itemClass = 'h-11 px-3 md:h-9 data-[state=on]:bg-primary data-[state=on]:text-primary-foreground'
</script>

<template>
  <header class="flex h-(--header-height) items-center gap-3 border-b bg-background px-4 pt-[env(safe-area-inset-top)]">
    <div class="flex min-w-0 items-baseline gap-2">
      <h1 class="text-lg font-extrabold tracking-tight">DublinFix AI</h1>
    </div>
    <ToggleGroup
      :model-value="layer"
      type="single"
      variant="outline"
      class="ml-auto bg-card"
      aria-label="Map view"
      @update:model-value="(value) => value && (layer = value)"
    >
      <ToggleGroupItem value="pins" aria-label="Pins" :class="itemClass">
        <MapPin />
        <span class="hidden sm:inline">Pins</span>
      </ToggleGroupItem>
      <ToggleGroupItem value="heat" aria-label="Heatmap" :class="itemClass">
        <Flame />
        <span class="hidden sm:inline">Heat</span>
      </ToggleGroupItem>
    </ToggleGroup>
    <Tooltip>
      <TooltipTrigger as-child>
        <Button
          variant="outline"
          size="icon"
          class="size-11 bg-card md:size-9"
          :aria-label="dark ? 'Switch to light mode' : 'Switch to dark mode'"
          @click="dark = !dark"
        >
          <Sun v-if="dark" />
          <Moon v-else />
        </Button>
      </TooltipTrigger>
      <TooltipContent>{{ dark ? 'Light mode' : 'Dark mode' }}</TooltipContent>
    </Tooltip>
  </header>
</template>
