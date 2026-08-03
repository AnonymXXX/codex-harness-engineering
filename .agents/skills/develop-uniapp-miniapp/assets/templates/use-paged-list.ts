import type { Ref } from 'vue'
import { isRef, ref, watch } from 'vue'

export interface UsePagedListOptions<Item, Raw = Item, Params = Record<string, any>> {
  fetchPage: (params: Params & { skip: number, limit: number }) => Promise<{ data?: Raw[] } | Raw[]>
  adaptItem?: (item: Raw) => Item
  pageSize?: number
  immediate?: boolean
  params?: Ref<Params> | (() => Params) | Params
  clearOnReset?: boolean
}

export function usePagedList<Item, Raw = Item, Params extends Record<string, any> = Record<string, any>>(
  options: UsePagedListOptions<Item, Raw, Params>,
) {
  const {
    fetchPage,
    adaptItem,
    pageSize = 10,
    immediate = true,
    params = {} as Params,
    clearOnReset = true,
  } = options

  const items = ref<Item[]>([]) as Ref<Item[]>
  const loading = ref(false)
  const refreshing = ref(false)
  const finished = ref(false)
  const refreshError = ref(false)
  const loadMoreError = ref(false)
  const page = ref(1)

  function getParams(): Params {
    if (typeof params === 'function')
      return params()
    if (isRef(params))
      return params.value
    return params
  }

  async function loadPage(options: { reset?: boolean, retry?: boolean, source?: 'initial' | 'refresh' | 'loadMore' | 'reset' } = {}) {
    const { reset = false, retry = false, source = reset ? 'refresh' : 'loadMore' } = options

    if (loading.value)
      return

    if (!reset && !retry && (refreshing.value || finished.value || loadMoreError.value))
      return

    if (reset) {
      page.value = 1
      finished.value = false
    }

    loading.value = true
    if (source === 'refresh' || source === 'reset')
      refreshError.value = false
    if (source === 'loadMore' || source === 'initial' || source === 'reset' || retry)
      loadMoreError.value = false

    try {
      const response = await fetchPage({
        ...getParams(),
        skip: (page.value - 1) * pageSize,
        limit: pageSize,
      })
      const rawItems = Array.isArray(response) ? response : (response.data ?? [])
      const nextItems = adaptItem ? rawItems.map(adaptItem) : (rawItems as unknown as Item[])

      if (reset || page.value === 1)
        items.value = nextItems
      else
        items.value = [...items.value, ...nextItems]

      finished.value = rawItems.length < pageSize
      if (rawItems.length > 0 || page.value === 1)
        page.value += 1
    }
    catch (error) {
      if (source === 'refresh' || source === 'reset')
        refreshError.value = true
      else
        loadMoreError.value = true
      throw error
    }
    finally {
      loading.value = false
      refreshing.value = false
    }
  }

  function loadMore() {
    return loadPage({ source: 'loadMore' })
  }

  function retryLoadMore() {
    return loadPage({ retry: true, source: 'loadMore' })
  }

  async function refresh() {
    if (refreshing.value)
      return

    refreshing.value = true
    refreshError.value = false
    loadMoreError.value = false
    finished.value = false
    page.value = 1

    try {
      await loadPage({ reset: true, source: 'refresh' })
    }
    catch (error) {
      refreshing.value = false
      throw error
    }
  }

  function reset(clear = clearOnReset) {
    if (clear)
      items.value = []
    page.value = 1
    finished.value = false
    refreshError.value = false
    loadMoreError.value = false
    return loadPage({ reset: true, source: 'reset' })
  }

  if (isRef(params) || typeof params === 'function') {
    watch(params, () => {
      reset()
    }, { deep: true })
  }

  if (immediate)
    loadPage({ source: 'initial' })

  return {
    items,
    loading,
    refreshing,
    finished,
    refreshError,
    loadMoreError,
    refresh,
    loadMore,
    retryLoadMore,
    reset,
  }
}
