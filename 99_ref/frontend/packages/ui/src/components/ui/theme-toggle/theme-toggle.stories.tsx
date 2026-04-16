import type { Meta, StoryObj } from "@storybook/react";
import { ThemeToggle } from "./theme-toggle";

const meta: Meta<typeof ThemeToggle> = {
  title: "UI/ThemeToggle",
  component: ThemeToggle,
  tags: ["autodocs"],
  parameters: {
    layout: "centered",
  },
};

export default meta;
type Story = StoryObj<typeof ThemeToggle>;

export const PremiumToggle: Story = {};

export const DemoOne: Story = {
  render: () => <ThemeToggle />,
};
