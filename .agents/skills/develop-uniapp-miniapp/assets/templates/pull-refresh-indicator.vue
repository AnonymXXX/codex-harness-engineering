<script setup lang="ts">
import { computed } from 'vue'
import { PullStatus } from './use-refresh-pull'

const props = defineProps<{
  status: PullStatus
  statusText: string
  themeColor: string
  distance: number
  threshold: number
  duration: number
}>()

const symbol = computed(() => {
  switch (props.status) {
    case PullStatus.Loosing:
      return '↑'
    case PullStatus.Loading:
      return '↻'
    case PullStatus.Success:
      return '✓'
    case PullStatus.Error:
      return '✕'
    default:
      return '↓'
  }
})

const symbolClass = computed(() => {
  return props.status === PullStatus.Loading ? 'app-pull-spin' : ''
})
</script>

<template>
  <view
    class="pointer-events-none absolute left-0 right-0 top-0 z-10 flex justify-center"
    :style="{ height: `${threshold}px`, transform: `translateY(${distance - threshold}px)`, transitionDuration: `${duration}ms` }"
  >
    <view class="flex h-full w-full items-end justify-center pb-[16rpx]">
      <view class="flex items-center gap-[16rpx] rounded-full bg-black/70 px-[24rpx] py-[12rpx] backdrop-blur-sm">
        <view
          class="flex h-[48rpx] w-[48rpx] items-center justify-center rounded-full border border-white/10"
          :style="{ borderColor: `${themeColor}66` }"
        >
          <text class="text-[24rpx] font-bold" :class="symbolClass" :style="{ color: themeColor }">
            {{ symbol }}
          </text>
        </view>

        <view class="min-w-0">
          <text class="block text-[20rpx] font-medium" :style="{ color: themeColor }">
            {{ statusText }}
          </text>
          <view class="mt-[6rpx] h-[4rpx] w-[160rpx] overflow-hidden rounded-full bg-white/10">
            <view
              class="h-full rounded-full"
              :style="{ width: `${Math.min((distance / threshold) * 100, 100)}%`, backgroundColor: themeColor }"
            />
          </view>
        </view>
      </view>
    </view>
  </view>
</template>

<style scoped>
.app-pull-spin {
  animation: app-pull-spin 1s linear infinite;
}

@keyframes app-pull-spin {
  from {
    transform: rotate(0deg);
  }

  to {
    transform: rotate(360deg);
  }
}
</style>
