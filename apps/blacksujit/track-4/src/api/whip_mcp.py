"""Minimal client for the hosted WhipScribe MCP server.

Endpoint: https://whipscribe.com/mcp (MCP Streamable HTTP, JSON-RPC 2.0).
Auth: ``Authorization: Bearer <WhipScribe API key>`` - the server answers
401 MISSING_BEARER to an X-API-Key header. Responses arrive as
``text/event-stream`` (one ``data:`` line per JSON-RPC message) or plain JSON.
Tool results wrap a JSON document in ``result.content[0].text`` of the shape
``{"ok": true, ...}`` or ``{"ok": false, "error": {"code", "message"}}``.

Tools used here (all real, discovered with tools/list - see
docs/whipscribe-mcp-tools.md):
  clips_prepare            kick the one-time sentence/feature index for a job
  clips_get_high_signal    pre-flagged hook / question / number sentences
  clips_search_transcript  token search over a job's sentences (Griot evidence)
"""

import json
import re
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests

MCP_URL = "https://whipscribe.com/mcp"
PROTOCOL_VERSION = "2025-06-18"
CLIENT_INFO = {"name": "callcoach-ai", "version": "1.0"}


class WhipMCPError(RuntimeError):
    """Transport, protocol or tool-level failure talking to the MCP server."""

    def __init__(self, message, code=None):
        super().__init__(message)
        self.code = code


def _parse_body(resp):
    """Return the JSON-RPC message from a JSON or SSE response body."""
    ctype = resp.headers.get("Content-Type", "")
    text = resp.text or ""
    if "text/event-stream" in ctype or text.lstrip().startswith("event:") or text.lstrip().startswith("data:"):
        messages = []
        for line in text.splitlines():
            if line.startswith("data:"):
                chunk = line[5:].strip()
                if chunk:
                    try:
                        messages.append(json.loads(chunk))
                    except ValueError:
                        continue
        # The response to our request is the message carrying an id.
        for message in messages:
            if isinstance(message, dict) and ("result" in message or "error" in message):
                return message
        if messages:
            return messages[-1]
        raise WhipMCPError("Empty event stream from WhipScribe MCP", code="empty_response")
    try:
        return resp.json()
    except ValueError as exc:
        raise WhipMCPError(f"Non-JSON response from WhipScribe MCP: {text[:120]}", code="bad_response") from exc


