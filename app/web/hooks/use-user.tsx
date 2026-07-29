'use client'

import { createContext, useContext } from 'react'

type SessionUser = { id: string; email: string; username: string } | null

type UserContextType = { user: SessionUser }

const UserContext = createContext<UserContextType>({ user: null })

export function UserProvider({ children, user }: { children: React.ReactNode; user: SessionUser }) {
  return <UserContext.Provider value={{ user }}>{children}</UserContext.Provider>
}

export function useUser(): UserContextType {
  return useContext(UserContext)
}
