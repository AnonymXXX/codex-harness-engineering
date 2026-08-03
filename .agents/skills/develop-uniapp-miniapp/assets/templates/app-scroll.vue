<script setup lang="ts">
import { computed, getCurrentInstance, nextTick, onMounted, onUnmounted, ref, watch } from 'vue'
import PullRefreshIndicator from './pull-refresh-indicator.vue'
import { useRefreshPull } from './use-refresh-pull'

interface Props {
  refreshing?: boolean
  refreshError?: boolean
  enableRefresh?: boolean
  loading?: boolean
  loadMoreError?: boolean
  enableLoadMore?: boolean
  finished?: boolean
  empty?: boolean
  safePadding?: boolean
  customClass?: string
  observerThreshold?: number
  observerMargin?: string
}

defineOptions({
  options: {
    virtualHost: true,
  },
})

const props = withDefaults(defineProps<Props>(), {
  refreshing: false,
  refreshError: false,
  enableRefresh: true,
  loading: false,
  loadMoreError: false,
  enableLoadMore: true,
  finished: false,
  empty: false,
  safePadding: true,
  customClass: '',
  observerThreshold: 0.1,
  observerMargin: '100px',
})

const emit = defineEmits<{
  (e: 'update:refreshing', value: boolean): void
  (e: 'refresh'): void
  (e: 'loadMore'): void
  (e: 'scroll', event: any): void
}>()

const instance = getCurrentInstance()

const internalRefreshing = ref(false)
const scrollTopVal = ref(0)
const lockedScrollTop = ref<number | null>(null)
const effectiveScrollTop = computed(() => lockedScrollTop.value ?? scrollTopVal.value)
const loadTriggerLocked = ref(false)

let intersectionObserver: UniApp.IntersectionObserver | null = null

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
  finishRefresh,
} = useRefreshPull({
  getScrollTop: () => scrollTopVal.value,
  onRefresh: () => {
    internalRefreshing.value = true
    lockedScrollTop.value = scrollTopVal.value
    emit('update:refreshing', true)
    emit('refresh')
  },
})

watch(() => props.refreshing, (value, previousValue) => {
  internalRefreshing.value = value
  if (value) {
    lockedScrollTop.value = scrollTopVal.value
  }
  if (previousValue && !value)
    finishRefresh(props.refreshError)
})

watch(internalRefreshing, (value) => {
  if (value)
    lockedScrollTop.value = scrollTopVal.value
  else
    lockedScrollTop.value = null
})

watch(() => props.loading, (value) => {
  if (!value) {
    loadTriggerLocked.value = false
    nextTick(() => {
      destroyObserver()
      setTimeout(() => {
        initObserver()
      }, 100)
    })
  }
})

watch(() => props.enableLoadMore, (value) => {
  if (value) {
    nextTick(() => {
      initObserver()
    })
  }
  else {
    destroyObserver()
  }
})

watch(() => props.finished, (value) => {
  if (!value) {
    loadTriggerLocked.value = false
    nextTick(() => {
      destroyObserver()
      setTimeout(() => {
        initObserver()
      }, 100)
    })
  }
})

function destroyObserver() {
  if (!intersectionObserver)
    return
  intersectionObserver.disconnect()
  intersectionObserver = null
}

function triggerLoadMore() {
  if (props.loading || props.finished || props.empty || props.loadMoreError || internalRefreshing.value || loadTriggerLocked.value)
    return
  loadTriggerLocked.value = true
  emit('loadMore')
}

function initObserver() {
  destroyObserver()

  if (!instance || !props.enableLoadMore || props.loading || props.finished || props.empty || props.loadMoreError || internalRefreshing.value)
    return

  intersectionObserver = uni.createIntersectionObserver(instance, {
    thresholds: [props.observerThreshold],
    initialRatio: 0,
    observeAll: false,
  })

  intersectionObserver.relativeToViewport({
    bottom: Number.parseInt(props.observerMargin, 10) || 100,
  }).observe('.app-scroll-load-trigger', (result) => {
    if (result.intersectionRatio > 0)
      triggerLoadMore()
  })
}