class WhipMCPClient:
    """initialize -> tools/list -> tools/call over Streamable HTTP."""

    def __init__(self, api_key, url=MCP_URL, timeout=30):
        if not api_key:
            raise WhipMCPError("No WhipScribe API key for the MCP server", code="no_api_key")
        self.api_key = api_key
        self.url = url
        self.timeout = timeout
        self.session_id = None
        self.server_info = None
        self._next_id = 0
        self._lock = threading.Lock()
        self._initialized = False

    def _id(self):
        with self._lock:
            self._next_id += 1
            return self._next_id

    def _post(self, payload, timeout=None):
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream",
            "MCP-Protocol-Version": PROTOCOL_VERSION,
        }
        if self.session_id:
            headers["Mcp-Session-Id"] = self.session_id
        try:
            resp = requests.post(self.url, headers=headers, json=payload, timeout=timeout or self.timeout)
        except requests.exceptions.RequestException as exc:
            raise WhipMCPError(f"WhipScribe MCP unreachable: {type(exc).__name__}", code="unreachable") from exc
        if resp.status_code == 401:
            raise WhipMCPError("WhipScribe MCP rejected the API key (401)", code="unauthorized")
        if resp.status_code == 202 and "id" not in payload:
            return None  # notification accepted
        if resp.status_code >= 400:
            raise WhipMCPError(f"WhipScribe MCP returned HTTP {resp.status_code}", code=f"http_{resp.status_code}")
        sid = resp.headers.get("Mcp-Session-Id")
        if sid:
            self.session_id = sid
        if "id" not in payload:
            return None
        message = _parse_body(resp)
        if isinstance(message, dict) and message.get("error"):
            err = message["error"]
            raise WhipMCPError(f"MCP error: {err.get('message')}", code=str(err.get("code")))
        return (message or {}).get("result")

    def initialize(self):
        if self._initialized:
            return self.server_info
        result = self._post({
            "jsonrpc": "2.0",
            "id": self._id(),
            "method": "initialize",
            "params": {"protocolVersion": PROTOCOL_VERSION, "capabilities": {}, "clientInfo": CLIENT_INFO},
        })
        self.server_info = (result or {}).get("serverInfo")
        try:
            self._post({"jsonrpc": "2.0", "method": "notifications/initialized"})
        except WhipMCPError:
            pass  # stateless servers may not care about the notification
        self._initialized = True
        return self.server_info

    def list_tools(self):
        self.initialize()
        result = self._post({"jsonrpc": "2.0", "id": self._id(), "method": "tools/list", "params": {}})
        return (result or {}).get("tools", [])

    def call_tool(self, name, arguments, timeout=None):
        """Call a tool and return its decoded JSON document.

        Raises WhipMCPError when the transport fails, the result is flagged
        isError, or the tool's document says {"ok": false}.
        """
        self.initialize()
        result = self._post(
            {"jsonrpc": "2.0", "id": self._id(), "method": "tools/call",
             "params": {"name": name, "arguments": arguments}},
            timeout=timeout,
        )
        result = result or {}
        doc = result.get("structuredContent")
        if doc is None:
            texts = [c.get("text", "") for c in result.get("content", []) if isinstance(c, dict) and c.get("type") == "text"]
            raw = "".join(texts)
            try:
                doc = json.loads(raw) if raw else {}
            except ValueError:
                doc = {"ok": not result.get("isError"), "text": raw}
        if result.get("isError") and not (isinstance(doc, dict) and doc.get("error")):
            raise WhipMCPError(f"Tool {name} failed", code="tool_error")
        if isinstance(doc, dict) and doc.get("ok") is False:
            err = doc.get("error") or {}
            raise WhipMCPError(err.get("message") or f"Tool {name} failed", code=err.get("code") or "tool_error")
        return doc


# ----------------------------------------------------------------- tools/list cache

_TOOLS_CACHE = {"names": None, "at": 0.0}
_TOOLS_TTL = 3600


def available_tools(client):
    """Tool names advertised by the server (cached for an hour)."""
    now = time.time()
    if _TOOLS_CACHE["names"] is not None and now - _TOOLS_CACHE["at"] < _TOOLS_TTL:
        return _TOOLS_CACHE["names"]
    names = {tool.get("name") for tool in client.list_tools() if isinstance(tool, dict)}
    _TOOLS_CACHE.update({"names": names, "at": now})
    return names


# ------------------------------------------------------------------- key moments

def high_signal_moments(api_key, job_id, kinds=("hook", "question", "number"), limit=5, client=None):
    """Key moments via clips_get_high_signal. Returns (moments, reason | None).

    When the job's clip features are not computed yet, clips_prepare is kicked
    (idempotent, ~30-60 s server side) and ([], "preparing") is returned so
    the caller can say so instead of showing an empty panel as if nothing
    happened.
    """
    from src.api.whip_api import REASON_NOT_READY, REASON_UNAVAILABLE, _dedupe_moments, parse_moments

    try:
        client = client or WhipMCPClient(api_key, timeout=15)
        moments = []
        for kind in kinds:
            try:
                doc = client.call_tool("clips_get_high_signal", {"job_id": job_id, "kind": kind, "limit": limit})
            except WhipMCPError as exc:
                if exc.code == "clips_not_ready":
                    try:
                        client.call_tool("clips_prepare", {"job_id": job_id})
                    except WhipMCPError:
                        pass
                    return [], REASON_NOT_READY
                raise
            for moment in parse_moments(doc, source="whipscribe-mcp"):
                if moment["why"] == "high-signal sentence":
                    moment["why"] = kind
                moments.append(moment)
        return _dedupe_moments(moments, limit), None
    except WhipMCPError as exc:
        return [], f"{REASON_UNAVAILABLE}: {exc.code or exc}"


# ------------------------------------------------------------ Griot retrieval

_STOPWORDS = set("""
a an and are as at be been but by can could did do does for from had has have how i if in into is it its
me my of on or our should so than that the their them then there these they this to was we were what
when where which who why will with would you your about across any all call calls did didn't ever
tell show give find list get many much most more said say says times time over us
anyone someone anybody somebody everyone ever never
""".split())


