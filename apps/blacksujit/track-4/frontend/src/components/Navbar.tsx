"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { motion } from "framer-motion";

const springHover = { type: "spring" as const, stiffness: 100, damping: 20 };

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
    <motion.nav
      className="sticky top-0 z-30 bg-paper/95 backdrop-blur-sm border-b border-rule"
      initial={{ y: -20, opacity: 0 }}
      animate={{ y: 0, opacity: 1 }}
      transition={springHover}
    >
      <div className="container-960 mx-auto px-6 py-4 flex items-center justify-between gap-8">
        <Link
          href="/"
          className="text-v4-ink font-semibold tracking-[-0.04em] text-xl"
        >
          whisp<span className="text-[#c5f44b]">·</span>scribe<span className="text-[#c5f44b]"></span> <span className="text-sm align-top opacity-70">x CallCoach-AI</span>
        </Link>
        <div className="hidden md:flex items-center gap-8">
          {navItems.map((item) => {
            const isActive = pathname === item.href;
            return (
              <Link
                key={item.href}
                href={item.href}
                className="relative nav-link text-sm font-medium"
              >
                {item.label}
                {isActive && (
                  <motion.span
                    className="absolute -bottom-1 left-0 right-0 h-0.5 bg-lime rounded-full"
                    layoutId="nav-underline"
                    initial={{ opacity: 0, scale: 0.8 }}
                    animate={{ opacity: 1, scale: 1 }}
                    transition={springHover}
                  />
                )}
              </Link>
            );
          })}
        </div>
        <Link href="/settings" className="btn-primary text-xs px-5 py-2.5">
          Connect source
        </Link>
      </div>
    </motion.nav>
  );
}