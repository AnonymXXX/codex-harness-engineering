import { storeToRefs } from 'pinia'
import type { ModalOptions } from '../stores/modal'
import { useModalStore } from '../stores/modal'

export function useAppModal() {
  const modalStore = useModalStore()
  const { modal } = storeToRefs(modalStore)

  return {
    modal,
    showModal: (options: ModalOptions = {}) => modalStore.showModal(options),
    hideModal: () => modalStore.hideModal(),
    resolveModal: (confirm: boolean) => modalStore.resolveModal(confirm),
  }
}
