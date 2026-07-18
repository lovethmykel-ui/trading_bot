"use client";

import { useEffect, useState } from "react";

export function PortfolioOverview() {
  const [balance, setBalance] = useState({ usdt_free: 0, usdt_total: 0 });
  
  useEffect(() => {
    const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
    fetch(`${API_URL}/portfolio`)
      .then(res => res.json())
      .then(data => {
         if (data.status === "success" && data.data) {
           const usdt = data.data.balances.find((b: any) => b.asset === "USDT");
           if (usdt) {
             setBalance({ usdt_free: usdt.free, usdt_total: usdt.free + usdt.locked });
           }
         }
      })
      .catch(err => console.error(err));
  }, []);

  const stats = [
    { label: "Portfolio Value", value: `$${balance.usdt_total.toLocaleString(undefined, {minimumFractionDigits: 2})}`, change: "0.0%", trend: "neutral" },
    { label: "Free USDT", value: `$${balance.usdt_free.toLocaleString(undefined, {minimumFractionDigits: 2})}`, change: "Ready", trend: "up" },
    { label: "Win Rate", value: "0.0%", change: "0.0%", trend: "neutral" },
    { label: "Open Positions", value: "0", change: "0", trend: "neutral" },
  ];

  return (
    <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4 w-full">
      {stats.map((stat, i) => (
        <div key={i} className="relative group overflow-hidden rounded-2xl border border-white/10 bg-white/5 backdrop-blur-xl p-6 transition-all duration-300 hover:bg-white/10 hover:shadow-[0_0_30px_rgba(245,158,11,0.15)] hover:border-primary/30 cursor-pointer">
          <div className="absolute inset-0 bg-gradient-to-br from-primary/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-500"></div>
          
          <h3 className="text-sm font-medium text-slate-400 tracking-wider uppercase font-exo2 relative z-10">
            {stat.label}
          </h3>
          
          <div className="mt-2 text-3xl font-bold font-orbitron tracking-wide text-white relative z-10 group-hover:text-primary transition-colors duration-300 drop-shadow-[0_0_8px_rgba(255,255,255,0.3)]">
            {stat.value}
          </div>
          
          <div className="mt-4 flex items-center gap-2 relative z-10">
            <span className={`text-xs px-2 py-0.5 rounded-full border ${stat.trend === "up" ? "bg-green-500/10 text-green-400 border-green-500/20" : "bg-white/5 text-slate-400 border-white/10"}`}>
              {stat.change}
            </span>
            <span className="text-xs text-slate-500">from last period</span>
          </div>
        </div>
      ))}
    </div>
  );
}
