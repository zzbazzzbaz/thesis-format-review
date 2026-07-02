<template>
  <Teleport to="body">
    <div class="pointer-events-none fixed bottom-6 right-6 z-[60] flex flex-col gap-3">
      <TransitionGroup name="toast">
        <div
          v-for="toast in toasts"
          :key="toast.id"
          class="pointer-events-auto flex cursor-pointer items-center gap-3 rounded-lg px-4 py-3 shadow-lg"
          :class="toastClass(toast.type)"
          @click="removeToast(toast.id)"
        >
          <component :is="toastIcon(toast.type)" class="h-5 w-5 shrink-0" aria-hidden="true" />
          <span class="text-sm font-medium">{{ toast.message }}</span>
        </div>
      </TransitionGroup>
    </div>
  </Teleport>
</template>

<script setup lang="ts">
import { CircleCheck, CircleX, Info } from '@lucide/vue'
import type { Component } from 'vue'

import { useToasts, removeToast, type ToastItem } from '@/utils/toast'

const toasts = useToasts()

function toastClass(type: ToastItem['type']) {
  switch (type) {
    case 'success':
      return 'bg-emerald-600 text-white'
    case 'error':
      return 'bg-red-600 text-white'
    default:
      return 'bg-slate-800 text-white'
  }
}

function toastIcon(type: ToastItem['type']): Component {
  switch (type) {
    case 'success':
      return CircleCheck
    case 'error':
      return CircleX
    default:
      return Info
  }
}
</script>

<style scoped>
.toast-enter-active,
.toast-leave-active {
  transition: all 250ms ease;
}

.toast-enter-from {
  opacity: 0;
  transform: translateX(40px);
}

.toast-leave-to {
  opacity: 0;
  transform: translateX(40px);
}
</style>
