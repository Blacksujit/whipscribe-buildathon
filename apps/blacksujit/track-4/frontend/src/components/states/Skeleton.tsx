interface SkeletonProps {
  width?: string | number;
  height?: string | number;
  className?: string;
}

/** Single shimmer block. Hidden from assistive tech; pair with a visible status line. */
export function Skeleton({ width = "100%", height = 14, className = "" }: SkeletonProps) {
  return <div className={`skeleton ${className}`} style={{ width, height }} aria-hidden="true" />;
}

/** Page-shaped loading layout: header lines plus a card of rows, matching the loaded layout. */
export function PageSkeleton({ rows = 3, label = "Loading" }: { rows?: number; label?: string }) {
  return (
    <div className="st-skeleton" role="status" aria-live="polite">
      <span className="sr-only">{label}...</span>
      <Skeleton width={110} height={12} className="st-sk-eyebrow" />
      <Skeleton width="min(520px, 80%)" height={34} className="st-sk-title" />
      <Skeleton width="min(380px, 60%)" height={14} />
      <div className="card st-sk-card">
        {Array.from({ length: rows }).map((_, i) => (
          <Skeleton key={i} height={52} className="st-sk-row" />
        ))}
      </div>
    </div>
  );
}

export default Skeleton;
