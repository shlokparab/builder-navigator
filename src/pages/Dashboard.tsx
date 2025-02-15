import { FeatureCard } from "@/components/FeatureCard";
import { LightbulbIcon, Rocket, Users, PlusCircle } from "lucide-react";
import { useState } from "react";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
  DropdownMenuSeparator,
} from "@/components/ui/dropdown-menu";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

const features = [
  {
    title: "Step 1 - Idea Validation",
    description: "Validate your startup idea with proven frameworks and methodologies",
    icon: LightbulbIcon,
    href: "/chat",
  },
  {
    title: "Step 2 - MVP Generation",
    description: "Build and launch your minimum viable product efficiently",
    icon: Rocket,
    href: "/mvp",
  },
  {
    title: "Step 3 - Investor Outreach",
    description: "Connect with potential investors and prepare for fundraising",
    icon: Users,
    href: "/investors",
  },
];

const Dashboard = () => {
  const [selectedProject, setSelectedProject] = useState("My First Project");
  const [isNewProjectDialogOpen, setIsNewProjectDialogOpen] = useState(false);
  const [newProjectName, setNewProjectName] = useState("");

  const projects = ["My First Project", "Second Project", "Another Project"]; // This would come from your backend

  const handleCreateProject = () => {
    // Handle project creation logic here
    console.log("Creating project:", newProjectName);
    setIsNewProjectDialogOpen(false);
    setNewProjectName("");
  };

  return (
    <div className="min-h-screen bg-background pt-16">
      <main className="p-4 md:p-8 animate-fadeIn">
        <div className="max-w-7xl mx-auto">
          <header className="mb-8">
            <div className="flex items-center justify-between">
              <h1 className="text-3xl font-bold bg-gradient-to-r from-cyan-400 to-cyan-200 bg-clip-text text-transparent">
                Welcome back
              </h1>
              <div className="flex items-center gap-2">
                <DropdownMenu>
                  <DropdownMenuTrigger asChild>
                    <Button variant="outline">{selectedProject}</Button>
                  </DropdownMenuTrigger>
                  <DropdownMenuContent>
                    {projects.map((project) => (
                      <DropdownMenuItem
                        key={project}
                        onClick={() => setSelectedProject(project)}
                      >
                        {project}
                      </DropdownMenuItem>
                    ))}
                    <DropdownMenuSeparator />
                    <DropdownMenuItem
                      onClick={() => setIsNewProjectDialogOpen(true)}
                    >
                      <PlusCircle className="mr-2 h-4 w-4" />
                      New Project
                    </DropdownMenuItem>
                  </DropdownMenuContent>
                </DropdownMenu>
              </div>
            </div>
            <p className="mt-2 text-gray-400">
              Track and accelerate your entrepreneurial journey
            </p>
          </header>

          <Dialog open={isNewProjectDialogOpen} onOpenChange={setIsNewProjectDialogOpen}>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>Create New Project</DialogTitle>
                <DialogDescription>
                  Enter a name for your new project. You can always change this later.
                </DialogDescription>
              </DialogHeader>
              <div className="py-4">
                <Input
                  placeholder="Project name"
                  value={newProjectName}
                  onChange={(e) => setNewProjectName(e.target.value)}
                />
              </div>
              <DialogFooter>
                <Button
                  variant="outline"
                  onClick={() => setIsNewProjectDialogOpen(false)}
                >
                  Cancel
                </Button>
                <Button onClick={handleCreateProject}>Create Project</Button>
              </DialogFooter>
            </DialogContent>
          </Dialog>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 md:gap-6">
            {features.map((feature) => (
              <FeatureCard key={feature.title} {...feature} />
            ))}
          </div>
        </div>
      </main>
    </div>
  );
};

export default Dashboard;
