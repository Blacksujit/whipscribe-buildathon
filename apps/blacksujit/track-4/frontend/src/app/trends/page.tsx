'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { getTrends } from '@/lib/api';

export default function Trends() {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchData() {
      setLoading(true);
      const result = await getTrends();
      setData(result);
      setLoading(false);
    }
    fetchData();
  }, []);

  if (loading) {
    return (
      <div className="min-h-screen bg-white">
        <nav className="bg-white border-b border-slate-200 sticky top-0 z-50">
          <div className="max-w-5xl mx-auto px-6 py-4 flex items-center justify-between">
            <Link href="/" className="text-lg font-bold text-blue-600">
              CallCoach AI
            </Link>
            <div className="flex gap-6">
              <Link href="/trends" className="text-blue-600 font-semibold text-sm">
                Trends
              </Link>
              <Link href="/settings" className="text-slate-600 hover:text-black font-medium text-sm">
                Settings
              </Link>
            </div>
          </div>
        </nav>
        <div className="max-w-5xl mx-auto px-6 py-12">
          <div className="text-slate-600">Loading...</div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-white">
      {/* Navigation - WhipScribe Style */}
      <nav className="bg-white border-b border-slate-200 sticky top-0 z-50">
        <div className="max-w-5xl mx-auto px-6 py-4 flex items-center justify-between">
          <Link href="/" className="text-lg font-bold text-blue-600">
            CallCoach AI
          </Link>
          <div className="flex gap-6">
            <Link href="/trends" className="text-blue-600 font-semibold text-sm">
              Trends
            </Link>
            <Link href="/settings" className="text-slate-600 hover:text-black font-medium text-sm">
              Settings
            </Link>
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <div className="max-w-5xl mx-auto px-6 py-12">
        <h1 className="text-3xl font-bold text-black mb-2">Quality Trends</h1>
        <p className="text-slate-600 mb-8">Track team performance over time</p>

        {/* Metrics Grid - Minimal Style */}
        <div className="grid grid-cols-4 gap-4 mb-12">
          <div className="border border-slate-200 rounded-lg p-6 text-center">
            <div className="text-3xl font-bold text-blue-600">87</div>
            <div className="text-sm text-slate-600 mt-2">Average Score</div>
          </div>
          <div className="border border-slate-200 rounded-lg p-6 text-center">
            <div className="text-3xl font-bold text-blue-600">12</div>
            <div className="text-sm text-slate-600 mt-2">Meetings Analyzed</div>
          </div>
          <div className="border border-slate-200 rounded-lg p-6 text-center">
            <div className="text-3xl font-bold text-green-600">+5%</div>
            <div className="text-sm text-slate-600 mt-2">Improvement</div>
          </div>
          <div className="border border-slate-200 rounded-lg p-6 text-center">
            <div className="text-3xl font-bold text-amber-600">3</div>
            <div className="text-sm text-slate-600 mt-2">Issues Found</div>
          </div>
        </div>

        {/* Evidence Cards - WhipScribe Style */}
        <h2 className="text-xl font-semibold text-black mb-4">Performance Insights</h2>
        <div className="space-y-4 mb-12">
          <div className="border border-slate-200 rounded-lg p-6">
            <h3 className="font-semibold text-black mb-2">Sarah · Sales Lead · High Performance</h3>
            <p className="text-slate-600 text-sm mb-2">
              Consistently high action item completion rate. Clear communication on compliance topics.
            </p>
            <p className="text-slate-500 text-xs font-mono">
              Evidence: Q4 Planning · 00:07:02
            </p>
          </div>

          <div className="border border-slate-200 rounded-lg p-6">
            <h3 className="font-semibold text-black mb-2">Mike · Product Manager · Needs Coaching</h3>
            <p className="text-slate-600 text-sm mb-2">
              Action items sometimes lack clear ownership. Consider following up with written summaries.
            </p>
            <p className="text-slate-500 text-xs font-mono">
              Evidence: Retro Sprint 12 · 00:15:30
            </p>
          </div>

          <div className="border border-slate-200 rounded-lg p-6">
            <h3 className="font-semibold text-black mb-2">John · Account Executive · Tension Detected</h3>
            <p className="text-slate-600 text-sm mb-2">
              Tension signals detected in 3 of 4 calls. Recommend training on difficult conversations.
            </p>
            <p className="text-slate-500 text-xs font-mono">
              Evidence: Sales Call #23 · 00:23:45
            </p>
          </div>
        </div>

        {/* Notice */}
        <div className="bg-slate-50 border border-slate-200 rounded-lg p-6">
          <h3 className="text-lg font-semibold text-black mb-2">Trend Analysis</h3>
          <p className="text-slate-600">
            Trend analysis requires at least 2 analyzed meetings. Analyze more meetings from the 
            <Link href="/" className="text-blue-600 hover:underline"> home page</Link> to see quality trends.
          </p>
        </div>
      </div>
    </div>
  );
}
