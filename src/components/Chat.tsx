import { useState, useEffect } from "react";
import { supabase } from "@/integrations/supabase/client";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { SendHorizontal } from "lucide-react";
import { useToast } from "@/components/ui/use-toast";
import { Json } from "@/integrations/supabase/types";
import { GoogleGenerativeAI } from "@google/generative-ai";

// Initialize Gemini AI
const genAI = new GoogleGenerativeAI(import.meta.env.VITE_GEMINI_API_KEY || "");
const model = genAI.getGenerativeModel({ model: "gemini-2.0-flash" });

interface ChatMessage {
  user_id: string;
  message: string;
  bot_response: string;
  created_at: string;
}

type DatabaseChat = ChatMessage[] | null;

const SYSTEM_PROMPT = `You are an AI startup advisor. Your role is to help users validate their startup ideas by:
1. Analyzing the feasibility of their idea
2. Identifying potential market opportunities and challenges
3. Suggesting improvements or pivots if necessary
4. Providing actionable next steps

Keep your responses concise, practical, and focused on helping the user move forward with their idea.
Format your responses in clear sections without any special characters or markdown:

Analysis:
[Your analysis here]

Market Potential:
[Market potential details]

Challenges:
[Key challenges]

Recommendations:
[Your recommendations]
`;

export default function Chat() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [newMessage, setNewMessage] = useState("");
  const [isLoading, setIsLoading] = useState(false);
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

  const generateGeminiResponse = async (
    prompt: string,
    history: ChatMessage[]
  ) => {
    try {
      // Create chat context from history
      const chatContext = history
        .map((msg) => `User: ${msg.message}\nAssistant: ${msg.bot_response}`)
        .join("\n");

      // Combine system prompt, history, and new message
      const fullPrompt = `${SYSTEM_PROMPT}\n\nChat History:\n${chatContext}\n\nUser: ${prompt}\nAssistant:`;

      const result = await model.generateContent(fullPrompt);
      const response = await result.response;
      const text = response.text();
      // Remove any potential markdown or special characters
      return text.replace(/[*_~`]/g, '');
    } catch (error) {
      console.error("Error generating AI response:", error);
      return "I apologize, but I encountered an error while analyzing your idea. Please try again.";
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
        bot_response: "Analyzing your idea...",
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

      // Generate AI response
      const aiResponse = await generateGeminiResponse(newMessage, existingChat);

      const botResponse: ChatMessage = {
        ...newChatMessage,
        bot_response: aiResponse,
        created_at: new Date().toISOString(),
      };

      const finalChat = [...updatedChat.slice(0, -1), botResponse];

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
                <div className="flex justify-end">
                  <div className="bg-primary text-primary-foreground px-4 py-2 rounded-lg max-w-[80%]">
                    {msg.message}
                  </div>
                </div>
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
              placeholder="Describe your startup idea..."
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
