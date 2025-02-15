import { Toaster } from "@/components/ui/toaster";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import { Navbar } from "./components/Navbar";
import Login from "./pages/Login";
import Dashboard from "./pages/Dashboard";
import IdeaValidation from "./pages/IdeaValidation";
import MvpGeneration from "./pages/MvpGeneration";
import InvestorOutreach from "./pages/InvestorOutreach";
import NotFound from "./pages/NotFound";
import Profile from "./pages/Profile";
import Chat from "./components/Chat";

const queryClient = new QueryClient();

const App = () => (
  <QueryClientProvider client={queryClient}>
    <TooltipProvider>
      <Toaster />
      <Sonner />
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<Login />} />
          <Route
            path="/dashboard"
            element={
              <>
                <Navbar />
                <Dashboard />
              </>
            }
          />
          <Route
            path="/ideas"
            element={
              <>
                <Navbar />
                <IdeaValidation />
              </>
            }
          />
          <Route
            path="/mvp"
            element={
              <>
                <Navbar />
                <MvpGeneration />
              </>
            }
          />
          <Route
            path="/investors"
            element={
              <>
                <Navbar />
                <InvestorOutreach />
              </>
            }
          />
          <Route
            path="/profile"
            element={
              <>
                <Navbar />
                <Profile />
              </>
            }
          />
          <Route
            path="/chat"
            element={
              <>
                <Navbar />
                <div className="p-8">
                  <Chat />
                </div>
              </>
            }
          />
          <Route path="*" element={<NotFound />} />
        </Routes>
      </BrowserRouter>
    </TooltipProvider>
  </QueryClientProvider>
);

export default App;
