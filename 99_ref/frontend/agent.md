# Component Creation Guidelines

This document serves as a guide for creating new components in the `@kcontrol/ui` package to ensure consistency across the codebase.

## 1. Directory Structure
Every component must reside in its own subdirectory within `packages/ui/src/components/ui/`.

```text
packages/ui/src/components/ui/
  └── my-component/
      ├── MyComponent.tsx       # Component implementation
      ├── index.ts              # Local export (export * from "./MyComponent")
      └── MyComponent.stories.tsx # Storybook component stories
```

## 2. Implementation Rules
- Always use `React.forwardRef`.
- Use `cn()` utility for merging class names.
- For variant-based components, use `class-variance-authority`.
- Ensure dark mode compatibility using standard Tailwind classes (e.g., `text-foreground`, `dark:text-primary`).

## 3. Storybook
Every new component **must** include a story. This allows for isolated testing.
- Place it in the same folder as the component.
- Import the component from the local file.
- Define at least one "Default" story.

## 4. Documentation
Add a brief comment block at the top of the component describing its purpose and any unique props.

## 5. Exports
- Export the component from its local `index.ts`.
- Add an explicit export in `packages/ui/src/index.ts`:
  `export * from "./components/ui/my-component/index";`
