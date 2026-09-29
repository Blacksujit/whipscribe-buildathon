"use client";

import { motion } from "framer-motion";
import CountUp from "@/components/reactbits/CountUp/CountUp";

interface ScoreRingProps {
  score: number;
  size?: number;
  label?: string;
}

function ringColor(score: number): string {
  if (score >= 80) return "var(--cat-ok)";
  if (score >= 60) return "var(--color-7)";
  if (score >= 40) return "var(--accent)";
  return "var(--cat-compliance)";
}

/** Animated radial score gauge. */
export default function ScoreRing({ score, size = 180, label }: ScoreRingProps) {
  const stroke = size >= 150 ? 12 : 9;
  const radius = (size - stroke) / 2;
  const circumference = 2 * Math.PI * radius;
  const clamped = Math.max(0, Math.min(100, score));
  const color = ringColor(clamped);

  return (
    <div className="score-ring" style={{ width: size, height: size }}>
      <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`} role="img" aria-label={`Score ${clamped} out of 100`}>
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke="var(--rule)"
          strokeWidth={stroke}
        />
        <motion.circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke={color}
          strokeWidth={stroke}
          strokeLinecap="round"
          strokeDasharray={circumference}
          initial={{ strokeDashoffset: circumference }}
          animate={{ strokeDashoffset: circumference * (1 - clamped / 100) }}
          transition={{ duration: 1.1, ease: [0.22, 0.61, 0.36, 1], delay: 0.15 }}
          transform={`rotate(-90 ${size / 2} ${size / 2})`}
        />
      </svg>
      <div className="score-ring-center">
        <span className="score-ring-value">
          <CountUp from={0} to={clamped} duration={1.4} delay={0.15} />
        </span>
        <span className="score-ring-total">/100</span>
        {label && <span className="score-ring-label">{label}</span>}
      </div>
    </div>
  );
}
