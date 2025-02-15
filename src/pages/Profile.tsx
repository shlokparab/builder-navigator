
import { useEffect, useState } from "react";
import { Camera, LogOut, Mail, Moon, Bell } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Switch } from "@/components/ui/switch";
import { useToast } from "@/components/ui/use-toast";
import { supabase } from "@/integrations/supabase/client";
import { useNavigate } from "react-router-dom";

interface Profile {
  id: string;
  full_name: string | null;
  avatar_url: string | null;
  bio: string | null;
  email_notifications: boolean;
  preferred_theme: string;
}

const Profile = () => {
  const [profile, setProfile] = useState<Profile | null>(null);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const { toast } = useToast();
  const navigate = useNavigate();

  useEffect(() => {
    fetchProfile();
  }, []);

  const fetchProfile = async () => {
    try {
      const { data: { user } } = await supabase.auth.getUser();
      
      if (!user) {
        navigate('/login');
        return;
      }

      const { data, error } = await supabase
        .from('profiles')
        .select('*')
        .eq('id', user.id)
        .single();

      if (error) throw error;
      setProfile(data);
    } catch (error) {
      console.error('Error fetching profile:', error);
      toast({
        variant: "destructive",
        title: "Error",
        description: "Failed to load profile data.",
      });
    } finally {
      setLoading(false);
    }
  };

  const uploadAvatar = async (event: React.ChangeEvent<HTMLInputElement>) => {
    try {
      setUploading(true);
      
      if (!event.target.files || !event.target.files[0]) return;
      
      const file = event.target.files[0];
      const fileExt = file.name.split('.').pop();
      const filePath = `${profile?.id}/${Math.random()}.${fileExt}`;

      const { error: uploadError } = await supabase.storage
        .from('avatars')
        .upload(filePath, file);

      if (uploadError) throw uploadError;

      const { data: { publicUrl } } = supabase.storage
        .from('avatars')
        .getPublicUrl(filePath);

      const { error: updateError } = await supabase
        .from('profiles')
        .update({ avatar_url: publicUrl })
        .eq('id', profile?.id);

      if (updateError) throw updateError;

      setProfile(prev => prev ? { ...prev, avatar_url: publicUrl } : null);
      
      toast({
        title: "Success",
        description: "Profile picture updated successfully.",
      });
    } catch (error) {
      console.error('Error uploading avatar:', error);
      toast({
        variant: "destructive",
        title: "Error",
        description: "Failed to update profile picture.",
      });
    } finally {
      setUploading(false);
    }
  };

  const handleLogout = async () => {
    try {
      const { error } = await supabase.auth.signOut();
      if (error) throw error;
      navigate('/login');
    } catch (error) {
      console.error('Error logging out:', error);
      toast({
        variant: "destructive",
        title: "Error",
        description: "Failed to log out. Please try again.",
      });
    }
  };

  const updateProfile = async (updates: Partial<Profile>) => {
    try {
      const { error } = await supabase
        .from('profiles')
        .update(updates)
        .eq('id', profile?.id);

      if (error) throw error;

      setProfile(prev => prev ? { ...prev, ...updates } : null);
      
      toast({
        title: "Success",
        description: "Profile settings updated successfully.",
      });
    } catch (error) {
      console.error('Error updating profile:', error);
      toast({
        variant: "destructive",
        title: "Error",
        description: "Failed to update profile settings.",
      });
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-background pt-16">
        <div className="p-8 animate-fadeIn">
          <div className="max-w-3xl mx-auto">
            Loading...
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background pt-16">
      <div className="p-4 sm:p-8 animate-fadeIn">
        <div className="max-w-3xl mx-auto space-y-6 sm:space-y-8">
          <header>
            <h1 className="text-2xl sm:text-3xl font-bold bg-gradient-to-r from-cyan-400 to-cyan-200 bg-clip-text text-transparent">
              Profile Settings
            </h1>
            <p className="mt-2 text-gray-400">Manage your account preferences and settings</p>
          </header>

          <div className="glass-effect p-4 sm:p-6 rounded-xl space-y-6 sm:space-y-8">
            {/* Profile Picture Section */}
            <div className="flex flex-col sm:flex-row items-center gap-4 sm:gap-6">
              <div className="relative">
                <Avatar className="w-20 h-20 sm:w-24 sm:h-24">
                  <AvatarImage src={profile?.avatar_url || undefined} />
                  <AvatarFallback>{profile?.full_name?.charAt(0) || 'U'}</AvatarFallback>
                </Avatar>
                <label 
                  className="absolute bottom-0 right-0 p-2 bg-cyan-500 rounded-full cursor-pointer hover:bg-cyan-600 transition-colors"
                  htmlFor="avatar-upload"
                >
                  <Camera className="w-4 h-4 text-white" />
                  <input
                    id="avatar-upload"
                    type="file"
                    accept="image/*"
                    className="hidden"
                    onChange={uploadAvatar}
                    disabled={uploading}
                  />
                </label>
              </div>
              <div className="text-center sm:text-left">
                <h2 className="text-xl font-semibold text-white">{profile?.full_name}</h2>
                <p className="text-gray-400">{profile?.bio || 'No bio yet'}</p>
              </div>
            </div>

            {/* Settings Section */}
            <div className="space-y-4">
              <div className="flex items-center justify-between py-3 border-b border-white/10">
                <div className="flex items-center gap-3">
                  <Moon className="w-5 h-5 text-gray-400" />
                  <div>
                    <h3 className="text-sm font-medium text-white">Dark Mode</h3>
                    <p className="text-sm text-gray-400">Enable dark mode theme</p>
                  </div>
                </div>
                <Switch
                  checked={profile?.preferred_theme === 'dark'}
                  onCheckedChange={(checked) => 
                    updateProfile({ preferred_theme: checked ? 'dark' : 'light' })
                  }
                />
              </div>

              <div className="flex items-center justify-between py-3 border-b border-white/10">
                <div className="flex items-center gap-3">
                  <Bell className="w-5 h-5 text-gray-400" />
                  <div>
                    <h3 className="text-sm font-medium text-white">Email Notifications</h3>
                    <p className="text-sm text-gray-400">Receive email updates</p>
                  </div>
                </div>
                <Switch
                  checked={profile?.email_notifications}
                  onCheckedChange={(checked) => 
                    updateProfile({ email_notifications: checked })
                  }
                />
              </div>
            </div>

            {/* Logout Button */}
            <Button
              variant="outline"
              className="w-full glass-effect hover:bg-white/5 text-white border-white/10"
              onClick={handleLogout}
            >
              <LogOut className="w-4 h-4 mr-2" />
              Sign Out
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Profile;
