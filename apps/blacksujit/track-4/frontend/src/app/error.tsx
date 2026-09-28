"use client";

import { useEffect } from "react";
import Link from "next/link";
import Navbar from "@/components/Navbar";

export default function Error({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    console.error(error);
  }, [error]);

  return (
    <main className="site-shell">
      <Navbar />
      <section className="section-wide section-pad">
        <p className="section-eyebrow">Something went wrong</p>
        <h1 className="section-title">This page hit an error.</h1>
        <div className="status-banner status-banner-error">
          {error.message || "An unexpected error occurred."}
        </div>
        <div style={{ display: "flex", gap: "24px", marginTop: "24px" }}>
          <button className="btn-primary" onClick={() => reset()}>Try again</button>
          <Link href="/" className="text-link">Back to home</Link>
        </div>
      </section>
    </main>
  );
}
