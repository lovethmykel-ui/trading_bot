"use client";

import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";

export default function OrdersPage() {
  const [symbol, setSymbol] = useState("BTCUSDT");
  const [size, setSize] = useState("");

  return (
    <div className="flex-1 space-y-4 p-8 pt-6">
      <div className="flex items-center justify-between space-y-2">
        <h2 className="text-3xl font-bold tracking-tight">Trade Terminal</h2>
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-7">
        <Card className="col-span-2">
          <CardHeader>
            <CardTitle>Manual Execution</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label>Symbol</Label>
              <Input value={symbol} onChange={(e) => setSymbol(e.target.value)} />
            </div>
            <div className="space-y-2">
              <Label>Order Size</Label>
              <Input type="number" placeholder="0.00" value={size} onChange={(e) => setSize(e.target.value)} />
            </div>
            <div className="grid grid-cols-2 gap-4 pt-4">
              <Button className="bg-green-600 hover:bg-green-700">Buy / Long</Button>
              <Button className="bg-red-600 hover:bg-red-700">Sell / Short</Button>
            </div>
          </CardContent>
        </Card>

        <Card className="col-span-5">
          <CardHeader>
            <CardTitle>Trade Journal</CardTitle>
          </CardHeader>
          <CardContent>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Time</TableHead>
                  <TableHead>Symbol</TableHead>
                  <TableHead>Side</TableHead>
                  <TableHead>Price</TableHead>
                  <TableHead>Size</TableHead>
                  <TableHead>Status</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                <TableRow>
                  <TableCell>12:45:33</TableCell>
                  <TableCell>BTCUSDT</TableCell>
                  <TableCell className="text-green-500">LONG</TableCell>
                  <TableCell>64,250.00</TableCell>
                  <TableCell>0.5</TableCell>
                  <TableCell>Filled</TableCell>
                </TableRow>
              </TableBody>
            </Table>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}