import { nextTick, ref } from 'vue'

export interface EnsureScrollOptions {
  maxTries?: number
  intervalMs?: number
  startDelayMs?: number
}

export interface ScrollToLatestOptions {
  force?: boolean
  animate?: boolean
}

export interface UseAnchoredScrollOptions {
  pageProxy: any
  scrollSelector?: string
  getLastAnchorId?: () => string
}

export function useAnchoredScroll(options: UseAnchoredScrollOptions) {
  const {
    pageProxy,
    scrollSelector = '.anchored-scroll',
    getLastAnchorId = () => 'anchored-scroll-last',
  } = options

  const scrollIntoView = ref('')
  const scrollTopVal = ref(0)
  const scrollWithAnimation = ref(true)
  const lastScrollTop = ref(0)
  const lastScrollHeight = ref(0)
  const scrollViewHeight = ref(0)
  const isNearBottom = ref(true)
  const unseenCount = ref(0)

  let ensureJobId = 0
  let scrollForceCounter = 0

  function updateScrollViewHeight() {
    if (!pageProxy)
      return

    uni.createSelectorQuery().in(pageProxy).select(scrollSelector).boundingClientRect((rect: any) => {
      if (rect?.height)
        scrollViewHeight.value = rect.height
    }).exec()
  }

  function isAtBottomNow(thresholdPx = 6) {
    const viewHeight = Number(scrollViewHeight.value || 0)
    const scrollHeight = Number(lastScrollHeight.value || 0)
    const scrollTop = Number(lastScrollTop.value || 0)
    if (!viewHeight || !scrollHeight)
      return false
    const distanceToBottom = scrollHeight - (scrollTop + viewHeight)
    return distanceToBottom <= thresholdPx
  }

  function scrollToBottom() {
    if (!scrollViewHeight.value || !isNearBottom.value)
      return

    const anchorId = getLastAnchorId()
    if (!anchorId)
      return

    scrollIntoView.value = ''
    nextTick(() => {
      scrollIntoView.value = anchorId
    })
  }

  function scrollToBottomForce(options?: ScrollToLatestOptions) {
    const animate = options?.animate ?? false
    const force = options?.force ?? false

    if (!force && isAtBottomNow())
      return

    scrollWithAnimation.value = animate
    scrollForceCounter += 1
    scrollTopVal.value = 900000 + scrollForceCounter

    if (!animate) {
      setTimeout(() => {
        scrollWithAnimation.value = true
      }, 0)
    }
  }

  function ensureScrollToBottom(options?: EnsureScrollOptions) {
    const maxTries = options?.maxTries ?? 8
    const intervalMs = options?.intervalMs ?? 100
    const startDelayMs = options?.startDelayMs ?? 0
    const anchorId = getLastAnchorId()

    if (!anchorId)
      return

    ensureJobId += 1
    const currentJobId = ensureJobId
    let tries = 0

    const tick = () => {
      if (currentJobId !== ensureJobId)
        return

      tries += 1
      updateScrollViewHeight()

      scrollIntoView.value = ''
      nextTick(() => {
        scrollIntoView.value = anchorId
      })

      if (tries < maxTries)
        setTimeout(tick, intervalMs)
    }

    if (startDelayMs > 0)
      setTimeout(tick, startDelayMs)
    else
      tick()
  }

  function scrollToLatestStable(options?: ScrollToLatestOptions, layoutShift?: { keyboardOffset?: number, panelHeight?: number }) {
    const force = Boolean(options?.force)
    if (!force && !isNearBottom.value)
      return

    unseenCount.value = 0
    scrollToBottomForce({ force: true, animate: options?.animate ?? false })

    setTimeout(() => {
      scrollToBottomForce({ force: true, animate: false })
    }, 360)

    if ((layoutShift?.keyboardOffset && layoutShift.keyboardOffset > 0) || (layoutShift?.panelHeight && layoutShift.panelHeight > 0)) {
      setTimeout(() => {
        scrollToBottomForce({ force: true, animate: false })
      }, 720)
    }
  }

  function handleScroll(event: any, onNearBottom?: () => void) {
    const scrollTop = Number(event?.detail?.scrollTop || 0)
    const scrollHeight = Number(event?.detail?.scrollHeight || 0)
    lastScrollTop.value = scrollTop
    lastScrollHeight.value = scrollHeight

    const viewHeight = Number(scrollViewHeight.value || 0)
    if (!scrollHeight || !viewHeight) {
      if (scrollTop > 0)
        isNearBottom.value = false
      return
    }

    const threshold = 80
    const distanceToBottom = scrollHeight - (scrollTop + viewHeight)
    const nextIsNearBottom = distanceToBottom <= threshold
    const previousIsNearBottom = isNearBottom.value

    isNearBottom.value = nextIsNearBottom

    if (nextIsNearBottom) {
      const hadUnseen = unseenCount.value > 0
      if (hadUnseen)
        unseenCount.value = 0
      if (!previousIsNearBottom || hadUnseen)
        onNearBottom?.()
    }
  }

  function handleClickNewItems(onRead?: () => void) {
    unseenCount.value = 0
    scrollToBottomForce({ force: true, animate: true })
    onRead?.()
  }

  return {
    scrollIntoView,
    scrollTopVal,
    scrollWithAnimation,
    lastScrollTop,
    lastScrollHeight,
    scrollViewHeight,
    isNearBottom,
    unseenCount,
    updateScrollViewHeight,
    isAtBottomNow,
    scrollToBottom,
    scrollToBottomForce,
    ensureScrollToBottom,
    scrollToLatestStable,
    handleScroll,
    handleClickNewItems,
  }
}
