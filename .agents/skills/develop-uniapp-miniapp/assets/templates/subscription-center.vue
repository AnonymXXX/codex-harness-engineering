<script setup lang="ts">
const channels = ref([
  {
    label: '消息提醒',
    color: '#22c55e',
    templates: [
      { key: 'message', title: '私信提醒', desc: '收到新私信时提醒' },
      { key: 'comment', title: '评论提醒', desc: '收到评论时提醒' },
    ],
  },
])

const activeIndex = ref(0)
</script>

<template>
  <view class="min-h-screen bg-black px-[24rpx] py-[24rpx] text-white">
    <view class="mb-[24rpx] text-[28rpx] font-bold">
      订阅中心
    </view>
    <view class="mb-[24rpx] flex gap-[16rpx]">
      <view
        v-for="(channel, index) in channels"
        :key="channel.label"
        class="rounded-[20rpx] px-[20rpx] py-[16rpx] text-[24rpx] font-bold"
        :class="activeIndex === index ? 'bg-white text-black' : 'bg-white/10 text-white/70'"
        @click="activeIndex = index"
      >
        {{ channel.label }}
      </view>
    </view>
    <view class="rounded-[24rpx] bg-white/5 p-[24rpx]">
      <view
        v-for="item in channels[activeIndex].templates"
        :key="item.key"
        class="mb-[24rpx] rounded-[20rpx] border border-white/10 p-[24rpx]"
      >
        <view class="mb-[8rpx] text-[24rpx] font-bold">
          {{ item.title }}
        </view>
        <view class="mb-[16rpx] text-[20rpx] text-white/60">
          {{ item.desc }}
        </view>
        <view class="inline-flex rounded-[16rpx] bg-emerald-500 px-[20rpx] py-[12rpx] text-[20rpx] font-bold text-black">
          订阅
        </view>
      </view>
    </view>
  </view>
</template>
