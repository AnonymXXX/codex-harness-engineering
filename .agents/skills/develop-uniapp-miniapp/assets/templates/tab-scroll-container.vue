<script setup lang="ts">
import { computed, getCurrentInstance, nextTick, onMounted, onUnmounted, ref, watch } from 'vue'
import PullRefreshIndicator from './pull-refresh-indicator.vue'
import { useLoadMoreObserver } from './use-load-more-observer'
import { useRefreshPull } from './use-refresh-pull'

interface TabItem {
  label: string
  value: string
  count?: number
}

interface TabState {
  refreshing: boolean
  loading: boolean
  finished: boolean
  refreshError: boolean
  loadMoreError: boolean
  scrollTop: number
  empty: boolean
}

const props = withDefaults(defineProps<{
  modelValue: string
  tabs: TabItem[]
  disableSwipe?: boolean
  safePadding?: boolean
  stickyTabs?: boolean
  tabBgClass?: string
  accentColor?: string
}>(), {
  disableSwipe: false,
  safePadding: true,
  stickyTabs: true,
  tabBgClass: 'bg-black/90',
  accentColor: '#3B82F6',
})

const emit = defineEmits<{
  (e: 'update:modelValue', value: string): void
  (e: 'change', value: string, index: number): void
  (e: 'refresh', value: string): void
  (e: 'loadMore', value: string): void
  (e: 'scroll', value: string, event: any): void
}>()

const instance = getCurrentInstance()

const containerHeight = ref(0)
const fixedTopHeight = ref(0)
const contentHeight = computed(() => Math.max(0, containerHeight.value - fixedTopHeight.value))

const currentIndex = computed(() => {
  return Math.max(0, props.tabs.findIndex(tab => tab.value === props.modelValue))
})

const swipeIndex = ref(currentIndex.value)
const touchStartX = ref(0)
const touchStartY = ref(0)
const touchDeltaX = ref(0)
const isTouching = ref(false)
const isHorizontal = ref<boolean | null>(null)
const isHorizontalSwiping = ref(false)

const tabStates = ref(new Map<string, TabState>())

const HORIZONTAL_RATIO = 1.3
const DIRECTION_MIN_PX = 8

function getTabState(value: string) {
  if (!tabStates.value.has(value)) {
    tabStates.value.set(value, {
      refreshing: false,
      loading: false,
      finished: false,
      refreshError: false,
      loadMoreError: false,
      scrollTop: 0,
      empty: false,
    })
  }
  return tabStates.value.get(value)!
}

function measureLayout() {
  if (!instance)
    return

  const query = uni.createSelectorQuery().in(instance)
  query.select('.tsc-container').boundingClientRect((rect: any) => {
    if (rect)
      containerHeight.value = rect.height
  })
  query.select('.tsc-fixed-top').boundingClientRect((rect: any) => {
    fixedTopHeight.value = rect?.height || 0
  })
  query.exec()
}

function selectTab(tab: TabItem, index: number) {
  if (tab.value === props.modelValue)
    return
  swipeIndex.value = index
  emit('update:modelValue', tab.value)
  emit('change', tab.value, index)
}

function onSwipeTouchStart(event: any) {
  if (props.disableSwipe)
    return

  const touch = event?.touches?.[0] || event?.changedTouches?.[0]
  if (!touch)
    return

  touchStartX.value = touch.clientX
  touchStartY.value = touch.clientY
  touchDeltaX.value = 0
  isTouching.value = true
  isHorizontal.value = null
}

function onSwipeTouchMove(event: any) {
  if (props.disableSwipe || !isTouching.value)
    return

  const touch = event?.touches?.[0] || event?.changedTouches?.[0]
  if (!touch)
    return

  const deltaX = touch.clientX - touchStartX.value
  const deltaY = touch.clientY - touchStartY.value

  if (isHorizontal.value === null) {
    const absX = Math.abs(deltaX)
    const absY = Math.abs(deltaY)
    if (absX < DIRECTION_MIN_PX && absY < DIRECTION_MIN_PX)
      return
    isHorizontal.value = absX > absY * HORIZONTAL_RATIO
    if (!isHorizontal.value) {
      isTouching.value = false
      return
    }
    isHorizontalSwiping.value = true
  }

  if (!isHorizontal.value)
    return

  let finalDelta = deltaX
  if (swipeIndex.value === 0 && deltaX > 0)
    finalDelta = deltaX * 0.3
  else if (swipeIndex.value === props.tabs.length - 1 && deltaX < 0)
    finalDelta = deltaX * 0.3

  touchDeltaX.value = finalDelta
  event?.preventDefault?.()
}

