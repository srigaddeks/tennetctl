import type { Meta, StoryObj } from "@storybook/react";
import { DataTableDemo } from "./demo";
import React from "react";

const meta: Meta<typeof DataTableDemo> = {
  title: "UI/DataTable",
  component: DataTableDemo,
  tags: ["autodocs"],
  parameters: {
    layout: "fullscreen",
  },
};

export default meta;
type Story = StoryObj<typeof DataTableDemo>;

export const Default: Story = {
  render: () => (
    <div className="p-8">
      <DataTableDemo />
    </div>
  ),
};
