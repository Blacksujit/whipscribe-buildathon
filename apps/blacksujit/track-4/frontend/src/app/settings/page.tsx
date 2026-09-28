"use client";

import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import Navbar from "@/components/Navbar";
import { getSettings, saveSettings, SettingsResponse, SettingsUpdate } from "@/lib/api";
import PageTransition from "@/components/PageTransition";

const springReveal = { type: "spring" as const, stiffness: 200, damping: 20 };

const PROVIDERS = [
  { value: "groq", label: "Groq (default)" },
  { value: "openai", label: "OpenAI" },
  { value: "anthropic", label: "Anthropic" },
];

const MODELS = [
  { value: "openai/gpt-oss-120b", label: "GPT-OSS 120B (Groq default)" },
  { value: "gpt-4o-mini", label: "GPT-4o Mini" },
  { value: "gpt-4o", label: "GPT-4o" },
  { value: "claude-3-5-sonnet-20241022", label: "Claude 3.5 Sonnet (Anthropic)" },
];

export default function SettingsPage() {
  const [settings, setSettings] = useState<SettingsResponse | null>(null);
  const [loadError, setLoadError] = useState(false);
  const [apiKey, setApiKey] = useState("");
  const [llmProvider, setLlmProvider] = useState("groq");
  const [llmModel, setLlmModel] = useState("openai/gpt-oss-120b");
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
        setLlmProvider(result.llm_provider || "groq");
        setLlmModel(result.llm_model || "openai/gpt-oss-120b");
        setNotionDb(result.notion_database_id || "");
      } else {
        setLoadError(true);
      }
      setLoading(false);
    }
    fetchSettings();
  }, []);

  async function handleSave() {
    setError("");
    setSaving(true);
    setSaved(false);

    // Secrets are only sent when the user typed a new value; the masked
    // placeholders from the API are never posted back.
    const update: SettingsUpdate = {
      llm_provider: llmProvider,
      llm_model: llmModel,
    };
    if (apiKey.trim()) update.whipscribe_api_key = apiKey.trim();
    if (slackWebhook.trim()) update.slack_webhook = slackWebhook.trim();
    if (notionToken.trim()) update.notion_token = notionToken.trim();
    if (notionDb.trim()) update.notion_database_id = notionDb.trim();

    const result = await saveSettings(update);
    setSaving(false);
    if (!result.success) {
      setError(result.error || "Save failed");
      return;
    }

    setSaved(true);
    setApiKey("");
    setSlackWebhook("");
    setNotionToken("");
    const refreshed = await getSettings();
    if (refreshed) setSettings(refreshed);
    setTimeout(() => setSaved(false), 3000);
  }

  if (loading) {
    return (
      <main className="site-shell">
        <Navbar />
        <div className="section-wide section-pad">
          <motion.p initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={springReveal}>
            Loading settings...
          </motion.p>
        </div>
      </main>
    );
  }

  if (loadError) {
    return (
      <main className="site-shell">
        <Navbar />
        <section className="section-wide section-pad">
          <p className="section-eyebrow">Settings</p>
          <h1 className="section-title">Cannot reach the API.</h1>
          <div className="status-banner status-banner-error">
            The dashboard could not load settings from the Flask backend. Start it with
            <code> python app.py</code> and check <code>NEXT_PUBLIC_API_URL</code> in
            <code> frontend/.env.local</code>.
          </div>
        </section>
      </main>
    );
  }

  return (
    <PageTransition>
    <main className="site-shell">
      <Navbar />
      <section className="section-wide section-pad">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ ...springReveal, delay: 0.1 }}
        >
          <p className="section-eyebrow">Settings</p>
          <h1 className="section-title">Connect your tools.</h1>
          <p className="section-subtitle">Keys stay on your machine; the dashboard reads them from the API.</p>
        </motion.div>

        <div className="settings-form">
          {/* Connection status */}
          <motion.div
            className="connection-status"
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ ...springReveal, delay: 0.2 }}
          >
            <div className="connection-indicator">
              <span className={`connection-dot ${settings?.configured ? "connected" : "disconnected"}`}></span>
              <span className="connection-label">
                WhipScribe: {settings?.configured ? "Connected" : "Not configured"}
              </span>
            </div>
          </motion.div>

          {/* WhipScribe Connection */}
          <motion.div
            className="card settings-section"
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ ...springReveal, delay: 0.3 }}
          >
            <h2>WhipScribe Connection</h2>
            <div className="settings-field">
              <label>API Key</label>
              <input
                type="password"
                value={apiKey}
                onChange={(e) => setApiKey(e.target.value)}
                placeholder={settings?.api_key_set ? "Saved - enter a new key to replace" : "Enter your WhipScribe API key"}
                className="settings-input"
              />
              <p className="settings-help">
                Get your API key from{" "}
                <a
                  href="https://whipscribe.com/account"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-link"
                >
                  WhipScribe Account - API key
                </a>
                {settings?.api_key_set && !apiKey && " (connected)"}
              </p>
            </div>
          </motion.div>

          {/* AI Model */}
          <motion.div
            className="card settings-section"
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ ...springReveal, delay: 0.4 }}
          >
            <h2>AI Model</h2>
            <div className="settings-field">
              <label>LLM Provider</label>
              <select
                value={llmProvider}
                onChange={(e) => setLlmProvider(e.target.value)}
                className="settings-input"
              >
                {PROVIDERS.map((provider) => (
                  <option key={provider.value} value={provider.value}>{provider.label}</option>
                ))}
              </select>
              <p className="settings-help">
                The provider key (GROQ_API_KEY, OPENAI_API_KEY, ANTHROPIC_API_KEY) comes from the
                server environment or is stored with this setting.
              </p>
            </div>
            <div className="settings-field">
              <label>Model</label>
              <select
                value={llmModel}
                onChange={(e) => setLlmModel(e.target.value)}
                className="settings-input"
              >
                {MODELS.map((model) => (
                  <option key={model.value} value={model.value}>{model.label}</option>
                ))}
              </select>
              <p className="settings-help">Higher-quality models cost more and take longer per analysis.</p>
            </div>
          </motion.div>

          {/* Integrations */}
          <motion.div
            className="card settings-section"
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ ...springReveal, delay: 0.5 }}
          >
            <h2>Integrations</h2>

            <div className="settings-field">
              <label>Slack Webhook URL</label>
              <input
                type="url"
                value={slackWebhook}
                onChange={(e) => setSlackWebhook(e.target.value)}
                placeholder={settings?.slack_webhook_set ? "Saved - enter a new webhook to replace" : "https://hooks.slack.com/services/..."}
                className="settings-input"
              />
              <p className="settings-help">Receive quality reports and trend summaries in Slack after analysis.</p>
            </div>

            <div className="settings-field">
              <label>Notion Integration Token</label>
              <input
                type="password"
                value={notionToken}
                onChange={(e) => setNotionToken(e.target.value)}
                placeholder={settings?.notion_token_set ? "Saved - enter a new token to replace" : "notion_secret_..."}
                className="settings-input"
              />
            </div>

            <div className="settings-field">
              <label>Notion Database ID</label>
              <input
                type="text"
                value={notionDb}
                onChange={(e) => setNotionDb(e.target.value)}
                placeholder="Database UUID"
                className="settings-input"
              />
              <p className="settings-help">Export scorecards directly to your Notion workspace.</p>
            </div>
          </motion.div>

          {/* Save Button */}
          <motion.div
            className="save-row"
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ ...springReveal, delay: 0.6 }}
          >
            <motion.button
              className="btn-primary"
              onClick={handleSave}
              disabled={saving}
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              transition={springReveal}
            >
              {saving ? "Saving..." : "Save Settings"}
            </motion.button>
            {error && <span className="save-error">{error}</span>}
            {saved && (
              <motion.span
                className="save-success"
                initial={{ opacity: 0, x: -8 }}
                animate={{ opacity: 1, x: 0 }}
                transition={springReveal}
              >
                Saved
              </motion.span>
            )}
          </motion.div>
        </div>
      </section>
    </main>
    </PageTransition>
  );
}
