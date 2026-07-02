import type { Metadata, Viewport } from "next";
import "./globals.css";
import { LiveProvider } from "@/components/LiveProvider";
import { Providers } from "@/components/Providers";
import { Sidebar } from "@/components/Sidebar";

export const metadata: Metadata = {
  title: "FC Edge — The FC Trading Terminal",
  description:
    "Market intelligence, AI ratings and squad tools for EA Sports FC. Know what to buy, what to sell and which SBCs are worth it.",
  manifest: "/manifest.webmanifest",
};

export const viewport: Viewport = {
  themeColor: "#0a0a12",
  width: "device-width",
  initialScale: 1,
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="min-h-screen">
        <Providers>
          <LiveProvider />
          <div className="mx-auto flex max-w-[1400px]">
            <Sidebar />
            <main className="min-w-0 flex-1 px-4 py-6 md:px-8">{children}</main>
          </div>
        </Providers>
      </body>
    </html>
  );
}
