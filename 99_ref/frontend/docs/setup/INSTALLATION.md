# Installation Guide

Follow these steps to set up the development environment for K-Control.

## Prerequisites

- **Node.js**: version 22.14.0 (LTS).
- **pnpm**: version 10.4.1 (managed via Corepack).

## 🤝 Team Coordination & Version Consistency

To ensure every developer has the same environment and to avoid lockfile conflicts, we use the following:

### Node.js Version
We use **Node.js v22.14.0**. You can manage this automatically using a version manager:
- **nvm (macOS/Linux)**: run `nvm use` to automatically pick up the version from `.nvmrc`.
- **fnm / Volta**: Will automatically switch versions based on `.node-version`.

### pnpm Version (Corepack)
We lock the pnpm version to **10.4.1**. You **must** enable Corepack to ensure you are using the correct version:
```bash
corepack enable
```
Once enabled, `pnpm` will automatically switch to the version defined in `package.json` whenever you are inside this project.

## 🚀 Running the Project

All commands should be executed from the **root directory** of the monorepo: `c:\Users\lenovo\Desktop\Kreesalis\kcontrol\frontend`.

### 1. Start Development Server
This will start both the UI documentation and the main web application using Turborepo and Turbopack.

```bash
pnpm dev
```

### 2. Access the Application
- **Main Web App**: [http://localhost:3000](http://localhost:3000)

---

## 🛠️ Setup Commands

### Windows (PowerShell)

```powershell
# 1. Enable Corepack to manage pnpm versions
corepack enable

# 2. Prepare the specific pnpm version
corepack prepare pnpm@10.4.1 --activate

# 3. Install dependencies
pnpm install

# 4. Start development server (using Turbopack)
pnpm dev
```

### Windows (Command Prompt - CMD)

```cmd
:: 1. Enable Corepack
corepack enable

:: 2. Prepare pnpm
corepack prepare pnpm@10.4.1 --activate

:: 3. Install dependencies
pnpm install

:: 4. Start development
pnpm dev
```

### Linux / macOS (Terminal)

```bash
# 1. Enable Corepack
sudo corepack enable

# 2. Prepare pnpm
corepack prepare pnpm@10.4.1 --activate

# 3. Install dependencies
pnpm install

# 4. Start development
pnpm dev
```

---

## 🧪 Common Commands

- **Build all packages**: `pnpm build`
- **Lint the entire workspace**: `pnpm lint`
- **Check TypeScript types**: `pnpm typecheck` (run within a package directory)
- **Format code**: `pnpm format`
