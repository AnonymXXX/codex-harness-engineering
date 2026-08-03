import { computed, ref } from 'vue'
import { onHide, onShow } from '@dcloudio/uni-app'

export function usePageState() {
  const keyword = ref('')
  const loading = ref(false)

  const statusText = computed(() =>
    keyword.value.trim()
      ? `当前关键词：${keyword.value.trim()}`
      : '这里放页面局部 hook 管理的状态与编排。',
  )

  function setKeyword(next: string) {
    keyword.value = next
  }

  async function handleSubmit() {
    if (loading.value)
      return
    loading.value = true
    try {
      await Promise.resolve()
    }
    finally {
      loading.value = false
    }
  }

  onShow(() => {
    loading.value = false
  })

  onHide(() => {
    loading.value = false
  })

  return {
    keyword,
    loading,
    statusText,
    setKeyword,
    handleSubmit,
  }
}
