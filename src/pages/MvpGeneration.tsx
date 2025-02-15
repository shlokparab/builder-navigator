
import { FeatureCard } from "@/components/FeatureCard";
import { Code, Puzzle, Zap, BarChart } from "lucide-react";

const MvpGeneration = () => {
  return (
    <div className="p-6 pl-72 pt-24">
      <div className="max-w-6xl mx-auto space-y-8">
        <div className="space-y-4">
          <h1 className="text-4xl font-bold bg-gradient-to-r from-cyan-400 to-cyan-200 bg-clip-text text-transparent">
            MVP Generation
          </h1>
          <p className="text-gray-400">
            Build and launch your Minimum Viable Product efficiently
          </p>
        </div>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <FeatureCard
            title="Feature Planning"
            description="Define core features for your MVP"
            icon={Puzzle}
            href="#feature-planning"
          />
          <FeatureCard
            title="Tech Stack"
            description="Choose the right technologies for your product"
            icon={Code}
            href="#tech-stack"
          />
          <FeatureCard
            title="Rapid Development"
            description="Implement fast development cycles"
            icon={Zap}
            href="#development"
          />
          <FeatureCard
            title="Analytics Setup"
            description="Track key metrics and user behavior"
            icon={BarChart}
            href="#analytics"
          />
        </div>
      </div>
    </div>
  );
};

export default MvpGeneration;
