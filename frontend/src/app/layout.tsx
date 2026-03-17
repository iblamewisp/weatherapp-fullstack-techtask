import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { Notification } from "@/components/Notification";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "Weather App",
  description: "Real-time weather information",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className={inter.className}>
        <Notification />
        {children}
      </body>
    </html>
  );
}
