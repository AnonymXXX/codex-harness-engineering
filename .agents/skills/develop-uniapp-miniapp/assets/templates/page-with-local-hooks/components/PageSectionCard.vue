<script setup lang="ts">
interface Props {
  title?: string
  description?: string
  loading?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  title: '区块标题',
  description: '这里放页面局部组件的展示内容。',
  loading: false,
})

const emit = defineEmits<{
  action: []
}>()

function handleAction() {
  if (props.loading)
    return
  emit('action')
}
</script>

<template>
  <view class="rounded-[24rpx] bg-white/5 p-[24rpx]">
    <view class="text-[24rpx] font-semibold text-white">
      {{ title }}
    </view>
    <view class="mt-[12rpx] text-[20rpx] text-white/70">
      {{ description }}
    </view>
    <view
      class="mt-[20rpx] rounded-[20rpx] bg-emerald-500 px-[24rpx] py-[20rpx] text-center text-[24rpx] font-semibold text-black"
      @tap="handleAction"
    >
      {{ loading ? '处理中' : '触发动作' }}
    </view>
  </view>
</template>
