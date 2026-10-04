"use client";

import { useCallback, useEffect, useState, type ReactNode } from "react";
import Navbar from "@/components/Navbar";
import PageHeader from "@/components/PageHeader";
import PageTransition from "@/components/PageTransition";
import AnimatedContent from "@/components/reactbits/AnimatedContent/AnimatedContent";
import { SlackMark, NotionMark, HubSpotMark, WhipScribeMark } from "@/components/BrandIcons";
import { CheckCircleIcon, AlertIcon, SparkIcon } from "@/components/icons";
import { ColdStartNotice, ErrorState, OfflineBanner, PageSkeleton } from "@/components/states";
import {
  getConnections,
  getOauthConfig,
  testWhipscribe,
  connectSlack,
  testToolDelivery,
  disconnectSlack,
  connectNotion,
  disconnectNotion,
  connectHubspot,
  disconnectHubspot,
  setAutoDeliver,
  getOauthUrl,
  getSlackChannels,
  selectSlackChannel,
  getNotionDatabases,
  selectNotionDatabase,
  type ConnectCenterResponse,
  type OauthConfig,
  type ToolConnection,
} from "@/lib/api";

type ToolKey = "slack" | "notion" | "hubspot";
type Notice = { tool: ToolKey | "whipscribe"; ok: boolean; text: string };

function StatusPill({ connected }: { connected: boolean }) {
  return (
    <span className={`pill ${connected ? "pill-on" : "pill-off"}`}>
      <span className="pill-dot" />
      {connected ? "Connected" : "Not connected"}
    </span>
  );
}

function NoticeLine({ notice }: { notice: Notice | null }) {
  if (!notice) return null;
  return (
    <div
      className={notice.ok ? "status-banner status-banner-ok" : "status-banner status-banner-error"}
      role="status"
    >
      {notice.ok ? <CheckCircleIcon size={14} /> : <AlertIcon size={14} />} {notice.text}
    </div>
  );
}

function AutoToggle({
  enabled,
  onToggle,
}: {
  enabled: boolean;
  onToggle: (next: boolean) => void;
}) {
  return (
    <label className="switch">
      <input type="checkbox" checked={enabled} onChange={(event) => onToggle(event.target.checked)} />
      <span className="switch-track" aria-hidden="true">
        <span className="switch-knob" />
      </span>
      <span className="switch-label">Deliver every new scorecard automatically</span>
    </label>
  );
}

function OauthSetup({
  name,
  config,
}: {
  name: string;
  config: OauthConfig["slack"] | undefined;
}) {
  const [open, setOpen] = useState(false);
  const [copied, setCopied] = useState(false);
  if (!config || config.available) return null;
  return (
    <div className="oauth-setup">
      <button type="button" className="link-btn" onClick={() => setOpen((value) => !value)}>
        {open ? "Hide one-click setup" : "Set up one-click connect"}
      </button>
      {open && (
        <div className="oauth-steps">
          <p>
            One-time setup (about two minutes). After this, the button is a single click for everyone -
            no tokens, no copy-paste.
          </p>
          <ol>
            <li>
              Create the {name} app:{" "}
              <a href={config.setup_url} target="_blank" rel="noopener noreferrer">
                {config.setup_url.replace("https://", "")}
              </a>
            </li>
            <li className="oauth-copy-row">
              <span>Add this redirect URL in the app:</span>
              <code>{config.redirect_uri}</code>
              <button
                type="button"
                className="copy-btn"
                onClick={async () => {
                  try {
                    await navigator.clipboard.writeText(config.redirect_uri);
                    setCopied(true);
                    setTimeout(() => setCopied(false), 1500);
                  } catch {
                    setCopied(false);
                  }
                }}
              >
                {copied ? "Copied" : "Copy"}
              </button>
            </li>
            <li className="oauth-copy-row">
              <span>
                Add these two keys to the server&apos;s environment (on Render: Environment, then Save - the
                service restarts itself), and one-click is live for everyone:
              </span>
              <code>{config.env.join(", ")}</code>
              <button
                type="button"
                className="copy-btn"
                onClick={async () => {
                  try {
                    await navigator.clipboard.writeText(config.env.join(", "));
                    setCopied(true);
                    setTimeout(() => setCopied(false), 1500);
                  } catch {
                    setCopied(false);
                  }
                }}
              >
                {copied ? "Copied" : "Copy"}
              </button>
            </li>
          </ol>
        </div>
      )}
    </div>
  );
}

