'use client'

import { useState } from 'react'
import Link from 'next/link'
import { useForm } from 'react-hook-form'
import { BiSolidLockAlt } from 'react-icons/bi'
import { MdEmail } from 'react-icons/md'

import { Button } from '@/components/ui/button'
import { Form, FormControl, FormField, FormItem } from '@/components/ui/form'
import { Input } from '@/components/ui/input'

import AnimatedTrianglesBackground from '../login/_components/AnimatedTrianglesBackground'

type LoginFormValues = {
  identifier: string
  password: string
}

export default function LoginPage() {
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [submitError, setSubmitError] = useState('')

  const form = useForm<LoginFormValues>({
    defaultValues: {
      identifier: '',
      password: '',
    },
    mode: 'onSubmit',
  })

  const handleLogin = async (values: LoginFormValues) => {
    setSubmitError('')
    setIsSubmitting(true)

    try {
      const res = await fetch('/api/auth/login', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ email: values.identifier, password: values.password }),
      })
      const data = await res.json()

      if (!res.ok) {
        setSubmitError('Nao foi possivel entrar. Confira suas credenciais e tente novamente.')
        console.log('Erro:', data)
        return
      }

      console.log('Login bem-sucedido:', data)
    } catch (error) {
      setSubmitError('Erro inesperado ao tentar entrar. Tente novamente em instantes.')
      console.error('Erro', error)
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <div className="relative grid min-h-screen w-full grid-rows-[300px_1fr] items-center justify-center overflow-hidden md:grid-cols-2 md:grid-rows-1">
      <AnimatedTrianglesBackground />

      <section className="z-1 flex w-100% flex-col items-center gap-16 rounded-lg pt-16 pb-16">
        <h3 className="text-center text-2xl">Faca seu Login no Cabulous</h3>

        <Form {...form}>
          <form className="flex flex-col items-center gap-8" onSubmit={form.handleSubmit(handleLogin)}>
            <FormField
              control={form.control}
              name="identifier"
              rules={{ required: 'E-mail ou usuario e obrigatorio.' }}
              render={({ field, fieldState }) => (
                <FormItem className="w-full">
                  <FormControl>
                    <Input
                      {...field}
                      id="identifier"
                      type="text"
                      placeholder="Email/User"
                      startAdornment={<MdEmail />}
                      error={fieldState.error?.message}
                    />
                  </FormControl>
                </FormItem>
              )}
            />

            <FormField
              control={form.control}
              name="password"
              rules={{
                required: 'Senha e obrigatoria.',
                minLength: { value: 8, message: 'A senha deve ter pelo menos 8 caracteres.' },
              }}
              render={({ field, fieldState }) => (
                <FormItem className="w-full">
                  <FormControl>
                    <Input
                      {...field}
                      id="password"
                      type="password"
                      placeholder="Password"
                      startAdornment={<BiSolidLockAlt />}
                      error={fieldState.error?.message}
                    />
                  </FormControl>
                </FormItem>
              )}
            />

            {submitError ? <p className="text-sm text-destructive">{submitError}</p> : null}

            <Button asChild variant="link" className="text-white">
              <Link href="/forgot-password">Esqueceu sua senha?</Link>
            </Button>

            <Button type="submit" variant="default" size="xl" className="w-45 rounded-full" disabled={isSubmitting}>
              {isSubmitting ? 'Entrando...' : 'Sign in'}
            </Button>
          </form>
        </Form>
      </section>

      <section className="z-1 order-first basis-auto text-white md:order-last">
        <div className="z-10 text-center">
          <h1 className="text-4xl font-bold">Bem vindo de volta!</h1>
          <p className="mt-2 opacity-70">Por favor, insira seus dados pessoais para continuar conectado.</p>
        </div>
      </section>
    </div>
  )
}
