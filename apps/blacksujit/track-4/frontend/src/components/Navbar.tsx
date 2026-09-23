"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

export default function Navbar() {
  const pathname = usePathname();

  const navItems = [
    { href: "/", label: "Meetings" },
    { href: "/trends", label: "Trends" },
    { href: "/speakers", label: "Speakers" },
    { href: "/coach", label: "Coach" },
    { href: "/settings", label: "Settings" },
  ];

  return (
    <nav className="bg-v4-bg border-b" style={{ borderColor: "var(--color-v4-border)" }}>
      <div className="container-960 mx-auto px-6 py-4 flex items-center justify-between">
        <Link
          href="/"
          className="text-v4-ink font-semibold"
          style={{ fontSize: "var(--text-body)" }}
        >
          CallCoach AI
        </Link>
        <div className="flex gap-8">
          {navItems.map((item) => (
            <Link
              key={item.href}
              href={item.href}
              className={`nav-link ${pathname === item.href ? "nav-link-active" : ""}`}
            >
              {item.label}
            </Link>
          ))}
        </div>
      </div>
    </nav>
  );
}