function onSwipeTouchEnd() {
  if (props.disableSwipe)
    return

  const wasHorizontal = isHorizontal.value
  isTouching.value = false
  isHorizontalSwiping.value = false

  if (!wasHorizontal) {
    touchDeltaX.value = 0
    return
  }

  const delta = touchDeltaX.value
  let nextIndex = swipeIndex.value

  if (Math.abs(delta) > 50) {
    if (delta > 0 && swipeIndex.value > 0)
      nextIndex = swipeIndex.value - 1
    else if (delta < 0 && swipeIndex.value < props.tabs.length - 1)
      nextIndex = swipeIndex.value + 1
  }

  touchDeltaX.value = 0

  if (nextIndex !== swipeIndex.value) {
    swipeIndex.value = nextIndex
    const nextTab = props.tabs[nextIndex]
    if (nextTab) {
      emit('update:modelValue', nextTab.value)
      emit('change', nextTab.value, nextIndex)
    }
  }
}

const swipeTrackStyle = computed(() => {
  const offset = -swipeIndex.value * 100
  return {
    transform: `translateX(calc(${offset}% + ${touchDeltaX.value}px))`,
    transition: isTouching.value ? 'none' : 'transform 300ms ease',
  }
})

function getCurrentScrollTop() {
  const currentTab = props.tabs[swipeIndex.value]
  if (!currentTab)
    return 999
  return getTabState(currentTab.value).scrollTop
}

const {
  threshold,
  status,
  distance,
  duration,
  statusText,
  themeColor,
  handleTouchStart,
  handleTouchMove,
  handleTouchEnd,
  handleTouchCancel,
  finishRefresh: finishRefreshInternal,
} = useRefreshPull({
  getScrollTop: getCurrentScrollTop,
  isHorizontalSwiping: () => isHorizontalSwiping.value,
  onRefresh: () => {
    const currentTab = props.tabs[swipeIndex.value]
    if (!currentTab)
      return
    getTabState(currentTab.value).refreshing = true
    emit('refresh', currentTab.value)
  },
})

function finishRefresh(tabValue: string, error = false) {
  const state = getTabState(tabValue)
  state.refreshing = false
  state.refreshError = error

  const currentTab = props.tabs[swipeIndex.value]
  if (currentTab?.value !== tabValue)
    return

  finishRefreshInternal(error)
}

function toSelectorKey(value: string) {
  return String(value).replace(/[^a-zA-Z0-9_-]/g, '-')
}

const {
  initObserver,
  destroyAll,
  finishLoadMore,
  triggerLoadMore,
} = useLoadMoreObserver({
  instance,
  getState: key => getTabState(key),
  onLoadMore: key => emit('loadMore', key),
  getTriggerSelector: key => `.tsc-load-trigger-${toSelectorKey(key)}`,
})

function onTabScroll(value: string, event: any) {
  const top = Number(event?.detail?.scrollTop ?? 0)
  getTabState(value).scrollTop = Number.isNaN(top) ? 0 : (top <= 5 ? 0 : top)
  emit('scroll', value, event)
}

function onScrollToUpper(value: string) {
  getTabState(value).scrollTop = 0
}

function onContainerTouchStart(event: any) {
  const handled = handleTouchStart(event)
  if (handled)
    event?.stopPropagation?.()
}

function onContainerTouchMove(event: any) {
  const handled = handleTouchMove(event)
  if (handled) {
    event?.preventDefault?.()
    event?.stopPropagation?.()
  }
}

function onContainerTouchEnd(event: any) {
  const handled = handleTouchEnd()
  if (handled)
    event?.stopPropagation?.()
}

function onContainerTouchCancel(event: any) {
  const handled = handleTouchCancel()
  if (handled)
    event?.stopPropagation?.()
}

function formatCount(count?: number) {
  if (count === undefined || count === null)
    return ''
  if (count >= 10000)
    return `${(count / 10000).toFixed(1)}w`
  return count.toString()
}

defineExpose({
  finishRefresh,
  finishLoadMore,
  getTabState,
  measureLayout,
  initObserver,
  triggerLoadMore,
})

watch(() => props.modelValue, () => {
  swipeIndex.value = currentIndex.value
})

watch(currentIndex, (value) => {
  const currentTab = props.tabs[value]
  if (!currentTab)
    return
  nextTick(() => {
    setTimeout(() => {
      initObserver(currentTab.value)
    }, 120)
  })
})

