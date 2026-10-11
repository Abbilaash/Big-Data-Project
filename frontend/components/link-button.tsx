import Link from "next/link"
import type { VariantProps } from "class-variance-authority"

import { buttonVariants } from "@/components/ui/button"
import { cn } from "@/lib/utils"

type LinkButtonProps = VariantProps<typeof buttonVariants> & {
  href: string
  className?: string
  children: React.ReactNode
  /** Plain <a> for off-site or non-Next destinations. */
  external?: boolean
  newTab?: boolean
}

/**
 * A real link (role "link") styled as a button. Base UI's Button renders
 * `<a role="button">` for non-native elements, which mislabels navigation for
 * assistive tech; use this for anything that navigates.
 */
export function LinkButton({ href, variant, size, className, children, external, newTab }: LinkButtonProps) {
  const classes = cn(buttonVariants({ variant, size }), className)
  if (external) {
    return (
      <a
        href={href}
        className={classes}
        {...(newTab ? { target: "_blank", rel: "noopener noreferrer" } : {})}
      >
        {children}
      </a>
    )
  }
  return (
    <Link href={href} className={classes}>
      {children}
    </Link>
  )
}
