<script setup>
import { RouterView } from 'vue-router'
import 'vue-sonner/style.css'
import { Toaster } from '@/components/ui/sonner'
import { TooltipProvider } from '@/components/ui/tooltip'
</script>

<template>
  <TooltipProvider ignore-non-keyboard-focus>
    <RouterView />
    <Toaster position="top-center" />
  </TooltipProvider>
</template>