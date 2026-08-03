interface RealtimeLike {
  on: (type: string, handler: (data: any) => void) => void
  off: (type: string, handler: (data: any) => void) => void
}

export function useRealtimeEvents(
  createHandlers: () => Partial<Record<string, (data: any) => void>>,
  getClient: () => RealtimeLike | null,
) {
  let client: RealtimeLike | null = null
  const active = new Map<string, (data: any) => void>()

  function bind() {
    const next = getClient()
    if (!next)
      return
    if (client && client !== next)
      unbind()
    client = next
    if (active.size > 0)
      return
    const handlers = createHandlers()
    Object.entries(handlers).forEach(([type, handler]) => {
      if (!handler)
        return
      active.set(type, handler)
      client?.on(type, handler)
    })
  }

  function unbind() {
    if (!client)
      return
    active.forEach((handler, type) => {
      client?.off(type, handler)
    })
    active.clear()
    client = null
  }

  onShow(bind)
  onHide(unbind)
  onUnload(unbind)

  return {
    bind,
    unbind,
  }
}
