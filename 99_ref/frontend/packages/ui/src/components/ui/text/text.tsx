import * as React from "react"
import { cva, type VariantProps } from "class-variance-authority"
import { cn } from "../../../lib/utils"

const textVariants = cva(
  "font-primary text-foreground transition-colors duration-200",
  {
    variants: {
      variant: {
        h1: "font-secondary text-4xl font-bold leading-tight tracking-tight text-foreground",
        h2: "font-secondary text-3xl font-semibold leading-tight tracking-tight text-foreground",
        h3: "font-secondary text-2xl font-semibold leading-tight tracking-tight text-foreground",
        h4: "font-secondary text-xl font-medium leading-tight tracking-tight text-foreground",
        h5: "font-secondary text-lg font-medium leading-tight tracking-tight text-foreground",
        h6: "font-secondary text-base font-medium leading-tight tracking-tight text-foreground",
        p: "font-primary text-base leading-relaxed text-foreground",
        lead: "font-primary text-lg leading-relaxed text-foreground",
        large: "font-primary text-lg font-semibold text-foreground",
        small: "font-primary text-sm leading-normal text-muted-foreground",
        muted: "font-primary text-base leading-relaxed text-muted-foreground",
        code: "font-mono text-sm bg-muted px-1.5 py-0.5 rounded-md text-foreground",
        blockquote: "font-primary text-lg italic border-l-4 border-primary pl-4 text-muted-foreground",
      },
      weight: {
        thin: "font-thin",
        extralight: "font-extralight",
        light: "font-light",
        normal: "font-normal",
        medium: "font-medium",
        semibold: "font-semibold",
        bold: "font-bold",
        extrabold: "font-extrabold",
        black: "font-black",
      },
      align: {
        left: "text-left",
        center: "text-center",
        right: "text-right",
        justify: "text-justify",
      },
      color: {
        default: "text-foreground",
        muted: "text-muted-foreground",
        primary: "text-primary",
        secondary: "text-secondary",
        accent: "text-accent",
        destructive: "text-destructive",
        success: "text-success",
        warning: "text-warning",
        error: "text-error",
      },
    },
    defaultVariants: {
      variant: "p",
      weight: "normal",
      align: "left",
      color: "default",
    },
  }
)

export interface TextProps
  extends Omit<React.HTMLAttributes<HTMLElement>, 'color'>,
    VariantProps<typeof textVariants> {
  as?: "h1" | "h2" | "h3" | "h4" | "h5" | "h6" | "p" | "span" | "div"
  children: React.ReactNode
}

const Text = React.forwardRef<HTMLElement, TextProps>(
  ({ className, variant, weight, align, color: colorVariant, as, children, ...props }, ref) => {
    // Determine the element to render based on variant or as prop
    const getElement = () => {
      if (as) return as
      if (variant?.startsWith("h")) return variant as "h1" | "h2" | "h3" | "h4" | "h5" | "h6"
      return "p"
    }

    const Component = getElement()

    return (
      <Component
        className={cn(textVariants({ variant, weight, align, color: colorVariant, className }))}
        ref={ref as any}
        {...props}
      >
        {children}
      </Component>
    )
  }
)

Text.displayName = "Text"

export { Text, textVariants }