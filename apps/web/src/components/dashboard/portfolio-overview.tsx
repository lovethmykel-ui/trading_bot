import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

export function PortfolioOverview() {
  const stats = [
    { label: "Portfolio Value", value: "$124,532.00", change: "+5.2%", trend: "up" },
    { label: "Today's PnL", value: "+$1,240.50", change: "+1.0%", trend: "up" },
    { label: "Win Rate", value: "68.5%", change: "+2.1%", trend: "up" },
    { label: "Open Positions", value: "4", change: "0", trend: "neutral" },
  ];

  return (
    <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4 w-full">
      {stats.map((stat, i) => (
        <Card key={i}>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              {stat.label}
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stat.value}</div>
            <p className={`text-xs mt-1 ${stat.trend === "up" ? "text-green-500" : "text-muted-foreground"}`}>
              {stat.change} from last period
            </p>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}
