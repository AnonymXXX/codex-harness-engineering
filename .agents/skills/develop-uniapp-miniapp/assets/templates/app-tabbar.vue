<script setup lang="ts">
import type { TabBarActionItem, TabBarItem, TabBarPageItem } from './tabbar-config'

const props = defineProps<{
  activeKey?: string
  items: TabBarItem[]
}>()

const emit = defineEmits<{
  (e: 'change', item: TabBarPageItem, index: number): void
  (e: 'action', item: TabBarActionItem, index: number): void
}>()

function isActionItem(item: TabBarItem): item is TabBarActionItem {
  return item.type === 'action'
}

function normalizePath(pagePath: string) {
  return pagePath.startsWith('/') ? pagePath : `/${pagePath}`
}

function getCurrentRoute() {
  const pages = getCurrentPages()
  const currentPage = pages[pages.length - 1]
  return currentPage ? `/${currentPage.route}` : ''
}

function isActive(item: TabBarItem) {
  if (isActionItem(item))
    return false
  if (props.activeKey)
    return props.activeKey === item.key
  return getCurrentRoute() === normalizePath(item.pagePath)
}

function hasBadge(item: TabBarItem) {
  return item.badge !== undefined && item.badge !== null && item.badge !== ''
}

function formatBadge(item: TabBarItem) {
  if (typeof item.badge === 'number')
    return item.badge > 99 ? '99+' : `${item.badge}`
  return `${item.badge ?? ''}`
}

function getIconToneClass(item: TabBarItem) {
  if (isActionItem(item))
    return item.center ? 'h-[88rpx] w-[88rpx] rounded-full bg-brand-primary text-white shadow-lg' : 'text-ui-muted'
  return isActive(item) ? 'text-brand-primary' : 'text-ui-muted'
}

function getIconClass(item: TabBarItem) {
  if (!isActionItem(item) && isActive(item) && item.activeIcon)
    return item.activeIcon
  return item.icon
}

function getTextToneClass(item: TabBarItem) {
  return !isActionItem(item) && isActive(item) ? 'text-brand-primary' : 'text-ui-muted'
}

function selectItem(item: TabBarItem, index: number) {
  if (item.disabled)
    return

  if (isActionItem(item)) {
    emit('action', item, index)
    return
  }

  const targetRoute = normalizePath(item.pagePath)
  if (getCurrentRoute() !== targetRoute)
    uni.switchTab({ url: targetRoute })

  emit('change', item, index)
}
</script>

<template>
  <view
    class="border-t border-black/10 bg-white px-[20rpx] pt-[12rpx]"
    :style="{ paddingBottom: 'max(env(safe-area-inset-bottom), 24rpx)' }"
  >
    <view class="flex items-end justify-between gap-[12rpx]">
      <view
        v-for="(item, index) in items"
        :key="item.key"
        class="relative flex flex-1 flex-col items-center px-[8rpx] py-[8rpx]"
        :class="item.disabled ? 'opacity-40' : 'active:opacity-80'"
        @click="selectItem(item, index)"
      >
        <view
          v-if="item.dot"
          class="absolute right-[22rpx] top-[4rpx] h-[14rpx] w-[14rpx] rounded-full bg-rose-500"
        />
        <view
          v-else-if="hasBadge(item)"
          class="absolute right-[8rpx] top-0 flex min-w-[28rpx] items-center justify-center rounded-full bg-rose-500 px-[6rpx] py-[2rpx]"
        >
          <text class="text-[20rpx] font-bold text-white">
            {{ formatBadge(item) }}
          </text>
        </view>
        <view
          class="flex items-center justify-center text-[28rpx]"
          :class="[
            getIconToneClass(item),
            getIconClass(item),
          ]"
        />
        <text
          v-if="item.text"
          class="mt-[8rpx] text-[20rpx]"
          :class="getTextToneClass(item)"
        >
          {{ item.text }}
        </text>
      </view>
    </view>
  </view>
</template>
