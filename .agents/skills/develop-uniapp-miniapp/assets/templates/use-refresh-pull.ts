import { computed, ref } from 'vue'

const MIN_LOADING_DURATION = 500
const RESULT_STATE_DURATION = 250
const RESET_ANIMATION_DURATION = 280
const TOP_EPSILON = 5

export enum PullStatus {
  Normal = 'normal',
  Pulling = 'pulling',
  Loosing = 'loosing',
  Loading = 'loading',
  Success = 'success',
  Error = 'error',
}

export interface UseRefreshPullOptions {
  threshold?: number
  maxDistance?: number
  getScrollTop: () => number
  isHorizontalSwiping?: () => boolean
  onRefresh: () => void
}

export function useRefreshPull(options: UseRefreshPullOptions) {
  const {
    threshold = 80,
    maxDistance = 150,
    getScrollTop,
    isHorizontalSwiping = () => false,
    onRefresh,
  } = options

  const status = ref<PullStatus>(PullStatus.Normal)
  const distance = ref(0)
  const duration = ref(0)
  let startY = 0
  let loadingStartTime = 0

  const trackStyle = computed(() => ({
    transform: `translate3d(0, ${distance.value}px, 0)`,
    transitionDuration: `${duration.value}ms`,
  }))

  const statusText = computed(() => {
    switch (status.value) {
      case PullStatus.Loosing:
        return '释放刷新'
      case PullStatus.Loading:
        return '刷新中'
      case PullStatus.Success:
        return '刷新完成'
      case PullStatus.Error:
        return '刷新失败'
      default:
        return '下拉刷新'
    }
  })

  const themeColor = computed(() => {
    return status.value === PullStatus.Error ? '#EF4444' : '#10B981'
  })

  function handleTouchStart(event: any) {
    if (isHorizontalSwiping())
      return false
    if (status.value === PullStatus.Loading || status.value === PullStatus.Success || status.value === PullStatus.Error)
      return false
    if (getScrollTop() > TOP_EPSILON)
      return false

    const touch = event?.touches?.[0]
    if (!touch)
      return false

    startY = touch.clientY
    duration.value = 0
    return true
  }

  function handleTouchMove(event: any) {
    if (isHorizontalSwiping() || status.value === PullStatus.Loading)
      return false
    if (getScrollTop() > TOP_EPSILON)
      return false

    const touch = event?.touches?.[0]
    if (!touch)
      return false

    const diff = touch.clientY - startY
    if (diff <= 0)
      return false

    const moveDistance = Math.min(diff * 0.5, maxDistance)
    distance.value = moveDistance
    status.value = moveDistance >= threshold ? PullStatus.Loosing : PullStatus.Pulling
    return true
  }

  function handleTouchEnd() {
    if (status.value === PullStatus.Loading)
      return false

    const previousStatus = status.value
    duration.value = RESET_ANIMATION_DURATION

    if (status.value === PullStatus.Loosing) {
      status.value = PullStatus.Loading
      distance.value = threshold
      loadingStartTime = Date.now()
      onRefresh()
      return true
    }

    status.value = PullStatus.Normal
    distance.value = 0
    return previousStatus === PullStatus.Pulling || previousStatus === PullStatus.Loosing
  }

  function handleTouchCancel() {
    if (status.value === PullStatus.Loading)
      return false

    if (status.value === PullStatus.Pulling || status.value === PullStatus.Loosing) {
      duration.value = RESET_ANIMATION_DURATION
      status.value = PullStatus.Normal
      distance.value = 0
      return true
    }

    return false
  }

  function finishRefresh(error = false) {
    const elapsed = Date.now() - loadingStartTime
    const waitTime = Math.max(0, MIN_LOADING_DURATION - elapsed)

    setTimeout(() => {
      status.value = error ? PullStatus.Error : PullStatus.Success

      setTimeout(() => {
        duration.value = RESET_ANIMATION_DURATION
        distance.value = 0

        setTimeout(() => {
          if (status.value === PullStatus.Success || status.value === PullStatus.Error)
            status.value = PullStatus.Normal
        }, RESET_ANIMATION_DURATION)
      }, RESULT_STATE_DURATION)
    }, waitTime)
  }

  return {
    threshold,
    status,
    distance,
    duration,
    trackStyle,
    statusText,
    themeColor,
    handleTouchStart,
    handleTouchMove,
    handleTouchEnd,
    handleTouchCancel,
    finishRefresh,
  }
}
