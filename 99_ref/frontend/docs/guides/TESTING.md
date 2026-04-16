# Testing Guide

Quality is a first-class citizen in K-Control. We use a multi-layered testing strategy to ensure stability.

## 🧪 Testing Strategy

1.  **Unit Tests**: Testing individual functions and logic in isolation.
2.  **Component Tests**: Verifying UI components behave correctly (via Storybook and Vitest/Testing Library).
3.  **E2E Tests**: (Planned) Testing full user flows across the application.

## 🛠️ Running Tests

> [!NOTE]
> We are currently setting up the testing infrastructure. Below are the planned commands.

### All Tests
```bash
pnpm test
```

### Package/App Specific
```bash
pnpm test --filter=@kcontrol/ui
```

## 🎨 Component Testing (Storybook)

Storybook is our primary tool for visual and interaction testing of UI components.
- Run `pnpm dev:ui` to start the Storybook environment.
- Use the **Interactions** tab in Storybook to run simulated user actions.

## 📝 Writing Tests

- Place test files next to the code they test (e.g., `Button.test.tsx`).
- Use descriptive `describe` and `it` blocks.
- Focus on testing behavior and accessibility rather than implementation details.
