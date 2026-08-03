<script setup lang="ts">
import { computed } from 'vue'
import { useModalStore } from '@/stores/modal'

const modalStore = useModalStore()
const modal = computed(() => modalStore.modal)
const isBottomPlacement = computed(() => modal.value.placement === 'bottom')

const containerClassName = computed(() => {
  return isBottomPlacement.value
    ? 'items-end justify-center'
    : 'items-center justify-center'
})

const panelClassName = computed(() => {
  return isBottomPlacement.value
    ? 'w-full rounded-t-[32rpx] border-t border-white/10 bg-ui-panel px-[32rpx] pt-[28rpx] shadow-lg'
    : 'mx-[32rpx] w-[calc(100%-64rpx)] max-w-[680rpx] rounded-[24rpx] border border-white/10 bg-ui-panel p-[32rpx] shadow-lg'
})

const panelStyle = computed(() => {
  return isBottomPlacement.value
    ? { paddingBottom: 'max(env(safe-area-inset-bottom), 32rpx)' }
    : {}
})

function handleMaskClick() {
  if (modal.value.maskClosable)
    modalStore.resolveModal(false)
}

function handleCancel() {
  modalStore.resolveModal(false)
}

function handleConfirm() {
  modalStore.resolveModal(true)
}
</script>

<template>
  <view
    v-if="modal.show"
    class="fixed inset-0 z-[1000] flex"
    :class="containerClassName"
  >
    <view
      class="absolute inset-0 bg-black/50"
      :class="modal.maskClassName"
      :style="modal.maskStyle"
      @click="handleMaskClick"
    />

    <view
      class="relative min-h-0 text-ui-text"
      :class="[panelClassName, modal.panelClassName]"
      :style="[panelStyle, modal.panelStyle]"
    >
      <view v-if="modal.title" class="mb-[20rpx] text-[28rpx] font-semibold text-ui-text" :class="modal.titleClassName">
        {{ modal.title }}
      </view>

      <scroll-view
        v-if="modal.maxHeight"
        scroll-y
        class="w-full"
        :style="[{ height: modal.maxHeight }, modal.contentStyle]"
        :class="modal.contentClassName"
      >
        <view class="pr-[4rpx]">
          <text class="whitespace-pre-line text-[24rpx] leading-[1.6] text-ui-muted">
            {{ modal.content }}
          </text>
        </view>
      </scroll-view>

      <view
        v-else
        class="pr-[4rpx]"
        :class="modal.contentClassName"
        :style="modal.contentStyle"
      >
        <text class="whitespace-pre-line text-[24rpx] leading-[1.6] text-ui-muted">
          {{ modal.content }}
        </text>
      </view>

      <view
        v-if="modal.showCancel || modal.showConfirm"
        class="mt-[24rpx] flex gap-[16rpx]"
        :class="modal.footerClassName"
        :style="modal.footerStyle"
      >
        <view
          v-if="modal.showCancel"
          class="flex-1 rounded-[16rpx] border border-white/10 bg-white/5 px-[24rpx] py-[20rpx] text-center text-[24rpx] text-ui-text"
          @click="handleCancel"
        >
          {{ modal.cancelText }}
        </view>

        <view
          v-if="modal.showConfirm"
          class="flex-1 rounded-[16rpx] bg-ui-text px-[24rpx] py-[20rpx] text-center text-[24rpx] text-ui-bg"
          @click="handleConfirm"
        >
          {{ modal.confirmText }}
        </view>
      </view>
    </view>
  </view>
</template>
