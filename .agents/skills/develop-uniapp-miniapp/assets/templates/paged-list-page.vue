<script setup lang="ts">
import { onMounted, ref } from 'vue'

const activeFilter = ref('all')
const items = ref<any[]>([])
const loading = ref(false)
const refreshing = ref(false)
const finished = ref(false)
const loadMoreError = ref(false)

async function loadPage(reset = false) {
  if (loading.value)
    return
  loading.value = true
  loadMoreError.value = false
  try {
    const nextItems: any[] = []
    items.value = reset ? nextItems : [...items.value, ...nextItems]
    finished.value = nextItems.length === 0
  }
  catch {
    loadMoreError.value = true
  }
  finally {
    loading.value = false
    refreshing.value = false
  }
}

function onRefresh() {
  if (refreshing.value)
    return
  refreshing.value = true
  finished.value = false
  loadPage(true)
}

function onRefreshRestore() {
  if (!loading.value)
    refreshing.value = false
}

function onRefreshAbort() {
  refreshing.value = false
}

function onLoadMore() {
  if (loading.value || refreshing.value || finished.value || loadMoreError.value)
    return
  loadPage(false)
}

onMounted(() => {
  loadPage(true)
})
</script>

<template>
  <PageLayout title="列表标题">
    <view class="flex min-h-0 flex-1 flex-col bg-black text-white">
      <view class="shrink-0 px-[24rpx] py-[24rpx] text-[24rpx] text-white/70">
        当前筛选：{{ activeFilter }}
      </view>
      <scroll-view
        scroll-y
        class="flex-1 h-0"
        :show-scrollbar="false"
        lower-threshold="120"
        refresher-enabled
        :refresher-triggered="refreshing"
        refresher-default-style="white"
        refresher-background="transparent"
        @scrolltolower="onLoadMore"
        @refresherrefresh="onRefresh"
        @refresherrestore="onRefreshRestore"
        @refresherabort="onRefreshAbort"
      >
        <view class="px-[24rpx] pb-[48rpx]">
          <view
            v-for="(item, index) in items"
            :key="item.id || index"
            class="mb-[24rpx] rounded-[24rpx] bg-white/5 p-[24rpx]"
          >
            <text class="text-[24rpx]">
              {{ item.title || item.name || 'Item' }}
            </text>
          </view>
          <view v-if="loading" class="py-[24rpx] text-center text-[24rpx] text-white/60">
            加载中
          </view>
          <view v-else-if="loadMoreError" class="py-[24rpx] text-center text-[20rpx] text-rose-400" @click="onLoadMore">
            加载失败，点击重试
          </view>
          <view v-else-if="finished" class="py-[24rpx] text-center text-[24rpx] text-white/40">
            没有更多了
          </view>
        </view>
      </scroll-view>
    </view>
  </PageLayout>
</template>
