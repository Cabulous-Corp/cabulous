'use client'

import { ReactNode } from 'react'

// TODO: Implementar Contexto de Usuário real no futuro
/*
interface UserContextType {
  user: any | null
}
// ... (resto do contexto comentado)
*/

// Implementação provisória mínima ("mock") para não quebrar a aplicação
export function UserProvider({ children }: { children: ReactNode }) {
  return <>{children}</>
}

export function useUser() {
  // Retorna um usuário mockado para a interface funcionar sem workspaces
  return {
    user: {
      name: 'Usuário',
      email: 'usuario@cabulous.com',
      avatar: null,
    },
  }
}
