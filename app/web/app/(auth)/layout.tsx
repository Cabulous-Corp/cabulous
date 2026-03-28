import React from 'react'

export default function AuthLayout({ children }: { children: React.ReactNode }) {
  // TODO: Criar a estrutura e o layout novo de Login/Auth no futuro
  return (
    <div className="divlay flex min-h-screen items-center justify-center bg-background bg-radial-[at_0_100%] from-[#413361]">
      {children}
    </div>
  )
}
