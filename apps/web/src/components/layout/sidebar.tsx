import Link from 'next/link';
import { LayoutDashboard, LineChart, Wallet, ShoppingCart, ShieldAlert, BrainCircuit, FlaskConical, Settings } from 'lucide-react';

const sidebarItems = [
  { icon: LayoutDashboard, label: 'Dashboard', href: '/' },
  { icon: LineChart, label: 'Markets', href: '/markets' },
  { icon: Wallet, label: 'Portfolio', href: '/portfolio' },
  { icon: ShoppingCart, label: 'Orders', href: '/orders' },
  { icon: ShieldAlert, label: 'Risk', href: '/risk' },
  { icon: BrainCircuit, label: 'Strategies', href: '/strategies' },
  { icon: FlaskConical, label: 'AI Lab', href: '/ai-lab' },
  { icon: Settings, label: 'Settings', href: '/settings' },
];

export function Sidebar() {
  return (
    <aside className="w-72 border-r border-white/10 bg-white/5 backdrop-blur-xl flex flex-col h-full shadow-[4px_0_24px_rgba(0,0,0,0.2)] z-10">
      <div className="p-6 border-b border-white/10 flex items-center gap-3">
        <div className="relative">
          <div className="absolute inset-0 bg-primary rounded-full blur-md opacity-50"></div>
          <BrainCircuit className="w-8 h-8 text-primary relative z-10" />
        </div>
        <h1 className="text-xl font-bold font-orbitron tracking-widest text-white">
          QUANTUM<span className="text-primary block text-[0.65rem] tracking-[0.3em] uppercase opacity-80">Ensemble</span>
        </h1>
      </div>
      <nav className="flex-1 p-4 space-y-1.5 overflow-y-auto">
        {sidebarItems.map((item) => {
          const Icon = item.icon;
          return (
            <Link
              key={item.href}
              href={item.href}
              className="group flex items-center gap-3 px-4 py-3 text-slate-300 hover:text-white rounded-xl transition-all duration-300 hover:bg-white/10 hover:shadow-[0_0_15px_rgba(255,255,255,0.05)] border border-transparent hover:border-white/10 relative overflow-hidden"
            >
              <div className="absolute inset-0 bg-gradient-to-r from-primary/0 via-primary/5 to-primary/0 translate-x-[-100%] group-hover:translate-x-[100%] transition-transform duration-700"></div>
              <Icon className="w-5 h-5 group-hover:text-primary transition-colors duration-300 relative z-10" />
              <span className="font-medium tracking-wide relative z-10">{item.label}</span>
            </Link>
          );
        })}
      </nav>
      <div className="p-4 border-t border-white/10 bg-white/5">
        <div className="flex items-center gap-3 px-4 py-3 rounded-xl border border-white/5 bg-black/20">
          <div className="w-10 h-10 rounded-full bg-gradient-to-br from-primary to-purple-600 flex items-center justify-center shadow-[0_0_15px_rgba(245,158,11,0.4)]">
            <span className="text-sm font-bold text-white font-orbitron">OP</span>
          </div>
          <div className="flex flex-col">
            <span className="text-sm font-medium text-white tracking-wide">Operator</span>
            <span className="text-xs text-primary font-mono opacity-80">SYS.ADMIN_ON</span>
          </div>
        </div>
      </div>
    </aside>
  );
}
