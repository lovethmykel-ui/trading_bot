import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

export function SystemHealth() {
  return (
    <Card>
      <CardHeader>
        <CardTitle>System Health</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="flex items-center justify-between">
          <span className="text-sm font-medium">API Status</span>
          <span className="text-sm text-green-500 flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-green-500"></span> Online
          </span>
        </div>
        <div className="flex items-center justify-between">
          <span className="text-sm font-medium">WebSocket</span>
          <span className="text-sm text-green-500 flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-green-500"></span> Connected
          </span>
        </div>
        <div className="flex items-center justify-between">
          <span className="text-sm font-medium">Database</span>
          <span className="text-sm text-green-500 flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-green-500"></span> Synced
          </span>
        </div>
        <div className="flex items-center justify-between">
          <span className="text-sm font-medium">Latency</span>
          <span className="text-sm text-muted-foreground">42ms</span>
        </div>
      </CardContent>
    </Card>
  );
}
