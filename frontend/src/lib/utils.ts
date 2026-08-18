import { type ClassValue, clsx } from 'clsx'
import { twMerge } from 'tailwind-merge'

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

export function formatValue(value: number | null | undefined, unit: string): string {
  if (value === null || value === undefined) return '--'
  return `${value.toFixed(1)}${unit}`
}
