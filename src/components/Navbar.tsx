import { User, Home, LightbulbIcon, Rocket, Users } from "lucide-react";
import { Link } from "react-router-dom";

const navigation = [
  { name: "Dashboard", href: "/dashboard", icon: Home },
  { name: "Idea Validation", href: "/ideas", icon: LightbulbIcon },
  { name: "MVP Generation", href: "/mvp", icon: Rocket },
  { name: "Investor Outreach", href: "/investors", icon: Users },
];

export const Navbar = () => {
  return (
    <nav className="fixed top-0 right-0 left-0 z-50 h-16 glass-effect px-4">
      <div className="h-full flex items-center justify-between max-w-7xl mx-auto">
        <div className="flex items-center gap-4">
          <Link 
            to="/dashboard" 
            className="p-2 hover:bg-white/5 rounded-full transition-colors"
          >
            <Home className="w-5 h-5 text-gray-300" />
          </Link>
          <h1 className="text-xl font-semibold text-white">PathFinder</h1>
        </div>
        <div className="flex items-center gap-4">
          <Link to="/profile" className="p-2 hover:bg-white/5 rounded-full transition-colors">
            <User className="w-5 h-5 text-gray-300" />
          </Link>
        </div>
      </div>
    </nav>
  );
};
