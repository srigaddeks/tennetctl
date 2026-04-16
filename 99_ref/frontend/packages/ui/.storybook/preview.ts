import type { Preview } from "@storybook/react";
import React from "react";
import { ThemeProvider } from "next-themes";
import "../src/globals.css";

const preview: Preview = {
  decorators: [
    (Story) => (
      React.createElement(ThemeProvider, {
        attribute: "class",
        defaultTheme: "system",
        enableSystem: true
      }, React.createElement(Story))
    ),
  ],
  parameters: {
    controls: {
      matchers: {
        color: /(background|color)$/i,
        date: /Date$/i,
      },
    },
  },
};

export default preview;