def query_terms(question, max_terms=4):
    """Keywords for a token search: drop stopwords, keep order, prefer longer words."""
    words = re.findall(r"[A-Za-z0-9$%][A-Za-z0-9$%'.-]*", question or "")
    seen = []
    for word in words:
        w = word.lower().strip(".'")
        if len(w) < 3 or w in _STOPWORDS or w in seen:
            continue
        seen.append(w)
    seen.sort(key=lambda w: -len(w))
    return seen[:max_terms]


def search_term(term):
    """Light stem for clips_search_transcript, which matches substrings.

    Real behaviour (2026-10): the tool ORs whitespace-separated tokens and
    matches each as a substring, so "pricing" finds nothing in a call that
    says "price" while "pric" finds it. Common English suffixes are trimmed.
    """
    for suffix, keep in (("ing", 4), ("ed", 4), ("es", 4), ("s", 4)):
        if term.endswith(suffix) and len(term) - len(suffix) >= keep:
            if suffix == "s" and term.endswith("ss"):
                break
            return term[: -len(suffix)]
    return term


def search_calls(api_key, question, jobs, per_call=3, max_calls=8, client=None, deadline_s=20):
    """Cross-call evidence: clips_search_transcript over each stored call.

    ``jobs`` is a list of {"job_id", "meeting_name"}. Returns a dict:
    {"citations": [{job_id, meeting_name, speaker, start, end, quote}],
     "searched": n, "not_ready": [job_id...], "errors": [code...]}.
    Raises WhipMCPError only when the server cannot be used at all
    (no key, auth failure, unreachable, tool missing).
    """
    terms = query_terms(question)
    if not terms:
        return {"citations": [], "searched": 0, "not_ready": [], "errors": ["no_terms"], "query": ""}
    stems = [search_term(t) for t in terms]
    query = " ".join(dict.fromkeys(stems))
    client = client or WhipMCPClient(api_key)
    if "clips_search_transcript" not in available_tools(client):
        raise WhipMCPError("WhipScribe MCP has no clips_search_transcript tool", code="tool_missing")

    jobs = [j for j in jobs if j.get("job_id")][:max_calls]
    citations, not_ready, errors = [], [], []

    def one(job):
        try:
            doc = client.call_tool(
                "clips_search_transcript",
                {"job_id": job["job_id"], "query": query, "limit": per_call},
                timeout=deadline_s,
            )
            return job, doc, None
        except WhipMCPError as exc:
            return job, None, exc

    fatal = None
    with ThreadPoolExecutor(max_workers=min(8, max(1, len(jobs)))) as pool:
        futures = [pool.submit(one, job) for job in jobs]
        try:
            finished = list(as_completed(futures, timeout=deadline_s + 5))
        except TimeoutError:
            finished = [f for f in futures if f.done()]
            errors.append("timeout")
        for future in finished:
            job, doc, exc = future.result()
            if exc is not None:
                if exc.code == "clips_not_ready":
                    not_ready.append(job["job_id"])
                    try:
                        client.call_tool("clips_prepare", {"job_id": job["job_id"]}, timeout=10)
                    except WhipMCPError:
                        pass
                elif exc.code in ("unauthorized", "unreachable"):
                    fatal = exc
                else:
                    errors.append(str(exc.code))
                continue
            for match in (doc or {}).get("matches", []) or []:
                text = str(match.get("text") or "").strip()
                if not text or match.get("start") is None:
                    continue
                citations.append({
                    "job_id": job["job_id"],
                    "meeting_name": job.get("meeting_name") or job["job_id"][:8],
                    "speaker": match.get("speaker"),
                    "start": round(float(match["start"]), 2),
                    "end": round(float(match["end"]), 2) if match.get("end") is not None else None,
                    "quote": text[:280],
                    "_rank": _overlap(text, stems),
                })
    if fatal is not None and not citations:
        raise fatal
    citations.sort(key=lambda c: -c["_rank"])
    for c in citations:
        c.pop("_rank", None)
    return {"citations": citations[:12], "searched": len(jobs), "not_ready": not_ready, "errors": errors, "query": query}


def _overlap(text, terms):
    low = (text or "").lower()
    return sum(1 for t in terms if t in low)
