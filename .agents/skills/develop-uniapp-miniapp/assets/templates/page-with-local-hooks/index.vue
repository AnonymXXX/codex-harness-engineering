<script setup lang="ts">
import PageSectionCard from './components/PageSectionCard.vue'
import { usePageState } from './hooks/usePageState'

const { keyword, loading, statusText, setKeyword, handleSubmit } = usePageState()
</script>

<template>
  <PageLayout title="页面标题">
    <view class="flex min-h-0 flex-1 flex-col bg-black px-[24rpx] py-[24rpx] text-white">
      <view class="mb-[24rpx] rounded-[24rpx] bg-white/5 p-[24rpx]">
        <view class="mb-[12rpx] text-[24rpx] text-white/70">
          页面输入
        </view>
        <input
          :value="keyword"
          class="min-h-[88rpx] text-[24rpx]"
          placeholder="请输入关键词"
          placeholder-style="font-size: 24rpx; color: rgba(255, 255, 255, 0.4);"
          @input="setKeyword(($event as any).detail.value)"
        />
      </view>

      <PageSectionCard
        title="局部组件"
        :description="statusText"
        :loading="loading"
        @action="handleSubmit"
      />
    </view>
  </PageLayout>
</template>
