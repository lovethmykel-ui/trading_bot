"use client";

import { useEffect, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";

interface Trade {
  price: string;
  size: string;
  time: string;
  isUp: boolean;
}

export function OrderBookTrades() {
  const [trades, setTrades] = useState<Trade[]>([]);

  useEffect(() => {
    // Generate initial trades only on client side to avoid hydration mismatch
    // Using setTimeout to avoid synchronous setState inside useEffect warning
    const timer = setTimeout(() => {
      const initialTrades: Trade[] = [...Array(10)].map((_, i) => ({
        price: `65,${(Math.random() * 999).toFixed(2)}`,
        size: (Math.random() * 2).toFixed(4),
        time: new Date(Date.now() - i * 5000).toLocaleTimeString([], { hour12: false }),
        isUp: Math.random() > 0.5
      }));
      setTrades(initialTrades);
    }, 0);
    return () => clearTimeout(timer);
  }, []);

  return (
    <Card className="col-span-1 xl:col-span-1 h-[400px] overflow-hidden flex flex-col">
      <CardHeader>
        <CardTitle>Recent Trades</CardTitle>
      </CardHeader>
      <CardContent className="flex-1 overflow-auto p-0">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Price</TableHead>
              <TableHead>Size</TableHead>
              <TableHead className="text-right">Time</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {trades.map((trade, i) => (
              <TableRow key={i}>
                <TableCell className={trade.isUp ? "text-green-500" : "text-red-500"}>
                  {trade.price}
                </TableCell>
                <TableCell>{trade.size}</TableCell>
                <TableCell className="text-right text-muted-foreground">
                  {trade.time}
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </CardContent>
    </Card>
  );
}
