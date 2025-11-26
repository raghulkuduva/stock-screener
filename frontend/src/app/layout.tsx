import type { Metadata } from "next";
import "./globals.css";
import { ThemeProvider } from "@/components/theme-provider";

export const metadata: Metadata = {
  title: "Momentum Stock Screener | Indian & US Stocks",
  description: "Screen Indian and US stocks using momentum-based technical analysis. Find high-momentum opportunities with our 4-gate filtering system.",
  keywords: ["stock screener", "momentum stocks", "NSE", "Indian stocks", "US stocks", "S&P 500", "NASDAQ", "technical analysis", "Nifty 50"],
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className="antialiased">
        <ThemeProvider
          attribute="class"
          defaultTheme="system"
          enableSystem
          disableTransitionOnChange
        >
          {children}
        </ThemeProvider>
      </body>
    </html>
  );
}
