"use client";

import { useCallback, useEffect, useState, type ReactNode } from "react";
import Link from "next/link";
import Navbar from "@/components/Navbar";
import PageHeader from "@/components/PageHeader";
import PageTransition from "@/components/PageTransition";
import AnimatedContent from "@/components/reactbits/AnimatedContent/AnimatedContent";
import {
  WaveformIcon,
  MessageIcon,
  DocumentIcon,
  SparkIcon,
  LinkIcon,
  AlertIcon,
  CheckCircleIcon,
} from "@/components/icons";
import {
  getConnections,
  testWhipscribe,
  connectSlack,
  testSlack,
  disconnectSlack,
  connectNotion,
  testNotion,
  disconnectNotion,
  type ConnectionsResponse,
  type ActionResult,
} from "@/lib/api";

function useAction() {
  const [busy, setBusy] = useState(false);
  const [result, setResult] = useState<ActionResult | null>(null);

  const run = useCallback(async (fn: () => Promise<ActionResult>, after?: () => Promise<void>) => {
    setBusy(true);
    setResult(null);
    const res = await fn();
    setResult(res);
    if (res.success && after) await after();
    setBusy(false);
  }, []);

  return { busy, result, run };
}

function StatusPill({ connected }: { connected: boolean }) {
  return (
    <span className={`pill ${connected ? "pill-on" : "pill-off"}`}>
      <span className="pill-dot" />
      {connected ? "Connected" : "Not connected"}
    </span>
  );
}

function ResultBanner({ result }: { result: ActionResult | null }) {
  if (!result) return null;
  return (
    <div className={result.success ? "status-banner status-banner-ok" : "status-banner status-banner-error"} role="status">
      {result.success ? <CheckCircleIcon size={14} /> : <AlertIcon size={14} />}{" "}
      {result.success ? result.message || "Done." : result.error || "Something went wrong."}
    </div>
  );
}

function ConnectionCard({
  icon,
  title,
  description,
  connected,
  source,
  children,
}: {
  icon: ReactNode;
  title: string;
  description: string;
  connected: boolean;
  source?: "env" | "stored" | null;
  children: ReactNode;
}) {
  const sourceNote =
    source === "env" ? "set in the server environment" : source === "stored" ? "saved from this dashboard" : null;
  return (
    <div className="card connection-card">
      <div className="connection-head">
        <span className="connection-icon" aria-hidden="true">{icon}</span>
        <div style={{ minWidth: 0 }}>
          <h2 className="connection-title">{title}</h2>
          {sourceNote && <span className="source-note">{sourceNote}</span>}
        </div>
        <span style={{ marginLeft: "auto" }}>
          <StatusPill connected={connected} />
        </span>
      </div>
      <p className="connection-desc">{description}</p>
      <div className="connection-body">{children}</div>
    </div>
  );
}

