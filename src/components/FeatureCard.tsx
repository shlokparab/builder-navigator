
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
      className="group relative overflow-hidden rounded-xl bg-white p-6 shadow-lg transition-all duration-300 hover:shadow-xl hover:-translate-y-1"
    >
      <div className="flex flex-col gap-4">
        <span className="inline-flex h-12 w-12 items-center justify-center rounded-lg bg-gray-50 group-hover:bg-gray-100 transition-colors">
          <Icon className="h-6 w-6 text-gray-600 group-hover:text-gray-900" />
        </span>
        <div>
          <h3 className="text-lg font-semibold text-gray-900">{title}</h3>
          <p className="mt-2 text-gray-600">{description}</p>
        </div>
      </div>
      <div className="absolute inset-x-0 bottom-0 h-1 bg-gradient-to-r from-gray-200 to-gray-300 transform scale-x-0 transition-transform group-hover:scale-x-100" />
    </a>
  );
};
