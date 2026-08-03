type MessageHandler = (data: any) => void

export interface WebSocketClientOptions {
  url: string
  reconnectInterval?: number
  heartbeatInterval?: number
  maxReconnectAttempts?: number
}

export class WebSocketClient {
  private socket: UniApp.SocketTask | null = null
  private readonly options: Required<WebSocketClientOptions>
  private reconnectAttempts = 0
  private reconnectTimer: number | null = null
  private heartbeatTimer: number | null = null
  private connecting = false
  private manualClose = false
  private handlers = new Map<string, Set<MessageHandler>>()

  constructor(options: WebSocketClientOptions) {
    this.options = {
      reconnectInterval: 5000,
      heartbeatInterval: 30000,
      maxReconnectAttempts: 5,
      ...options,
    }
  }

  connect(path = '') {
    if (this.socket || this.connecting)
      return
    this.connecting = true
    this.manualClose = false

    this.socket = uni.connectSocket({
      url: `${this.options.url}${path}`,
    })

    this.socket.onOpen(() => {
      this.connecting = false
      this.reconnectAttempts = 0
      this.startHeartbeat()
    })

    this.socket.onMessage((event) => {
      const payload = JSON.parse(event.data as string)
      const type = payload.type || '*'
      this.handlers.get(type)?.forEach(handler => handler(payload.data))
      this.handlers.get('*')?.forEach(handler => handler(payload))
    })

    this.socket.onClose(() => {
      this.stopHeartbeat()
      this.socket = null
      this.connecting = false
      if (!this.manualClose)
        this.scheduleReconnect(path)
    })

    this.socket.onError(() => {
      this.stopHeartbeat()
      this.connecting = false
    })
  }

  disconnect() {
    this.manualClose = true
    this.clearReconnectTimer()
    this.stopHeartbeat()
    this.socket?.close({})
    this.socket = null
  }

  send(data: any) {
    if (!this.socket)
      return
    this.socket.send({ data: JSON.stringify(data) })
  }

  on(type: string, handler: MessageHandler) {
    if (!this.handlers.has(type))
      this.handlers.set(type, new Set())
    this.handlers.get(type)?.add(handler)
  }

  off(type: string, handler: MessageHandler) {
    this.handlers.get(type)?.delete(handler)
  }

  private startHeartbeat() {
    this.stopHeartbeat()
    this.heartbeatTimer = setInterval(() => {
      this.send({ type: 'ping' })
    }, this.options.heartbeatInterval) as unknown as number
  }

  private stopHeartbeat() {
    if (this.heartbeatTimer) {
      clearInterval(this.heartbeatTimer)
      this.heartbeatTimer = null
    }
  }

  private scheduleReconnect(path: string) {
    if (this.reconnectAttempts >= this.options.maxReconnectAttempts)
      return
    this.clearReconnectTimer()
    this.reconnectAttempts += 1
    this.reconnectTimer = setTimeout(() => {
      this.connect(path)
    }, this.options.reconnectInterval) as unknown as number
  }

  private clearReconnectTimer() {
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer)
      this.reconnectTimer = null
    }
  }
}
