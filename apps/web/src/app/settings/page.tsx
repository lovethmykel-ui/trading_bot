"use client";

import { useState, useEffect, useCallback } from "react";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

type StatusType = { type: "success" | "error" | "info"; message: string } | null;
type BotStatus = {
  running: boolean;
  last_scan: string | null;
  last_trade: any | null;
  last_signal: any | null;
  pairs_scanned: number;
  trades_today: number;
  errors: string[];
};
type ConnectionStatus = {
  connected: boolean;
  testnet: boolean;
  balance?: { usdt_free: number; usdt_total: number };
};

export default function SettingsPage() {
  const [apiKey, setApiKey] = useState("");
  const [apiSecret, setApiSecret] = useState("");
  const [isTestnet, setIsTestnet] = useState(true);
  const [exchangeType, setExchangeType] = useState<"bybit" | "paper">("bybit");
  const [paperFundAmount, setPaperFundAmount] = useState("10000");
  const [testing, setTesting] = useState(false);
  const [saving, setSaving] = useState(false);
  const [status, setStatus] = useState<StatusType>(null);
  const [connectionStatus, setConnectionStatus] = useState<ConnectionStatus | null>(null);
  const [botStatus, setBotStatus] = useState<BotStatus | null>(null);
  const [botLoading, setBotLoading] = useState(false);
  const [resetting, setResetting] = useState(false);
  const [showResetConfirm, setShowResetConfirm] = useState(false);

  const fetchStatus = useCallback(async () => {
    try {
      const [connRes, botRes] = await Promise.all([
        fetch(`${API}/exchange/status`),
        fetch(`${API}/bot/status`),
      ]);
      if (connRes.ok) setConnectionStatus(await connRes.json());
      if (botRes.ok) {
        const d = await botRes.json();
        setBotStatus(d.data);
      }
    } catch (_) {}
  }, []);

  useEffect(() => {
    fetchStatus();
    const interval = setInterval(fetchStatus, 10000);
    return () => clearInterval(interval);
  }, [fetchStatus]);

  const handleTest = async () => {
    if (exchangeType !== "paper" && (!apiKey || !apiSecret)) {
      setStatus({ type: "error", message: "Enter both API Key and Secret" });
      return;
    }
    setTesting(true);
    setStatus({ type: "info", message: "Testing connection…" });
    try {
      const res = await fetch(`${API}/exchange/test`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ api_key: apiKey, api_secret: apiSecret, is_testnet: isTestnet, exchange_name: exchangeType }),
      });
      const data = await res.json();
      if (res.ok) {
        setStatus({
          type: "success",
          message: `✅ Connection successful! USDT Balance: $${data.balance?.usdt_free?.toLocaleString() ?? "?"}`,
        });
      } else {
        setStatus({ type: "error", message: data.detail || "Connection failed" });
      }
    } catch {
      setStatus({ type: "error", message: "Cannot reach the backend API. Is it running?" });
    } finally {
      setTesting(false);
    }
  };

  const handleConnect = async () => {
    if (exchangeType !== "paper" && (!apiKey || !apiSecret)) {
      setStatus({ type: "error", message: "Enter both API Key and Secret" });
      return;
    }
    setSaving(true);
    setStatus({ type: "info", message: "Connecting and validating…" });
    try {
      const res = await fetch(`${API}/exchange/connect`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ api_key: apiKey, api_secret: apiSecret, is_testnet: isTestnet, exchange_name: exchangeType }),
      });
      const data = await res.json();
      if (res.ok) {
        setStatus({
          type: "success",
          message: `🔗 ${data.message} — USDT: $${data.balance?.usdt_free?.toLocaleString() ?? "?"}`,
        });
        if (exchangeType !== "paper") {
            setApiKey("");
            setApiSecret("");
        }
        fetchStatus();
      } else {
        setStatus({ type: "error", message: data.detail || "Failed to connect" });
      }
    } catch {
      setStatus({ type: "error", message: "Cannot reach the backend API" });
    } finally {
      setSaving(false);
    }
  };

  const handleFundPaper = async () => {
    setStatus({ type: "info", message: "Funding paper account…" });
    try {
      const res = await fetch(`${API}/exchange/paper/fund`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ amount: parseFloat(paperFundAmount) }),
      });
      const data = await res.json();
      if (res.ok) {
        setStatus({ type: "success", message: data.message });
        fetchStatus();
      } else {
        setStatus({ type: "error", message: data.detail || "Funding failed" });
      }
    } catch {
      setStatus({ type: "error", message: "Cannot reach backend API" });
    }
  };

  const handleStartBot = async () => {
    setBotLoading(true);
    try {
      const res = await fetch(`${API}/bot/start`, { method: "POST" });
      const data = await res.json();
      setStatus({
        type: res.ok ? "success" : "error",
        message: data.message || data.detail || "Unknown",
      });
      fetchStatus();
    } catch {
      setStatus({ type: "error", message: "Failed to start bot" });
    } finally {
      setBotLoading(false);
    }
  };

  const handleStopBot = async () => {
    setBotLoading(true);
    try {
      const res = await fetch(`${API}/bot/stop`, { method: "POST" });
      const data = await res.json();
      setStatus({ type: "success", message: data.message });
      fetchStatus();
    } catch {
      setStatus({ type: "error", message: "Failed to stop bot" });
    } finally {
      setBotLoading(false);
    }
  };

  const handleReset = async () => {
    setResetting(true);
    setShowResetConfirm(false);
    try {
      const res = await fetch(`${API}/bot/reset`, { method: "POST" });
      const data = await res.json();
      if (res.ok) {
        setStatus({ type: "success", message: data.message });
        fetchStatus();
      } else {
        setStatus({ type: "error", message: data.detail || "Reset failed" });
      }
    } catch {
      setStatus({ type: "error", message: "Cannot reach the backend API" });
    } finally {
      setResetting(false);
    }
  };

  const statusColor = status?.type === "success"
    ? "bg-green-500/10 text-green-400 border-green-500/30"
    : status?.type === "info"
    ? "bg-blue-500/10 text-blue-400 border-blue-500/30"
    : "bg-red-500/10 text-red-400 border-red-500/30";

  return (
    <div className="flex-1 space-y-6 p-8 pt-6 max-w-5xl mx-auto">
      {/* Header */}
      <div>
        <h2 className="text-3xl font-bold tracking-tight">System Settings</h2>
        <p className="text-muted-foreground mt-1">Configure your exchange connection and control the trading bot.</p>
      </div>

      {/* Status Banner */}
      {status && (
        <div className={`p-4 rounded-lg text-sm border ${statusColor} flex items-center gap-2`}>
          <span>{status.message}</span>
        </div>
      )}

      <div className="grid gap-6 md:grid-cols-2">

        {/* ── Connection Card ── */}
        <div className="relative group overflow-hidden rounded-2xl border border-white/10 bg-white/5 backdrop-blur-xl p-8 space-y-6 transition-all duration-300 hover:bg-white/10 hover:shadow-[0_0_30px_rgba(245,158,11,0.15)] hover:border-primary/30">
          <div className="absolute inset-0 bg-gradient-to-br from-primary/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-500"></div>
          <div className="relative z-10">
            <h3 className="text-xl font-bold font-orbitron tracking-wide text-white">Exchange Connection</h3>
            <p className="text-sm text-slate-400 mt-1 font-exo2">
              {connectionStatus?.connected
                ? `✅ Connected (${connectionStatus.testnet ? "Testnet" : "Mainnet"}) — $${connectionStatus.balance?.usdt_free?.toLocaleString() ?? "?"} USDT free`
                : "⚠️ Not connected — configure your integration"}
            </p>
          </div>

          {/* Network/Mode toggle */}
          <div className="flex items-center gap-3 pb-4 border-b border-white/10 relative z-10">
            <span className="text-sm font-medium w-16 text-slate-400 uppercase tracking-wider text-xs">Mode:</span>
            <button
              onClick={() => setExchangeType("bybit")}
              className={`px-4 py-2 rounded-lg text-xs font-bold tracking-widest uppercase transition-all duration-300 border ${
                exchangeType === "bybit"
                  ? "bg-primary/20 text-primary border-primary/50 shadow-[0_0_15px_rgba(245,158,11,0.2)]"
                  : "text-slate-400 border-white/10 hover:bg-white/10"
              }`}
            >
              Bybit API
            </button>
            <button
              onClick={() => setExchangeType("paper")}
              className={`px-4 py-2 rounded-lg text-xs font-bold tracking-widest uppercase transition-all duration-300 border ${
                exchangeType === "paper"
                  ? "bg-purple-500/20 text-purple-400 border-purple-500/50 shadow-[0_0_15px_rgba(139,92,246,0.2)]"
                  : "text-slate-400 border-white/10 hover:bg-white/10"
              }`}
            >
              Paper Trading
            </button>
          </div>

          {exchangeType === "bybit" ? (
            <div className="relative z-10 space-y-6">
              {/* Testnet/Mainnet toggle */}
              <div className="flex items-center gap-3">
                <span className="text-sm font-medium w-16 text-slate-400 uppercase tracking-wider text-xs">Network:</span>
                <button
                  onClick={() => setIsTestnet(true)}
                  className={`px-4 py-2 rounded-lg text-xs font-bold tracking-widest uppercase transition-all duration-300 border ${
                    isTestnet
                      ? "bg-yellow-500/20 text-yellow-400 border-yellow-500/50 shadow-[0_0_15px_rgba(234,179,8,0.2)]"
                      : "text-slate-400 border-white/10 hover:bg-white/10"
                  }`}
                >
                  Testnet
                </button>
                <button
                  onClick={() => setIsTestnet(false)}
                  className={`px-4 py-2 rounded-lg text-xs font-bold tracking-widest uppercase transition-all duration-300 border ${
                    !isTestnet
                      ? "bg-green-500/20 text-green-400 border-green-500/50 shadow-[0_0_15px_rgba(34,197,94,0.2)]"
                      : "text-slate-400 border-white/10 hover:bg-white/10"
                  }`}
                >
                  Mainnet
                </button>
              </div>

              {/* API Key fields */}
              <div className="space-y-4">
                <div>
                  <label className="text-xs font-bold tracking-widest text-primary uppercase">API Key</label>
                  <input
                    type="password"
                    placeholder="Enter API Key"
                    value={apiKey}
                    onChange={(e) => setApiKey(e.target.value)}
                    className="mt-2 flex h-10 w-full rounded-lg border border-white/10 bg-black/20 px-4 py-2 text-sm text-white shadow-inner placeholder:text-slate-500 focus:outline-none focus:ring-1 focus:ring-primary focus:border-primary/50 transition-all font-mono"
                  />
                </div>
                <div>
                  <label className="text-xs font-bold tracking-widest text-primary uppercase">API Secret</label>
                  <input
                    type="password"
                    placeholder="Enter Secret"
                    value={apiSecret}
                    onChange={(e) => setApiSecret(e.target.value)}
                    className="mt-2 flex h-10 w-full rounded-lg border border-white/10 bg-black/20 px-4 py-2 text-sm text-white shadow-inner placeholder:text-slate-500 focus:outline-none focus:ring-1 focus:ring-primary focus:border-primary/50 transition-all font-mono"
                  />
                </div>
              </div>
            </div>
          ) : (
            <div className="relative z-10 space-y-4 p-5 rounded-xl border bg-purple-500/10 border-purple-500/30 shadow-inner">
              <p className="text-sm text-purple-300 font-exo2">
                Paper Trading mode simulates all trades locally without hitting any exchange API.
                You can add mock funds to test the bot risk-free.
              </p>
              <div>
                <label className="text-xs font-bold tracking-widest text-purple-400 uppercase">Mock USDT Balance</label>
                <div className="flex gap-3 mt-2">
                  <input
                    type="number"
                    placeholder="Amount"
                    value={paperFundAmount}
                    onChange={(e) => setPaperFundAmount(e.target.value)}
                    className="flex h-10 w-full rounded-lg border border-white/10 bg-black/40 px-4 py-2 text-sm text-white shadow-inner placeholder:text-slate-500 focus:outline-none focus:ring-1 focus:ring-purple-500 focus:border-purple-500/50 transition-all font-mono"
                  />
                  <button
                    onClick={handleFundPaper}
                    className="inline-flex items-center justify-center rounded-lg text-sm font-bold uppercase tracking-wider bg-purple-600 text-white hover:bg-purple-500 h-10 px-6 transition-colors shadow-[0_0_15px_rgba(147,51,234,0.4)] shrink-0"
                  >
                    Fund
                  </button>
                </div>
              </div>
            </div>
          )}

          {/* Buttons */}
          <div className="flex gap-3 relative z-10 pt-2">
            <button
              onClick={handleTest}
              disabled={testing || saving}
              className="flex-1 inline-flex items-center justify-center rounded-lg text-xs font-bold tracking-widest uppercase bg-white/5 text-white shadow hover:bg-white/10 border border-white/10 h-10 px-4 disabled:opacity-50 transition-all hover:shadow-[0_0_15px_rgba(255,255,255,0.1)]"
            >
              {testing ? "Testing…" : "Test Connection"}
            </button>
            <button
              onClick={handleConnect}
              disabled={testing || saving}
              className="flex-1 inline-flex items-center justify-center rounded-lg text-xs font-bold tracking-widest uppercase bg-primary text-black shadow hover:bg-yellow-400 h-10 px-4 disabled:opacity-50 transition-all hover:shadow-[0_0_15px_rgba(245,158,11,0.4)]"
            >
              {saving ? "Connecting…" : "Connect & Save"}
            </button>
          </div>
        </div>

        {/* ── Bot Control Card ── */}
        <div className="relative group overflow-hidden rounded-2xl border border-white/10 bg-white/5 backdrop-blur-xl p-8 space-y-6 transition-all duration-300 hover:bg-white/10 hover:shadow-[0_0_30px_rgba(245,158,11,0.15)] hover:border-primary/30">
          <div className="absolute inset-0 bg-gradient-to-br from-primary/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-500"></div>
          <div className="relative z-10">
            <h3 className="text-xl font-bold font-orbitron tracking-wide text-white">Autonomous Trading Bot</h3>
            <p className="text-sm text-slate-400 mt-1 font-exo2">
              Scans entire USDT market every 5 minutes. Trades top pairs when AI conviction ≥ 65%.
            </p>
          </div>

          {/* Bot status badge */}
          <div className="flex items-center gap-3 relative z-10">
            <div className={`flex items-center gap-2 px-4 py-2 rounded-lg text-xs font-bold tracking-widest uppercase border ${
              botStatus?.running
                ? "bg-green-500/10 text-green-400 border-green-500/30 shadow-[0_0_15px_rgba(34,197,94,0.2)]"
                : "bg-white/5 text-slate-400 border-white/10"
            }`}>
              <span className={`w-2 h-2 rounded-full ${botStatus?.running ? "bg-green-400 animate-pulse shadow-[0_0_8px_rgba(34,197,94,0.8)]" : "bg-slate-500"}`} />
              {botStatus?.running ? "Bot Running" : "Bot Stopped"}
            </div>
            {(botStatus?.pairs_scanned ?? 0) > 0 && (
              <span className="text-xs text-slate-400 font-mono tracking-wider">{botStatus?.pairs_scanned} pairs scanned</span>
            )}
          </div>

          {/* Config summary */}
          <div className="grid grid-cols-3 gap-3 text-center relative z-10">
            {[
              { label: "Risk/Trade", value: "10%" },
              { label: "Stop Loss", value: "2%" },
              { label: "Take Profit", value: "4%" },
            ].map((item) => (
              <div key={item.label} className="rounded-xl bg-black/20 border border-white/5 p-3 hover:bg-black/40 transition-colors">
                <div className="text-lg font-bold text-white font-orbitron">{item.value}</div>
                <div className="text-xs text-slate-400 uppercase tracking-widest mt-1">{item.label}</div>
              </div>
            ))}
          </div>

          {/* Last signal */}
          {botStatus?.last_signal && (
            <div className="relative z-10 rounded-xl bg-black/20 border border-white/5 p-4 space-y-2">
              <div className="text-xs font-bold tracking-widest text-primary uppercase">Last Signal</div>
              <div className="flex items-center gap-3 font-mono">
                <span className={`px-2 py-1 rounded text-xs font-bold ${botStatus.last_signal.decision === "LONG" ? "bg-green-500/20 text-green-400" : "bg-red-500/20 text-red-400"}`}>
                  {botStatus.last_signal.decision}
                </span>
                <span className="text-white font-bold">{botStatus.last_signal.symbol}</span>
                <span className="ml-auto text-slate-400 text-xs">{botStatus.last_signal.confidence}% confidence</span>
              </div>
            </div>
          )}

          {/* Start/Stop buttons */}
          <div className="relative z-10 pt-2">
            {!botStatus?.running ? (
              <button
                onClick={handleStartBot}
                disabled={botLoading || !connectionStatus?.connected}
                className="w-full inline-flex items-center justify-center rounded-lg text-xs font-bold tracking-widest uppercase bg-primary text-black shadow hover:bg-yellow-400 h-12 px-4 disabled:opacity-50 transition-all hover:shadow-[0_0_20px_rgba(245,158,11,0.5)]"
              >
                {botLoading ? "Starting…" : "🚀 Start Auto-Trading"}
              </button>
            ) : (
              <button
                onClick={handleStopBot}
                disabled={botLoading}
                className="w-full inline-flex items-center justify-center rounded-lg text-xs font-bold tracking-widest uppercase bg-red-600/20 text-red-400 border border-red-500/50 shadow hover:bg-red-600/30 h-12 px-4 disabled:opacity-50 transition-all hover:shadow-[0_0_20px_rgba(239,68,68,0.3)]"
              >
                {botLoading ? "Stopping…" : "🛑 Stop Bot"}
              </button>
            )}

            {!connectionStatus?.connected && (
              <p className="text-xs text-slate-400 text-center mt-3 font-exo2">Connect your API keys first to start the bot.</p>
            )}
          </div>
        </div>
      </div>

      {/* ── Bot Activity ── */}
      {botStatus?.last_trade && (
        <div className="relative group overflow-hidden rounded-2xl border border-white/10 bg-white/5 backdrop-blur-xl p-8 transition-all duration-300 hover:bg-white/10 hover:shadow-[0_0_30px_rgba(245,158,11,0.15)] hover:border-primary/30">
          <h3 className="text-xl font-bold font-orbitron tracking-wide text-white mb-6">Last Auto-Trade</h3>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm relative z-10">
            {[
              { label: "Symbol", value: botStatus.last_trade.symbol },
              { label: "Side", value: botStatus.last_trade.side },
              { label: "Qty", value: botStatus.last_trade.qty },
              { label: "Price", value: `$${Number(botStatus.last_trade.price).toLocaleString()}` },
              { label: "Stop Loss", value: `$${botStatus.last_trade.sl}` },
              { label: "Take Profit", value: `$${botStatus.last_trade.tp}` },
              { label: "Order ID", value: botStatus.last_trade.bybit_order_id || "N/A" },
              { label: "Time", value: botStatus.last_trade.at ? new Date(botStatus.last_trade.at).toLocaleTimeString() : "—" },
            ].map((item) => (
              <div key={item.label} className="rounded-xl bg-black/20 border border-white/5 p-4">
                <div className="text-xs font-bold tracking-widest text-slate-400 uppercase">{item.label}</div>
                <div className="font-mono mt-1 text-white text-base">{item.value}</div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* ── Danger Zone ── */}
      <div className="relative overflow-hidden rounded-2xl border border-red-500/30 bg-red-950/20 backdrop-blur-xl p-8 space-y-6">
        <div className="absolute inset-0 bg-red-500/5"></div>
        <div className="relative z-10">
          <h3 className="text-xl font-bold font-orbitron tracking-wide text-red-400">⚠️ Danger Zone</h3>
          <p className="text-sm text-red-300/70 mt-1 font-exo2">
            Wipe all local data (orders, trades, positions, balances, API keys). This does NOT affect your Bybit account.
          </p>
        </div>
        <div className="relative z-10">
          {!showResetConfirm ? (
            <button
              onClick={() => setShowResetConfirm(true)}
              className="inline-flex items-center justify-center rounded-lg text-xs font-bold tracking-widest uppercase bg-red-900/40 text-red-400 border border-red-500/30 hover:bg-red-900/60 h-10 px-6 transition-all hover:shadow-[0_0_15px_rgba(239,68,68,0.2)]"
            >
              Wipe All Data & Reset
            </button>
          ) : (
            <div className="flex items-center gap-4 bg-red-950/50 p-4 rounded-xl border border-red-500/20">
              <span className="text-sm text-red-400 font-bold tracking-wide">Are you sure? This cannot be undone.</span>
              <button
                onClick={handleReset}
                disabled={resetting}
                className="inline-flex items-center justify-center rounded-lg text-xs font-bold tracking-widest uppercase bg-red-600 text-white shadow hover:bg-red-500 h-10 px-6 disabled:opacity-50 transition-all hover:shadow-[0_0_15px_rgba(239,68,68,0.4)]"
              >
                {resetting ? "Resetting…" : "Yes, Wipe Everything"}
              </button>
              <button
                onClick={() => setShowResetConfirm(false)}
                className="inline-flex items-center justify-center rounded-lg text-xs font-bold tracking-widest uppercase bg-white/10 text-white hover:bg-white/20 h-10 px-6 transition-colors"
              >
                Cancel
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}