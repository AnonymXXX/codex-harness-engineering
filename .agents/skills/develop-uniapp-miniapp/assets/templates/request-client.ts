export interface RequestClientOptions {
  baseUrl: string
  getToken?: () => string
  ensureReady?: () => Promise<void>
  refreshAuth?: () => Promise<boolean>
  showLoading?: (message?: string) => void
  hideLoading?: () => void
  toast?: (message: string) => void
  buildHeaders?: (input: {
    url: string
    method: string
    data?: any
    headers: Record<string, any>
  }) => Promise<Record<string, any>> | Record<string, any>
}

export interface RequestOptions extends UniApp.RequestOptions {
  loading?: boolean
  showError?: boolean
  _retried?: boolean
}

export class RequestClient {
  private readonly options: RequestClientOptions
  private isRefreshing = false
  private pending: Array<() => void> = []

  constructor(options: RequestClientOptions) {
    this.options = options
  }

  async request<T = any>(options: RequestOptions): Promise<T> {
    if (options.loading)
      this.options.showLoading?.(typeof options.loading === 'string' ? options.loading : '加载中...')

    try {
      await this.options.ensureReady?.()
      const method = (options.method || 'GET').toUpperCase()
      let headers: Record<string, any> = { ...(options.header || {}) }
      const token = this.options.getToken?.()
      if (token)
        headers.Authorization = `Bearer ${token}`
      if (this.options.buildHeaders) {
        headers = await this.options.buildHeaders({
          url: options.url,
          method,
          data: options.data,
          headers,
        })
      }

      return await new Promise<T>((resolve, reject) => {
        uni.request({
          ...options,
          method,
          url: options.url.startsWith('http') ? options.url : `${this.options.baseUrl}${options.url}`,
          header: headers,
          success: async (response) => {
            if (response.statusCode >= 200 && response.statusCode < 300) {
              resolve(response.data as T)
              return
            }
            if (response.statusCode === 401 && !options._retried && this.options.refreshAuth) {
              const ok = await this.retryAfterRefresh()
              if (ok) {
                this.request<T>({ ...options, _retried: true }).then(resolve).catch(reject)
                return
              }
            }
            const payload: any = response.data || {}
            if (options.showError !== false)
              this.options.toast?.(payload.msg || payload.message || '请求失败')
            reject(payload)
          },
          fail: (error: any) => {
            if (options.showError !== false)
              this.options.toast?.(error?.errMsg || '请求失败')
            reject(error)
          },
        })
      })
    }
    finally {
      if (options.loading)
        this.options.hideLoading?.()
    }
  }

  private async retryAfterRefresh() {
    if (this.isRefreshing) {
      return await new Promise<boolean>((resolve) => {
        this.pending.push(() => resolve(true))
      })
    }

    this.isRefreshing = true
    try {
      const ok = await this.options.refreshAuth?.()
      if (!ok)
        return false
      this.pending.splice(0).forEach(run => run())
      return true
    }
    finally {
      this.isRefreshing = false
      this.pending = []
    }
  }

  get<T = any>(url: string, data?: any, options?: Omit<RequestOptions, 'url' | 'method' | 'data'>) {
    return this.request<T>({ ...options, url, method: 'GET', data })
  }

  post<T = any>(url: string, data?: any, options?: Omit<RequestOptions, 'url' | 'method' | 'data'>) {
    return this.request<T>({ ...options, url, method: 'POST', data })
  }

  put<T = any>(url: string, data?: any, options?: Omit<RequestOptions, 'url' | 'method' | 'data'>) {
    return this.request<T>({ ...options, url, method: 'PUT', data })
  }

  delete<T = any>(url: string, data?: any, options?: Omit<RequestOptions, 'url' | 'method' | 'data'>) {
    return this.request<T>({ ...options, url, method: 'DELETE', data })
  }
}
