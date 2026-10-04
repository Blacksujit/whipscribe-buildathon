"use client";

import { useEffect, useRef, useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { motion } from "framer-motion";
import ShinyText from "@/components/reactbits/ShinyText/ShinyText";

const springHover = { type: "spring" as const, stiffness: 100, damping: 20 };

const navItems = [
  { href: "/", label: "Home" },
  { href: "/spotter", label: "Spotter" },
  { href: "/trends", label: "Trends" },
  { href: "/coach", label: "Coach" },
  { href: "/speakers", label: "Speakers" },
  { href: "/connections", label: "Connections" },
];

export default function Navbar() {
  const pathname = usePathname();
  // The menu remembers the path it was opened on, so navigating closes it without an effect.
  const [openedOn, setOpenedOn] = useState<string | null>(null);
  const menuOpen = openedOn !== null && openedOn === pathname;
  const setMenuOpen = (open: boolean | ((current: boolean) => boolean)) => {
    const next = typeof open === "function" ? open(menuOpen) : open;
    setOpenedOn(next ? pathname ?? "" : null);
  };
  const toggleRef = useRef<HTMLButtonElement | null>(null);
  const menuRef = useRef<HTMLDivElement | null>(null);

  // Escape closes the menu and returns focus to the toggle; outside clicks close it too.
  useEffect(() => {
    if (!menuOpen) return;
    const onKey = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        setOpenedOn(null);
        toggleRef.current?.focus();
      }
    };
    const onClick = (event: MouseEvent) => {
      const target = event.target as Node;
      if (menuRef.current?.contains(target) || toggleRef.current?.contains(target)) return;
      setOpenedOn(null);
    };
    document.addEventListener("keydown", onKey);
    document.addEventListener("mousedown", onClick);
    return () => {
      document.removeEventListener("keydown", onKey);
      document.removeEventListener("mousedown", onClick);
    };
  }, [menuOpen]);

  const isActive = (href: string) =>
    pathname === href || (href !== "/" && (pathname ?? "").startsWith(href));

  return (
    <motion.nav
      className="site-nav"
      aria-label="Main"
      initial={{ y: -20, opacity: 0 }}
      animate={{ y: 0, opacity: 1 }}
      transition={springHover}
    >
      <div className="nav-container">
        <Link href="/" className="nav-logo brand-lockup" aria-label="CallCoach-AI, built on WhipScribe">
          <span className="nav-logo-dot" aria-hidden="true">C</span>
          <span>CallCoach-AI</span>
          <span className="brand-x-suffix" aria-hidden="true">
            <ShinyText text="x WhipScribe" speed={4.5} />
          </span>
        </Link>

        <div className="nav-links nav-links-desktop">
          {navItems.map((item) => {
            const active = isActive(item.href);
            return (
              <Link
                key={item.href}
                href={item.href}
                className={`nav-link ${active ? "nav-link-active" : ""}`}
                aria-current={active ? "page" : undefined}
              >
                {item.label}
              </Link>
            );
          })}
        </div>

        <button
          ref={toggleRef}
          type="button"
          className="nav-toggle"
          aria-expanded={menuOpen}
          aria-controls="nav-mobile-menu"
          aria-label={menuOpen ? "Close menu" : "Open menu"}
          onClick={() => setMenuOpen((open) => !open)}
        >
          <span className={`nav-toggle-icon ${menuOpen ? "is-open" : ""}`} aria-hidden="true">
            <span />
            <span />
            <span />
          </span>
        </button>
      </div>

      <div
        ref={menuRef}
        id="nav-mobile-menu"
        className={`nav-mobile ${menuOpen ? "nav-mobile-open" : ""}`}
        hidden={!menuOpen}
      >
        <ul className="nav-mobile-list">
          {navItems.map((item) => {
            const active = isActive(item.href);
            return (
              <li key={item.href}>
                <Link
                  href={item.href}
                  className={`nav-mobile-link ${active ? "nav-mobile-link-active" : ""}`}
                  aria-current={active ? "page" : undefined}
                  onClick={() => setMenuOpen(false)}
                >
                  {item.label}
                </Link>
              </li>
            );
          })}
        </ul>
      </div>
    </motion.nav>
  );
}
