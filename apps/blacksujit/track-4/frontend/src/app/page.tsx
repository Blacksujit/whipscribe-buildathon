import Link from "next/link";
import Navbar from "@/components/Navbar";

export default function Home() {
  return (
    <main className="min-h-screen bg-v4-bg text-v4-ink">
      <Navbar />
      <section className="container-960 section mx-auto">
        <h1 className="font-display text-[clamp(44px,_5.6vw,_64px)] leading-[1.04] mb-6">
          Stop watching.<br />
          Start coaching.
        </h1>

        <p className="text-v4-ink-muted mb-12" style={{ fontSize: "var(--text-body)" }}>
          AI-powered meeting quality assurance that tracks trends across your
          library of WhipScribe recordings.
        </p>

        <div className="flex flex-col sm:flex-row gap-4 sm:gap-6 items-start sm:items-center mb-16">
          <Link href="/settings" className="btn-primary">
            Connect WhipScribe
          </Link>
          <span className="text-v4-ink-muted" style={{ fontSize: "var(--text-micro)" }}>
            No credit card. Works with your existing WhipScribe account.
          </span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="card p-6 text-center">
            <div className="text-3xl mb-2">🔒</div>
            <div className="font-medium mb-1">Private</div>
            <p className="text-v4-ink-muted" style={{ fontSize: "var(--text-micro)" }}>
              Your recordings never leave your account.
            </p>
          </div>
          <div className="card p-6 text-center">
            <div className="text-3xl mb-2">⚡</div>
            <div className="font-medium mb-1">Fast</div>
            <p className="text-v4-ink-muted" style={{ fontSize: "var(--text-micro)" }}>
              10x faster than reading transcripts manually.
            </p>
          </div>
          <div className="card p-6 text-center">
            <div className="text-3xl mb-2">🎯</div>
            <div className="font-medium mb-1">Actionable</div>
            <p className="text-v4-ink-muted" style={{ fontSize: "var(--text-micro)" }}>
              Get specific coaching insights, not just scores.
            </p>
          </div>
        </div>
      </section>
    </main>
  );
}
