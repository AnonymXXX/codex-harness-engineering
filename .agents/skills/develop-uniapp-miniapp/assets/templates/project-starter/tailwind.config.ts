import { getIconCollections, iconsPlugin } from '@egoist/tailwindcss-icons'
import type { Config } from 'tailwindcss'
import plugin from 'tailwindcss/plugin'

const iconMaskFix = plugin(({ addUtilities }) => {
  const iconFix = {
    'mask-size': 'contain !important',
    '-webkit-mask-size': 'contain !important',
    'mask-position': 'center !important',
    '-webkit-mask-position': 'center !important',
    'mask-repeat': 'no-repeat !important',
    '-webkit-mask-repeat': 'no-repeat !important',
  }

  addUtilities({
    '[class^="i-"]': iconFix,
    '[class*=" i-"]': iconFix,
  })
})

export default <Config>{
  content: ['./index.html', './src/**/*.{html,js,ts,jsx,tsx,vue}'],
  theme: {
    extend: {
      spacing: {
        safe: 'max(env(safe-area-inset-bottom), 32rpx)',
      },
      colors: {
        brand: {
          primary: '#22c55e',
          dark: '#050505',
        },
        ui: {
          text: '#ffffff',
          muted: '#9ca3af',
          bg: '#050505',
          panel: '#111111',
        },
      },
      boxShadow: {
        soft: '0 8px 24px rgba(0, 0, 0, 0.24)',
      },
    },
  },
  plugins: [
    iconsPlugin({
      collections: getIconCollections(['fa6-solid']),
    }),
    iconMaskFix,
  ],
}
