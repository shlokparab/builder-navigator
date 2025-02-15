
import { FeatureCard } from "@/components/FeatureCard";
import { Presentation, FileSpreadsheet, Handshake, TrendingUp } from "lucide-react";

const InvestorOutreach = () => {
  return (
    <div className="p-6 pl-72 pt-24">
      <div className="max-w-6xl mx-auto space-y-8">
        <div className="space-y-4">
          <h1 className="text-4xl font-bold bg-gradient-to-r from-cyan-400 to-cyan-200 bg-clip-text text-transparent">
            Investor Outreach
          </h1>
          <p className="text-gray-400">
            Connect with investors and secure funding for your startup
          </p>
        </div>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <FeatureCard
            title="Pitch Deck"
            description="Create compelling investor presentations"
            icon={Presentation}
            href="#pitch-deck"
          />
          <FeatureCard
            title="Financial Models"
            description="Develop comprehensive financial projections"
            icon={FileSpreadsheet}
            href="#financials"
          />
          <FeatureCard
            title="Investor Network"
            description="Connect with relevant investors"
            icon={Handshake}
            href="#network"
          />
          <FeatureCard
            title="Growth Metrics"
            description="Showcase your traction and growth"
            icon={TrendingUp}
            href="#metrics"
          />
        </div>
      </div>
    </div>
  );
};

export default InvestorOutreach;