watch(() => props.tabs.length, () => {
  nextTick(() => {
    setTimeout(() => {
      measureLayout()
    }, 80)
  })
})

onMounted(() => {
  setTimeout(() => {
    measureLayout()
  }, 50)
  setTimeout(() => {
    measureLayout()
  }, 250)
  setTimeout(() => {
    const currentTab = props.tabs[swipeIndex.value]
    if (currentTab)
      initObserver(currentTab.value)
  }, 300)
})

onUnmounted(() => {
  destroyAll()
})
</script>

<template>
  <view class="tsc-container flex min-h-0 flex-1 flex-col overflow-hidden">
    <view class="tsc-fixed-top shrink-0">
      <slot v-if="!stickyTabs" name="header" />

      <view class="border-b border-white/10 px-[12rpx] py-[12rpx]" :class="tabBgClass">
        <view class="flex items-center">
          <view
            v-for="(tab, index) in tabs"
            :key="tab.value"
            class="flex-1 px-[12rpx] py-[16rpx] text-center"
            @click="selectTab(tab, index)"
          >
            <text
              class="text-[24rpx] font-bold"
              :class="modelValue === tab.value ? 'text-white' : 'text-white/50'"
            >
              {{ tab.label }}
            </text>
            <text
              v-if="tab.count !== undefined"
              class="ml-[6rpx] text-[20rpx]"
              :class="modelValue === tab.value ? 'text-white/70' : 'text-white/35'"
            >
              {{ formatCount(tab.count) }}
            </text>
            <view
              class="mx-auto mt-[10rpx] h-[6rpx] w-[40rpx] rounded-full transition-all"
              :style="{ backgroundColor: accentColor }"
              :class="modelValue === tab.value ? 'opacity-100' : 'opacity-0'"
            />
          </view>
        </view>
      </view>
    </view>

    <view
      class="relative overflow-hidden"
      :style="{ height: contentHeight ? `${contentHeight}px` : '100%' }"
      @touchstart="onContainerTouchStart"
      @touchmove="onContainerTouchMove"
      @touchend="onContainerTouchEnd"
      @touchcancel="onContainerTouchCancel"
    >
      <PullRefreshIndicator
        :status="status"
        :status-text="statusText"
        :theme-color="themeColor"
        :distance="distance"
        :threshold="threshold"
        :duration="duration"
      />

      <view class="h-full w-full" :style="{ transform: `translate3d(0, ${distance}px, 0)`, transitionDuration: `${duration}ms` }">
        <view
          class="flex h-full"
          :style="swipeTrackStyle"
          @touchstart="onSwipeTouchStart"
          @touchmove="onSwipeTouchMove"
          @touchend="onSwipeTouchEnd"
          @touchcancel="onSwipeTouchEnd"
        >
          <view
            v-for="(tab, index) in tabs"
            :key="tab.value"
            class="w-full h-full shrink-0 overflow-hidden"
          >
            <scroll-view
              :scroll-y="!getTabState(tab.value).refreshing"
              :scroll-with-animation="false"
              class="h-full w-full box-border overflow-hidden"
              upper-threshold="10"
              @scroll="(event: any) => onTabScroll(tab.value, event)"
              @scrolltoupper="() => onScrollToUpper(tab.value)"
            >
              <view class="box-border min-h-full" :class="safePadding ? 'pb-safe' : ''">
                <slot :name="`tab-${index}`" :tab="tab" :state="getTabState(tab.value)" />

                <view v-if="!getTabState(tab.value).empty && !getTabState(tab.value).refreshing" class="px-[32rpx] py-[24rpx] text-center">
                  <text v-if="getTabState(tab.value).loading" class="text-[20rpx] text-white/60">
                    正在加载更多
                  </text>
                  <text v-else-if="getTabState(tab.value).loadMoreError" class="text-[20rpx] text-rose-400" @click="triggerLoadMore(tab.value)">
                    加载失败，点击重试
                  </text>
                  <text v-else-if="getTabState(tab.value).finished" class="text-[20rpx] text-white/40">
                    没有更多了
                  </text>
                </view>

                <view
                  v-if="!getTabState(tab.value).empty && !getTabState(tab.value).refreshing && !getTabState(tab.value).loading && !getTabState(tab.value).finished && !getTabState(tab.value).loadMoreError"
                  :class="`tsc-load-trigger-${toSelectorKey(tab.value)}`"
                  class="h-[20rpx] w-full bg-transparent"
                />
              </view>
            </scroll-view>
          </view>
        </view>
      </view>
    </view>
  </view>
</template>
