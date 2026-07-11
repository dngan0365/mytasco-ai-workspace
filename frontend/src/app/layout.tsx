import type { Metadata } from "next"; import { Manrope } from "next/font/google"; import { Toaster } from "sonner"; import "./globals.css"; import { AuthProvider } from "@/hooks/use-auth"; import { AppShell } from "@/components/layout/AppShell";
const manrope = Manrope({ subsets: ["latin", "vietnamese"], variable: "--font-manrope" });
export const metadata: Metadata = { title: { default: "My Tasco AI Workspace", template: "%s · My Tasco" }, description: "Không gian tri thức doanh nghiệp an toàn với AI." };
export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) { return <html lang="vi"><body className={manrope.variable}><AuthProvider><AppShell>{children}</AppShell></AuthProvider><Toaster richColors position="top-right"/></body></html>; }
