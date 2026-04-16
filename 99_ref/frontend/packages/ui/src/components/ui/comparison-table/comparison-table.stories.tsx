import type { Meta, StoryObj } from "@storybook/react";
import { ComparisonTable } from "./comparison-table";
import React from "react";

const meta: Meta<typeof ComparisonTable> = {
  title: "UI/ComparisonTable",
  component: ComparisonTable,
  tags: ["autodocs"],
  parameters: {
    layout: "centered",
  },
};

export default meta;
type Story = StoryObj<typeof ComparisonTable>;

export const Default: Story = {};
