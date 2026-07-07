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
    <aside className="w-64 border-r border-border bg-card flex flex-col h-full">
      <div className="p-6 border-b border-border">
        <h1 className="text-xl font-bold flex items-center gap-2 text-primary">
          <BrainCircuit className="w-6 h-6" />
          Quantum Ensemble
        </h1>
      </div>
      <nav className="flex-1 p-4 space-y-2 overflow-y-auto">
        {sidebarItems.map((item) => {
          const Icon = item.icon;
          return (
            <Link
              key={item.href}
              href={item.href}
              className="flex items-center gap-3 px-4 py-3 text-muted-foreground hover:text-foreground hover:bg-accent rounded-md transition-colors"
            >
              <Icon className="w-5 h-5" />
              <span className="font-medium">{item.label}</span>
            </Link>
          );
        })}
      </nav>
      <div className="p-4 border-t border-border">
        <div className="flex items-center gap-3 px-4 py-3">
          <div className="w-8 h-8 rounded-full bg-accent flex items-center justify-center">
            <span className="text-sm font-bold">QE</span>
          </div>
          <div className="flex flex-col">
            <span className="text-sm font-medium">User Admin</span>
            <span className="text-xs text-muted-foreground">Pro Tier</span>
          </div>
        </div>
      </div>
    </aside>
  );
}
