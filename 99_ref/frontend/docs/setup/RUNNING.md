# Running the Project

This guide explains how to run the different parts of the K-Control project during development.

## 🚀 Quick Commands

All commands must be run from the **root directory**.

| Goal | Command | URL |
| :--- | :--- | :--- |
| **Run Everything** | `pnpm dev` | [http://localhost:3000](http://localhost:3000) |
| **Run Web App Only** | `pnpm dev:web` | [http://localhost:3000](http://localhost:3000) |
| **Run Storybook Only** | `pnpm dev:ui` | [http://localhost:6006](http://localhost:6006) |

---

## 🌐 Web Application (Next.js)

The main application resides in `apps/web`. We use **Turbopack** for fast development builds.

### To start the web app:
```bash
pnpm dev:web
```
This will start the development server on **Port 3000**.

---

## 🎨 Storybook (Component Library)

We use Storybook to develop and test UI components in isolation within the `@kcontrol/ui` package.

### To start Storybook:
```bash
pnpm dev:ui
```
This will start the component dashboard on **Port 6006**. It allows you to:
- Browse all primitive components.
- Interact with different variants (Primary, Outline, etc.).
- View automatic accessibility and documentation for each component.

---

## 🛠️ Common Troubleshooting

### Execution Policy Error (Windows)
If you get a security error saying "scripts is disabled on this system", run this in PowerShell:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Module Not Found
If you encounter "Module not found" errors after a large update:
1. Run `pnpm install` in the root.
2. Run `pnpm build` to ensure workspace links are fresh.
