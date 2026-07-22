import { toast } from 'sonner'

export function useClipboard() {
  const copy = async (text: string) => {
    try {
      await navigator.clipboard.writeText(text)
      toast.success('Copiado para a área de transferência')
    } catch (err) {
      toast.error('Erro ao copiar para a área de transferência')
    }
  }

  return {
    copy,
  }
}
