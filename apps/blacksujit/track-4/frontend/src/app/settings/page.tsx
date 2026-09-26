"use client";

import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import Link from "next/link";
import { useRouter } from "next/navigation";
import Navbar from "@/components/Navbar";
import { getSettings, saveSettings, SettingsResponse } from "@/lib/api";
import PageTransition from "@/components/PageTransition";

const springReveal = { type: "spring" as const, stiffness: 200, damping: 20 };
const springHover = { type: "spring" as const, stiffness: 100, damping: 20 };

export default function SettingsPage() {
  const router = useRouter();
  const [settings, setSettings] = useState<SettingsResponse | null>(null);
  const [apiKey, setApiKey] = useState("");
  const [llmModel, setLlmModel] = useState("gpt-4o-mini");
  const [slackWebhook, setSlackWebhook] = useState("");
  const [notionToken, setNotionToken] = useState("");
  const [notionDb, setNotionDb] = useState("");
  const [saved, setSaved] = useState(false);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    async function fetchSettings() {
      setLoading(true);
      const result = await getSettings();
      if (result) {
        setSettings(result);
        setLlmModel(result.llm_model || "gpt-4o-mini");
        setSlackWebhook(result.slack_webhook || "");
        setNotionToken(result.notion_token || "");
        setNotionDb(result.notion_database_id || "");
      }
      setLoading(false);
    }
    fetchSettings();
  }, []);

  async function handleSave() {
    setError("");
    setSaving(true);
    setSaved(false);
    const result = await saveSettings(apiKey, {
      llm_model: llmModel,
      slack_webhook: slackWebhook,
      notion_token: notionToken,
      notion_database_id: notionDb,
    });
    setSaving(false);
    if (!result.success) {
      setError(result.error || "Unable to save settings");
      return;
    }
    setSaved(true);
    setTimeout(() => setSaved(false), 3000);
  }

  if (loading) {
    return (
      <main className="site-shell">
        <Navbar />
        <div className="section-wide" style={{ paddingTop: "92px", paddingBottom: "60px" }}>
          <motion.p initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={springReveal}>
            Loading settings...
          </motion.p>
        </div>
      </main>
    );
  }

  return (
    <PageTransition>
    <main className="site-shell">
      <Navbar />
      <section className="section-wide" style={{ paddingTop: "92px" }}>
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ ...springReveal, delay: 0.1 }}
        >
          <p className="section-eyebrow">Settings</p>
          <h1>Configure your connections.</h1>
          <p className="hero-lede">
            Connect WhipScribe and AI services to power your workflow.
          </p>
        </motion.div>

        <div style={{ maxWidth: "640px", marginTop: "42px" }}>
          {/* WhipScribe Connection */}
          <motion.div
            className="card"
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ ...springReveal, delay: 0.2 }}
          >
            <h2 style={{ margin: "0 0 16px" }}>WhipScribe Connection</h2>
            <div style={{ marginBottom: "16px" }}>
              <label className="text-v4-ink-muted" style={{ display: "block", marginBottom: "6px", fontSize: "var(--text-micro)" }}>
                API Key
              </label>
              <input
                type="password"
                value={apiKey}
                onChange={(e) => setApiKey(e.target.value)}
                placeholder={settings?.configured ? "••••••••••••" : "Enter your WhipScribe API key"}
                className="w-full px-4 py-3 border border-rule rounded-card focus:outline-none focus:ring-1 focus:ring-brand bg-v4-bg text-v4-ink placeholder-v4-ink-muted"
                style={{ fontSize: "var(--text-body)" }}
              />
              <p className="text-v4-ink-muted" style={{ fontSize: "var(--text-micro)", marginTop: "8px" }}>
                Get your API key from{" "}
                <a
                  href="https://whipscribe.com/account"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-brand hover:underline"
                >
                  WhipScribe Account → API key
                </a>
                {settings?.configured && !apiKey && " (connected)"}
              </p>
            </div>
          </motion.div>

          {/* AI Model */}
          <motion.div
            className="card"
            style={{ marginTop: "16px" }}
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ ...springReveal, delay: 0.3 }}
          >
            <h2 style={{ margin: "0 0 16px" }}>AI Model</h2>
            <div style={{ marginBottom: "16px" }}>
              <label className="text-v4-ink-muted" style={{ display: "block", marginBottom: "6px", fontSize: "var(--text-micro)" }}>
                LLM Provider
              </label>
              <select
                value={llmModel}
                onChange={(e) => setLlmModel(e.target.value)}
                className="w-full px-4 py-3 border border-rule rounded-card focus:outline-none focus:ring-1 focus:ring-brand bg-v4-bg text-v4-ink"
                style={{ fontSize: "var(--text-body)" }}
              >
                <option value="gpt-4o-mini">GPT-4o Mini (Balanced)</option>
                <option value="gpt-4o">GPT-4o (Best quality)</option>
                <option value="anthropic/claude-3-5-sonnet-20241022">Claude 3.5 Sonnet (Reasoning)</option>
                <option value="openai/gpt-oss-120b">GPT-OSS 120B (Local)</option>
              </select>
              <p className="text-v4-ink-muted" style={{ fontSize: "var(--text-micro)", marginTop: "8px" }}>
                Higher-quality models cost more and take longer per analysis.
              </p>
            </div>
          </motion.div>

          {/* Integrations */}
          <motion.div
            className="card"
            style={{ marginTop: "16px" }}
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ ...springReveal, delay: 0.4 }}
          >
            <h2 style={{ margin: "0 0 16px" }}>Integrations</h2>

            <div style={{ marginBottom: "20px" }}>
              <label className="text-v4-ink-muted" style={{ display: "block", marginBottom: "6px", fontSize: "var(--text-micro)" }}>
                Slack Webhook URL
              </label>
              <input
                type="url"
                value={slackWebhook}
                onChange={(e) => setSlackWebhook(e.target.value)}
                placeholder="https://hooks.slack.com/services/..."
                className="w-full px-4 py-3 border border-rule rounded-card focus:outline-none focus:ring-1 focus:ring-brand bg-v4-bg text-v4-ink placeholder-v4-ink-muted"
                style={{ fontSize: "var(--text-body)" }}
              />
              <p className="text-v4-ink-muted" style={{ fontSize: "var(--text-micro)", marginTop: "8px" }}>
                Receive coaching summaries in Slack after analysis.
              </p>
            </div>

            <div style={{ marginBottom: "20px" }}>
              <label className="text-v4-ink-muted" style={{ display: "block", marginBottom: "6px", fontSize: "var(--text-micro)" }}>
                Notion Integration Token
              </label>
              <input
                type="password"
                value={notionToken}
                onChange={(e) => setNotionToken(e.target.value)}
                placeholder="notion_secret_..."
                className="w-full px-4 py-3 border border-rule rounded-card focus:outline-none focus:ring-1 focus:ring-brand bg-v4-bg text-v4-ink placeholder-v4-ink-muted"
                style={{ fontSize: "var(--text-body)" }}
              />
            </div>

            <div>
              <label className="text-v4-ink-muted" style={{ display: "block", marginBottom: "6px", fontSize: "var(--text-micro)" }}>
                Notion Database ID
              </label>
              <input
                type="text"
                value={notionDb}
                onChange={(e) => setNotionDb(e.target.value)}
                placeholder="Database UUID"
                className="w-full px-4 py-3 border border-rule rounded-card focus:outline-none focus:ring-1 focus:ring-brand bg-v4-bg text-v4-ink placeholder-v4-ink-muted"
                style={{ fontSize: "var(--text-body)" }}
              />
              <p className="text-v4-ink-muted" style={{ fontSize: "var(--text-micro)", marginTop: "8px" }}>
                Export scorecards directly to your Notion workspace.
              </p>
            </div>
          </motion.div>

          {/* Save Button */}
          <motion.div
            style={{ marginTop: "32px", display: "flex", gap: "16px", alignItems: "center" }}
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ ...springReveal, delay: 0.5 }}
          >
            <motion.button
              className="btn-primary"
              onClick={handleSave}
              disabled={saving}
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              transition={springHover}
            >
              {saving ? "Saving..." : "Save Settings"}
            </motion.button>
            {error && <span style={{ color: "var(--color-accent)", fontSize: "var(--text-micro)" }}>{error}</span>}
            {saved && (
              <motion.span
                style={{ color: "var(--color-ok)", fontSize: "var(--text-micro)" }}
                initial={{ opacity: 0, x: -8 }}
                animate={{ opacity: 1, x: 0 }}
              >
                Saved ✓
              </motion.span>
            )}
          </motion.div>
        </div>
      </section>
    </main>
  </PageTransition>
  );
}
