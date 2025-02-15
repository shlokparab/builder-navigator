
import { Home, LightbulbIcon, Rocket, Users } from "lucide-react";
import { NavLink } from "react-router-dom";

const navigation = [
  { name: "Dashboard", href: "/dashboard", icon: Home },
  { name: "Idea Validation", href: "/ideas", icon: LightbulbIcon },
  { name: "MVP Generation", href: "/mvp", icon: Rocket },
  { name: "Investor Outreach", href: "/investors", icon: Users },
];

export const Sidebar = () => {
  return (
    <aside className="fixed left-0 top-0 z-40 h-screen w-64 border-r bg-white/80 backdrop-blur-md pt-16">
      <div className="flex h-full flex-col px-3 py-4">
        <nav className="space-y-1">
          {navigation.map((item) => (
            <NavLink
              key={item.name}
              to={item.href}
              className={({ isActive }) =>
                `flex items-center px-2 py-2 text-sm font-medium rounded-lg transition-colors ${
                  isActive
                    ? "bg-gray-100 text-gray-900"
                    : "text-gray-600 hover:bg-gray-50 hover:text-gray-900"
                }`
              }
            >
              <item.icon className="mr-3 h-5 w-5" />
              {item.name}
            </NavLink>
          ))}
        </nav>
      </div>
    </aside>
  );
};
