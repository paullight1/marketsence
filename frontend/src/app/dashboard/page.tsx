import { Sidebar } from "@/components/layout/sidebar";
import { StatsCards } from "@/components/layout/stats-cards";
import { PriceTrendChart } from "@/components/layout/price-trend-chart";
import { RecentListings } from "@/components/layout/recent-listings";
import { CategoryChart } from "@/components/layout/category-chart";
import { TopProducts } from "@/components/layout/top-products";

export default function DashboardPage() {
  return (
    <div className="flex h-screen">
      <Sidebar />
      <main className="flex-1 overflow-y-auto bg-muted/30">
        <div className="p-6 space-y-6">
          <div>
            <h1 className="text-3xl font-bold">Dashboard</h1>
            <p className="text-muted-foreground mt-1">
              Nigerian Market Price Intelligence
            </p>
          </div>

          <StatsCards />

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <PriceTrendChart />
            <CategoryChart />
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <RecentListings />
            <TopProducts />
          </div>
        </div>
      </main>
    </div>
  );
}