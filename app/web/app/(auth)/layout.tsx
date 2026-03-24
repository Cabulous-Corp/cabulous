import React from 'react'

export default function AuthLayout({ children }: { children: React.ReactNode }) {
  // TODO: Criar a estrutura e o layout novo de Login/Auth no futuro
  return (
    <div className="flex min-h-screen items-center justify-center p-4">
      {children}
    </div>
  )
}