function DeliveryTile({
  tool,
  connection,
  icon,
  valueLine,
  children,
}: {
  tool: ToolKey;
  connection: ToolConnection | undefined;
  icon: ReactNode;
  valueLine: string;
  children: ReactNode;
}) {
  const connected = Boolean(connection?.connected);
  const last = connection?.last_delivery;
  return (
    <div className={`card connect-tile connect-tile-${tool}`}>
      <div className="connect-tile-head">
        <span className="connect-tile-icon" aria-hidden="true">
          {icon}
        </span>
        <div className="connect-tile-title">
          <h2>{tool === "hubspot" ? "HubSpot" : tool === "slack" ? "Slack" : "Notion"}</h2>
          <span className="connect-tile-value">{valueLine}</span>
        </div>
        <StatusPill connected={connected} />
      </div>

      {connected && (
        <div className="connect-tile-meta">
          {connection?.detail && <span className="connect-tile-detail">{connection.detail}</span>}
          <span className="connect-tile-last">
            {last
              ? `Last delivery ${last.status === "ok" ? "delivered" : "failed"} - ${last.created_at || ""}`
              : "No deliveries yet"}
          </span>
        </div>
      )}

      {children}
    </div>
  );
}

export default function ConnectionsPage() {
  const [data, setData] = useState<ConnectCenterResponse | null>(null);
  const [loadError, setLoadError] = useState(false);
  const [retrying, setRetrying] = useState(false);
  const [openForm, setOpenForm] = useState<ToolKey | null>(null);
  const [oauthStage, setOauthStage] = useState<Record<string, "idle" | "waiting" | "pick">>({});
  const [channels, setChannels] = useState<Array<{ id: string; name: string }>>([]);
  const [databases, setDatabases] = useState<Array<{ id: string; title: string }>>([]);
  const [picked, setPicked] = useState("");
  const [busy, setBusy] = useState<string | null>(null);
  const [notice, setNotice] = useState<Notice | null>(null);
  const [oauthConfig, setOauthConfig] = useState<OauthConfig | null>(null);

  const [slackWebhook, setSlackWebhook] = useState("");
  const [notionToken, setNotionToken] = useState("");
  const [notionDatabase, setNotionDatabase] = useState("");
  const [hubspotToken, setHubspotToken] = useState("");

  const applyConnections = useCallback((result: ConnectCenterResponse | null) => {
    setRetrying(false);
    if (result) {
      setData(result);
      setLoadError(false);
    } else {
      setLoadError(true);
    }
  }, []);

  const refresh = useCallback(() => getConnections().then(applyConnections), [applyConnections]);

  useEffect(() => {
    getConnections().then(applyConnections);
    getOauthConfig().then(setOauthConfig).catch(() => setOauthConfig(null));
  }, [applyConnections]);

  useEffect(() => {
    const onMessage = (event: MessageEvent) => {
      const payload = event.data;
      if (!payload || payload.source !== "callcoach-oauth") return;
      const tool = payload.tool as "slack" | "notion" | "hubspot";
      if (payload.status === "ok") {
        if (tool === "hubspot") {
          setNotice({ tool, ok: true, text: "HubSpot connected - scorecard tasks will land in that portal." });
          refresh();
          return;
        }
        setOauthStage((state) => ({ ...state, [tool]: "pick" }));
        setPicked("");
        if (tool === "slack") getSlackChannels().then(setChannels);
        if (tool === "notion") getNotionDatabases().then(setDatabases);
        refresh();
      } else {
        setNotice({ tool, ok: false, text: "Authorization failed - give it another try." });
      }
    };
    window.addEventListener("message", onMessage);
    return () => window.removeEventListener("message", onMessage);
  }, [refresh]);

  async function startOauth(tool: "slack" | "notion" | "hubspot") {
    setBusy(tool);
    const url = await getOauthUrl(tool);
    setBusy(null);
    if (!url) {
      setNotice({
        tool,
        ok: false,
        text: "One-click authorization is not set up on the server yet - use the paste option, or ask the admin to add the client keys.",
      });
      setOpenForm(tool);
      return;
    }
    const popup = window.open(url, "callcoach-oauth", "width=560,height=700");
    if (!popup) {
      setNotice({ tool, ok: false, text: "Your browser blocked the popup - allow popups and retry." });
      return;
    }
    setOauthStage((state) => ({ ...state, [tool]: "waiting" }));
  }

  async function toggleAuto(tool: ToolKey, enabled: boolean) {
    setData((current) =>
      current
        ? {
            ...current,
            [tool]: { ...current[tool], auto: enabled },
          }
        : current
    );
    await setAutoDeliver(tool, enabled);
  }

  async function runTest(tool: ToolKey) {
    setBusy(tool);
    const result = await testToolDelivery(tool);
    setBusy(null);
    setNotice({ tool, ok: result.success, text: result.message || result.error || "Done." });
    refresh();
  }

  async function disconnect(tool: ToolKey) {
    setBusy(tool);
    const result =
      tool === "slack"
        ? await disconnectSlack()
        : tool === "notion"
        ? await disconnectNotion()
        : await disconnectHubspot();
    setBusy(null);
    setNotice({ tool, ok: result.success, text: result.message || result.error || "Disconnected." });
    refresh();
  }

  if (loadError) {
    return (
      <main className="site-shell">
        <Navbar />
        <section className="section-wide section-pad">
          <OfflineBanner onReconnect={refresh} />
          <PageHeader eyebrow="Connections" title="Connect once. Every scorecard lands where your team works." />
          <ErrorState
            title="Could not load your connections."
            body="The dashboard is up; the analysis server is not answering right now. It sleeps on the free tier - give it about 30 seconds. Connection status is never guessed, so nothing is shown until it answers."
            onRetry={() => {
              setRetrying(true);
              refresh();
            }}
            retrying={retrying}
          />
          <ColdStartNotice active={retrying} />
        </section>
      </main>
    );
  }

  if (!data) {
    return (
      <main className="site-shell">
        <Navbar />
        <section className="section-wide section-pad">
          <OfflineBanner />
          <PageSkeleton rows={4} label="Checking your connections" />
          <ColdStartNotice active />
        </section>
      </main>
    );
  }

  return (
    <PageTransition>
    <main className="site-shell">
      <Navbar />
      <section className="section-wide section-pad">
        <OfflineBanner onReconnect={refresh} />
        <PageHeader
          eyebrow="Connect"
          title="Connect once. Every scorecard lands where your team works."
          subtitle="Pick a tool, click connect, and we verify it immediately with a real message or page. No webhook jargon - each step is spelled out, and everything is delivered for real."
        />

        <div className="connect-grid">
          {/* Slack */}
          <AnimatedContent>
            <DeliveryTile
              tool="slack"
              connection={data?.slack}
              icon={<SlackMark />}
              valueLine="Scorecards, commitments and trend summaries posted into a channel you choose."
            >
              {data?.slack.connected ? (
                <>
                  <AutoToggle enabled={data?.slack.auto !== false} onToggle={(next) => toggleAuto("slack", next)} />
                  <div className="connect-actions">
                    <button className="btn-secondary" disabled={busy === "slack"} onClick={() => runTest("slack")}>
                      {busy === "slack" ? "Sending..." : "Send test message"}
                    </button>
                    <button className="btn-secondary" disabled={busy === "slack"} onClick={() => disconnect("slack")}>
                      Disconnect
                    </button>
                  </div>
                </>
              ) : oauthStage.slack === "pick" ? (
                <div className="connect-form">
                  <label htmlFor="slack-channel">Pick the channel</label>
                  <select
                    id="slack-channel"
                    className="settings-input"
                    value={picked}
                    onChange={(event) => setPicked(event.target.value)}
                  >
                    <option value="">Choose a channel...</option>
                    {channels.map((channel) => (
                      <option key={channel.id} value={channel.id}>#{channel.name}</option>
                    ))}
                  </select>
                  <button
                    className="btn-primary"
                    disabled={!picked || busy === "slack"}
                    onClick={async () => {
                      setBusy("slack");
                      const result = await selectSlackChannel(picked);
                      setBusy(null);
                      setNotice({ tool: "slack", ok: result.success, text: result.message || result.error || "Done." });
                      if (result.success) {
                        setOauthStage((state) => ({ ...state, slack: "idle" }));
                        refresh();
                      }
                    }}
                  >
                    {busy === "slack" ? "Posting..." : "Connect this channel"}
                  </button>
                </div>
              ) : oauthStage.slack === "waiting" ? (
                <p className="connect-hint">Waiting for Slack to authorize in the popup...</p>
              ) : (
                <div className="connect-form">
                  {oauthConfig?.slack?.available ? (
                    <button className="btn-primary" disabled={busy === "slack"} onClick={() => startOauth("slack")}>
                      Continue with Slack
                    </button>
                  ) : (
                    <OauthSetup name="Slack" config={oauthConfig?.slack} />
                  )}
                  <button className="link-btn" type="button" onClick={() => setOpenForm(openForm === "slack" ? null : "slack")}>
                    {oauthConfig?.slack?.available ? "or paste a link instead" : "Connect with a link"}
                  </button>
                  {openForm === "slack" && (
                    <div className="connect-paste">
                      <label htmlFor="slack-webhook">The special link Slack gives you</label>
                      <input
                        id="slack-webhook"
                        className="settings-input"
                        type="url"
                        value={slackWebhook}
                        onChange={(event) => setSlackWebhook(event.target.value)}
                        placeholder="https://hooks.slack.com/services/..."
                      />
                      <button
                        className="btn-primary"
                        disabled={!slackWebhook.trim() || busy === "slack"}
                        onClick={async () => {
                          setBusy("slack");
                          const result = await connectSlack(slackWebhook.trim());
                          setBusy(null);
                          setNotice({ tool: "slack", ok: result.success, text: result.message || result.error || "Done." });
                          if (result.success) {
                            setOpenForm(null);
                            setSlackWebhook("");
                            refresh();
                          }
                        }}
                      >
                        {busy === "slack" ? "Connecting..." : "Connect Slack"}
                      </button>
                      <p className="connect-steps">
                        Fastest route:{" "}
                        <a href="https://my.slack.com/services/new/incoming-webhook/" target="_blank" rel="noopener noreferrer">
                          open Slack&apos;s webhook page
                        </a>{" "}
                        - pick the channel, copy the link it shows you, paste it above. We send one test
                        message before saving it.
                      </p>
                    </div>
                  )}
                </div>
              )}
              <NoticeLine notice={notice?.tool === "slack" ? notice : null} />
            </DeliveryTile>
          </AnimatedContent>

          {/* Notion */}
          <AnimatedContent delay={0.06}>
            <DeliveryTile
              tool="notion"
              connection={data?.notion}
              icon={<NotionMark />}
              valueLine="Every scorecard written into a Notion database as a page, with the quotes in context."
            >
              {data?.notion.connected ? (
                <>
                  <AutoToggle enabled={data?.notion.auto !== false} onToggle={(next) => toggleAuto("notion", next)} />
                  <div className="connect-actions">
                    <button className="btn-secondary" disabled={busy === "notion"} onClick={() => runTest("notion")}>
                      {busy === "notion" ? "Writing..." : "Create test page"}
                    </button>
                    <button className="btn-secondary" disabled={busy === "notion"} onClick={() => disconnect("notion")}>
                      Disconnect
                    </button>
                  </div>
                </>
              ) : oauthStage.notion === "pick" ? (
                <div className="connect-form">
                  <label htmlFor="notion-database">Pick the database</label>
                  <select
                    id="notion-database"
                    className="settings-input"
                    value={picked}
                    onChange={(event) => setPicked(event.target.value)}
                  >
                    <option value="">Choose a database...</option>
                    {databases.map((database) => (
                      <option key={database.id} value={database.id}>{database.title}</option>
                    ))}
                  </select>
                  <button
                    className="btn-primary"
                    disabled={!picked || busy === "notion"}
                    onClick={async () => {
                      setBusy("notion");
                      const name = databases.find((database) => database.id === picked)?.title;
                      const result = await selectNotionDatabase(picked, name);
                      setBusy(null);
                      setNotice({ tool: "notion", ok: result.success, text: result.message || result.error || "Done." });
                      if (result.success) {
                        setOauthStage((state) => ({ ...state, notion: "idle" }));
                        refresh();
                      }
                    }}
                  >
                    {busy === "notion" ? "Creating page..." : "Connect this database"}
                  </button>
                  <p className="connect-steps">
                    Nothing in the list? Share a database with the CallCoach integration inside Notion first,
                    then reload this page.
                  </p>
                </div>
              ) : oauthStage.notion === "waiting" ? (
                <p className="connect-hint">Waiting for Notion to authorize in the popup...</p>
              ) : (
                <div className="connect-form">
                  {oauthConfig?.notion?.available ? (
                    <button className="btn-primary" disabled={busy === "notion"} onClick={() => startOauth("notion")}>
                      Continue with Notion
                    </button>
                  ) : (
                    <OauthSetup name="Notion" config={oauthConfig?.notion} />
                  )}
                  <button className="link-btn" type="button" onClick={() => setOpenForm(openForm === "notion" ? null : "notion")}>
                    {oauthConfig?.notion?.available ? "or paste a token instead" : "Connect with a token"}
                  </button>
                  {openForm === "notion" && (
                    <div className="connect-paste">
                      <label htmlFor="notion-token">Integration token</label>
                      <input
                        id="notion-token"
                        className="settings-input"
                        type="password"
                        value={notionToken}
                        onChange={(event) => setNotionToken(event.target.value)}
                        placeholder="ntn_... or secret_..."
                      />
                      <label htmlFor="notion-database-link">Database link</label>
                      <input
                        id="notion-database-link"
                        className="settings-input"
                        type="text"
                        value={notionDatabase}
                        onChange={(event) => setNotionDatabase(event.target.value)}
                        placeholder="Paste the database URL from Notion"
                      />
                      <button
                        className="btn-primary"
                        disabled={!notionToken.trim() || !notionDatabase.trim() || busy === "notion"}
                        onClick={async () => {
                          setBusy("notion");
                          const result = await connectNotion(notionToken.trim(), notionDatabase.trim());
                          setBusy(null);
                          setNotice({ tool: "notion", ok: result.success, text: result.message || result.error || "Done." });
                          if (result.success) {
                            setOpenForm(null);
                            setNotionToken("");
                            setNotionDatabase("");
                            refresh();
                          }
                        }}
                      >
                        {busy === "notion" ? "Connecting..." : "Connect Notion"}
                      </button>
                      <p className="connect-steps">
                        Fastest route:{" "}
                        <a href="https://www.notion.so/my-integrations" target="_blank" rel="noopener noreferrer">
                          create a Notion integration
                        </a>{" "}
                        (one click), copy its token, then Share the database with it and paste the database
                        link above.
                      </p>
                    </div>
                  )}
                </div>
              )}
              <NoticeLine notice={notice?.tool === "notion" ? notice : null} />
            </DeliveryTile>
          </AnimatedContent>

          {/* HubSpot */}
          <AnimatedContent delay={0.12}>
            <DeliveryTile
              tool="hubspot"
              connection={data?.hubspot}
              icon={<HubSpotMark />}
              valueLine="A real CRM task per analyzed call - score, what to fix, commitments, and the report link."
            >
              {data?.hubspot.connected ? (
                <>
                  <AutoToggle enabled={data?.hubspot.auto !== false} onToggle={(next) => toggleAuto("hubspot", next)} />
                  <div className="connect-actions">
                    <button className="btn-secondary" disabled={busy === "hubspot"} onClick={() => runTest("hubspot")}>
                      {busy === "hubspot" ? "Creating..." : "Create test task"}
                    </button>
                    <button className="btn-secondary" disabled={busy === "hubspot"} onClick={() => disconnect("hubspot")}>
                      Disconnect
                    </button>
                  </div>
                </>
              ) : (
                <div className="connect-form">
                  {oauthConfig?.hubspot?.available ? (
                    <button className="btn-primary" disabled={busy === "hubspot"} onClick={() => startOauth("hubspot")}>
                      Continue with HubSpot
                    </button>
                  ) : (
                    <OauthSetup name="HubSpot" config={oauthConfig?.hubspot} />
                  )}
                  <button className="link-btn" type="button" onClick={() => setOpenForm(openForm === "hubspot" ? null : "hubspot")}>
                    {oauthConfig?.hubspot?.available ? "or paste a private-app token instead" : "Connect with a token"}
                  </button>
                  {openForm === "hubspot" && (
                    <div className="connect-paste">
                      <label htmlFor="hubspot-token">Private app token</label>
                      <input
                        id="hubspot-token"
                        className="settings-input"
                        type="password"
                        value={hubspotToken}
                        onChange={(event) => setHubspotToken(event.target.value)}
                        placeholder="pat-..."
                      />
                      <button
                        className="btn-primary"
                        disabled={!hubspotToken.trim() || busy === "hubspot"}
                        onClick={async () => {
                          setBusy("hubspot");
                          const result = await connectHubspot(hubspotToken.trim());
                          setBusy(null);
                          setNotice({ tool: "hubspot", ok: result.success, text: result.message || result.error || "Done." });
                          if (result.success) {
                            setOpenForm(null);
                            setHubspotToken("");
                            refresh();
                          }
                        }}
                      >
                        {busy === "hubspot" ? "Checking..." : "Connect HubSpot"}
                      </button>
                      <p className="connect-steps">
                        Fastest route:{" "}
                        <a href="https://app.hubspot.com/l/private-apps/" target="_blank" rel="noopener noreferrer">
                          open HubSpot private apps
                        </a>{" "}
                        - create one, add the Tasks read+write scope, copy its token, paste it above. We
                        verify it against the live API before saving.
                      </p>
                    </div>
                  )}
                </div>
              )}
              <NoticeLine notice={notice?.tool === "hubspot" ? notice : null} />
            </DeliveryTile>
          </AnimatedContent>
        </div>

        {/* Under the hood */}
        <div className="connect-under">
          <AnimatedContent delay={0.18}>
            <div className="card connect-mini">
              <div className="connect-tile-head">
                <span className="connect-tile-icon" aria-hidden="true"><WhipScribeMark /></span>
                <div className="connect-tile-title">
                  <h2>WhipScribe</h2>
                  <span className="connect-tile-value">
                    Transcription, speakers, timestamps, summaries and key moments for every call.
                  </span>
                </div>
                <StatusPill connected={Boolean(data?.whipscribe.connected)} />
              </div>
              <div className="connect-actions">
                <button
                  className="btn-secondary"
                  disabled={busy === "whipscribe" || !data?.whipscribe.connected}
                  onClick={async () => {
                    setBusy("whipscribe");
                    const result = await testWhipscribe();
                    setBusy(null);
                    setNotice({ tool: "whipscribe", ok: result.success, text: result.message || result.error || "Done." });
                  }}
                >
                  {busy === "whipscribe" ? "Checking..." : "Verify connection"}
                </button>
                {data?.whipscribe.account && <span className="source-note">{data.whipscribe.account}</span>}
                {data?.whipscribe.plan && <span className="source-note">plan: {data.whipscribe.plan}</span>}
              </div>
              <NoticeLine notice={notice?.tool === "whipscribe" ? notice : null} />
            </div>
          </AnimatedContent>

          <AnimatedContent delay={0.24}>
            <div className="card connect-mini">
              <div className="connect-tile-head">
                <span className="connect-tile-icon" aria-hidden="true"><SparkIcon size={22} /></span>
                <div className="connect-tile-title">
                  <h2>AI scoring</h2>
                  <span className="connect-tile-value">Four agents read every transcript. The model runs on the server.</span>
                </div>
                <StatusPill connected={Boolean(data?.llm.key_set)} />
              </div>
              <div className="connect-actions">
                <span className="pill">
                  {data?.llm.provider ? `${data.llm.provider} - ${data.llm.model}` : "No provider set"}
                </span>
              </div>
            </div>
          </AnimatedContent>
        </div>

        <p className="connect-foot">
          Delivery is proven, not promised: every attempt is logged and the last result is shown on each tile.
          Server-side settings live in <code>.env</code> on the API host.
        </p>
      </section>
    </main>
    </PageTransition>
  );
}
