
import { FeatureCard } from "@/components/FeatureCard";
import { BookOpen, Target, Users, MessageCircle } from "lucide-react";

const IdeaValidation = () => {
  return (
    <div className="p-6 pl-72 pt-24">
      <div className="max-w-6xl mx-auto space-y-8">
        <div className="space-y-4">
          <h1 className="text-4xl font-bold bg-gradient-to-r from-cyan-400 to-cyan-200 bg-clip-text text-transparent">
            Idea Validation
          </h1>
          <p className="text-gray-400">
            Validate your startup idea through market research and customer feedback
          </p>
        </div>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <FeatureCard
            title="Market Research"
            description="Analyze market size, trends, and competitive landscape"
            icon={BookOpen}
            href="#market-research"
          />
          <FeatureCard
            title="Target Audience"
            description="Define and understand your ideal customer profile"
            icon={Target}
            href="#target-audience"
          />
          <FeatureCard
            title="Customer Interviews"
            description="Gather insights through customer interviews"
            icon={Users}
            href="#customer-interviews"
          />
          <FeatureCard
            title="Feedback Analysis"
            description="Analyze and iterate based on customer feedback"
            icon={MessageCircle}
            href="#feedback"
          />
        </div>
      </div>
    </div>
  );
};

export default IdeaValidation;
