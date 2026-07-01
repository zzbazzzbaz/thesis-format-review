<template>
  <span class="status-badge" :class="toneClass">{{ meta.label }}</span>
</template>

<script setup lang="ts">
import { computed } from 'vue'

import type { ReviewTaskStatus } from '@/types/review'
import { getStatusMeta } from '@/utils/format'

const props = defineProps<{
  status: ReviewTaskStatus
}>()

const meta = computed(() => getStatusMeta(props.status))
const toneClass = computed(() => `status-badge-${meta.value.tone}`)
</script>
