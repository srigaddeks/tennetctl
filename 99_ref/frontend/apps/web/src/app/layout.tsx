import type { Metadata } from "next";
import "./globals.css";
import { ThemeProvider } from "@/components/theme-provider";
import { Inter, Sora } from "next/font/google";
import { AccessProvider } from "@/components/providers/AccessProvider";
import { Toaster } from "sonner";

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-primary",
  display: "swap",
});

const sora = Sora({
  subsets: ["latin"],
  variable: "--font-secondary",
  display: "swap",
});

export const metadata: Metadata = {
  title: "K-Control",
  description: "Next-generation compliance management",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" suppressHydrationWarning className={`${inter.variable} ${sora.variable}`}>
      <body className={`${inter.className} antialiased bg-background text-foreground transition-colors duration-300`}>
        <AccessProvider>
          <ThemeProvider
            attribute="class"
            defaultTheme="system"
            enableSystem
            disableTransitionOnChange
          >
            <div className="relative flex min-h-screen flex-col">
              {children}
            </div>
            <Toaster richColors position="top-right" />
          </ThemeProvider>
        </AccessProvider>
      </body>
    </html>
  );
}
