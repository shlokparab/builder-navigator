import { useState, useEffect, useRef } from "react";
import { supabase } from "@/integrations/supabase/client";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { SendHorizontal, Mic, MicOff } from "lucide-react";
import { useToast } from "@/components/ui/use-toast";
import { Json } from "@/integrations/supabase/types";

interface Competitor {
  name: string;
  description: string;
  differentiators: string;
  url: string;
}

interface MarketAnalysisResponse {
  analysis: string;
}

interface InvestorRecommendation {
  investors?: Array<{
    investor: string;
    id?: number;
  }>;
  emails?: Array<{
    investor: string;
    email: string;
  }>;
}

interface ChatMessage {
  user_id: string;
  message: string;
  bot_response: string;
  created_at: string;
  contemplator?: string;
  mvp_code?: string;
  mermaid?: string;
  is_audio?: boolean;
  competitors?: Competitor[];
  market_analysis?: string;
}

type DatabaseChat = ChatMessage[] | null;

interface ValidateIdeaResponse {
  status: string;
  contemplator: string;
  result: string;
}

interface ValidateAudioResponse {
  status: string;
  contemplator: string;
  result: string;
}

interface MVPResponse {
  main_response: string;
  code: string;
  mermaid: {
    system_architecture: string;
    process_flow: string;
  };
}

interface AudioRecorderProps {
  onAudioRecorded: (audioBlob: Blob, audioFileName: string) => void;
  isLoading: boolean;
}

function AudioRecorder({ onAudioRecorded, isLoading }: AudioRecorderProps) {
  const [isRecording, setIsRecording] = useState(false);
  const [mediaRecorder, setMediaRecorder] = useState<MediaRecorder | null>(
    null
  );
  const chunks = useRef<Blob[]>([]);

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const recorder = new MediaRecorder(stream);

      recorder.ondataavailable = (e) => {
        if (e.data.size > 0) {
          chunks.current.push(e.data);
        }
      };

      recorder.onstop = () => {
        const blob = new Blob(chunks.current, { type: "audio/wav" });
        chunks.current = [];

        // Generate unique filename
        const audioFileName = `audio_${Date.now()}.wav`;
        onAudioRecorded(blob, audioFileName);

        // Stop all tracks
        stream.getTracks().forEach((track) => track.stop());
      };

      setMediaRecorder(recorder);
      recorder.start();
      setIsRecording(true);
    } catch (error) {
      console.error("Error accessing microphone:", error);
    }
  };

  const stopRecording = () => {
    if (mediaRecorder && isRecording) {
      mediaRecorder.stop();
      setIsRecording(false);
    }
  };

  return (
    <Button
      type="button"
      disabled={isLoading}
      size="icon"
      variant={isRecording ? "destructive" : "default"}
      onClick={isRecording ? stopRecording : startRecording}
      className="transition-all duration-200 hover:scale-105"
    >
      {isRecording ? (
        <MicOff className="h-4 w-4 animate-pulse text-red-500" />
      ) : (
        <Mic className="h-4 w-4" />
      )}
    </Button>
  );
}

