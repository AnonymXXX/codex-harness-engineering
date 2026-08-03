<script setup lang="ts">
import { computed, ref } from 'vue'

interface FeatureItem {
  id: string | number
  title: string
  description?: string
  status?: string
}

const keyword = ref('')
const activeFilter = ref('all')
const refreshing = ref(false)
const loading = ref(false)
const finished = ref(false)
const loadMoreError = ref(false)
const items = ref<FeatureItem[]>([])
const detailRoute = ''

const isEmpty = computed(() => !loading.value && items.value.length === 0)

async function loadPage(reset = false) {
  if (loading.value)
    return

  loading.value = true
  loadMoreError.value = false

  try {
    const nextItems: FeatureItem[] = []
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

function handleRefresh() {
  if (refreshing.value)
    return
  refreshing.value = true
  finished.value = false
  loadPage(true)
}

function handleLoadMore() {
  if (loading.value || refreshing.value || finished.value || loadMoreError.value)
    return
  loadPage(false)
}

function handleRetry() {
  loadPage(items.value.length === 0)
}

function handleSearch() {
  finished.value = false
  loadPage(true)
}

function handleItemClick(item: FeatureItem) {
  if (!detailRoute) {
    uni.showToast({ title: '请先配置详情页路由', icon: 'none' })
    return
  }
  uni.navigateTo({ url: `${detailRoute}?id=${item.id}` })
}

loadPage(true)
</script>

<template>
  <PageLayout title="功能标题">
    <view class="flex min-h-0 flex-1 flex-col bg-[#f6f7f9]">
      <view class="shrink-0 px-[24rpx] pb-[20rpx] pt-[24rpx]">
        <view class="flex items-center gap-[16rpx] rounded-[12rpx] bg-white px-[20rpx] py-[16rpx]">
          <view class="i-fa6-solid-magnifying-glass text-[28rpx] text-[#667085]" />
          <input
            v-model="keyword"
            class="min-w-0 flex-1 text-[24rpx] text-[#101828]"
            placeholder="搜索"
            confirm-type="search"
            @confirm="handleSearch"
          >
        </view>

        <scroll-view scroll-x :show-scrollbar="false" class="mt-[20rpx] whitespace-nowrap">
          <view class="inline-flex gap-[16rpx]">
            <view
              v-for="filter in ['all', 'pending', 'done']"
              :key="filter"
              class="shrink-0 rounded-[8rpx] px-[24rpx] py-[12rpx]"
              :class="activeFilter === filter ? 'bg-[#1677ff]' : 'bg-white'"
              @click="activeFilter = filter"
            >
              <text class="text-[22rpx]" :class="activeFilter === filter ? 'text-white' : 'text-[#475467]'">
                {{ filter }}
              </text>
            </view>
          </view>
        </scroll-view>
      </view>

      <AppScroll
        v-model:refreshing="refreshing"
        :loading="loading"
        :finished="finished"
        :empty="isEmpty"
        :load-more-error="loadMoreError"
        @refresh="handleRefresh"
        @load-more="handleLoadMore"
      >
        <view class="box-border w-full px-[24rpx] pb-[48rpx]">
          <view v-if="isEmpty" class="py-[96rpx] text-center">
            <text class="text-[24rpx] text-[#667085]">
              暂无数据
            </text>
          </view>

          <view
            v-for="item in items"
            :key="item.id"
            class="mb-[20rpx] rounded-[8rpx] bg-white p-[24rpx]"
            @click="handleItemClick(item)"
          >
            <view class="flex items-start justify-between gap-[16rpx]">
              <text class="min-w-0 flex-1 text-[28rpx] font-medium text-[#101828]">
                {{ item.title }}
              </text>
              <text v-if="item.status" class="shrink-0 text-[22rpx] text-[#1677ff]">
                {{ item.status }}
              </text>
            </view>
            <text v-if="item.description" class="mt-[12rpx] block text-[24rpx] text-[#667085]">
              {{ item.description }}
            </text>
          </view>

          <view v-if="loadMoreError" class="py-[24rpx] text-center" @click="handleRetry">
            <text class="text-[22rpx] text-[#d92d20]">
              加载失败，点击重试
            </text>
          </view>
        </view>
      </AppScroll>
    </view>
  </PageLayout>
</template>
