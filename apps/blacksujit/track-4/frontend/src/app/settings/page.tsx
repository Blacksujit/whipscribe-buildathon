"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Navbar from "@/components/Navbar";
import { saveSettings } from "@/lib/api";

export default function Settings() {
  const [apiKey, setApiKey] = useState("");
  const [saved, setSaved] = useState(false);
  const [error, setError] = useState("");
  const [saving, setSaving] = useState(false);
  const router = useRouter();

  async function handleSave() {
    setError("");
    setSaving(true);
    const result = await saveSettings(apiKey);
    setSaving(false);
    if (!result.success) {
      setError(result.error || "Unable to save settings");
      return;
    }
    setSaved(true);
    router.push("/");
  }

  return (
    <div className="min-h-screen bg-v4-bg">
      <Navbar />
      <section className="container-960 section mx-auto">
        <h1 className="font-display text-h1 mb-2">Settings</h1>
        <p className="text-v4-ink-muted mb-12">Configure your WhipScribe and AI settings</p>

        <div className="max-w-2xl">
          {/* WhipScribe Connection */}
          <div className="card">
            <h2 className="text-h3 font-medium text-v4-ink mb-4">WhipScribe Connection</h2>

            <div>
              <label className="block text-sm text-v4-ink-muted mb-2">API Key</label>
              <input
                type="password"
                value={apiKey}
                onChange={(e) => setApiKey(e.target.value)}
                placeholder="Enter your WhipScribe API key"
                className="w-full px-4 py-3 border border-rule rounded-card focus:outline-none focus:ring-1 focus:ring-brand bg-v4-bg text-v4-ink placeholder-v4-ink-muted"
                style={{ fontSize: "var(--text-body)" }}
              />
              <p className="text-sm text-v4-ink-muted mt-2">
                Get your API key from{" "}
                <a
                  href="https://whipscribe.com/account"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-brand hover:underline"
                >
                  WhipScribe Account → API key
                </a>
              </p>
            </div>
          </div>

          {/* Save / Cancel */}
          <div className="flex gap-4 mt-8">
              <button onClick={handleSave} className="btn-primary" disabled={saving || !apiKey.trim()}>
              {saving ? "Saving..." : saved ? "Saved!" : "Save Settings"}
            </button>
            <button
              onClick={() => router.push("/")}
              className="btn-secondary"
            >
              Cancel
            </button>
          </div>

          {error && <p className="mt-4 text-sm text-red-700" role="alert">{error}</p>}

          {/* Privacy Notice */}
          <div className="card mt-8" style={{ backgroundColor: "var(--color-v4-bg-alt)" }}>
            <h3 className="text-v4-ink font-medium mb-2">Privacy Notice</h3>
            <p className="text-v4-ink-muted" style={{ fontSize: "var(--text-body)" }}>
              Your API key is stored by the local Flask backend and used only to call
              your WhipScribe account. Keep this development server private.
            </p>
          </div>
        </div>
      </section>
    </div>
  );
}
