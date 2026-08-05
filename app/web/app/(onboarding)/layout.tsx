import React from 'react'

export default function OnboardingLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex min-h-svh w-full items-center justify-center bg-background px-4 py-8 sm:py-12">
      {children}
    </div>
  )
}
