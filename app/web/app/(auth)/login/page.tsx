'use client'

import { useState } from 'react'
import { MdEmail } from 'react-icons/md'
import { BiSolidLockAlt } from 'react-icons/bi'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import AnimatedTrianglesBackground from '../login/_components/AnimatedTrianglesBackground'

export default function LoginPage() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  //const [error, setError] = useState('')

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!email || !password) {
      console.log('Email e senha são obrigatórios') //setError("preencha todos os campos")
      return
    }
    try {
      const res = await fetch('/api/auth/login', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ email, password }),
      })
      const data = await res.json()

      if (!res.ok) {
        //redirecionar para a dashboard
        console.log('Erro:', data) //setError(data.message || 'deu ruim')
        return
      }

      console.log('Login bem-sucedido:', data)
      //para redirecionar router.push('/dashboard')
    } catch (error) {
      console.error('Erro', error) //setError('deu ruim')
    }
  }

  return (
    <div className="relative w-full min-h-screen overflow-hidden grid grid-rows-[300px_1fr] md:grid-cols-2 md:grid-rows-1 items-center justify-center">
      <AnimatedTrianglesBackground />

      <section className="flex flex-col items-center gap-16 pt-16 pb-16 rounded-lg w-100% z-1">
        <h3 className="text-2xl text-center">Faça seu Login no Cabulous</h3>
        <form className="flex flex-col gap-8 items-center" onSubmit={handleLogin}>
          <Input
            placeholder="Email/User"
            type="email"
            id="email"
            startAdornment={<MdEmail />}
            value={email}
            onChange={(e) => setEmail(e.target.value)}
          />

          <Input
            placeholder="Password"
            type="password"
            id="password"
            startAdornment={<BiSolidLockAlt />}
            value={password}
            onChange={(e) => setPassword(e.target.value)}
          />
          <Button type="submit" variant="link" className="text-white">
            Esqueceu sua senha?
          </Button>

          <Button variant="default" size="xl" className="rounded-full w-45">
            Sign in
          </Button>
        </form>
      </section>

      <section className="basis-auto relative text-white order-first md:order-last z-1">
        <div className="z-10 text-center">
          <h1 className="text-4xl font-bold">Bem vindo de volta!</h1>
          <p className="opacity-70 mt-2">Por favor, insira seus dados pessoais para continuar conectado.</p>
        </div>
      </section>
    </div>
  )
}
