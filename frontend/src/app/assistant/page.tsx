"use client";

import { useState, useRef, useEffect, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Send, Mic, MicOff, Volume2, VolumeX, FileText, Network, Map, Download, Bot, User } from "lucide-react";
import Link from "next/link";
import { DashboardLayout } from "@/components/layout/sidebar";
import { ProtectedRoute } from "@/components/layout/protected-route";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { api, ChatResponse } from "@/lib/api";

interface Message {
  role: "user" | "assistant";
  content: string;
  confidence?: number;
  sources?: ChatResponse["sources"];
  actions?: ChatResponse["actions"];
  sql_query?: string;
}

function AssistantContent() {
  const [messages, setMessages] = useState<Message[]>([
    { role: "assistant", content: "ನಮಸ್ಕಾರ! I am SurakshAI, your crime intelligence assistant. Ask me about FIRs, criminals, hotspots, or investigations in English or Kannada.", confidence: 1 },
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [listening, setListening] = useState(false);
  const [speaking, setSpeaking] = useState(false);
  const [handsFree, setHandsFree] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);
  const mediaRef = useRef<MediaRecorder | null>(null);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
  }, [messages]);

  const speak = useCallback((text: string) => {
    if (typeof window === "undefined" || !window.speechSynthesis) return;
    window.speechSynthesis.cancel();
    const utter = new SpeechSynthesisUtterance(text);
    utter.rate = 0.95;
    utter.onstart = () => setSpeaking(true);
    utter.onend = () => setSpeaking(false);
    window.speechSynthesis.speak(utter);
  }, []);

  const sendMessage = async (text: string) => {
    if (!text.trim() || loading) return;
    setInput("");
    setMessages((m) => [...m, { role: "user", content: text }]);
    setLoading(true);

    try {
      const res = await api.post<ChatResponse>("/ai/chat", {
        message: text,
        session_id: sessionId,
        language: /[\u0C80-\u0CFF]/.test(text) ? "kn" : "en",
      });
      setSessionId(res.session_id);
      const msg: Message = {
        role: "assistant",
        content: res.message,
        confidence: res.confidence,
        sources: res.sources,
        actions: res.actions,
        sql_query: res.sql_query,
      };
      setMessages((m) => [...m, msg]);
      if (handsFree) speak(res.message);
    } catch {
      setMessages((m) => [...m, { role: "assistant", content: "Sorry, I encountered an error processing your request. Please ensure the backend is running and GROQ_API_KEY is configured." }]);
    } finally {
      setLoading(false);
    }
  };

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const recorder = new MediaRecorder(stream);
      const chunks: Blob[] = [];
      recorder.ondataavailable = (e) => chunks.push(e.data);
      recorder.onstop = async () => {
        const blob = new Blob(chunks, { type: "audio/webm" });
        const formData = new FormData();
        formData.append("audio", blob, "recording.webm");
        try {
          const res = await api.upload<{ text: string }>("/ai/transcribe", formData);
          if (res.text) await sendMessage(res.text);
        } catch {
          setMessages((m) => [...m, { role: "assistant", content: "Voice transcription failed. Check GROQ_API_KEY configuration." }]);
        }
        stream.getTracks().forEach((t) => t.stop());
      };
      mediaRef.current = recorder;
      recorder.start();
      setListening(true);
      setTimeout(() => {
        if (recorder.state === "recording") {
          recorder.stop();
          setListening(false);
        }
      }, 5000);
    } catch {
      setMessages((m) => [...m, { role: "assistant", content: "Microphone access denied." }]);
    }
  };

  const actionIcon = (type: string) => {
    switch (type) {
      case "view_fir": return FileText;
      case "view_graph": return Network;
      case "view_map": return Map;
      case "generate_pdf": return Download;
      default: return FileText;
    }
  };

  const actionHref = (action: { type: string; resource_id?: string }) => {
    switch (action.type) {
      case "view_fir": return `/fir/${action.resource_id}`;
      case "view_graph": return `/network?fir=${action.resource_id}`;
      case "view_map": return `/heatmap?fir=${action.resource_id}`;
      case "generate_pdf": return `${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api"}/reports/fir/${action.resource_id}/pdf`;
      default: return "#";
    }
  };

  return (
    <div className="flex flex-col h-[calc(100vh-4rem)]">
      <div className="mb-4">
        <h1 className="text-2xl font-bold">AI Crime Assistant</h1>
        <p className="text-muted-foreground">Evidence-based intelligence with English & Kannada support</p>
      </div>

      <Card className="flex-1 flex flex-col overflow-hidden">
        <CardContent className="flex-1 flex flex-col p-0 overflow-hidden">
          <div ref={scrollRef} className="flex-1 overflow-y-auto p-4 space-y-4">
            <AnimatePresence>
              {messages.map((msg, i) => (
                <motion.div
                  key={i}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  className={`flex gap-3 ${msg.role === "user" ? "justify-end" : ""}`}
                >
                  {msg.role === "assistant" && (
                    <div className="h-8 w-8 rounded-lg bg-primary/20 flex items-center justify-center shrink-0">
                      <Bot className="h-4 w-4 text-primary" />
                    </div>
                  )}
                  <div className={`max-w-[80%] space-y-2 ${msg.role === "user" ? "order-first" : ""}`}>
                    <div className={`rounded-xl px-4 py-3 text-sm ${msg.role === "user" ? "bg-primary text-primary-foreground ml-auto" : "bg-secondary"}`}>
                      {msg.content}
                    </div>
                    {msg.confidence !== undefined && msg.role === "assistant" && (
                      <div className="flex items-center gap-2 flex-wrap">
                        <Badge variant="outline">Confidence: {(msg.confidence * 100).toFixed(0)}%</Badge>
                        {msg.sources?.map((s, j) => (
                          <Link key={j} href={`/fir/${s.id}`}>
                            <Badge variant="secondary">{s.title} ({(s.relevance * 100).toFixed(0)}%)</Badge>
                          </Link>
                        ))}
                      </div>
                    )}
                    {msg.actions && msg.actions.length > 0 && (
                      <div className="flex gap-2 flex-wrap">
                        {msg.actions.map((action, j) => {
                          const Icon = actionIcon(action.type);
                          const href = actionHref(action);
                          const isPdf = action.type === "generate_pdf";
                          return isPdf ? (
                            <a key={j} href={href} target="_blank" rel="noopener">
                              <Button size="sm" variant="outline"><Icon className="h-3 w-3" /> {action.label}</Button>
                            </a>
                          ) : (
                            <Link key={j} href={href}>
                              <Button size="sm" variant="outline"><Icon className="h-3 w-3" /> {action.label}</Button>
                            </Link>
                          );
                        })}
                      </div>
                    )}
                    {msg.sql_query && (
                      <pre className="text-xs bg-background p-2 rounded border border-border overflow-x-auto">{msg.sql_query}</pre>
                    )}
                  </div>
                  {msg.role === "user" && (
                    <div className="h-8 w-8 rounded-lg bg-secondary flex items-center justify-center shrink-0">
                      <User className="h-4 w-4" />
                    </div>
                  )}
                </motion.div>
              ))}
            </AnimatePresence>
            {loading && (
              <div className="flex gap-2 items-center text-muted-foreground text-sm">
                <div className="h-2 w-2 rounded-full bg-primary animate-pulse" />
                Analyzing crime data...
              </div>
            )}
          </div>

          <div className="border-t border-border p-4">
            <div className="flex gap-2">
              <Input
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && sendMessage(input)}
                placeholder="Ask about crimes, FIRs, hotspots... (English or Kannada)"
                disabled={loading}
              />
              <Button size="icon" variant={listening ? "destructive" : "outline"} onClick={startRecording} disabled={loading}>
                {listening ? <MicOff className="h-4 w-4" /> : <Mic className="h-4 w-4" />}
              </Button>
              <Button size="icon" variant={speaking ? "secondary" : "outline"} onClick={() => { setHandsFree(!handsFree); if (speaking) window.speechSynthesis?.cancel(); }}>
                {handsFree ? <Volume2 className="h-4 w-4" /> : <VolumeX className="h-4 w-4" />}
              </Button>
              <Button onClick={() => sendMessage(input)} disabled={loading || !input.trim()}>
                <Send className="h-4 w-4" />
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

export default function AssistantPage() {
  return (
    <ProtectedRoute>
      <DashboardLayout><AssistantContent /></DashboardLayout>
    </ProtectedRoute>
  );
}
