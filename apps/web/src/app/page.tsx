import { PortfolioOverview } from "@/components/dashboard/portfolio-overview";
import { LiveBtcChart } from "@/components/dashboard/live-btc-chart";
import { OrderBookTrades } from "@/components/dashboard/orderbook-trades";
import { SystemHealth } from "@/components/dashboard/system-health";

export default function Home() {
  return (
    <div className="space-y-6">
      <PortfolioOverview />

      <div className="grid grid-cols-1 xl:grid-cols-4 gap-6">
        <LiveBtcChart />
        <OrderBookTrades />
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <SystemHealth />
      </div>
    </div>
  );
}
