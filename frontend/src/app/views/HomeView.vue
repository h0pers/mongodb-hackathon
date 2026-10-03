<script setup>
import { useCounterStore } from '@/app/stores/counter'
import { Button } from '@/components/ui/button'

const counter = useCounterStore()
</script>

<template>
  <div class="flex min-h-screen items-center justify-center">
    <div class="text-center space-y-4">
      <h1 class="text-4xl font-bold">Vue App</h1>
      <p class="text-muted-foreground">Count: {{ counter.count }}</p>
      <Button @click="counter.increment">Increment</Button>
    </div>
  </div>
</template>