
import { Bell, User } from "lucide-react";

export const Navbar = () => {
  return (
    <nav className="fixed top-0 right-0 left-0 z-50 h-16 bg-white/80 backdrop-blur-md border-b px-4">
      <div className="h-full flex items-center justify-between max-w-7xl mx-auto">
        <h1 className="text-xl font-semibold">Builder Navigator</h1>
        <div className="flex items-center gap-4">
          <button className="p-2 hover:bg-gray-100 rounded-full transition-colors">
            <Bell className="w-5 h-5 text-gray-600" />
          </button>
          <button className="p-2 hover:bg-gray-100 rounded-full transition-colors">
            <User className="w-5 h-5 text-gray-600" />
          </button>
        </div>
      </div>
    </nav>
  );
};
