import type { ComponentInternalInstance } from 'vue'
import { nextTick } from 'vue'

export interface LoadMoreState {
  loading: boolean
  finished: boolean
  refreshing: boolean
  loadMoreError: boolean
}

export interface UseLoadMoreObserverOptions {
  instance: ComponentInternalInstance | null
  getState: (key: string) => LoadMoreState
  onLoadMore: (key: string) => void
  triggerSelectorPrefix?: string
  getTriggerSelector?: (key: string) => string
  bottomMargin?: number
}

export function useLoadMoreObserver(options: UseLoadMoreObserverOptions) {
  const {
    instance,
    getState,
    onLoadMore,
    triggerSelectorPrefix = '.load-more-trigger-',
    getTriggerSelector,
    bottomMargin = 100,
  } = options

  const observerMap = new Map<string, UniApp.IntersectionObserver>()

  function resolveSelector(key: string) {
    if (getTriggerSelector)
      return getTriggerSelector(key)
    return `${triggerSelectorPrefix}${key}`
  }

  function initObserver(key: string) {
    destroyObserver(key)

    if (!instance)
      return

    const state = getState(key)
    if (state.loading || state.finished || state.refreshing || state.loadMoreError)
      return

    const observer = uni.createIntersectionObserver(instance, {
      thresholds: [0.1],
      initialRatio: 0,
      observeAll: false,
    })

    observer.relativeToViewport({ bottom: bottomMargin }).observe(resolveSelector(key), (result) => {
      if (result.intersectionRatio > 0)
        triggerLoadMore(key)
    })

    observerMap.set(key, observer)
  }

  function destroyObserver(key: string) {
    const observer = observerMap.get(key)
    if (!observer)
      return
    observer.disconnect()
    observerMap.delete(key)
  }

  function destroyAll() {
    observerMap.forEach(observer => observer.disconnect())
    observerMap.clear()
  }

  function triggerLoadMore(key: string) {
    const state = getState(key)
    if (state.loading || state.finished || state.refreshing || state.loadMoreError)
      return
    state.loading = true
    onLoadMore(key)
  }

  function finishLoadMore(key: string, finished = false, error = false) {
    const state = getState(key)
    state.loading = false
    state.finished = finished
    state.loadMoreError = error

    if (!finished && !error) {
      nextTick(() => {
        destroyObserver(key)
        setTimeout(() => {
          initObserver(key)
        }, 100)
      })
    }
  }

  return {
    initObserver,
    destroyObserver,
    destroyAll,
    triggerLoadMore,
    finishLoadMore,
  }
}
