import { useState, useEffect } from "react";
import { supabase } from "@/integrations/supabase/client";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { SendHorizontal } from "lucide-react";
import { useToast } from "@/components/ui/use-toast";
import { Json } from "@/integrations/supabase/types";

interface ChatMessage {
  user_id: string;
  message: string;
  bot_response: string;
  created_at: string;
  contemplator?: string;
}

type DatabaseChat = ChatMessage[] | null;

interface ValidateIdeaResponse {
  status: string;
  contemplator: string;
  result: string;
}

export default function Chat() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [newMessage, setNewMessage] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [askingForAnalysis, setAskingForAnalysis] = useState(false);
  const { toast } = useToast();

  useEffect(() => {
    fetchChatHistory();
  }, []);

  const fetchChatHistory = async () => {
    try {
      const {
        data: { user },
      } = await supabase.auth.getUser();
      if (!user) return;

      const { data, error } = await supabase
        .from("profiles")
        .select("chat")
        .eq("id", user.id)
        .single();

      if (error) throw error;

      if (data?.chat) {
        const chatHistory = data.chat as unknown as ChatMessage[];
        setMessages(chatHistory);
      }
    } catch (error) {
      console.error("Error fetching chat history:", error);
      toast({
        title: "Error",
        description: "Failed to load chat history",
        variant: "destructive",
      });
    }
  };

  const validateIdea = async (prompt: string): Promise<ValidateIdeaResponse> => {
    try {
      const response = await fetch(`https://builder-navigator.onrender.com/validate_idea?idea=${encodeURIComponent(prompt)}`, {
        method: 'GET',
        mode: 'cors',
        headers: {
          'Accept': 'application/json'
        }
      });
      console.log("Response:", response);
      if (!response.ok) {
        throw new Error('Failed to validate idea');
      }

      return await response.json();
    } catch (error) {
      console.error("Error validating idea:", error);
      throw error;
    }
  };

  const analyzeMarket = async (prompt: string): Promise<ValidateIdeaResponse> => {
    try {
      const response = await fetch(`https://builder-navigator.onrender.com/analyze_market?idea=${encodeURIComponent(prompt)}`, {
        method: 'GET',
        mode: 'cors',
        headers: {
          'Accept': 'application/json'
        }
      });
      if (!response.ok) {
        throw new Error('Failed to analyze market');
      }
      return await response.json();
    } catch (error) {
      console.error("Error analyzing market:", error);
      throw error;
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newMessage.trim() || isLoading) return;

    setIsLoading(true);

    try {
      const {
        data: { user },
      } = await supabase.auth.getUser();
      if (!user) throw new Error("Not authenticated");

      // Create new message
      const newChatMessage: ChatMessage = {
        user_id: user.id,
        message: newMessage,
        bot_response: askingForAnalysis ? "Analyzing market..." : "Analyzing your idea...",
        created_at: new Date().toISOString(),
      };

      // Get existing chat history
      const { data: profileData, error: fetchError } = await supabase
        .from("profiles")
        .select("chat")
        .eq("id", user.id)
        .single();

      if (fetchError) throw fetchError;

      const existingChat =
        (profileData?.chat as unknown as ChatMessage[]) || [];
      const updatedChat = [...existingChat, newChatMessage];

      // Update profile with new chat history
      const { error: updateError } = await supabase
        .from("profiles")
        .update({ chat: updatedChat as unknown as Json })
        .eq("id", user.id);

      if (updateError) throw updateError;

      // Update local state
      setMessages(updatedChat);
      setNewMessage("");

      let validationResponse;
      if (askingForAnalysis) {
        if (newMessage.toLowerCase().includes('yes')) {
          validationResponse = await analyzeMarket(messages[messages.length - 2].message);
          setAskingForAnalysis(false);
        } else {
          validationResponse = {
            status: 'declined',
            contemplator: '',
            result: 'No problem! Let me know if you want to analyze another startup idea.'
          };
          setAskingForAnalysis(false);
        }
      } else {
        validationResponse = await validateIdea(newMessage);
      }

      const botResponse: ChatMessage = {
        ...newChatMessage,
        bot_response: validationResponse.result,
        contemplator: validationResponse.contemplator,
        created_at: new Date().toISOString(),
      };

      const finalChat = [...updatedChat.slice(0, -1), botResponse];

      if (validationResponse.status === 'sufficient_information' && !askingForAnalysis) {
        setAskingForAnalysis(true);
        const analysisQuestion: ChatMessage = {
          user_id: user.id,
          message: "",
          bot_response: "Would you like me to perform a deep market analysis for your idea? (Yes/No)",
          created_at: new Date().toISOString(),
        };
        finalChat.push(analysisQuestion);
      }

      await supabase
        .from("profiles")
        .update({ chat: finalChat as unknown as Json })
        .eq("id", user.id);

      setMessages(finalChat);
    } catch (error) {
      console.error("Error sending message:", error);
      toast({
        title: "Error",
        description: "Failed to send message",
        variant: "destructive",
      });
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex flex-col h-[calc(100vh-2rem)] pt-16">
      <div className="flex-1 overflow-hidden">
        <ScrollArea className="h-full px-4">
          <div className="max-w-4xl mx-auto space-y-4 py-1">
            {messages.map((msg, index) => (
              <div key={index} className="space-y-4">
                {msg.message && (
                  <div className="flex justify-end">
                    <div className="bg-primary text-primary-foreground px-4 py-2 rounded-lg max-w-[80%]">
                      {msg.message}
                    </div>
                  </div>
                )}
                <div className="flex justify-start">
                  <div className="bg-muted px-4 py-2 rounded-lg max-w-[80%] whitespace-pre-line">
                    {msg.bot_response}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </ScrollArea>
      </div>

      <div className="p-2 border-t mt-auto">
        <form onSubmit={handleSubmit} className="max-w-4xl mx-auto">
          <div className="flex gap-2">
            <Input
              value={newMessage}
              onChange={(e) => setNewMessage(e.target.value)}
              placeholder={askingForAnalysis ? "Type 'yes' for market analysis..." : "Describe your startup idea..."}
              disabled={isLoading}
              className="flex-1"
            />
            <Button type="submit" disabled={isLoading} size="icon">
              {isLoading ? (
                <div className="h-4 w-4 animate-spin rounded-full border-2 border-primary border-t-transparent" />
              ) : (
                <SendHorizontal className="h-4 w-4" />
              )}
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
}
