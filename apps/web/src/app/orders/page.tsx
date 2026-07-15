"use client";

import { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";

const API = "http://localhost:8000";

interface LiveOrder {
  id?: number;
  order_id?: string;
  created_at?: string;
  symbol: string;
  side: string;
  price?: number;
  avg_price?: number;
  amount?: number;
  qty?: number;
  status?: string;
  order_type?: string;
}

interface LivePosition {
  symbol: string;
  side: string;
  size: number;
  entry_price: number;
  mark_price: number;
  unrealized_pnl: number;
  leverage: number;
}

type ExecStatus = { type: "success" | "error"; message: string } | null;

export default function OrdersPage() {
  const [symbol, setSymbol] = useState("BTCUSDT");
  const [size, setSize] = useState("");
  const [orders, setOrders] = useState<LiveOrder[]>([]);
  const [positions, setPositions] = useState<LivePosition[]>([]);
  const [executing, setExecuting] = useState(false);
  const [execStatus, setExecStatus] = useState<ExecStatus>(null);
  const [tab, setTab] = useState<"positions" | "history">("positions");

  const fetchData = async () => {
    try {
      const [ordersRes, posRes] = await Promise.all([
        fetch(`${API}/orders/live/history`).catch(() => null),
        fetch(`${API}/orders/positions`).catch(() => null),
      ]);
      if (ordersRes?.ok) {
        const d = await ordersRes.json();
        if (d.data) setOrders(d.data);
      }
      if (posRes?.ok) {
        const d = await posRes.json();
        if (d.data) setPositions(d.data);
      }
    } catch (e) {
      console.error("Fetch error:", e);
    }
  };

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 8000);
    return () => clearInterval(interval);
  }, []);

  const handleOrder = async (side: "BUY" | "SELL") => {
    const qty = parseFloat(size);
    if (!qty || qty <= 0) {
      setExecStatus({ type: "error", message: "Enter a valid order size" });
      return;
    }
    setExecuting(true);
    setExecStatus(null);
    try {
      const res = await fetch(`${API}/orders/live/execute`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          symbol: symbol.toUpperCase(),
          side,
          size: qty,
          order_type: "MARKET",
        }),
      });
      const json = await res.json();
      if (res.ok && json.status === "success") {
        const d = json.data;
        setExecStatus({
          type: "success",
          message: `${side} ${qty} ${symbol} executed @ $${Number(d.executed_price).toLocaleString()} | Order ID: ${d.bybit_order_id || "N/A"}`,
        });
        setSize("");
        setTimeout(fetchData, 1500);
      } else {
        setExecStatus({ type: "error", message: json.detail || "Execution failed" });
      }
    } catch (e: any) {
      setExecStatus({ type: "error", message: "Cannot reach backend: " + e.message });
    } finally {
      setExecuting(false);
    }
  };

  return (
    <div className="flex-1 space-y-5 p-8 pt-6">
      <div>
        <h2 className="text-3xl font-bold tracking-tight">Trade Terminal</h2>
        <p className="text-sm text-muted-foreground mt-1">
          Execute real orders on Bybit Testnet with automatic 2% SL &amp; 4% TP.
        </p>
      </div>

      <div className="grid gap-5 md:grid-cols-2 lg:grid-cols-7">
        {/* ── Order Panel ── */}
        <Card className="col-span-2">
          <CardHeader>
            <CardTitle>Manual Execution</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label>Symbol</Label>
              <Input
                value={symbol}
                onChange={(e) => setSymbol(e.target.value.toUpperCase())}
                placeholder="BTCUSDT"
              />
            </div>
            <div className="space-y-2">
              <Label>Qty (base currency)</Label>
              <Input
                type="number"
                placeholder="e.g. 0.01"
                value={size}
                onChange={(e) => setSize(e.target.value)}
                min="0"
                step="0.001"
              />
            </div>

            {execStatus && (
              <div
                className={`p-3 rounded-md text-xs border ${
                  execStatus.type === "success"
                    ? "bg-green-500/10 text-green-400 border-green-500/30"
                    : "bg-red-500/10 text-red-400 border-red-500/30"
                }`}
              >
                {execStatus.message}
              </div>
            )}

            <div className="grid grid-cols-2 gap-3 pt-1">
              <Button
                onClick={() => handleOrder("BUY")}
                disabled={executing}
                className="bg-green-600 hover:bg-green-500 text-white"
              >
                {executing ? "Submitting…" : "Buy / Long"}
              </Button>
              <Button
                onClick={() => handleOrder("SELL")}
                disabled={executing}
                className="bg-red-600 hover:bg-red-500 text-white"
              >
                {executing ? "Submitting…" : "Sell / Short"}
              </Button>
            </div>

            {/* Risk config info */}
            <div className="pt-2 border-t space-y-1 text-xs text-muted-foreground">
              <div className="flex justify-between"><span>Stop Loss</span><span className="text-red-400">-2%</span></div>
              <div className="flex justify-between"><span>Take Profit</span><span className="text-green-400">+4%</span></div>
              <div className="flex justify-between"><span>Leverage</span><span>5x</span></div>
              <div className="flex justify-between"><span>Mode</span><span className="text-yellow-400">Testnet</span></div>
            </div>
          </CardContent>
        </Card>

        {/* ── Right panel: positions + history ── */}
        <Card className="col-span-5">
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle>
                {tab === "positions" ? "Open Positions" : "Order History"}
              </CardTitle>
              <div className="flex gap-2">
                <button
                  onClick={() => setTab("positions")}
                  className={`text-xs px-3 py-1 rounded-md border transition-colors ${
                    tab === "positions"
                      ? "bg-primary text-primary-foreground border-primary"
                      : "text-muted-foreground border-border hover:bg-secondary"
                  }`}
                >
                  Positions ({positions.length})
                </button>
                <button
                  onClick={() => setTab("history")}
                  className={`text-xs px-3 py-1 rounded-md border transition-colors ${
                    tab === "history"
                      ? "bg-primary text-primary-foreground border-primary"
                      : "text-muted-foreground border-border hover:bg-secondary"
                  }`}
                >
                  History
                </button>
              </div>
            </div>
          </CardHeader>
          <CardContent>
            {tab === "positions" ? (
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Symbol</TableHead>
                    <TableHead>Side</TableHead>
                    <TableHead>Size</TableHead>
                    <TableHead>Entry</TableHead>
                    <TableHead>Mark</TableHead>
                    <TableHead>PnL</TableHead>
                    <TableHead>Lev</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {positions.length > 0 ? (
                    positions.map((p, i) => (
                      <TableRow key={i}>
                        <TableCell className="font-medium">{p.symbol}</TableCell>
                        <TableCell className={p.side === "Buy" ? "text-green-400" : "text-red-400"}>
                          {p.side}
                        </TableCell>
                        <TableCell>{p.size}</TableCell>
                        <TableCell>${Number(p.entry_price).toLocaleString()}</TableCell>
                        <TableCell>${Number(p.mark_price).toLocaleString()}</TableCell>
                        <TableCell
                          className={p.unrealized_pnl >= 0 ? "text-green-400" : "text-red-400"}
                        >
                          {p.unrealized_pnl >= 0 ? "+" : ""}${Number(p.unrealized_pnl).toFixed(2)}
                        </TableCell>
                        <TableCell>{p.leverage}x</TableCell>
                      </TableRow>
                    ))
                  ) : (
                    <TableRow>
                      <TableCell colSpan={7} className="text-center text-muted-foreground py-6">
                        No open positions. The bot will open positions automatically when signals are detected.
                      </TableCell>
                    </TableRow>
                  )}
                </TableBody>
              </Table>
            ) : (
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Symbol</TableHead>
                    <TableHead>Side</TableHead>
                    <TableHead>Type</TableHead>
                    <TableHead>Qty</TableHead>
                    <TableHead>Avg Price</TableHead>
                    <TableHead>Status</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {orders.length > 0 ? (
                    orders.map((o, i) => (
                      <TableRow key={o.order_id || i}>
                        <TableCell className="font-medium">{o.symbol}</TableCell>
                        <TableCell className={o.side === "Buy" ? "text-green-400" : "text-red-400"}>
                          {o.side}
                        </TableCell>
                        <TableCell>{o.order_type}</TableCell>
                        <TableCell>{o.qty ?? o.amount}</TableCell>
                        <TableCell>
                          {o.avg_price && o.avg_price > 0
                            ? `$${Number(o.avg_price).toLocaleString()}`
                            : "—"}
                        </TableCell>
                        <TableCell>
                          <span
                            className={`text-xs px-2 py-0.5 rounded-full font-medium ${
                              o.status === "Filled"
                                ? "bg-green-500/20 text-green-400"
                                : o.status === "Cancelled"
                                ? "bg-zinc-500/20 text-zinc-400"
                                : "bg-yellow-500/20 text-yellow-400"
                            }`}
                          >
                            {o.status}
                          </span>
                        </TableCell>
                      </TableRow>
                    ))
                  ) : (
                    <TableRow>
                      <TableCell colSpan={6} className="text-center text-muted-foreground py-6">
                        No order history yet.
                      </TableCell>
                    </TableRow>
                  )}
                </TableBody>
              </Table>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}