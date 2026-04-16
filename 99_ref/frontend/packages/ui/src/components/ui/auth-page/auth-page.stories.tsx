import type { Meta, StoryObj } from "@storybook/react";
import { AuthPage } from "./auth-page";

const meta: Meta<typeof AuthPage> = {
  title: "Pages/AuthPage",
  component: AuthPage,
  parameters: {
    layout: "fullscreen",
  },
};

export default meta;
type Story = StoryObj<typeof AuthPage>;

export const Login: Story = {
  args: {
    mode: "login",
  },
};

export const Register: Story = {
  args: {
    mode: "register",
  },
};
