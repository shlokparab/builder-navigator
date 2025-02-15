import { FeatureCard } from "@/components/FeatureCard";
import { LightbulbIcon, Rocket, Users } from "lucide-react";

const features = [
  {
    title: "Idea Validation",
    description: "Validate your startup idea with proven frameworks and methodologies",
    icon: LightbulbIcon,
    href: "/chat",
  },
  {
    title: "MVP Generation",
    description: "Build and launch your minimum viable product efficiently",
    icon: Rocket,
    href: "/mvp",
  },
  {
    title: "Investor Outreach",
    description: "Connect with potential investors and prepare for fundraising",
    icon: Users,
    href: "/investors",
  },
];

const Dashboard = () => {
  return (
    <div className="min-h-screen bg-background pt-16">
      <main className="p-4 md:p-8 animate-fadeIn">
        <div className="max-w-7xl mx-auto">
          <header className="mb-8">
            <h1 className="text-3xl font-bold bg-gradient-to-r from-cyan-400 to-cyan-200 bg-clip-text text-transparent">
              Welcome back
            </h1>
            <p className="mt-2 text-gray-400">Track and accelerate your entrepreneurial journey</p>
          </header>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 md:gap-6">
            {features.map((feature) => (
              <FeatureCard key={feature.title} {...feature} />
            ))}
          </div>
        </div>
      </main>
    </div>
  );
};

export default Dashboard;
