import antfu from '@antfu/eslint-config'

export default antfu({
  vue: true,
  typescript: true,
  jsonc: true,
  yaml: true,
  markdown: false,
  rules: {
    'no-console': 'off',
    'vue/multi-word-component-names': 'off',
  },
})