export default function ConnectionsPage() {
  const [data, setData] = useState<ConnectionsResponse | null>(null);
  const [loadError, setLoadError] = useState(false);
  const [webhook, setWebhook] = useState("");
  const [notionToken, setNotionToken] = useState("");
  const [notionDatabase, setNotionDatabase] = useState("");

  const refresh = useCallback(async () => {
    const result = await getConnections();
    if (result) {
      setData(result);
      setLoadError(false);
    } else {
      setLoadError(true);
    }
  }, []);

  useEffect(() => {
    refresh();
  }, [refresh]);

  const whipAction = useAction();
  const slackAction = useAction();
  const notionAction = useAction();

  if (loadError) {
    return (
      <main className="site-shell">
        <Navbar />
        <section className="section-wide section-pad">
          <PageHeader
            eyebrow="Connections"
            title="Cannot reach the API."
            subtitle="Start the Flask backend with python app.py, then reload this page."
          />
          <button className="btn-secondary" onClick={() => refresh()}>Try again</button>
        </section>
      </main>
    );
  }

  return (
    <PageTransition>
    <main className="site-shell">
      <Navbar />
      <section className="section-wide section-pad">
        <PageHeader
          eyebrow="Connections"
          title="Link the tools that get your scores."
          subtitle="Connect once - reports and trend summaries land where your team already works. Server keys stay on the server; nothing here asks for the WhipScribe key."
        />

        <div className="connections-grid">
          {/* WhipScribe */}
          <AnimatedContent>
            <ConnectionCard
              icon={<WaveformIcon size={20} />}
              title="WhipScribe"
              description="Transcription, speakers and timestamps for every upload. Nothing to paste here - the key lives on the server."
              connected={Boolean(data?.whipscribe.connected)}
              source={data?.whipscribe.source ?? null}
            >
              <div className="connection-actions">
                <button
                  className="btn-secondary"
                  disabled={whipAction.busy || !data?.whipscribe.connected}
                  onClick={() => whipAction.run(testWhipscribe)}
                >
                  {whipAction.busy ? "Checking..." : "Verify connection"}
                </button>
                {!data?.whipscribe.connected && (
                  <span className="section-subtitle" style={{ margin: 0 }}>
                    Add the key to <code>.env</code> and restart the API.
                  </span>
                )}
              </div>
              <ResultBanner result={whipAction.result} />
            </ConnectionCard>
          </AnimatedContent>

          {/* AI scoring */}
          <AnimatedContent delay={0.05}>
            <ConnectionCard
              icon={<SparkIcon size={20} />}
              title="AI scoring"
              description="Four agents score every call. The provider and key are configured on the server."
              connected={Boolean(data?.llm.key_set)}
              source={null}
            >
              <div className="connection-actions">
                <span className="pill">
                  {data?.llm.provider ? `${data.llm.provider} - ${data.llm.model}` : "No provider set"}
                </span>
              </div>
            </ConnectionCard>
          </AnimatedContent>

          {/* Slack */}
          <AnimatedContent delay={0.1}>
            <ConnectionCard
              icon={<MessageIcon size={20} />}
              title="Slack"
              description="Scores, commitments and trend summaries posted into a channel you choose."
              connected={Boolean(data?.slack.connected)}
              source={data?.slack.source ?? null}
            >
              {data?.slack.connected ? (
                <div className="connection-actions">
                  <button
                    className="btn-secondary"
                    disabled={slackAction.busy}
                    onClick={() => slackAction.run(testSlack)}
                  >
                    {slackAction.busy ? "Sending..." : "Send test message"}
                  </button>
                  <button
                    className="btn-secondary"
                    disabled={slackAction.busy}
                    onClick={() => slackAction.run(disconnectSlack, refresh)}
                  >
                    Disconnect
                  </button>
                </div>
              ) : (
                <>
                  <div className="settings-field">
                    <label htmlFor="slack-webhook">Incoming webhook URL</label>
                    <input
                      id="slack-webhook"
                      className="settings-input"
                      type="url"
                      value={webhook}
                      onChange={(e) => setWebhook(e.target.value)}
                      placeholder="https://hooks.slack.com/services/..."
                    />
                  </div>
                  <div className="connection-actions">
                    <button
                      className="btn-primary"
                      disabled={slackAction.busy || !webhook.trim()}
                      onClick={() => slackAction.run(() => connectSlack(webhook.trim()), refresh)}
                    >
                      {slackAction.busy ? "Connecting..." : "Connect Slack"}
                    </button>
                    <span className="section-subtitle" style={{ margin: 0 }}>
                      Slack: Apps - Incoming Webhooks - Add to a channel, then paste the URL. We send a test message before saving.
                    </span>
                  </div>
                </>
              )}
              <ResultBanner result={slackAction.result} />
            </ConnectionCard>
          </AnimatedContent>

          {/* Notion */}
          <AnimatedContent delay={0.15}>
            <ConnectionCard
              icon={<DocumentIcon size={20} />}
              title="Notion"
              description="Every report can be written into a Notion database as a new page."
              connected={Boolean(data?.notion.connected)}
              source={data?.notion.source ?? null}
            >
              {data?.notion.connected ? (
                <div className="connection-actions">
                  <button
                    className="btn-secondary"
                    disabled={notionAction.busy}
                    onClick={() => notionAction.run(testNotion)}
                  >
                    {notionAction.busy ? "Writing..." : "Create test page"}
                  </button>
                  <button
                    className="btn-secondary"
                    disabled={notionAction.busy}
                    onClick={() => notionAction.run(disconnectNotion, refresh)}
                  >
                    Disconnect
                  </button>
                  {data.notion.database_id && (
                    <span className="source-note">database {data.notion.database_id.slice(0, 8)}...</span>
                  )}
                </div>
              ) : (
                <>
                  <div className="settings-field">
                    <label htmlFor="notion-token">Integration token</label>
                    <input
                      id="notion-token"
                      className="settings-input"
                      type="password"
                      value={notionToken}
                      onChange={(e) => setNotionToken(e.target.value)}
                      placeholder="ntn_... or secret_..."
                    />
                  </div>
                  <div className="settings-field">
                    <label htmlFor="notion-database">Database link</label>
                    <input
                      id="notion-database"
                      className="settings-input"
                      type="text"
                      value={notionDatabase}
                      onChange={(e) => setNotionDatabase(e.target.value)}
                      placeholder="Paste the database URL from Notion"
                    />
                  </div>
                  <div className="connection-actions">
                    <button
                      className="btn-primary"
                      disabled={notionAction.busy || !notionToken.trim() || !notionDatabase.trim()}
                      onClick={() => notionAction.run(() => connectNotion(notionToken.trim(), notionDatabase.trim()), refresh)}
                    >
                      {notionAction.busy ? "Connecting..." : "Connect Notion"}
                    </button>
                    <span className="section-subtitle" style={{ margin: 0 }}>
                      Share the database with your integration first (Share - your integration).
                    </span>
                  </div>
                </>
              )}
              <ResultBanner result={notionAction.result} />
            </ConnectionCard>
          </AnimatedContent>
        </div>

        <AnimatedContent delay={0.2}>
          <p className="section-subtitle" style={{ marginTop: 26 }}>
            <LinkIcon size={14} /> Server-side settings live in <code>.env</code>: WHIPSKRIBE_API_KEY, GROQ_API_KEY,
            SLACK_WEBHOOK_URL, NOTION_TOKEN. Connections made here are stored on the API and never exposed back to the browser.
          </p>
        </AnimatedContent>
      </section>
    </main>
    </PageTransition>
  );
}
