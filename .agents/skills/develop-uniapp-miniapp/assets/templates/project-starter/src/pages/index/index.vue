<script setup lang="ts">
import { ref } from 'vue'
import { useAppModal } from '../../hooks/useAppModal'

const { showModal } = useAppModal()
const lastModalResult = ref('全局弹窗能力已就绪。')

async function openCenterModal() {
  const result = await showModal({
    title: '居中弹窗',
    content: '这是 starter 内置的全局弹窗示例，用于确认、提示和轻量说明。',
    placement: 'center',
  })

  lastModalResult.value = result.confirm
    ? '上一次操作：确认了居中弹窗。'
    : '上一次操作：取消了居中弹窗。'
}

async function openBottomModal() {
  const result = await showModal({
    title: '底部弹出',
    content: '这是 style-neutral 的底部弹出示例。复杂表单或强业务弹窗仍建议放在页面局部组件中。',
    placement: 'bottom',
    showCancel: false,
    confirmText: '我知道了',
    maxHeight: '360rpx',
  })

  lastModalResult.value = result.confirm
    ? '上一次操作：关闭了底部弹出。'
    : '上一次操作：取消了底部弹出。'
}
</script>

<template>
  <PageLayout title="首页" nav-mode="title-only">
    <view class="flex min-h-0 flex-1 flex-col bg-ui-bg px-[24rpx] py-[32rpx] text-ui-text">
      <view class="rounded-[24rpx] bg-ui-panel p-[24rpx] shadow-soft">
        <view class="mb-[16rpx] flex items-center gap-[12rpx] text-[28rpx] font-bold">
          <view class="i-fa6-solid-house text-[24rpx] text-brand-primary" />
          <text>UniApp WeChat Starter</text>
        </view>
        <view class="mb-[12rpx] text-[24rpx] text-ui-muted">
          这是一个最小可扩展的 uni-app 微信小程序起始页。
        </view>
        <view class="text-[20rpx] text-ui-muted">
          从这里继续添加页面、共享布局、请求层、登录态和业务模块。
        </view>

        <view class="mt-[24rpx] flex flex-col gap-[16rpx]">
          <view
            class="rounded-[16rpx] border border-white/10 bg-white/5 px-[24rpx] py-[20rpx] text-center text-[24rpx]"
            @click="openCenterModal"
          >
            打开居中弹窗
          </view>

          <view
            class="rounded-[16rpx] border border-white/10 bg-white/5 px-[24rpx] py-[20rpx] text-center text-[24rpx]"
            @click="openBottomModal"
          >
            打开底部弹窗
          </view>

          <view class="text-[20rpx] text-ui-muted">
            {{ lastModalResult }}
          </view>
        </view>
      </view>
    </view>
  </PageLayout>
</template>
