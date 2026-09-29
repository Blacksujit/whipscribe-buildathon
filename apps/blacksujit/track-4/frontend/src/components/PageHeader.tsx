"use client";

import type { ReactNode } from "react";
import { motion } from "framer-motion";

const springReveal = { type: "spring" as const, stiffness: 200, damping: 20 };

interface PageHeaderProps {
  eyebrow: string;
  title: string;
  subtitle?: string;
  actions?: ReactNode;
}

/** Consistent page header used by every dashboard page. */
export default function PageHeader({ eyebrow, title, subtitle, actions }: PageHeaderProps) {
  return (
    <motion.header
      className="page-header"
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={springReveal}
    >
      <div className="page-header-copy">
        <p className="section-eyebrow">{eyebrow}</p>
        <h1 className="section-title">{title}</h1>
        {subtitle && <p className="section-subtitle">{subtitle}</p>}
      </div>
      {actions && <div className="page-header-actions">{actions}</div>}
    </motion.header>
  );
}
