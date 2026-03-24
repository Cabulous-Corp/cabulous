'use client'

import * as React from 'react'
import { Check, ChevronsUpDown } from 'lucide-react'
import { cn } from '@/utils/utils'
import { Button } from '@/components/ui/button'
import { Command, CommandEmpty, CommandGroup, CommandInput, CommandItem, CommandList } from '@/components/ui/command'
import { Popover, PopoverContent, PopoverTrigger } from '@/components/ui/popover'
import { LoadingDots } from '@/components/loading-dots'

export interface ComboboxOption {
  value: string | number
  label: string
  description?: string
}

interface ComboboxProps {
  options: ComboboxOption[]
  value?: string | number
  onValueChange?: (value: string | number) => void
  onSearch?: (query: string) => void
  placeholder?: string
  emptyMessage?: string
  searchPlaceholder?: string
  disabled?: boolean
  isLoading?: boolean
  className?: string
  id?: string
}

export function Combobox({
  options,
  value,
  onValueChange,
  onSearch,
  placeholder = 'Selecione...',
  emptyMessage = 'Nenhum resultado encontrado.',
  searchPlaceholder = 'Buscar...',
  disabled = false,
  isLoading = false,
  className,
  id,
}: ComboboxProps) {
  const [open, setOpen] = React.useState(false)
  const [searchQuery, setSearchQuery] = React.useState('')

  const selectedOption = options.find((option) => option.value === value)

  const handleSearch = React.useCallback(
    (query: string) => {
      setSearchQuery(query)
      if (onSearch) {
        onSearch(query)
      }
    },
    [onSearch],
  )

  return (
    <Popover open={open} onOpenChange={setOpen}>
      <PopoverTrigger asChild>
        <Button
          id={id}
          variant="outline"
          role="combobox"
          aria-expanded={open}
          disabled={disabled}
          className={cn(
            'w-full h-12 font-medium justify-between text-muted-foreground bg-muted/30 border-border/50 text-foreground font-medium focus:ring-1',
            !selectedOption && 'text-muted-foreground',
            className,
          )}
        >
          {selectedOption ? selectedOption.label : placeholder}
          <ChevronsUpDown className="ml-2 h-4 w-4 shrink-0 opacity-50" />
        </Button>
      </PopoverTrigger>
      <PopoverContent className="w-[var(--radix-popover-trigger-width)] p-0" align="start">
        <Command shouldFilter={!onSearch}>
          <CommandInput placeholder={searchPlaceholder} value={searchQuery} onValueChange={handleSearch} />
          <CommandList>
            {isLoading ? (
              <div className="flex items-center justify-center gap-2 py-6">
                <LoadingDots />
                <span className="text-sm text-muted-foreground">Carregando...</span>
              </div>
            ) : (
              <>
                <CommandEmpty>{emptyMessage}</CommandEmpty>
                <CommandGroup>
                  {options.map((option) => (
                    <CommandItem
                      key={option.value}
                      value={option.value.toString()}
                      onSelect={() => {
                        onValueChange?.(option.value)
                        setOpen(false)
                      }}
                    >
                      <Check className={cn('mr-2 h-4 w-4', value === option.value ? 'opacity-100' : 'opacity-0')} />
                      <div className="flex flex-col">
                        <span>{option.label}</span>
                        {option.description && (
                          <span className="text-xs text-muted-foreground">{option.description}</span>
                        )}
                      </div>
                    </CommandItem>
                  ))}
                </CommandGroup>
              </>
            )}
          </CommandList>
        </Command>
      </PopoverContent>
    </Popover>
  )
}
