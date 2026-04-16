import type { Meta, StoryObj } from "@storybook/react";
import { Switch } from "./switch";
import React from "react";

const meta: Meta<typeof Switch> = {
  title: "UI/Switch",
  component: Switch,
  tags: ["autodocs"],
  parameters: {
    layout: "centered",
  },
};

export default meta;
type Story = StoryObj<typeof Switch>;

export const Default: Story = {
  args: {
    children: "Low power mode",
  },
};

export const Selected: Story = {
  args: {
    children: "Night mode",
    defaultSelected: true,
  },
};

export const Disabled: Story = {
  args: {
    children: "Airplane mode",
    isDisabled: true,
  },
};

export const DarkMode: Story = {
  render: (args) => (
    <div className="dark bg-background p-8 rounded-lg border">
      <Switch {...args} />
    </div>
  ),
  args: {
    children: "Dark theme switch",
    defaultSelected: true,
  },
};
