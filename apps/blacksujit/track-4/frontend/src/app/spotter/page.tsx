import type { Metadata } from "next";
import SpotterClient from "./SpotterClient";

export const metadata: Metadata = {
  title: "Spotter · CallCoach-AI x WhipScribe",
  description:
    "Say it before you say it: type or dictate a line and Spotter flags compliance, tension and clarity risks with a safer rewrite.",
};

export default function SpotterPage() {
  return <SpotterClient />;
}
