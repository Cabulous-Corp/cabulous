'use client'

import { LockKeyhole, Mail } from 'lucide-react'
import Link from 'next/link'
import { useRouter } from 'next/navigation'
import { useState } from 'react'
import { useForm } from 'react-hook-form'

import { loginAction } from '@/actions/session'
import { Button } from '@/components/ui/button'
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from '@/components/ui/form'
import { Input } from '@/components/ui/input'

type LoginFormValues = {
  identifier: string
  password: string
}

export default function LoginPage() {
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [submitError, setSubmitError] = useState('')
  const router = useRouter()

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
      const result = await loginAction({ identifier: values.identifier, password: values.password })
      if (!result.error) {
        router.push('/')
      } else {
        setSubmitError(result.error)
      }
    } catch {
      setSubmitError('Erro inesperado ao tentar entrar. Tente novamente em instantes.')
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <main className="grid min-h-svh w-full bg-background lg:grid-cols-[minmax(18rem,0.85fr)_minmax(28rem,1.15fr)]">
      <section
        data-login-panel="brand"
        className="relative isolate flex min-h-56 overflow-hidden bg-linear-to-br from-[#2b1d43] via-[#543a78] to-[#8b68bd] p-8 text-white lg:min-h-svh lg:p-12"
      >
        <div
          aria-hidden="true"
          className="animate-pulse-slow motion-reduce:animate-none absolute -top-20 -right-20 size-72 rounded-full bg-white/15 blur-3xl"
        />
        <div className="relative z-10 flex max-w-sm flex-col justify-between gap-12">
          <span className="text-sm font-semibold tracking-[0.24em] uppercase">Cabulous</span>
          <div>
            <h1 className="text-3xl font-semibold tracking-tight text-white sm:text-4xl">
              Conecte-se ao que importa.
            </h1>
            <p className="mt-4 max-w-xs text-sm leading-6 text-white/75">
              Entre para continuar sua jornada na comunidade.
            </p>
          </div>
        </div>
      </section>

      <section
        data-login-panel="form"
        className="flex items-center justify-center px-5 py-10 animate-in fade-in slide-in-from-bottom-3 duration-700 motion-reduce:animate-none sm:px-8 lg:px-12"
      >
        <Card className="w-full max-w-md border-border/70 shadow-lg shadow-foreground/5">
          <CardHeader className="gap-2 px-6 pt-7 sm:px-8 sm:pt-8">
            <CardTitle className="text-2xl">
              <h2>Entrar</h2>
            </CardTitle>
            <CardDescription>Use seu e-mail ou usuário para acessar sua conta.</CardDescription>
          </CardHeader>
          <CardContent className="px-6 pb-7 sm:px-8 sm:pb-8">
            <Form {...form}>
              <form className="grid gap-5" onSubmit={form.handleSubmit(handleLogin)}>
                <FormField
                  control={form.control}
                  name="identifier"
                  rules={{ required: 'E-mail ou usuário é obrigatório.' }}
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>E-mail ou usuário</FormLabel>
                      <FormControl>
                        <Input
                          {...field}
                          type="text"
                          placeholder="seu@email.com"
                          startAdornment={<Mail aria-hidden="true" />}
                        />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />

                <FormField
                  control={form.control}
                  name="password"
                  rules={{ required: 'Senha é obrigatória.' }}
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Senha</FormLabel>
                      <FormControl>
                        <Input
                          {...field}
                          type="password"
                          placeholder="••••••••"
                          startAdornment={<LockKeyhole aria-hidden="true" />}
                        />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />

                {submitError ? (
                  <p role="alert" className="text-sm text-destructive">
                    {submitError}
                  </p>
                ) : null}

                <div className="flex items-center justify-between gap-4">
                  <Button asChild variant="link" className="h-auto px-0 text-sm">
                    <Link href="/forgot-password">Esqueceu sua senha?</Link>
                  </Button>
                  <Button type="submit" size="lg" disabled={isSubmitting}>
                    {isSubmitting ? 'Entrando...' : 'Entrar'}
                  </Button>
                </div>
              </form>
            </Form>
          </CardContent>
        </Card>
      </section>
    </main>
  )
}
