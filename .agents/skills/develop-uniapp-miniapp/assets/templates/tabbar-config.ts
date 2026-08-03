interface BaseTabBarItem {
  key: string
  text?: string
  icon: string
  activeIcon?: string
  badge?: number | string | null
  dot?: boolean
  disabled?: boolean
}

export interface TabBarPageItem extends BaseTabBarItem {
  type?: 'page'
  text: string
  pagePath: string
}

export interface TabBarActionItem extends BaseTabBarItem {
  type: 'action'
  center?: boolean
}

export type TabBarItem = TabBarPageItem | TabBarActionItem

export const tabBarItems: TabBarItem[] = [
  {
    key: 'home',
    text: '首页',
    pagePath: '/pages/index/index',
    icon: 'i-fa6-solid-house',
    activeIcon: 'i-fa6-solid-house',
  },
  {
    key: 'discover',
    text: '发现',
    pagePath: '/pages/discover/index',
    icon: 'i-fa6-solid-compass',
    activeIcon: 'i-fa6-solid-compass',
  },
  {
    key: 'profile',
    text: '我的',
    pagePath: '/pages/profile/index',
    icon: 'i-fa6-solid-user',
    activeIcon: 'i-fa6-solid-user',
  },
]
