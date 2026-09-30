"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { getConnections, type ConnectCenterResponse } from "@/lib/api";
import { SlackMark, NotionMark, HubSpotMark } from "@/components/BrandIcons";

const TOOLS = [
  { key: "slack", name: "Slack", Mark: SlackMark },
  { key: "notion", name: "Notion", Mark: NotionMark },
  { key: "hubspot", name: "HubSpot", Mark: HubSpotMark },
] as const;

export default function ConnectedTools() {
  const [data, setData] = useState<ConnectCenterResponse | null>(null);
  const [failed, setFailed] = useState(false);

  useEffect(() => {
    getConnections()
      .then((result) => {
        if (result) setData(result);
        else setFailed(true);
      })
      .catch(() => setFailed(true));
  }, []);

  // Hidden while loading or when the backend is unreachable - never claim a false state.
  if (failed || !data) return null;

  const connectedCount = TOOLS.filter((tool) => data[tool.key]?.connected).length;

  return (
    <section className="connected-strip" aria-label="Connected delivery tools">
      <span className="connected-strip-label">
        {connectedCount > 0 ? "Every scorecard delivers to" : "Deliver scorecards to"}
      </span>
      <div className="connected-tools">
        {TOOLS.map(({ key, name, Mark }) => {
          const tool = data[key];
          const connected = Boolean(tool?.connected);
          const last = tool?.last_delivery;
          const tip = connected
            ? `${name}: connected${tool?.mode === "oauth" ? " (one-click)" : ""}${
                last ? ` - last delivery ${last.status === "ok" ? "succeeded" : "failed"}` : " - no deliveries yet"
              }`
            : `${name}: not connected - open the Connect Center to add it`;
          return (
            <Link
              key={key}
              href="/connections"
              className={`connected-tool ${connected ? "connected-tool-on" : "connected-tool-off"}`}
              title={tip}
              aria-label={tip}
            >
              <span className="connected-tool-mark" aria-hidden="true">
                <Mark size={22} />
              </span>
              <span className="connected-tool-name">{name}</span>
              <span className={`connected-tool-dot ${connected ? "connected-tool-dot-on" : ""}`} aria-hidden="true" />
            </Link>
          );
        })}
      </div>
      <Link href="/connections" className="connected-strip-manage">
        {connectedCount === TOOLS.length ? "Manage" : "Connect more"}
      </Link>
    </section>
  );
}
