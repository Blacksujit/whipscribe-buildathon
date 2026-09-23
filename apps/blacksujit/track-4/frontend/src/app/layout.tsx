import type { Metadata } from "next";
import { Inter, DM_Serif_Display, JetBrains_Mono } from "next/font/google";
import "./globals.css";

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-sans",
  display: "swap",
});

const serifDisplay = DM_Serif_Display({
  subsets: ["latin"],
  variable: "--font-display",
  display: "swap",
});

const jetbrainsMono = JetBrains_Mono({
  subsets: ["latin"],
  variable: "--font-mono",
  display: "swap",
});

export const metadata: Metadata = {
  title: "CallCoach AI",
  description:
    "Meeting quality coaching that tracks trends across your library of WhipScribe recordings.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body
        className={[
          inter.variable,
          serifDisplay.variable,
          jetbrainsMono.variable,
          "antialiased",
          "font-sans",
        ].join(" ")}
      >
        {children}
      </body>
    </html>
  );
}
