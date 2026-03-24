import { Avatar } from '@/components/ui/avatar'
import { cn } from '@/utils/utils'
import Image from 'next/image'
import Link from 'next/link'

export default function Logo({ className, href }: { className?: string; href?: string }) {
  return (
    <Link href={href ?? ''} className={className}>
      <Image
        src="/images/logo-black.png"
        alt="Cabulous"
        width={1680}
        height={430}
        className={cn('h-auto w-auto dark:hidden', className)}
        unoptimized
      />
      <Image
        src="/images/logo-white.png"
        alt="Cabulous"
        width={1680}
        height={430}
        className={cn('h-auto w-auto hidden dark:block', className)}
        unoptimized
      />
    </Link>
  )
}

export function LogoLetter({ className, href }: { className?: string; href?: string }) {
  return (
    <Link href={href ?? ''} className={className}>
      <Image
        src="/images/letter-black.png"
        alt="Cabulous"
        width={528}
        height={351}
        className={cn('h-auto w-auto dark:hidden', className)}
        unoptimized
      />
      <Image
        src="/images/letter-white.png"
        alt="Cabulous"
        width={528}
        height={351}
        className={cn('h-auto w-auto hidden dark:block', className)}
        unoptimized
      />
    </Link>
  )
}

export function LogoAvatar({ hidden = false }: { hidden?: boolean }) {
  return (
    <Avatar
      className={`h-8 w-8 mt-1 shrink-0 bg-transparent border flex items-center justify-center ${hidden ? 'invisible' : ''}`}
    >
      <LogoLetter className="w-full p-[2px]" />
    </Avatar>
  )
}
