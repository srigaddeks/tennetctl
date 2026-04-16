# Component Creation Guidelines (@kcontrol/ui)

Follow these rules when creating new components to maintain consistency and scalability.

## 1. Directory Structure
Always group components into folders within `packages/ui/src/components/ui/[component-name]/`.

```text
[component-name]/
├── index.ts        (Export * from "./[component-name]")
└── [component-name].tsx
```

## 2. Component Pattern
- Use **React 19** features (like simplified `ref` passing if applicable, though `forwardRef` is still standard).
- Use **Tailwind CSS v4** semantic classes (`bg-background`, `text-foreground`, `border-border`, etc.).
- Use **CVA (Class Variance Authority)** for managing variants and sizes.
- Use the **`cn` utility** for class merging.

### Template
```tsx
import * as React from "react";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "../../../lib/utils";

const variantStyles = cva(
  "inline-flex items-center ...",
  {
    variants: {
      variant: {
        default: "bg-primary text-primary-foreground",
        // ...
      },
    },
    defaultVariants: {
      variant: "default",
    },
  }
);

export interface ComponentProps
  extends React.HTMLAttributes<HTMLDivElement>,
    VariantProps<typeof variantStyles> {}

const MyComponent = React.forwardRef<HTMLDivElement, ComponentProps>(
  ({ className, variant, ...props }, ref) => {
    return (
      <div
        ref={ref}
        className={cn(variantStyles({ variant, className }))}
        {...props}
      />
    );
  }
);
MyComponent.displayName = "MyComponent";

export { MyComponent, variantStyles };
```

## 3. Dark Mode Support
- Rely on Tailwind semantic classes that map to CSS variables in `globals.css`.
- Avoid hardcoding colors like `bg-white` or `text-black`. Use `bg-background` and `text-foreground` instead.
- For hover states, use opacity or specific theme-aware colors (e.g., `hover:bg-accent`).

## 5. Storybook
Every component **must** include a story for isolated development and testing.
- Place it in the same directory: `[component-name].stories.tsx`.
- Define stories for all major variants and states.
- **Interactive components**: The `ThemeProvider` decorator is already configured, so theme-aware components will work correctly in the Storybook UI.

---
© 2026 Kreesalis. All rights reserved.
