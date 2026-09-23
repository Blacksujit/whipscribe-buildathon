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
    <nav className="sticky top-0 z-20 bg-v4-bg/95 backdrop-blur border-b">
      <div className="container-960 mx-auto px-6 py-5 flex items-center justify-between gap-8">
        <Link
          href="/"
          className="text-v4-ink font-semibold tracking-[-0.04em]"
          style={{ fontSize: "20px" }}
        >
          whipscribe<span className="text-[#a9dc28]">.</span>
        </Link>
        <div className="hidden md:flex items-center gap-7">
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
        <Link href="/settings" className="btn-primary hidden sm:inline-flex">Connect source</Link>
      </div>
    </nav>
  );
}
