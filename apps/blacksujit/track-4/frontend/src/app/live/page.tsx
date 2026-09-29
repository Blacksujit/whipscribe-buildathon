"use client";

import { useEffect, useState, useRef } from "react";

interface CoachingPrompt {
  type: string;
  priority: "high" | "medium" | "low";
  message: string;
  timestamp: number;
}

interface LiveStats {
  elapsed_time: number;
  segment_count: number;
  speaker_count: number;
  action_items: number;
  compliance_risks: number;
  clarity_issues: number;
  tension_signals: number;
  coaching_prompts: number;
  speakers: Record<string, { segments: number; duration: number }>;
}

interface AnalysisResult {
  segment: {
    text: string;
    speaker: string;
    start: number;
    end: number;
  };
  analysis: {
    sentiment: { label: string; score: number };
    action_item?: { text: string; speaker: string; start: number };
    compliance_risk?: { text: string; speaker: string; start: number };
    clarity_issue?: { text: string; speaker: string; start: number };
    tension_signal?: { text: string; speaker: string; start: number };
  };
  coaching_prompts: CoachingPrompt[];
  live_stats: LiveStats;
}

export default function LiveCoachingPage() {
  const [connected, setConnected] = useState(false);
  const [stats, setStats] = useState<LiveStats | null>(null);
  const [prompts, setPrompts] = useState<CoachingPrompt[]>([]);
  const [segments, setSegments] = useState<Array<{ text: string; speaker: string; start: number }>>([]);
  const [isCallActive, setIsCallActive] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    // Connect to WebSocket server
    const ws = new WebSocket("ws://localhost:8765");

    ws.onopen = () => {
      setConnected(true);
    };

    ws.onclose = () => {
      setConnected(false);
    };

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);

      if (data.type === "analysis") {
        const result: AnalysisResult = data.data;
        setStats(result.live_stats);
        setPrompts((prev) => [...result.coaching_prompts, ...prev].slice(0, 50));
        setSegments((prev) => [...prev, result.segment].slice(-20));
      } else if (data.type === "stats") {
        setStats(data.data);
      }
    };

    wsRef.current = ws;

    return () => {
      ws.close();
    };
  }, []);

  const startCall = () => {
    setIsCallActive(true);
    setPrompts([]);
    setSegments([]);
    wsRef.current?.send(JSON.stringify({ type: "reset" }));
  };

  const endCall = () => {
    setIsCallActive(false);
    wsRef.current?.send(JSON.stringify({ type: "get_summary" }));
  };

  const simulateSegment = () => {
    const sampleSegments = [
      { text: "I think we should launch in November. I'm not sure about the timeline.", speaker: "Sarah", start: Date.now() / 1000, end: Date.now() / 1000 + 5 },
      { text: "We'll definitely deliver by Q1. I promise.", speaker: "Mike", start: Date.now() / 1000, end: Date.now() / 1000 + 3 },
      { text: "Let me circle back with you by Friday. Thanks.", speaker: "Sarah", start: Date.now() / 1000, end: Date.now() / 1000 + 4 },
      { text: "The engineering team isn't ready yet. Can we push to December?", speaker: "Priya", start: Date.now() / 1000, end: Date.now() / 1000 + 6 },
      { text: "I guarantee this will be our best quarter ever.", speaker: "Mike", start: Date.now() / 1000, end: Date.now() / 1000 + 4 },
    ];

    const segment = sampleSegments[Math.floor(Math.random() * sampleSegments.length)];
    wsRef.current?.send(JSON.stringify({ type: "segment", segment }));
  };

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case "high": return "bg-red-100 border-red-500 text-red-800";
      case "medium": return "bg-yellow-100 border-yellow-500 text-yellow-800";
      case "low": return "bg-green-100 border-green-500 text-green-800";
      default: return "bg-gray-100 border-gray-500 text-gray-800";
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 p-4">
      <div className="max-w-6xl mx-auto">
        <header className="mb-6">
          <h1 className="text-2xl font-bold text-gray-900">Live Call Coaching</h1>
          <p className="text-gray-600">Real-time coaching prompts during your call</p>
        </header>

        {/* Connection Status */}
        <div className={`mb-4 p-3 rounded-lg ${connected ? "bg-green-100 text-green-800" : "bg-red-100 text-red-800"}`}>
          {connected ? "Connected to coaching server" : "Disconnected from coaching server"}
        </div>

        {/* Controls */}
        <div className="mb-6 flex gap-4">
          <button
            onClick={startCall}
            disabled={!isCallActive && connected}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-400"
          >
            Start Call
          </button>
          <button
            onClick={endCall}
            disabled={!isCallActive}
            className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 disabled:bg-gray-400"
          >
            End Call
          </button>
          <button
            onClick={simulateSegment}
            disabled={!isCallActive}
            className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:bg-gray-400"
          >
            Simulate Segment
          </button>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Live Stats */}
          <div className="lg:col-span-1">
            <div className="bg-white rounded-lg shadow p-4">
              <h2 className="text-lg font-semibold mb-4">Live Stats</h2>
              {stats ? (
                <div className="space-y-3">
                  <div className="flex justify-between">
                    <span className="text-gray-600">Elapsed Time</span>
                    <span className="font-mono">{stats.elapsed_time}s</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Segments</span>
                    <span className="font-mono">{stats.segment_count}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Speakers</span>
                    <span className="font-mono">{stats.speaker_count}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Action Items</span>
                    <span className="font-mono text-green-600">{stats.action_items}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Compliance Risks</span>
                    <span className="font-mono text-red-600">{stats.compliance_risks}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Clarity Issues</span>
                    <span className="font-mono text-yellow-600">{stats.clarity_issues}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Tension Signals</span>
                    <span className="font-mono text-orange-600">{stats.tension_signals}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Coaching Prompts</span>
                    <span className="font-mono text-blue-600">{stats.coaching_prompts}</span>
                  </div>
                </div>
              ) : (
                <p className="text-gray-500">No data yet. Start a call to see live stats.</p>
              )}
            </div>
          </div>

          {/* Coaching Prompts */}
          <div className="lg:col-span-1">
            <div className="bg-white rounded-lg shadow p-4">
              <h2 className="text-lg font-semibold mb-4">Coaching Prompts</h2>
              <div className="space-y-3 max-h-96 overflow-y-auto">
                {prompts.length > 0 ? (
                  prompts.map((prompt, i) => (
                    <div
                      key={i}
                      className={`p-3 rounded-lg border-l-4 ${getPriorityColor(prompt.priority)}`}
                    >
                      <div className="flex justify-between items-start mb-1">
                        <span className="text-xs font-semibold uppercase">{prompt.type}</span>
                        <span className="text-xs text-gray-500">{prompt.timestamp.toFixed(1)}s</span>
                      </div>
                      <p className="text-sm">{prompt.message}</p>
                    </div>
                  ))
                ) : (
                  <p className="text-gray-500">No coaching prompts yet.</p>
                )}
              </div>
            </div>
          </div>

          {/* Live Transcript */}
          <div className="lg:col-span-1">
            <div className="bg-white rounded-lg shadow p-4">
              <h2 className="text-lg font-semibold mb-4">Live Transcript</h2>
              <div className="space-y-3 max-h-96 overflow-y-auto">
                {segments.length > 0 ? (
                  segments.map((seg, i) => (
                    <div key={i} className="p-3 bg-gray-50 rounded-lg">
                      <div className="flex justify-between items-start mb-1">
                        <span className="text-xs font-semibold text-blue-600">{seg.speaker}</span>
                        <span className="text-xs text-gray-500">{seg.start.toFixed(1)}s</span>
                      </div>
                      <p className="text-sm text-gray-800">{seg.text}</p>
                    </div>
                  ))
                ) : (
                  <p className="text-gray-500">No segments yet.</p>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
