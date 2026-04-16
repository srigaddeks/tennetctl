# Project Architecture & Tech Stack

This document explains the technical architecture and design decisions for the K-Control monorepo.

## 🚀 Tech Stack Overview

- **Runtime**: Node.js >= 20
- **Package Manager**: pnpm 10.4.1
- **Monorepo Tooling**: Turborepo
- **Framework**: Next.js 15.2.3 (App Router + Turbopack)
- **UI Library**: React 19
- **Styling**: Tailwind CSS v4 (CSS-first engine)
- **Components**: Radix UI Primitives
- **Animation**: Motion & tw-animate-css
- **Validation**: Zod
- **Theming**: next-themes

## 🏗️ Monorepo Structure

We use **pnpm workspaces** to manage multiple packages within a single repository:

- `apps/web`: The main Next.js 15 application.
- `packages/ui`: Shared component library and design system tokens.
- `packages/eslint-config`: Centralized ESLint 9 (Flat Config) rules.
- `packages/typescript-config`: Shared `tsconfig.json` bases.
- `packages/prettier-config`: Shared code formatting rules.

## 🛠️ Key Design Decisions

### 1. Turborepo Orchestration
Turborepo handles task execution (build, lint, test) across all packages. It uses a build cache to ensure that tasks are only rerun when code changes, significantly speeding up development and CI.

### 2. Tailwind CSS v4 (@theme)
We use the new CSS-first engine of Tailwind v4. Instead of a `tailwind.config.js` file, all theme variables (colors, fonts, etc.) are defined as CSS variables inside the `@theme` block in `packages/ui/src/globals.css`. This ensures that both the UI components and the web app use a synchronized design system.

### 3. Component Architecture (CVA)
Our components in `@kcontrol/ui` use **Class Variance Authority (CVA)**. This pattern allows us to define component variants (like `primary`, `secondary`, `sm`, `lg`) in a type-safe and readable way, keeping Tailwind logic isolated from component business logic.

### 4. Shared Utility Tooling
The `cn()` utility (using `clsx` and `tailwind-merge`) is used across the project to resolve Tailwind class conflicts predictably, ensuring that overrides and dynamic classes behave as expected.

## 🤝 Team Collaboration & Version Consistency

To avoid "it works on my machine" issues and lockfile conflicts, we enforce version consistency:

- **Node.js**: Specified as `22.14.0` in `.nvmrc` and `.node-version`. We recommend using a version manager like **nvm** or **Volta**.
- **pnpm**: Locked to `10.4.1` via the `packageManager` field in `package.json`.
- **Corepack**: We use Corepack to ensure every developer uses the exact same `pnpm` version automatically. This prevents the `pnpm-lock.yaml` from changing formats between developers.
