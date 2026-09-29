"use client";

/**
 * AnimatedContent - ported from reactbits.dev (React Bits, MIT), Animations.
 * Scroll-triggered reveal with spring physics.
 */

import { motion } from "framer-motion";
import type { ReactNode } from "react";

interface AnimatedContentProps {
  children: ReactNode;
  className?: string;
  distance?: number;
  delay?: number;
  direction?: "vertical" | "horizontal";
  duration?: number;
}

export default function AnimatedContent({
  children,
  className = "",
  distance = 24,
  delay = 0,
  direction = "vertical",
  duration = 0.6,
}: AnimatedContentProps) {
  const offset = direction === "vertical" ? { y: distance } : { x: distance };

  return (
    <motion.div
      className={className}
      initial={{ opacity: 0, ...offset }}
      whileInView={{ opacity: 1, x: 0, y: 0 }}
      viewport={{ once: true, amount: 0.2 }}
      transition={{ type: "spring", stiffness: 90, damping: 20, delay, duration }}
    >
      {children}
    </motion.div>
  );
}
