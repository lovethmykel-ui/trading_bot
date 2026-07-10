"use client";

import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";

export default function RiskPage() {
  const [balance, setBalance] = useState("100000");
  const [riskPct, setRiskPct] = useState("1.0");
  const [entry, setEntry] = useState("64000");
  const [stop, setStop] = useState("63000");
  const [result, setResult] = useState<{size: number, risk_amount: number, total_exposure: number} | null>(null);

  const calculateSize = () => {
    const riskAmt = Number(balance) * (Number(riskPct) / 100);
    const riskPerUnit = Math.abs(Number(entry) - Number(stop));
    const size = riskAmt / riskPerUnit;

    setResult({
      size: Number(size.toFixed(4)),
      risk_amount: riskAmt,
      total_exposure: size * Number(entry)
    });
  };

  return (
    <div className="flex-1 space-y-4 p-8 pt-6">
      <div className="flex items-center justify-between space-y-2">
        <h2 className="text-3xl font-bold tracking-tight">Risk Analytics</h2>
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        <Card className="col-span-1">
          <CardHeader>
            <CardTitle>Position Sizer</CardTitle>
            <CardDescription>Calculate optimal size based on risk parameters</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label>Account Balance</Label>
              <Input type="number" value={balance} onChange={(e) => setBalance(e.target.value)} />
            </div>
            <div className="space-y-2">
              <Label>Risk Percentage (%)</Label>
              <Input type="number" step="0.1" value={riskPct} onChange={(e) => setRiskPct(e.target.value)} />
            </div>
            <div className="space-y-2">
              <Label>Entry Price</Label>
              <Input type="number" value={entry} onChange={(e) => setEntry(e.target.value)} />
            </div>
            <div className="space-y-2">
              <Label>Stop Loss</Label>
              <Input type="number" value={stop} onChange={(e) => setStop(e.target.value)} />
            </div>
            <Button onClick={calculateSize} className="w-full">Calculate Size</Button>

            {result && (
              <div className="mt-6 p-4 bg-muted rounded-lg space-y-2">
                <div className="flex justify-between">
                  <span className="text-sm font-medium">Position Size:</span>
                  <span className="font-bold">{result.size}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm font-medium">Risk Amount:</span>
                  <span className="font-bold">${result.risk_amount}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm font-medium">Total Exposure:</span>
                  <span className="font-bold">${result.total_exposure.toFixed(2)}</span>
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}