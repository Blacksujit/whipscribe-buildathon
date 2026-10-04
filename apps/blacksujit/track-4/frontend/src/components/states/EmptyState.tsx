import type { ReactNode } from "react";
import { InboxIcon } from "@/components/icons";

interface EmptyStateProps {
  title: string;
  body?: ReactNode;
  icon?: ReactNode;
  action?: ReactNode;
  compact?: boolean;
}

/** Designed "nothing here yet" panel: icon, one-line title, a reason, and the next step. */
export default function EmptyState({ title, body, icon, action, compact }: EmptyStateProps) {
  return (
    <div className={`st-panel st-empty${compact ? " st-compact" : ""}`}>
      <span className="st-icon" aria-hidden="true">
        {icon ?? <InboxIcon size={24} />}
      </span>
      <h2 className="st-title">{title}</h2>
      {body && <p className="st-body">{body}</p>}
      {action && <div className="st-actions">{action}</div>}
    </div>
  );
}
