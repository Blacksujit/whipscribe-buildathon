"use client";

import { useState } from "react";

interface Feature {
  id: string;
  name: string;
  description: string;
  status: "active" | "inactive";
  icon: string;
}

const features: Feature[] = [
  { id: "realtime", name: "Real-Time Coaching", description: "Live coaching during calls", status: "active", icon: "⚡" },
  { id: "postcall", name: "Post-Call Analysis", description: "4-agent scoring with evidence", status: "active", icon: "📊" },
  { id: "crosscall", name: "Cross-Call Intelligence", description: "Trend analysis across calls", status: "active", icon: "📈" },
  { id: "crm", name: "HubSpot delivery", description: "Real CRM tasks per scored call", status: "active", icon: "🔗" },
  { id: "followup", name: "Follow-Up Emails", description: "Automated email generation", status: "active", icon: "📧" },
  { id: "benchmark", name: "Team Benchmarking", description: "Compare reps", status: "active", icon: "📊" },
  { id: "rubrics", name: "Custom Rubrics", description: "Define your own scoring", status: "active", icon: "🎯" },
  { id: "sentiment", name: "Sentiment Analysis", description: "Track sentiment trends", status: "active", icon: "😊" },
  { id: "plans", name: "Coaching Plans", description: "Personalized coaching plans", status: "active", icon: "📋" },
  { id: "multilang", name: "Multi-Language", description: "12 languages supported", status: "active", icon: "🌍" },
  { id: "assistant", name: "AI Assistant", description: "Conversational coaching", status: "active", icon: "🤖" },
  { id: "export", name: "Export", description: "Multiple formats", status: "active", icon: "📤" },
  { id: "mcp", name: "MCP Integration", description: "WhipScribe MCP server", status: "active", icon: "🔌" },
];

export default function DashboardPage() {
  const [selectedFeature, setSelectedFeature] = useState<Feature | null>(null);

  return (
    <div className="min-h-screen bg-gray-50 p-4">
      <div className="max-w-7xl mx-auto">
        <header className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">CallCoach-AI Dashboard</h1>
          <p className="text-gray-600 mt-2">All 13 high-impact features in one place</p>
        </header>

        {/* Feature Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4 mb-8">
          {features.map((feature) => (
            <div
              key={feature.id}
              onClick={() => setSelectedFeature(feature)}
              className={`p-4 rounded-lg border-2 cursor-pointer transition-all ${
                selectedFeature?.id === feature.id
                  ? "border-blue-500 bg-blue-50"
                  : "border-gray-200 bg-white hover:border-blue-300"
              }`}
            >
              <div className="text-2xl mb-2">{feature.icon}</div>
              <h3 className="font-semibold text-gray-900">{feature.name}</h3>
              <p className="text-sm text-gray-600 mt-1">{feature.description}</p>
              <div className="mt-3">
                <span className={`inline-block px-2 py-1 text-xs rounded-full ${
                  feature.status === "active"
                    ? "bg-green-100 text-green-800"
                    : "bg-gray-100 text-gray-800"
                }`}>
                  {feature.status}
                </span>
              </div>
            </div>
          ))}
        </div>

        {/* Selected Feature Detail */}
        {selectedFeature && (
          <div className="bg-white rounded-lg shadow-lg p-6">
            <div className="flex items-center gap-3 mb-4">
              <span className="text-3xl">{selectedFeature.icon}</span>
              <div>
                <h2 className="text-xl font-bold text-gray-900">{selectedFeature.name}</h2>
                <p className="text-gray-600">{selectedFeature.description}</p>
              </div>
            </div>

            <div className="border-t pt-4">
              <h3 className="font-semibold text-gray-900 mb-3">Quick Actions</h3>
              <div className="flex flex-wrap gap-2">
                <button className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700">
                  Run Demo
                </button>
                <button className="px-4 py-2 bg-gray-200 text-gray-800 rounded-lg hover:bg-gray-300">
                  View Docs
                </button>
                <button className="px-4 py-2 bg-gray-200 text-gray-800 rounded-lg hover:bg-gray-300">
                  Configure
                </button>
              </div>
            </div>

            <div className="border-t mt-4 pt-4">
              <h3 className="font-semibold text-gray-900 mb-3">API Example</h3>
              <pre className="bg-gray-900 text-green-400 p-4 rounded-lg overflow-x-auto text-sm">
{`from src.core.${selectedFeature.id} import *

# Initialize
component = ${selectedFeature.name.replace(/\s/g, "")}()

# Run
result = component.run()
print(result)`}
              </pre>
            </div>
          </div>
        )}

        {/* Stats Summary */}
        <div className="mt-8 grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="bg-white rounded-lg shadow p-4 text-center">
            <div className="text-3xl font-bold text-blue-600">13</div>
            <div className="text-sm text-gray-600">Features</div>
          </div>
          <div className="bg-white rounded-lg shadow p-4 text-center">
            <div className="text-3xl font-bold text-green-600">52</div>
            <div className="text-sm text-gray-600">Tests Passing</div>
          </div>
          <div className="bg-white rounded-lg shadow p-4 text-center">
            <div className="text-3xl font-bold text-purple-600">12</div>
            <div className="text-sm text-gray-600">Languages</div>
          </div>
          <div className="bg-white rounded-lg shadow p-4 text-center">
            <div className="text-3xl font-bold text-orange-600">1st</div>
            <div className="text-sm text-gray-600">Real-Time Coaching</div>
          </div>
        </div>
      </div>
    </div>
  );
}
