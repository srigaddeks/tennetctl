import type { Meta, StoryObj } from "@storybook/react";
import { Toggle } from "./toggle";
import { Bold } from "lucide-react";
import React from "react";

const meta: Meta<typeof Toggle> = {
  title: "UI/Toggle",
  component: Toggle,
  tags: ["autodocs"],
  parameters: {
    layout: "centered",
  },
};

export default meta;
type Story = StoryObj<typeof Toggle>;

export const Default: Story = {
  args: {
    children: <Bold className="h-4 w-4" />,
    "aria-label": "Toggle bold",
  },
};

export const Outline: Story = {
  args: {
    variant: "outline",
    children: <Bold className="h-4 w-4" />,
    "aria-label": "Toggle bold",
  },
};

export const WithText: Story = {
  args: {
    children: "Toggle Me",
  },
};
