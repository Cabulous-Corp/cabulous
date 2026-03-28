'use client'

import { MdEmail } from 'react-icons/md'
import { BiSolidLockAlt } from 'react-icons/bi'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import AnimatedTrianglesBackground from '../login/_components/AnimatedTrianglesBackground'

export default function LoginPage() {
  // TODO: Implementar a página de Login do zero

  //   const handleLogin = async () => {}

  return (
    <div className="relative w-full min-h-screen overflow-hidden flex flex-col-reverse md:flex-row items-center justify-center md:justify-around md:grow">
      <AnimatedTrianglesBackground />

      <section className="flex flex-col items-center gap-16 pt-16 pb-16 rounded-lg w-100% z-1">
        <h3 className="text-2xl text-center">Faça seu Login no Cabulous</h3>
        <form className="flex flex-col gap-8 items-center">
          <Input placeholder="Email/User" type="email" id="email" startAdornment={<MdEmail />} />
          <Input placeholder="Password" type="password" id="password" startAdornment={<BiSolidLockAlt />} />
          <Button variant="link" className="text-white">
            Esqueceu sua senha?
          </Button>

          <Button variant="default" size="xl" className="rounded-full w-45">
            Sign in
          </Button>
        </form>
      </section>

      <section className="basis-auto relative text-white flex items-center justify-center">
        <div className="z-10 text-center">
          <h1 className="text-4xl font-bold">Bem vindo de volta!</h1>
          <p className="opacity-70 mt-2">Por favor, insira seus dados pessoais para continuar conectado.</p>
        </div>
      </section>
    </div>
  )
}
