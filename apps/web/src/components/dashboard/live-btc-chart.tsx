"use client";

import { useEffect, useRef } from "react";
import { createChart, ColorType, LineSeries, Time } from "lightweight-charts";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

export function LiveBtcChart() {
  const chartContainerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!chartContainerRef.current) return;

    const chart = createChart(chartContainerRef.current, {
      layout: {
        background: { type: ColorType.Solid, color: "transparent" },
        textColor: "#a1a1aa",
      },
      grid: {
        vertLines: { color: "rgba(42, 46, 57, 0.5)" },
        horzLines: { color: "rgba(42, 46, 57, 0.5)" },
      },
      width: chartContainerRef.current.clientWidth,
      height: 400,
    });

    const lineSeries = chart.addSeries(LineSeries, {
      color: "#22c55e",
      lineWidth: 2,
    });

    // Mock initial data
    // Time in lightweight-charts must be formatted as UTCTimestamp (number of seconds since epoch)
    const initialData: { time: Time; value: number }[] = [];
    let currentTime = Math.floor(Date.now() / 1000) - 100 * 3600;
    let price = 65000;

    for (let i = 0; i < 100; i++) {
      initialData.push({ time: currentTime as Time, value: price });
      price += (Math.random() - 0.5) * 1000;
      currentTime += 3600; // hourly
    }

    lineSeries.setData(initialData);

    const handleResize = () => {
      if (chartContainerRef.current) {
        chart.applyOptions({ width: chartContainerRef.current.clientWidth });
      }
    };

    window.addEventListener("resize", handleResize);

    // Mock live updates
    let liveTime = currentTime;
    const interval = setInterval(() => {
      price += (Math.random() - 0.5) * 500;
      liveTime += 10; // strictly increasing timestamp
      lineSeries.update({ time: liveTime as Time, value: price });
    }, 2000);


    return () => {
      window.removeEventListener("resize", handleResize);
      clearInterval(interval);
      chart.remove();
    };
  }, []);

  return (
    <Card className="col-span-full xl:col-span-3">
      <CardHeader>
        <CardTitle>Live BTC Chart</CardTitle>
      </CardHeader>
      <CardContent>
        <div ref={chartContainerRef} className="w-full h-[400px]" />
      </CardContent>
    </Card>
  );
}
