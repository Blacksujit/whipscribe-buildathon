"use client";

import { useEffect, useState } from "react";

// Small fetch layer for the first-run + report surfaces. Unlike lib/api.ts it
// keeps the HTTP status and tells a network failure (offline / server
// unreachable) apart from an HTTP error, so the UI can show an honest state.

export type FetchResult<T> =
  | { ok: true; status: number; data: T }
  | { ok: false; status: number; error: string; network: boolean; data?: Record<string, unknown> };

export const NETWORK_FAIL_EVENT = "callcoach:network-fail";
export const NETWORK_OK_EVENT = "callcoach:network-ok";
export const RETRY_EVENT = "callcoach:retry";

function emit(name: string) {
  if (typeof window !== "undefined") window.dispatchEvent(new CustomEvent(name));
}

export async function fetchJson<T>(url: string, init?: RequestInit, timeoutMs = 90000): Promise<FetchResult<T>> {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);
  try {
    const res = await fetch(url, { ...init, signal: controller.signal });
    const body = (await res.json().catch(() => ({}))) as Record<string, unknown>;
    emit(NETWORK_OK_EVENT);
    if (!res.ok) {
      const error =
        (typeof body.error === "string" && body.error) ||
        (res.status >= 500
          ? `The analysis server answered with HTTP ${res.status}. It may still be starting up.`
          : `HTTP ${res.status}`);
      return { ok: false, status: res.status, error, network: false, data: body };
    }
    return { ok: true, status: res.status, data: body as T };
  } catch (err) {
    const aborted = err instanceof DOMException && err.name === "AbortError";
    if (!aborted) emit(NETWORK_FAIL_EVENT);
    return {
      ok: false,
      status: 0,
      network: !aborted,
      error: aborted
        ? "The analysis server did not answer in time."
        : typeof navigator !== "undefined" && !navigator.onLine
        ? "You're offline."
        : "Could not reach the analysis server.",
    };
  } finally {
    clearTimeout(timer);
  }
}

/** True once `active` has been true for `delayMs` - used for the cold-start hint. */
export function useSlowHint(active: boolean, delayMs = 3000): boolean {
  const [slow, setSlow] = useState(false);
  useEffect(() => {
    if (!active) return;
    const timer = setTimeout(() => setSlow(true), delayMs);
    return () => {
      clearTimeout(timer);
      setSlow(false);
    };
  }, [active, delayMs]);
  return active && slow;
}

/** Re-run `fn` when the visitor presses Retry in the offline banner or comes back online. */
export function useRetrySignal(fn: () => void) {
  useEffect(() => {
    const handler = () => fn();
    window.addEventListener(RETRY_EVENT, handler);
    window.addEventListener("online", handler);
    return () => {
      window.removeEventListener(RETRY_EVENT, handler);
      window.removeEventListener("online", handler);
    };
  }, [fn]);
}

export function requestRetry() {
  emit(RETRY_EVENT);
}

export function fmtClock(seconds?: number | null): string {
  const s = Math.max(0, Math.floor(seconds || 0));
  const h = Math.floor(s / 3600);
  const m = Math.floor(s / 60) % 60;
  const sec = String(s % 60).padStart(2, "0");
  return h > 0 ? `${h}:${String(m).padStart(2, "0")}:${sec}` : `${m}:${sec}`;
}
