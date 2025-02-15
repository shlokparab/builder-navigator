import { Bell, Menu, User, Home, LightbulbIcon, Rocket, Users } from "lucide-react";
import { Link } from "react-router-dom";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";

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
          <DropdownMenu>
            <DropdownMenuTrigger className="p-2 hover:bg-white/5 rounded-full transition-colors">
              <Menu className="w-5 h-5 text-gray-300" />
            </DropdownMenuTrigger>
            <DropdownMenuContent className="glass-effect border-gray-800">
              {navigation.map((item) => (
                <DropdownMenuItem key={item.name} asChild>
                  <Link
                    to={item.href}
                    className="flex items-center gap-2 text-gray-300 hover:text-white"
                  >
                    <item.icon className="h-4 w-4" />
                    <span>{item.name}</span>
                  </Link>
                </DropdownMenuItem>
              ))}
            </DropdownMenuContent>
          </DropdownMenu>
          <h1 className="text-xl font-semibold text-white">BuilderNavigator</h1>
        </div>
        <div className="flex items-center gap-4">
          <button className="p-2 hover:bg-white/5 rounded-full transition-colors">
            <Bell className="w-5 h-5 text-gray-300" />
          </button>
          <Link to="/profile" className="p-2 hover:bg-white/5 rounded-full transition-colors">
            <User className="w-5 h-5 text-gray-300" />
          </Link>
        </div>
      </div>
    </nav>
  );
};
