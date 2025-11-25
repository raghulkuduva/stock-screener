import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Momentum Stock Screener | Indian Stocks",
  description: "Screen Indian stocks using momentum-based technical analysis. Find high-momentum opportunities with our 4-gate filtering system.",
  keywords: ["stock screener", "momentum stocks", "NSE", "Indian stocks", "technical analysis", "Nifty 50"],
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="dark">
      <body className="antialiased">{children}</body>
    </html>
  );
}
