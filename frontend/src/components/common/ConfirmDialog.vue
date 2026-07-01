<template>
  <Teleport to="body">
    <div v-if="open" class="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/35">
      <div class="w-[420px] rounded-lg bg-white shadow-xl">
        <div class="border-b border-slate-200 px-5 py-4">
          <h3 class="text-base font-semibold text-slate-950">{{ title }}</h3>
        </div>
        <div class="px-5 py-4 text-sm leading-6 text-slate-600">{{ message }}</div>
        <div class="flex justify-end gap-3 border-t border-slate-200 px-5 py-4">
          <button class="btn btn-secondary" type="button" @click="$emit('cancel')">取消</button>
          <button class="btn btn-primary" type="button" @click="$emit('confirm')">确认</button>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup lang="ts">
defineProps<{
  open: boolean
  title: string
  message: string
}>()

defineEmits<{
  confirm: []
  cancel: []
}>()
</script>