function onScroll(event: any) {
  const top = Number(event?.detail?.scrollTop ?? 0)
  if (lockedScrollTop.value == null)
    scrollTopVal.value = Number.isNaN(top) ? 0 : (top <= 5 ? 0 : top)
  emit('scroll', event)
}

function onScrollToUpper() {
  scrollTopVal.value = 0
}

function onPullTouchStart(event: any) {
  if (internalRefreshing.value)
    return
  const handled = handleTouchStart(event)
  if (handled)
    event?.stopPropagation?.()
}

function onPullTouchMove(event: any) {
  if (internalRefreshing.value) {
    event?.preventDefault?.()
    event?.stopPropagation?.()
    return
  }
  const handled = handleTouchMove(event)
  if (handled) {
    event?.preventDefault?.()
    event?.stopPropagation?.()
  }
}

function onPullTouchEnd(event: any) {
  if (internalRefreshing.value)
    return
  const handled = handleTouchEnd()
  if (handled)
    event?.stopPropagation?.()
}

function onPullTouchCancel(event: any) {
  if (internalRefreshing.value)
    return
  const handled = handleTouchCancel()
  if (handled)
    event?.stopPropagation?.()
}

function reinitObserver() {
  if (!props.enableLoadMore || props.finished)
    return
  destroyObserver()
  setTimeout(() => {
    initObserver()
  }, 150)
}

defineExpose({ reinitObserver })

onMounted(() => {
  internalRefreshing.value = props.refreshing
  setTimeout(() => {
    initObserver()
  }, 200)
})

onUnmounted(() => {
  destroyObserver()
})
</script>

<template>
  <view class="relative flex h-full min-h-0 w-full flex-col overflow-hidden">
    <PullRefreshIndicator
      :status="status"
      :status-text="statusText"
      :theme-color="themeColor"
      :distance="distance"
      :threshold="threshold"
      :duration="duration"
    />

    <view class="flex-1 min-h-0">
      <scroll-view
        :scroll-y="lockedScrollTop == null"
        :scroll-top="lockedScrollTop != null ? effectiveScrollTop : undefined"
        :scroll-with-animation="false"
        class="h-full w-full overflow-hidden box-border"
        :class="customClass"
        upper-threshold="10"
        @scroll="onScroll"
        @scrolltoupper="onScrollToUpper"
        @touchstart="onPullTouchStart"
        @touchmove="onPullTouchMove"
        @touchend="onPullTouchEnd"
        @touchcancel="onPullTouchCancel"
      >
        <view class="box-border min-h-full" :class="safePadding ? 'pb-safe' : ''">
          <slot v-if="!empty" />

          <slot v-else name="empty">
            <view class="flex min-h-[320rpx] items-center justify-center px-[32rpx] py-[48rpx]">
              <text class="text-[24rpx] text-white/50">
                暂无内容
              </text>
            </view>
          </slot>

          <view v-if="!empty && enableLoadMore && !internalRefreshing" class="px-[32rpx] py-[24rpx] text-center">
            <text v-if="loading" class="text-[20rpx] text-white/60">
              正在加载更多
            </text>
            <text v-else-if="loadMoreError" class="text-[20rpx] text-rose-400" @click="emit('loadMore')">
              加载失败，点击重试
            </text>
            <text v-else-if="finished" class="text-[20rpx] text-white/40">
              没有更多了
            </text>
          </view>

          <view
            v-if="!empty && enableLoadMore && !internalRefreshing && !loading && !finished && !loadMoreError"
            class="app-scroll-load-trigger h-[20rpx] w-full bg-transparent"
          />
        </view>
      </scroll-view>
    </view>
  </view>
</template>
