import type { Metadata } from "next";
import { Exo_2, Orbitron } from "next/font/google";
import "./globals.css";
import { Sidebar } from "@/components/layout/sidebar";

const exo2 = Exo_2({ subsets: ["latin"], variable: "--font-exo2" });
const orbitron = Orbitron({ subsets: ["latin"], variable: "--font-orbitron" });

export const metadata: Metadata = {
  title: "Quantum Ensemble | AI Trading Intelligence",
  description: "Institutional AI Trading Intelligence Platform",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="dark">
      <body className={`${exo2.className} ${exo2.variable} ${orbitron.variable} bg-background text-foreground min-h-screen flex bg-[radial-gradient(ellipse_at_top_right,_var(--tw-gradient-stops))] from-slate-900 via-[#0F172A] to-[#0a0f1d]`}>
        <Sidebar />
        <main className="flex-1 flex flex-col h-screen overflow-hidden">
          <header className="h-16 border-b border-white/5 bg-white/5 flex items-center justify-between px-6 backdrop-blur-md shadow-[0_4px_30px_rgba(0,0,0,0.1)]">
            <div className="flex items-center gap-4">
              <span className={`font-semibold text-xl text-primary font-orbitron tracking-wider`}>Command Center</span>
            </div>
            <div className="flex items-center gap-4">
              <span className="text-sm text-green-400 flex items-center gap-2 px-3 py-1 rounded-full bg-green-400/10 border border-green-400/20 font-medium">
                <span className="w-2 h-2 rounded-full bg-green-400 shadow-[0_0_8px_rgba(74,222,128,0.8)] animate-pulse"></span>
                System Operational
              </span>
            </div>
          </header>
          <div className="flex-1 overflow-auto p-6 relative z-0">
            {children}
          </div>
        </main>
      </body>
    </html>
  );
}
