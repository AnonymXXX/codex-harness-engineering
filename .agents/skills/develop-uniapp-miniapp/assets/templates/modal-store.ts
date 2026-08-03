import { defineStore } from 'pinia'

export type ModalPlacement = 'center' | 'bottom'

export type ModalStyleValue = string | Record<string, string | number>

export interface ModalOptions {
  title?: string
  content?: string
  placement?: ModalPlacement
  showCancel?: boolean
  showConfirm?: boolean
  cancelText?: string
  confirmText?: string
  maskClosable?: boolean
  maxHeight?: string
  maskClassName?: string
  panelClassName?: string
  titleClassName?: string
  contentClassName?: string
  footerClassName?: string
  maskStyle?: ModalStyleValue
  panelStyle?: ModalStyleValue
  contentStyle?: ModalStyleValue
  footerStyle?: ModalStyleValue
}

export interface ModalResult {
  confirm: boolean
  cancel: boolean
}

export interface ModalState {
  show: boolean
  title: string
  content: string
  placement: ModalPlacement
  showCancel: boolean
  showConfirm: boolean
  cancelText: string
  confirmText: string
  maskClosable: boolean
  maxHeight: string
  maskClassName: string
  panelClassName: string
  titleClassName: string
  contentClassName: string
  footerClassName: string
  maskStyle: ModalStyleValue
  panelStyle: ModalStyleValue
  contentStyle: ModalStyleValue
  footerStyle: ModalStyleValue
}

function createDefaultModalState(): ModalState {
  return {
    show: false,
    title: '提示',
    content: '',
    placement: 'center',
    showCancel: true,
    showConfirm: true,
    cancelText: '取消',
    confirmText: '确定',
    maskClosable: true,
    maxHeight: '',
    maskClassName: '',
    panelClassName: '',
    titleClassName: '',
    contentClassName: '',
    footerClassName: '',
    maskStyle: '',
    panelStyle: '',
    contentStyle: '',
    footerStyle: '',
  }
}

export const useModalStore = defineStore('app-modal', {
  state: () => ({
    modal: createDefaultModalState(),
    modalResolver: null as ((result: ModalResult) => void) | null,
  }),

  actions: {
    showModal(options: ModalOptions = {}) {
      if (this.modalResolver) {
        this.modalResolver({ confirm: false, cancel: true })
        this.modalResolver = null
      }

      this.modal = {
        ...createDefaultModalState(),
        ...options,
        show: true,
      }

      return new Promise<ModalResult>((resolve) => {
        this.modalResolver = resolve
      })
    },

    hideModal() {
      this.resolveModal(false)
    },

    resolveModal(confirm: boolean) {
      this.modal.show = false
      const resolver = this.modalResolver
      this.modalResolver = null
      if (resolver)
        resolver({ confirm, cancel: !confirm })
    },
  },
})
