/**
 * CallCoach-AI icon set - clean 1.5px stroke SVGs that replace emoji glyphs.
 * All icons inherit currentColor and size from CSS (default 20px).
 */

interface IconProps {
  size?: number;
  className?: string;
}

const base = (size: number) => ({
  width: size,
  height: size,
  viewBox: "0 0 24 24",
  fill: "none",
  stroke: "currentColor",
  strokeWidth: 1.5,
  strokeLinecap: "round" as const,
  strokeLinejoin: "round" as const,
  "aria-hidden": true,
});

export function ShieldCheckIcon({ size = 20, className }: IconProps) {
  return (
    <svg {...base(size)} className={className}>
      <path d="M12 3l7 3v5c0 4.5-3 8-7 10-4-2-7-5.5-7-10V6l7-3z" />
      <path d="M9 12l2 2 4-4" />
    </svg>
  );
}

export function WaveformIcon({ size = 20, className }: IconProps) {
  return (
    <svg {...base(size)} className={className}>
      <path d="M3 12h2l2-6 3 12 3-9 2 5 2-3h4" />
    </svg>
  );
}

export function CrosshairIcon({ size = 20, className }: IconProps) {
  return (
    <svg {...base(size)} className={className}>
      <circle cx="12" cy="12" r="8" />
      <path d="M12 3v3M12 18v3M3 12h3M18 12h3" />
      <circle cx="12" cy="12" r="2.5" />
    </svg>
  );
}

export function ListChecksIcon({ size = 20, className }: IconProps) {
  return (
    <svg {...base(size)} className={className}>
      <path d="M4 6l1.5 1.5L8 5" />
      <path d="M4 13l1.5 1.5L8 12" />
      <path d="M4 20l1.5 1.5L8 19" />
      <path d="M12 7h8M12 14h8M12 21h8" />
    </svg>
  );
}

export function UploadIcon({ size = 20, className }: IconProps) {
  return (
    <svg {...base(size)} className={className}>
      <path d="M12 16V4" />
      <path d="M7 9l5-5 5 5" />
      <path d="M4 16v3a1 1 0 001 1h14a1 1 0 001-1v-3" />
    </svg>
  );
}

export function TrendUpIcon({ size = 20, className }: IconProps) {
  return (
    <svg {...base(size)} className={className}>
      <path d="M3 17l6-6 4 4 7-7" />
      <path d="M15 8h5v5" />
    </svg>
  );
}

export function UsersIcon({ size = 20, className }: IconProps) {
  return (
    <svg {...base(size)} className={className}>
      <circle cx="9" cy="8" r="3.25" />
      <path d="M3.5 19c.6-3 2.8-4.5 5.5-4.5S13.9 16 14.5 19" />
      <path d="M16 5.5a3 3 0 010 5.5M17.5 19c-.3-2-1.1-3.5-2.3-4.4 2.3-.2 4.5 1 5.3 4.4" />
    </svg>
  );
}

export function SlidersIcon({ size = 20, className }: IconProps) {
  return (
    <svg {...base(size)} className={className}>
      <path d="M4 8h10M18 8h2M4 16h2M10 16h10" />
      <circle cx="16" cy="8" r="2" />
      <circle cx="8" cy="16" r="2" />
    </svg>
  );
}

export function InboxIcon({ size = 20, className }: IconProps) {
  return (
    <svg {...base(size)} className={className}>
      <path d="M4 13l2-8h12l2 8v5a1 1 0 01-1 1H5a1 1 0 01-1-1v-5z" />
      <path d="M4 13h4l1 2h6l1-2h4" />
    </svg>
  );
}

export function AlertIcon({ size = 20, className }: IconProps) {
  return (
    <svg {...base(size)} className={className}>
      <path d="M12 4l9 16H3l9-16z" />
      <path d="M12 10v4M12 17.5v.01" />
    </svg>
  );
}

export function CheckCircleIcon({ size = 20, className }: IconProps) {
  return (
    <svg {...base(size)} className={className}>
      <circle cx="12" cy="12" r="8.5" />
      <path d="M8.5 12.5l2.5 2.5 4.5-5" />
    </svg>
  );
}

export function ExternalLinkIcon({ size = 20, className }: IconProps) {
  return (
    <svg {...base(size)} className={className}>
      <path d="M14 5h5v5" />
      <path d="M19 5l-8 8" />
      <path d="M19 14v5a1 1 0 01-1 1H6a1 1 0 01-1-1V6a1 1 0 011-1h5" />
    </svg>
  );
}
