import { FeatureCard } from "@/components/FeatureCard";
import { LightbulbIcon, Rocket, Users } from "lucide-react";
import { useState } from "react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { useNavigate } from "react-router-dom";

const features = [
  {
    title: "Step 1 - Idea Validation",
    description: "Validate your startup idea with proven frameworks and methodologies",
    icon: LightbulbIcon,
    longDescription: "In this step, we'll help you validate your startup idea using proven frameworks and methodologies. We'll analyze market potential, identify target customers, and assess competitive landscape to ensure your idea has the best chance of success.",
  },
  {
    title: "Step 2 - MVP Generation",
    description: "Build and launch your minimum viable product efficiently",
    icon: Rocket,
    longDescription: "Learn how to build a Minimum Viable Product (MVP) that effectively tests your core value proposition. We'll guide you through prioritizing features, planning development, and gathering early user feedback.",
  },
  {
    title: "Step 3 - Investor Outreach",
    description: "Connect with potential investors and prepare for fundraising",
    icon: Users,
    longDescription: "Prepare for successful fundraising by learning how to craft compelling pitch decks, understand investor expectations, and develop effective networking strategies to connect with the right investors.",
  },
];

const Dashboard = () => {
  const navigate = useNavigate();
  const [selectedFeature, setSelectedFeature] = useState<(typeof features)[0] | null>(null);

  return (
    <div className="min-h-screen bg-background pt-16">
      <main className="p-4 md:p-8 animate-fadeIn">
        <div className="max-w-7xl mx-auto">
          <header className="mb-8">
            <div className="flex items-center justify-between">
              <h1 className="text-3xl font-bold bg-gradient-to-r from-cyan-400 to-cyan-200 bg-clip-text text-transparent">
                Welcome back
              </h1>
            </div>
            <p className="mt-2 text-gray-400">
              Track and accelerate your entrepreneurial journey
            </p>
          </header>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 md:gap-6">
            {features.map((feature) => (
              <FeatureCard 
                key={feature.title} 
                {...feature}
                href="#"
                onClick={() => setSelectedFeature(feature)}
              />
            ))}
          </div>

          <div className="mt-8 text-center">
            <Button 
              size="lg"
              onClick={() => navigate('/chat')}
              className="bg-gradient-to-r from-cyan-500 to-cyan-400 hover:from-cyan-400 hover:to-cyan-300"
            >
              Let's Start
            </Button>
          </div>

          <Dialog open={!!selectedFeature} onOpenChange={() => setSelectedFeature(null)}>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>{selectedFeature?.title}</DialogTitle>
                <DialogDescription className="pt-4">
                  {selectedFeature?.longDescription}
                </DialogDescription>
              </DialogHeader>
            </DialogContent>
          </Dialog>

        </div>
      </main>
    </div>
  );
};

export default Dashboard;
