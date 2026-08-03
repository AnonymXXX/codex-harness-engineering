<script setup lang="ts">
const submitting = ref(false)
const form = ref({
  title: '',
  content: '',
})

async function submit() {
  if (submitting.value)
    return
  submitting.value = true
  try {
    await Promise.resolve()
    uni.showToast({ title: '提交成功', icon: 'success' })
  }
  finally {
    submitting.value = false
  }
}
</script>

<template>
  <PageLayout title="表单标题">
    <view class="bg-black px-[24rpx] py-[24rpx] text-white">
      <view class="mb-[24rpx] rounded-[24rpx] bg-white/5 p-[24rpx]">
        <view class="mb-[12rpx] text-[24rpx] text-white/70">
          标题
        </view>
        <input v-model="form.title" class="min-h-[88rpx] text-[24rpx]" />
      </view>
      <view class="mb-[24rpx] rounded-[24rpx] bg-white/5 p-[24rpx]">
        <view class="mb-[12rpx] text-[24rpx] text-white/70">
          内容
        </view>
        <textarea v-model="form.content" class="min-h-[240rpx] w-full text-[24rpx]" />
      </view>
      <view
        class="rounded-[24rpx] bg-emerald-500 px-[24rpx] py-[20rpx] text-center text-[24rpx] font-bold text-black"
        @click="submit"
      >
        {{ submitting ? '提交中' : '提交' }}
      </view>
    </view>
  </PageLayout>
</template>
