export default function PortfolioPage() {
  return (
    <div className="flex-1 space-y-4 p-8 pt-6">
      <div className="flex items-center justify-between space-y-2">
        <h2 className="text-3xl font-bold tracking-tight">Portfolio Manager</h2>
      </div>
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <div className="rounded-xl border bg-card text-card-foreground shadow">
          <div className="p-6 flex flex-row items-center justify-between space-y-0 pb-2">
            <h3 className="tracking-tight text-sm font-medium">Total Balance</h3>
          </div>
          <div className="p-6 pt-0">
            <div className="text-2xl font-bold">$124,532.00</div>
            <p className="text-xs text-muted-foreground">+5.2% from last month</p>
          </div>
        </div>
      </div>
    </div>
  );
}