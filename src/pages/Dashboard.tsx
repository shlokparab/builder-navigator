import { FeatureCard } from "@/components/FeatureCard";
import { LightbulbIcon, Rocket, Users, PlusCircle } from "lucide-react";
import { useState, useEffect } from "react";
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
import { useNavigate } from "react-router-dom";
import { supabase } from "@/integrations/supabase/client";
import { useToast } from "@/components/ui/use-toast";

const debug = (message: string, data?: any) => {
  console.log(`[Dashboard] ${message}`, data || '');
};

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
  const { toast } = useToast();
  const [projects, setProjects] = useState<string[]>([]);
  const [selectedProject, setSelectedProject] = useState<string>("");
  const [isNewProjectDialogOpen, setIsNewProjectDialogOpen] = useState(false);
  const [newProjectName, setNewProjectName] = useState("");
  const navigate = useNavigate();

  useEffect(() => {
    debug('Component mounted, fetching projects');
    fetchProjects();
  }, []);

  const fetchProjects = async () => {
    debug('Fetching projects');
    try {
      const { data: { user } } = await supabase.auth.getUser();
      if (!user) {
        debug('No user found');
        return;
      }

      const { data, error } = await supabase
        .from("projects")
        .select("name")
        .eq("user_id", user.id);

      if (error) throw error;

      const projectNames = data.map(project => project.name);
      debug('Projects fetched', projectNames);
      setProjects(projectNames);
      
      if (!selectedProject && projectNames.length > 0) {
        debug('Setting initial selected project', projectNames[0]);
        setSelectedProject(projectNames[0]);
      }
    } catch (error) {
      debug('Error fetching projects', error);
      toast({
        title: "Error",
        description: "Failed to load projects",
        variant: "destructive",
      });
    }
  };

  const handleCreateProject = async () => {
    debug('Creating new project', newProjectName);
    try {
      const { data: { user } } = await supabase.auth.getUser();
      if (!user) {
        debug('No user found during project creation');
        throw new Error("Not authenticated");
      }

      const { error } = await supabase
        .from("projects")
        .insert({
          name: newProjectName,
          user_id: user.id,
          chat_history: [],
        });

      if (error) throw error;

      debug('Project created successfully');
      setSelectedProject(newProjectName);
      setIsNewProjectDialogOpen(false);
      setNewProjectName("");
      
      await fetchProjects();

      toast({
        title: "Success",
        description: "Project created successfully",
      });
    } catch (error) {
      debug('Error creating project', error);
      toast({
        title: "Error",
        description: "Failed to create project",
        variant: "destructive",
      });
    }
  };

  const handleFeatureClick = (href: string) => {
    debug('Feature clicked', { href, selectedProject });
    navigate(href, { state: { projectId: selectedProject } });
  };

  const handleProjectSelect = (project: string) => {
    debug('Project selected', project);
    setSelectedProject(project);
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
                    <Button variant="outline" disabled={projects.length === 0}>
                      {selectedProject || "No projects"}
                    </Button>
                  </DropdownMenuTrigger>
                  <DropdownMenuContent>
                    {projects.map((project) => (
                      <DropdownMenuItem
                        key={project}
                        onClick={() => handleProjectSelect(project)}
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
              <FeatureCard 
                key={feature.title} 
                {...feature} 
                onClick={() => handleFeatureClick(feature.href)}
              />
            ))}
          </div>
        </div>
      </main>
    </div>
  );
};

export default Dashboard;
