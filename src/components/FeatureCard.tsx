import { LucideIcon } from "lucide-react";

interface FeatureCardProps {
  title: string;
  description: string;
  icon: LucideIcon;
  href: string;
  onClick?: (href: string) => void;
}

export const FeatureCard = ({
  title,
  description,
  icon: Icon,
  href,
  onClick,
}: FeatureCardProps) => {
  return (
    <div
      className="group relative rounded-lg border p-6 hover:border-foreground/50 transition-colors"
      onClick={() => onClick?.(href)}
      role="button"
      tabIndex={0}
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
    </div>
  );
};
