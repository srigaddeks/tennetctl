# Contribution Guide

Welcome! We're glad you're here. This guide outlines the workflow for contributing to the K-Control project.

## 👨‍💻 Development Workflow

We follow a typical GitHub Flow:

1.  **Branching**: Create a new branch for every feature or bug fix.
    - Format: `feature/short-description` or `fix/issue-id`.
2.  **Committing**: Keep commits atomic and use descriptive messages.
    - Recommended: [Conventional Commits](https://www.conventionalcommits.org/).
3.  **Syncing**: Regularly pull from `main` to avoid large merge conflicts.
4.  **Pull Requests**:
    - Push your branch and open a PR against `main`.
    - Fill out the PR template (if available) with a summary of changes.
    - Ensure all CI checks (lint, build, test) pass.
5.  **Review**: At least one peer review is required before merging.

## 📏 Coding Standards

- **TypeScript**: Strictly typed code is preferred. Avoid `any`.
- **Styling**: Follow the Tailwind v4 guidelines in `docs/guides/COMPONENT_DEVELOPMENT.md`.
- **Formatting**: We use Prettier. Your IDE should be configured to format on save, or run `pnpm format`.
- **Linting**: We use ESLint 9. Run `pnpm lint` before pushing.

## 🏗️ Monorepo Best Practices

- Use `workspace:*` for internal dependencies.
- Add dependencies to the root `package.json` only if they are global dev tools (like `turbo` or `prettier`). Otherwise, add them to the specific app or package.
- Respect the boundaries between `apps/` and `packages/`.
