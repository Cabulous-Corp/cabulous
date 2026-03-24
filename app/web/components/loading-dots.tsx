import { cn } from '@/utils/utils'

export function LoadingDots() {
  const delays = ['delay-0', 'delay-100', 'delay-200']
  const dots = Array.from(
    {
      length: 3,
    },
    (_, index) => (
      <div
        key={index}
        className={cn(
          'w-2 h-2 bg-primary/50 dark:bg-secondary-foreground/50 rounded-full animate-in fade-in duration-1000 delay-1000 repeat-infinite',
          delays[index],
        )}
      ></div>
    ),
  )
  return <div className="flex gap-1">{dots}</div>
}
