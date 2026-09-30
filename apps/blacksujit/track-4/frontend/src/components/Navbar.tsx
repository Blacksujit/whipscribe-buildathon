"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { motion } from "framer-motion";
import ShinyText from "@/components/reactbits/ShinyText/ShinyText";

const springHover = { type: "spring" as const, stiffness: 100, damping: 20 };

export default function Navbar() {
  const pathname = usePathname();

  const navItems = [
    { href: "/", label: "Home" },
    { href: "/trends", label: "Trends" },
    { href: "/coach", label: "Coach" },
    { href: "/assistant", label: "Assistant" },
    { href: "/speakers", label: "Speakers" },
    { href: "/connections", label: "Connections" },
  ];

  return (
    <motion.nav
      className="site-nav"
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

        <div className="nav-links">
          {navItems.map((item) => {
            const isActive =
              pathname === item.href ||
              (item.href !== "/" && pathname.startsWith(item.href));
            return (
              <Link
                key={item.href}
                href={item.href}
                className={`nav-link ${isActive ? "nav-link-active" : ""}`}
              >
                {item.label}
              </Link>
            );
          })}
        </div>
      </div>
    </motion.nav>
  );
}
