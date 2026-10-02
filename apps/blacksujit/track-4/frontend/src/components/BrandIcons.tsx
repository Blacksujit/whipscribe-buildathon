// Brand marks for the Connect Center. Simple, recognizable shapes.

export function SlackMark({ size = 26 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" aria-hidden="true">
      <path fill="#36C5F0" d="M9.4 2a2 2 0 0 0-2 2v5a2 2 0 1 0 4 0V4a2 2 0 0 0-2-2Z" />
      <path fill="#2EB67D" d="M22 9.4a2 2 0 0 0-2-2h-5a2 2 0 1 0 0 4h5a2 2 0 0 0 2-2Z" />
      <path fill="#ECB22E" d="M14.6 22a2 2 0 0 0 2-2v-5a2 2 0 1 0-4 0v5a2 2 0 0 0 2 2Z" />
      <path fill="#E01E5A" d="M2 14.6a2 2 0 0 0 2 2h5a2 2 0 1 0 0-4H4a2 2 0 0 0-2 2Z" />
    </svg>
  );
}

export function NotionMark({ size = 26 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" aria-hidden="true">
      <rect x="2" y="2" width="20" height="20" rx="4" fill="#111111" />
      <path
        fill="#ffffff"
        d="M8 17V7h1.9l4.3 6.4V7H16v10h-1.9L9.8 10.5V17H8Z"
      />
    </svg>
  );
}

export function HubSpotMark({ size = 26 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" aria-hidden="true">
      <circle cx="15" cy="14" r="4.4" fill="none" stroke="#FF7A59" strokeWidth="2.4" />
      <circle cx="15" cy="14" r="1.5" fill="#FF7A59" />
      <path d="M4 6v9.5" stroke="#FF7A59" strokeWidth="2.4" strokeLinecap="round" />
      <path d="M4 12.5 10.8 13.2" stroke="#FF7A59" strokeWidth="2.4" strokeLinecap="round" />
      <circle cx="4" cy="4" r="2" fill="#FF7A59" />
    </svg>
  );
}

export function WhipScribeMark({ size = 26 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" aria-hidden="true">
      <rect x="2" y="9" width="3" height="6" rx="1.5" fill="#c5f44f" />
      <rect x="7" y="5" width="3" height="14" rx="1.5" fill="#8ad431" />
      <rect x="12" y="2" width="3" height="20" rx="1.5" fill="#4d9b1f" />
      <rect x="17" y="7" width="3" height="10" rx="1.5" fill="#8ad431" />
    </svg>
  );
}
