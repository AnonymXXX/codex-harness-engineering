<script setup lang="ts">
import { computed, ref, useSlots } from 'vue'

interface Props {
  title?: string
  showNavbar?: boolean
  navMode?: 'back' | 'close' | 'home' | 'title-only'
  immersive?: boolean
  bgClass?: string
  customBack?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  title: '',
  showNavbar: true,
  navMode: 'back',
  immersive: false,
  bgClass: 'bg-ui-bg',
  customBack: false,
})

const emit = defineEmits<{
  (e: 'nav-click-left'): void
}>()

const slots = useSlots()
const statusBarHeight = ref(0)
const safeAreaBottom = ref(0)

try {
  const systemInfo = uni.getSystemInfoSync()
  statusBarHeight.value = systemInfo.statusBarHeight || 0
  safeAreaBottom.value = systemInfo.safeAreaInsets?.bottom || 0
}
catch {
  statusBarHeight.value = 0
  safeAreaBottom.value = 0
}

const leftIconClass = computed(() => props.navMode === 'close' ? 'i-fa6-solid-xmark' : 'i-fa6-solid-arrow-left')
const showLeftAction = computed(() => props.navMode !== 'home' && props.navMode !== 'title-only')
const bottomStyle = computed(() => ({
  paddingBottom: `${safeAreaBottom.value}px`,
}))

function handleClickLeft() {
  emit('nav-click-left')

  if (props.customBack || !showLeftAction.value)
    return

  const pages = getCurrentPages()
  if (pages && pages.length > 1)
    uni.navigateBack()
}
</script>

<template>
  <view class="flex min-h-screen flex-col text-ui-text" :class="bgClass">
    <view v-if="!immersive" class="w-full shrink-0" :style="{ height: `${statusBarHeight}px` }" />

    <view v-if="showNavbar" class="shrink-0 border-b border-white/10 bg-ui-panel">
      <view class="flex h-[88rpx] items-center justify-between px-[24rpx]">
        <view class="flex min-w-[88rpx] items-center">
          <view
            v-if="showLeftAction"
            class="flex h-[56rpx] w-[56rpx] items-center justify-center"
            @click="handleClickLeft"
          >
            <view class="text-[32rpx] text-ui-text" :class="leftIconClass" />
          </view>
        </view>

        <view class="min-w-0 flex-1 px-[12rpx] text-center">
          <slot name="nav-center">
            <text class="text-[28rpx] font-bold text-ui-text">
              {{ title }}
            </text>
          </slot>
        </view>

        <view class="flex min-w-[88rpx] justify-end">
          <slot name="nav-right" />
        </view>
      </view>
    </view>

    <view class="min-h-0 flex-1 flex flex-col">
      <slot />
    </view>

    <view v-if="slots.bottom" class="shrink-0" :style="bottomStyle">
      <slot name="bottom" />
    </view>

    <slot name="overlay" />
  </view>
</template>
