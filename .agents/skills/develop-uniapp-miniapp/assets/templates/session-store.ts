import { defineStore } from 'pinia'
import { computed, ref } from 'vue'

export interface SessionProfile {
  id: number | string
  nickname?: string
  avatar?: string
  [key: string]: any
}

export interface SessionStoreOptions<TProfile extends SessionProfile, TLoginPayload> {
  storageKey?: string
  loginWithCode: (code: string) => Promise<TLoginPayload>
  fetchCurrentUser: () => Promise<TProfile>
  extractToken: (payload: TLoginPayload) => string
  extractProfile?: (payload: TLoginPayload) => TProfile | null | undefined
}

export function createSessionStore<TProfile extends SessionProfile, TLoginPayload>(
  id: string,
  options: SessionStoreOptions<TProfile, TLoginPayload>,
) {
  const storageKey = options.storageKey || `session:${id}`

  return defineStore(id, () => {
    const token = ref<string>(uni.getStorageSync(`${storageKey}:token`) || '')
    const profile = ref<TProfile | null>(uni.getStorageSync(`${storageKey}:profile`) || null)
    const loginInFlight = ref<Promise<boolean> | null>(null)

    const isLoggedIn = computed(() => !!token.value)

    function setToken(value: string) {
      token.value = value
      uni.setStorageSync(`${storageKey}:token`, value)
    }

    function setProfile(value: TProfile | null) {
      profile.value = value
      if (value)
        uni.setStorageSync(`${storageKey}:profile`, value)
      else
        uni.removeStorageSync(`${storageKey}:profile`)
    }

    function logout() {
      token.value = ''
      profile.value = null
      uni.removeStorageSync(`${storageKey}:token`)
      uni.removeStorageSync(`${storageKey}:profile`)
    }

    async function silentLogin() {
      if (loginInFlight.value)
        return loginInFlight.value

      loginInFlight.value = (async () => {
        try {
          const result = await uni.login({ provider: 'weixin' })
          if (!result.code)
            return false
          const payload = await options.loginWithCode(result.code)
          setToken(options.extractToken(payload))
          const currentProfile = options.extractProfile?.(payload)
          if (currentProfile)
            setProfile(currentProfile)
          return true
        }
        catch {
          return false
        }
        finally {
          loginInFlight.value = null
        }
      })()

      return loginInFlight.value
    }

    async function refreshProfile() {
      if (!token.value)
        return false
      try {
        const currentProfile = await options.fetchCurrentUser()
        setProfile(currentProfile)
        return true
      }
      catch {
        return false
      }
    }

    return {
      token,
      profile,
      isLoggedIn,
      setToken,
      setProfile,
      logout,
      silentLogin,
      refreshProfile,
    }
  })
}
