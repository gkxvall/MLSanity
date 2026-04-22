import { useState } from "react";
import { OverviewPage } from "@/components/dashboard/OverviewPage";
import { DistributionPage } from "@/components/dashboard/DistributionPage";
import { ChecksPage } from "@/components/dashboard/ChecksPage";
import { Activity, BarChart3, Shield, Zap } from "lucide-react";

const tabs = [
  { id: "overview", label: "Overview", icon: Activity },
  { id: "distribution", label: "Distribution", icon: BarChart3 },
  { id: "checks", label: "Checks", icon: Shield },
] as const;

type Tab = typeof tabs[number]["id"];

const Index = () => {
  const [activeTab, setActiveTab] = useState<Tab>("overview");

  return (
    <div className="min-h-screen bg-background">
      {/* Sticky header */}
      <header className="sticky top-0 z-50 border-b border-border bg-surface-1/80 backdrop-blur-lg">
        <div className="max-w-7xl mx-auto px-4 sm:px-6">
          <div className="flex items-center justify-between h-14">
            <div className="flex items-center gap-2.5">
              <div className="w-7 h-7 rounded-md bg-primary flex items-center justify-center">
                <Zap className="w-4 h-4 text-primary-foreground" />
              </div>
              <span className="text-sm font-bold tracking-tight">MLSanity</span>
            </div>
            <nav className="flex items-center gap-1">
              {tabs.map(tab => (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md text-sm font-medium transition-colors ${
                    activeTab === tab.id
                      ? "bg-primary/10 text-primary"
                      : "text-muted-foreground hover:text-foreground hover:bg-surface-2"
                  }`}
                >
                  <tab.icon className="w-3.5 h-3.5" />
                  {tab.label}
                </button>
              ))}
            </nav>
          </div>
        </div>
      </header>

      {/* Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 py-6">
        {activeTab === "overview" && <OverviewPage />}
        {activeTab === "distribution" && <DistributionPage />}
        {activeTab === "checks" && <ChecksPage />}
      </main>
    </div>
  );
};

export default Index;