export default function Chat() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [newMessage, setNewMessage] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [askingForAnalysis, setAskingForAnalysis] = useState(false);
  const [askingForMVP, setAskingForMVP] = useState(false);
  const [askingForInvestors, setAskingForInvestors] = useState(false);
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

  const validateIdea = async (
    prompt: string
  ): Promise<ValidateIdeaResponse> => {
    try {
      const response = await fetch(
        `https://builder-navigator.onrender.com/validate_idea?idea=${encodeURIComponent(
          prompt
        )}`,
        {
          method: "GET",
          mode: "cors",
          headers: {
            Accept: "application/json",
          },
        }
      );
      if (!response.ok) {
        throw new Error("Failed to validate idea");
      }

      return await response.json();
    } catch (error) {
      console.error("Error validating idea:", error);
      throw error;
    }
  };

  const analyzeMarket = async (
    prompt: string
  ): Promise<MarketAnalysisResponse> => {
    try {
      const response = await fetch(
        `https://builder-navigator.onrender.com/market_analysis`,
        {
          method: "GET",
          mode: "cors",
          headers: {
            Accept: "application/json",
          },
        }
      );
      if (!response.ok) {
        throw new Error("Failed to analyze market");
      }
      return await response.json();
    } catch (error) {
      console.error("Error analyzing market:", error);
      throw error;
    }
  };

  const generateMVP = async (prompt: string): Promise<MVPResponse> => {
    try {
      const response = await fetch(
        `https://builder-navigator.onrender.com/generate_mvp`,
        {
          method: "GET",
          mode: "cors",
          headers: {
            Accept: "application/json",
          },
        }
      );
      if (!response.ok) {
        throw new Error("Failed to generate MVP");
      }
      return await response.json();
    } catch (error) {
      console.error("Error generating MVP:", error);
      throw error;
    }
  };

  const handleAudioRecorded = async (
    audioBlob: Blob,
    audioFileName: string
  ) => {
    if (isLoading) return;

    setIsLoading(true);
    try {
      // Show audio message from user immediately
      const audioMessage: ChatMessage = {
        user_id: "user",
        message: "🎤 Audio message sent",
        bot_response: "Processing audio...",
        created_at: new Date().toISOString(),
        is_audio: true,
      };
      setMessages((prev) => [...prev, audioMessage]);

      // Upload audio file to Supabase Storage
      const { data: uploadData, error: uploadError } = await supabase.storage
        .from("audio_file")
        .upload(audioFileName, audioBlob, {
          contentType: "audio/wav",
        });

      if (uploadError) {
        console.error("Error uploading to Supabase Storage:", uploadError);
        throw uploadError;
      }

      // Get the public URL for the uploaded file
      const {
        data: { publicUrl },
      } = supabase.storage.from("audio_file").getPublicUrl(audioFileName);

      // Update audio column in profiles table with the public URL
      const {
        data: { user },
      } = await supabase.auth.getUser();
      if (!user) throw new Error("Not authenticated");

      const { error: updateError } = await supabase
        .from("profiles")
        .update({ audio: publicUrl })
        .eq("id", user.id);

      if (updateError) {
        console.error("Error updating profile:", updateError);
        throw updateError;
      }

      try {
        const response = await fetch(
          `https://builder-navigator.onrender.com/validate_audio?audio_url=${encodeURIComponent(
            publicUrl
          )}`,
          {
            method: "GET",
            headers: {
              Accept: "application/json",
            },
          }
        );

        if (!response.ok) {
          throw new Error("Failed to transcribe audio");
        }

        const audioResponse: ValidateAudioResponse = await response.json();

        // Update the message with the audio analysis
        const updatedAudioMessage: ChatMessage = {
          user_id: user.id,
          message: "🎤 Audio pitch analyzed",
          bot_response: audioResponse.result,
          contemplator: audioResponse.contemplator,
          created_at: new Date().toISOString(),
          is_audio: true,
        };

        setMessages((prev) => [...prev.slice(0, -1), updatedAudioMessage]);

        if (audioResponse.status === "sufficient_information") {
          setAskingForAnalysis(true);
          const analysisQuestion: ChatMessage = {
            user_id: user.id,
            message: "",
            bot_response:
              "Would you like me to perform a deep market analysis for your idea? (Yes/No)",
            created_at: new Date().toISOString(),
          };
          setMessages((prev) => [...prev, analysisQuestion]);
        }
      } catch (backendError) {
        console.error(
          "Backend processing failed but file was uploaded to Supabase:",
          backendError
        );
        toast({
          title: "Partial Success",
          description: "Audio uploaded but analysis failed",
          variant: "default",
        });
      }
    } catch (error) {
      console.error("Error processing audio:", error);
      toast({
        title: "Error",
        description: "Failed to process audio message",
        variant: "destructive",
      });
    } finally {
      setIsLoading(false);
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
        bot_response: askingForAnalysis
          ? "Analyzing market..."
          : askingForMVP
          ? "Generating MVP..."
          : askingForInvestors
          ? "Generating investor resources..."
          : "Analyzing your idea...",
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
      let mvpResponse;
      let marketAnalysisResponse;

      if (askingForMVP) {
        if (newMessage.toLowerCase().includes("yes")) {
          mvpResponse = await generateMVP(
            messages[messages.length - 3].message
          );
          const botResponse: ChatMessage = {
            ...newChatMessage,
            bot_response: mvpResponse.main_response,
            mvp_code: mvpResponse.code,
            mermaid: mvpResponse.mermaid.system_architecture,
            created_at: new Date().toISOString(),
          };
          const investorQuestion: ChatMessage = {
            user_id: user.id,
            message: "",
            bot_response:
              "Would you like me to provide you with an investor list and email templates for outreach? (Yes/No)",
            created_at: new Date().toISOString(),
          };
          const finalChat = [
            ...updatedChat.slice(0, -1),
            botResponse,
            investorQuestion,
          ];
          await supabase
            .from("profiles")
            .update({ chat: finalChat as unknown as Json })
            .eq("id", user.id);
          setMessages(finalChat);
          setAskingForInvestors(true);
        } else {
          const botResponse: ChatMessage = {
            ...newChatMessage,
            bot_response:
              "Would you like me to provide you with an investor list and email templates for outreach? (Yes/No)",
            created_at: new Date().toISOString(),
          };
          const finalChat = [...updatedChat.slice(0, -1), botResponse];
          await supabase
            .from("profiles")
            .update({ chat: finalChat as unknown as Json })
            .eq("id", user.id);
          setMessages(finalChat);
          setAskingForInvestors(true);
        }
        setAskingForMVP(false);
      } else if (askingForInvestors) {
        if (newMessage.toLowerCase().includes("yes")) {
          const response = await fetch(
            `https://builder-navigator.onrender.com/investor_recommendations`,
            {
              method: "GET",
              mode: "cors",
              headers: {
                Accept: "application/json",
              },
            }
          );
          if (!response.ok) {
            throw new Error("Failed to get investor recommendations");
          }
          const investorData: InvestorRecommendation = await response.json();
          const botResponse: ChatMessage = {
            ...newChatMessage,
            bot_response: `Here are some recommended investors for your startup:
${
  investorData.investors?.[0]?.investor.split(" (ID:")[0] ||
  "No investor data available"
}

${
  investorData.investors?.[1]?.investor.split(" (ID:")[0] ||
  "No investor data available"
}

${
  investorData.investors?.[2]?.investor.split(" (ID:")[0] ||
  "No investor data available"
}

Email templates for outreach:
${investorData.emails?.[0]?.email || "No email template available"}

${investorData.emails?.[1]?.email || "No email template available"}

${investorData.emails?.[2]?.email || "No email template available"}`,
            created_at: new Date().toISOString(),
          };
          const finalChat = [...updatedChat.slice(0, -1), botResponse];
          await supabase
            .from("profiles")
            .update({ chat: finalChat as unknown as Json })
            .eq("id", user.id);
          setMessages(finalChat);
        } else {
          const botResponse: ChatMessage = {
            ...newChatMessage,
            bot_response:
              "Alright! Let me know if you want to explore another startup idea.",
            created_at: new Date().toISOString(),
          };
          const finalChat = [...updatedChat.slice(0, -1), botResponse];
          await supabase
            .from("profiles")
            .update({ chat: finalChat as unknown as Json })
            .eq("id", user.id);
          setMessages(finalChat);
        }
        setAskingForInvestors(false);
      } else if (askingForAnalysis) {
        if (newMessage.toLowerCase().includes("yes")) {
          marketAnalysisResponse = await analyzeMarket(
            messages[messages.length - 2].message
          );
          const botResponse: ChatMessage = {
            ...newChatMessage,
            bot_response: marketAnalysisResponse.analysis,
            market_analysis: marketAnalysisResponse.analysis,
            created_at: new Date().toISOString(),
          };
          const mvpQuestion: ChatMessage = {
            user_id: user.id,
            message: "",
            bot_response:
              "Would you like me to generate an MVP and architecture diagram for your idea? (Yes/No)",
            created_at: new Date().toISOString(),
          };
          const finalChat = [
            ...updatedChat.slice(0, -1),
            botResponse,
            mvpQuestion,
          ];
          await supabase
            .from("profiles")
            .update({ chat: finalChat as unknown as Json })
            .eq("id", user.id);
          setMessages(finalChat);
          setAskingForMVP(true);
        } else {
          const botResponse: ChatMessage = {
            ...newChatMessage,
            bot_response:
              "Would you like me to generate an MVP and architecture diagram for your idea? (Yes/No)",
            created_at: new Date().toISOString(),
          };
          const finalChat = [...updatedChat.slice(0, -1), botResponse];
          await supabase
            .from("profiles")
            .update({ chat: finalChat as unknown as Json })
            .eq("id", user.id);
          setMessages(finalChat);
          setAskingForMVP(true);
        }
        setAskingForAnalysis(false);
      } else {
        validationResponse = await validateIdea(newMessage);
        const botResponse: ChatMessage = {
          ...newChatMessage,
          bot_response: validationResponse.result,
          contemplator: validationResponse.contemplator,
          created_at: new Date().toISOString(),
        };

        const finalChat = [...updatedChat.slice(0, -1), botResponse];

        if (validationResponse.status === "sufficient_information") {
          setAskingForAnalysis(true);
          const analysisQuestion: ChatMessage = {
            user_id: user.id,
            message: "",
            bot_response:
              "Would you like me to perform a deep market analysis for your idea? (Yes/No)",
            created_at: new Date().toISOString(),
          };
          finalChat.push(analysisQuestion);
        }

        await supabase
          .from("profiles")
          .update({ chat: finalChat as unknown as Json })
          .eq("id", user.id);

        setMessages(finalChat);
      }
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
    <div className="flex flex-col h-[calc(100vh-2rem)] pt-16 bg-gray-900">
      <div className="flex-1 overflow-hidden">
        <ScrollArea className="h-full px-4">
          <div className="max-w-4xl mx-auto space-y-6 py-4">
            {messages.map((msg, index) => (
              <div key={index} className="space-y-4">
                {msg.message && (
                  <div className="flex justify-end">
                    <div className="bg-primary text-primary-foreground px-6 py-3 rounded-2xl max-w-[80%] shadow-lg transform hover:scale-[1.02] transition-transform duration-200">
                      {msg.is_audio ? (
                        <div className="flex items-center gap-2">
                          <Mic className="h-4 w-4 animate-pulse" />
                          {msg.message}
                        </div>
                      ) : (
                        msg.message
                      )}
                    </div>
                  </div>
                )}
                <div className="flex justify-start">
                  <div className="bg-gray-800 px-6 py-3 rounded-2xl max-w-[80%] shadow-lg transform hover:scale-[1.02] transition-transform duration-200 whitespace-pre-line">
                    {msg.bot_response}
                    {msg.mermaid && (
                      <div className="mt-6 p-4 bg-gray-900 text-gray-100 rounded-xl overflow-x-auto shadow-inner">
                        <h4 className="text-sm font-semibold mb-2">
                          Flow Diagram
                        </h4>
                        <pre className="font-mono text-sm">{msg.mermaid}</pre>
                      </div>
                    )}
                    {msg.mvp_code && (
                      <div className="mt-6 p-4 bg-gray-900 text-gray-100 rounded-xl overflow-x-auto shadow-inner">
                        <pre className="font-mono text-sm">{msg.mvp_code}</pre>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </ScrollArea>
      </div>

      <div className="p-4 border-t border-gray-800 bg-gray-800/50 backdrop-blur-lg">
        <form onSubmit={handleSubmit} className="max-w-4xl mx-auto">
          <div className="flex gap-3">
            <Input
              value={newMessage}
              onChange={(e) => setNewMessage(e.target.value)}
              placeholder={
                askingForAnalysis
                  ? "Type 'yes' for market analysis..."
                  : askingForMVP
                  ? "Type 'yes' for MVP generation..."
                  : askingForInvestors
                  ? "Type 'yes' for investor resources..."
                  : "Describe your startup idea..."
              }
              disabled={isLoading}
              className="flex-1 rounded-xl shadow-sm focus:ring-2 focus:ring-primary transition-all duration-200 bg-gray-900 border-gray-700"
            />
            <AudioRecorder
              onAudioRecorded={handleAudioRecorded}
              isLoading={isLoading}
            />
            <Button
              type="submit"
              disabled={isLoading}
              size="icon"
              className="rounded-xl shadow-sm transition-all duration-200 hover:scale-105"
            >
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
