'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';

export default function Settings() {
  const [apiKey, setApiKey] = useState('');
  const [saved, setSaved] = useState(false);
  const router = useRouter();

  useEffect(() => {
    const key = localStorage.getItem('whipscribe_api_key');
    if (key) setApiKey(key);
  }, []);

  function handleSave() {
    localStorage.setItem('whipscribe_api_key', apiKey);
    setSaved(true);
    setTimeout(() => {
      router.push('/');
    }, 1000);
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
            <Link href="/trends" className="text-slate-600 hover:text-black font-medium text-sm">
              Trends
            </Link>
            <Link href="/settings" className="text-blue-600 font-semibold text-sm">
              Settings
            </Link>
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <div className="max-w-5xl mx-auto px-6 py-12">
        <h1 className="text-3xl font-bold text-black mb-2">Settings</h1>
        <p className="text-slate-600 mb-8">Configure your WhipScribe and AI settings</p>

        <div className="max-w-2xl space-y-8">
          {/* WhipScribe API Settings - Minimal Style */}
          <div className="border border-slate-200 rounded-lg p-6">
            <h2 className="text-xl font-semibold text-black mb-4">WhipScribe Connection</h2>
            
            <div className="space-y-2">
              <label className="block text-sm font-medium text-black">
                API Key
              </label>
              <input
                type="password"
                value={apiKey}
                onChange={(e) => setApiKey(e.target.value)}
                placeholder="Enter your WhipScribe API key"
                className="w-full px-4 py-3 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-600 focus:border-transparent"
              />
              <p className="text-sm text-slate-600">
                Get your API key from{' '}
                <a
                  href="https://whipscribe.com/account"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-blue-600 hover:underline"
                >
                  WhipScribe Account → API key
                </a>
              </p>
            </div>
          </div>

          {/* Save Button */}
          <div className="flex gap-4">
            <button
              onClick={handleSave}
              className="bg-blue-600 text-white px-8 py-3 rounded-lg font-medium hover:bg-blue-700"
            >
              {saved ? 'Saved!' : 'Save Settings'}
            </button>
            <Link
              href="/"
              className="bg-white text-black border border-slate-200 px-8 py-3 rounded-lg font-medium hover:bg-slate-50 inline-block text-center"
            >
              Cancel
            </Link>
          </div>

          {/* Privacy Notice - WhipScribe Style */}
          <div className="p-6 bg-slate-50 rounded-lg border border-slate-200">
            <h3 className="text-lg font-semibold text-black mb-2">Privacy Notice</h3>
            <p className="text-slate-600 text-sm">
              Your API key is stored locally in your browser and is never sent to our servers.
              All analysis happens on your WhipScribe account using your own API credentials.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
