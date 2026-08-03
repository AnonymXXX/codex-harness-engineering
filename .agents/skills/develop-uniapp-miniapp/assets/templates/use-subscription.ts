export interface SubscriptionStatus {
  remaining: number
  rejected: boolean
}

export interface SubscriptionRequester {
  loadStatus: () => Promise<Record<string, SubscriptionStatus>>
  reportResult?: (results: Record<string, string>) => Promise<void>
}

export function createSubscriptionHelper(
  templateMap: Record<string, string>,
  requester: SubscriptionRequester,
) {
  const statusMap = ref<Record<string, SubscriptionStatus>>({})

  async function refresh() {
    statusMap.value = await requester.loadStatus()
    return statusMap.value
  }

  function getTemplateId(key: string) {
    return templateMap[key]
  }

  function isSubscribed(key: string) {
    const templateId = getTemplateId(key)
    const state = templateId ? statusMap.value[templateId] : undefined
    return !!state && state.remaining > 0
  }

  async function request(keys: string[]) {
    const templateIds = keys.map(getTemplateId).filter(Boolean) as string[]
    const results: Record<string, string> = {}

    for (let index = 0; index < templateIds.length; index += 3) {
      const batch = templateIds.slice(index, index + 3)
      const response: any = await new Promise((resolve, reject) => {
        uni.requestSubscribeMessage({
          tmplIds: batch,
          success: resolve,
          fail: reject,
        })
      })

      batch.forEach((templateId) => {
        results[templateId] = response[templateId] || 'reject'
      })
    }

    if (Object.keys(results).length > 0)
      await requester.reportResult?.(results)

    await refresh()
    return results
  }

  return {
    statusMap,
    refresh,
    request,
    isSubscribed,
  }
}
