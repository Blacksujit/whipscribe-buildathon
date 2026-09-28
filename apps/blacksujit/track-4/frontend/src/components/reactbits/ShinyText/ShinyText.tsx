"use client";

/**
 * ShinyText - ported from reactbits.dev (React Bits, MIT), Text Animations.
 * A light sweep travels across the text. Pure CSS animation, no re-renders.
 */

interface ShinyTextProps {
  text: string;
  disabled?: boolean;
  className?: string;
  color?: string;
  shineColor?: string;
  speed?: number;
}

export default function ShinyText({
  text,
  disabled = false,
  className = "",
  color = "#374151",
  shineColor = "#a3dc2d",
  speed = 3.2,
}: ShinyTextProps) {
  const gradient = `linear-gradient(120deg, ${color} 0%, ${color} 38%, ${shineColor} 50%, ${color} 62%, ${color} 100%)`;

  return (
    <span
      className={`shiny-text ${disabled ? "shiny-text-disabled" : ""} ${className}`}
      style={{
        backgroundImage: gradient,
        animationDuration: `${speed}s`,
      }}
    >
      {text}
    </span>
  );
}
