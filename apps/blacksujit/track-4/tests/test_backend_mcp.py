"""WhipScribe MCP client (Streamable HTTP, JSON-RPC 2.0) against recorded SSE replies."""

import json
import os

import pytest
import requests

from src.api import whip_mcp

FIX = os.path.join(os.path.dirname(__file__), "fixtures", "whipscribe")
JOB = "bcfcea2d-b6d7-4cff-b75c-d5e3628ec5e7"
INIT_SSE = (
    'event: message\ndata: {"jsonrpc":"2.0","id":1,"result":{"protocolVersion":"2025-06-18",'
    '"capabilities":{"tools":{"listChanged":false}},"serverInfo":{"name":"whipscribe-mcp-remote","version":"1.13.1"}}}\n\n'
)


def sse(name):
    with open(os.path.join(FIX, name), encoding="utf-8") as f:
        return f.read()


def tools_list_sse():
    with open(os.path.join(FIX, "mcp_tools_list.json"), encoding="utf-8") as f:
        tools = json.load(f)["tools"]
    body = {"jsonrpc": "2.0", "id": 2, "result": {"tools": tools}}
    return "event: message\ndata: " + json.dumps(body) + "\n\n"


class SSEResponse:
    def __init__(self, text, status=200):
        self.status_code = status
        self.text = text
        self.headers = {"Content-Type": "text/event-stream"}

    def json(self):
        return json.loads(self.text)


class FakeServer:
    """Answers by JSON-RPC method / tool name; records requests."""

    def __init__(self, tool_replies):
        self.tool_replies = tool_replies
        self.requests = []

    def __call__(self, url, headers=None, json=None, timeout=None, **kw):
        self.requests.append({"url": url, "headers": headers, "json": json})
        method = json.get("method")
        if method == "initialize":
            return SSEResponse(INIT_SSE)
        if method == "notifications/initialized":
            return SSEResponse("", status=202)
        if method == "tools/list":
            return SSEResponse(tools_list_sse())
        if method == "tools/call":
            reply = self.tool_replies[json["params"]["name"]]
            return SSEResponse(reply(json["params"]["arguments"]) if callable(reply) else reply)
        raise AssertionError(method)


@pytest.fixture(autouse=True)
def reset_tools_cache():
    whip_mcp._TOOLS_CACHE.update({"names": None, "at": 0.0})
    yield


def test_handshake_uses_bearer_auth(monkeypatch):
    server = FakeServer({})
    monkeypatch.setattr(requests, "post", server)
    client = whip_mcp.WhipMCPClient("secret")
    info = client.initialize()
    assert info["name"] == "whipscribe-mcp-remote"
    first = server.requests[0]
    assert first["url"] == "https://whipscribe.com/mcp"
    assert first["headers"]["Authorization"] == "Bearer secret"
    assert "text/event-stream" in first["headers"]["Accept"]
    assert first["json"]["jsonrpc"] == "2.0"


def test_tools_list_has_clip_search(monkeypatch):
    monkeypatch.setattr(requests, "post", FakeServer({}))
    names = {t["name"] for t in whip_mcp.WhipMCPClient("k").list_tools()}
    assert len(names) == 37
    assert {"clips_search_transcript", "clips_get_high_signal", "clips_prepare"} <= names


def test_high_signal_moments_parsed(monkeypatch):
    replies = {"clips_get_high_signal": lambda a: sse(f"mcp_hs_{a['kind']}.sse")}
    monkeypatch.setattr(requests, "post", FakeServer(replies))
    moments, reason = whip_mcp.high_signal_moments("k", JOB)
    assert reason is None and moments
    assert moments == sorted(moments, key=lambda m: m["start"])
    first = moments[0]
    assert first["start"] == 11.22 and first["end"] == 13.32
    assert first["title"] == "May I speak with Janine Correa?"
    assert first["source"] == "whipscribe-mcp" and "question" in first["why"]


def test_high_signal_not_ready_kicks_prepare(monkeypatch):
    server = FakeServer({"clips_get_high_signal": sse("mcp_not_ready.sse"), "clips_prepare": sse("mcp_prepare.sse")})
    monkeypatch.setattr(requests, "post", server)
    moments, reason = whip_mcp.high_signal_moments("k", JOB)
    assert moments == [] and reason == "preparing"
    called = [r["json"]["params"]["name"] for r in server.requests if r["json"].get("method") == "tools/call"]
    assert called == ["clips_get_high_signal", "clips_prepare"]


def test_tool_error_document_raises(monkeypatch):
    monkeypatch.setattr(requests, "post", FakeServer({"clips_get_high_signal": sse("mcp_bad.sse")}))
    with pytest.raises(whip_mcp.WhipMCPError) as info:
        whip_mcp.WhipMCPClient("k").call_tool("clips_get_high_signal", {"job_id": "0", "kind": "hook"})
    assert info.value.code == "not_found"


def test_unauthorized(monkeypatch):
    monkeypatch.setattr(requests, "post", lambda *a, **k: SSEResponse('{"error":"Missing Bearer token"}', status=401))
    with pytest.raises(whip_mcp.WhipMCPError) as info:
        whip_mcp.WhipMCPClient("k").initialize()
    assert info.value.code == "unauthorized"


def test_search_calls_returns_citations(monkeypatch):
    replies = {"clips_search_transcript": lambda a: sse("mcp_search.sse") if a["job_id"] == JOB else sse("mcp_not_ready.sse"),
               "clips_prepare": sse("mcp_prepare.sse")}
    server = FakeServer(replies)
    monkeypatch.setattr(requests, "post", server)
    jobs = [{"job_id": JOB, "meeting_name": "Sample Call ENG MA"}, {"job_id": "other-job", "meeting_name": "Other"}]
    found = whip_mcp.search_calls("k", "Did we guarantee the price?", jobs)
    assert found["searched"] == 2 and found["not_ready"] == ["other-job"]
    assert "price" in found["query"] and "guarantee" in found["query"]
    c = found["citations"][0]
    assert set(c) == {"job_id", "meeting_name", "speaker", "start", "end", "quote"}
    assert c["job_id"] == JOB and c["meeting_name"] == "Sample Call ENG MA"
    assert "guaranteed" in c["quote"]  # best keyword overlap ranks first


def test_query_terms_drop_stopwords():
    assert set(whip_mcp.query_terms("What did we promise about the pricing?")) == {"pricing", "promise"}


def test_search_term_stems_for_substring_search():
    # Live clips_search_transcript: "pricing" -> 0 matches, "pric" -> 3 on a call that says "price".
    assert whip_mcp.search_term("pricing") == "pric"
    assert whip_mcp.search_term("promised") == "promis"
    assert whip_mcp.search_term("discounts") == "discount"
    assert whip_mcp.search_term("process") == "process"
    assert whip_mcp.search_term("price") == "price"
