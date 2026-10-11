"use client"

import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"

export interface Option {
  value: string
  label: string
}

/**
 * Thin wrapper over the shadcn/Base UI select. Passing `items` lets the
 * trigger show the selected *label* even before the popup has mounted.
 */
export function SelectField({
  id,
  value,
  onChange,
  options,
  placeholder,
  className,
  disabled,
  "aria-label": ariaLabel,
}: {
  id?: string
  value: string
  onChange: (value: string) => void
  options: Option[]
  placeholder?: string
  className?: string
  disabled?: boolean
  "aria-label"?: string
}) {
  return (
    <Select
      value={value}
      items={options}
      disabled={disabled}
      onValueChange={(v) => onChange((v as string | null) ?? "")}
    >
      <SelectTrigger id={id} className={className} aria-label={ariaLabel}>
        <SelectValue placeholder={placeholder} />
      </SelectTrigger>
      <SelectContent>
        {options.map((o) => (
          <SelectItem key={o.value} value={o.value}>
            {o.label}
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  )
}
