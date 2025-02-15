
import { LucideIcon } from "lucide-react";

interface FeatureCardProps {
  title: string;
  description: string;
  icon: LucideIcon;
  href: string;
}

export const FeatureCard = ({ title, description, icon: Icon, href }: FeatureCardProps) => {
  return (
    <a
      href={href}
      className="group relative overflow-hidden rounded-xl bg-black/40 backdrop-blur-md border border-white/10 p-6 shadow-lg transition-all duration-300 hover:shadow-cyan-500/10 hover:-translate-y-1"
    >
      <div className="flex flex-col gap-4">
        <span className="inline-flex h-12 w-12 items-center justify-center rounded-lg bg-cyan-500/10 group-hover:bg-cyan-500/20 transition-colors">
          <Icon className="h-6 w-6 text-cyan-400" />
        </span>
        <div>
          <h3 className="text-lg font-semibold text-white">{title}</h3>
          <p className="mt-2 text-gray-400">{description}</p>
        </div>
      </div>
      <div className="absolute inset-x-0 bottom-0 h-1 bg-gradient-to-r from-cyan-500/50 to-cyan-300/50 transform scale-x-0 transition-transform group-hover:scale-x-100" />
    </a>
  );
};
