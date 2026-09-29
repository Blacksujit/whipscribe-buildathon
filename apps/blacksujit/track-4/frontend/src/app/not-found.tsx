import Link from "next/link";
import Navbar from "@/components/Navbar";

export default function NotFound() {
  return (
    <main className="site-shell">
      <Navbar />
      <section className="section-wide section-pad">
        <p className="section-eyebrow">404</p>
        <h1 className="section-title">That page does not exist.</h1>
        <p className="section-subtitle">Check the address, or head back to your recordings.</p>
        <Link href="/" className="btn-primary">Back to home</Link>
      </section>
    </main>
  );
}
