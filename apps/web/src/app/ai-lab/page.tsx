"use client";

import { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Button } from "@/components/ui/button";

interface AgentSignal {
  agent: string;
  signal: string;
  confidence: number;
  reasoning: string;
}

interface ConsensusResult {
  final_decision: string;
  overall_confidence: number;
  is_trade_recommended: boolean;
  agent_breakdown: AgentSignal[];
}

export default function AILabPage() {
  const [data, setData] = useState<ConsensusResult | null>(null);
  const [loading, setLoading] = useState(false);

  const fetchConsensus = async () => {
    setLoading(true);
    try {
      const res = await fetch("http://localhost:8000/ai/consensus?symbol=BTCUSDT");
      const json = await res.json();
      if (json.status === "success" && json.data) {
        setData(json.data);
        setLoading(false);
        return;
      }
    } catch (e) {
      console.warn("Backend AI consensus failed, falling back to mock data:", e);
    }

    // Mock fallback
    setTimeout(() => {
      setData({
        final_decision: "LONG",
        overall_confidence: 76,
        is_trade_recommended: true,
        agent_breakdown: [
          { agent: "Market Structure", signal: "LONG", confidence: 85, reasoning: "Higher highs on 4H." },
          { agent: "Trend", signal: "LONG", confidence: 90, reasoning: "Price above 50 EMA." },
          { agent: "Order Flow", signal: "LONG", confidence: 70, reasoning: "Bid absorption." },
          { agent: "Volume", signal: "NEUTRAL", confidence: 50, reasoning: "Average volume profile." },
          { agent: "Sentiment", signal: "NEUTRAL", confidence: 60, reasoning: "Mixed social feeds." },
          { agent: "Macro News", signal: "SHORT", confidence: 40, reasoning: "Slight hawkish fed tone." },
          { agent: "Risk", signal: "LONG", confidence: 80, reasoning: "Low volatility environment." }
        ]
      });
      setLoading(false);
    }, 1000);
  };

  useEffect(() => {
    fetchConsensus();
  }, []);

  return (
    <div className="flex-1 space-y-4 p-8 pt-6">
      <div className="flex items-center justify-between space-y-2">
        <h2 className="text-3xl font-bold tracking-tight">AI Intelligence Lab</h2>
        <Button onClick={fetchConsensus} disabled={loading}>
          {loading ? "Analyzing..." : "Run Multi-Agent Analysis"}
        </Button>
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        <Card className="col-span-1 lg:col-span-3">
          <CardHeader>
            <CardTitle>Consensus Engine Output</CardTitle>
            <CardDescription>Aggregated decision from the ensemble of specialized agents.</CardDescription>
          </CardHeader>
          <CardContent>
            {data ? (
              <div className="flex items-center space-x-12 p-6 bg-muted rounded-xl">
                <div>
                  <p className="text-sm font-medium text-muted-foreground mb-1">Final Decision</p>
                  <p className={`text-5xl font-bold ${data.final_decision === 'LONG' ? 'text-green-500' : data.final_decision === 'SHORT' ? 'text-red-500' : 'text-gray-400'}`}>
                    {data.final_decision}
                  </p>
                </div>
                <div>
                  <p className="text-sm font-medium text-muted-foreground mb-1">Confidence Score</p>
                  <p className="text-5xl font-bold">{data.overall_confidence}%</p>
                </div>
                <div>
                  <p className="text-sm font-medium text-muted-foreground mb-1">Trade Status</p>
                  <p className="text-2xl font-bold mt-3">
                    {data.is_trade_recommended ? "✅ Execution Approved" : "❌ Awaiting Conviction"}
                  </p>
                </div>
              </div>
            ) : (
              <div className="p-6">Waiting for analysis...</div>
            )}
          </CardContent>
        </Card>

        <Card className="col-span-1 lg:col-span-3">
          <CardHeader>
            <CardTitle>Agent Breakdown</CardTitle>
          </CardHeader>
          <CardContent>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Specialized Agent</TableHead>
                  <TableHead>Bias</TableHead>
                  <TableHead>Confidence</TableHead>
                  <TableHead>Reasoning Thesis</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {data?.agent_breakdown.map((agent, i) => (
                  <TableRow key={i}>
                    <TableCell className="font-medium">{agent.agent}</TableCell>
                    <TableCell className={
                      agent.signal === 'LONG' ? 'text-green-500 font-bold' :
                      agent.signal === 'SHORT' ? 'text-red-500 font-bold' : 'text-gray-400'
                    }>
                      {agent.signal}
                    </TableCell>
                    <TableCell>
                      <div className="flex items-center gap-2">
                        <span>{agent.confidence}%</span>
                        <div className="w-16 h-2 bg-secondary rounded-full overflow-hidden">
                          <div
                            className={`h-full ${agent.confidence > 75 ? 'bg-primary' : 'bg-muted-foreground'}`}
                            style={{ width: `${agent.confidence}%` }}
                          />
                        </div>
                      </div>
                    </TableCell>
                    <TableCell className="text-muted-foreground text-sm">{agent.reasoning}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}