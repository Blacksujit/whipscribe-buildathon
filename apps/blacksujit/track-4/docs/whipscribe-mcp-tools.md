# WhipScribe MCP tools (live `tools/list`)

Captured 2026-10-03 from `https://whipscribe.com/mcp` (server `whipscribe-mcp-remote` 1.13.1, protocol 2025-06-18) with a real `initialize` -> `tools/list` call.

- Transport: MCP Streamable HTTP, JSON-RPC 2.0; replies arrive as `text/event-stream`. No `Mcp-Session-Id` is issued (stateless).
- Auth: `Authorization: Bearer <WhipScribe API key>`. `X-API-Key` is rejected with `401 MISSING_BEARER` (`resource_metadata` points at `/.well-known/oauth-protected-resource`).
- Tool results: `result.content[0].text` holds a JSON document `{"ok": true, ...}` or `{"ok": false, "error": {"code", "message", "retryable"}}` (e.g. `clips_not_ready`, `not_found`) with `isError: false`.
- `clips_search_transcript` semantics (probed live 2026-10-04): whitespace-separated tokens are OR-ed and each is matched as a substring, so `pricing` finds nothing in a call that says "price" while `pric` finds 3 sentences, and `eligible zzzz` still matches. Griot therefore drops stopwords and trims common suffixes (`search_term()`) before searching. Matches carry `start`/`end` but `speaker: null`; the speaker is filled from the stored diarized transcript when one exists.
- Client: `src/api/whip_mcp.py`. **Used by CallCoach-AI** column marks the tools the app calls.

37 tools:

| Tool | What it does | Used by CallCoach-AI |
|---|---|---|
| `transcribe_url` | Transcribe audio or video from a URL (direct media link, podcast episode, or Creative-Commons YouTube). |  |
| `transcribe_file` | Transcribe a local audio or video file. |  |
| `get_job_status` | Poll the current status of a transcription job by job_id. |  |
| `get_transcript` | Fetch a finished transcript in the requested format. |  |
| `list_recent_jobs` | List jobs submitted by the authenticated caller. |  |
| `transcribe_urls_batch` | Transcribe a list of URLs (YouTube, podcast, direct media) concurrently. |  |
| `library_list_folders` | List the user's library folders, optionally restricted to children of a parent folder. |  |
| `library_create_folder` | Create a new Knowledge folder, optionally under an existing parent. |  |
| `library_get_folder` | Read a single library folder including its items array. |  |
| `library_add_item` | Append an item to a Knowledge folder. |  |
| `library_trash_item` | Move an item to the trash (soft delete). |  |
| `library_restore_item` | Restore a trashed item — clears its deleted_at flag so it shows up in the regular folder again. |  |
| `library_list_trash` | List every trashed item across the user's library, newest in trash first. |  |
| `library_empty_trash` | Permanently delete every trashed item. |  |
| `library_get_graph` | Return the user's whole library as a graph (nodes + links) in one call — cheaper than walking with library_list_folders + library_get_folder. |  |
| `library_share_folder` | Mint a read-only share link for a library folder. |  |
| `list_my_transcripts` | Return the user's recent transcripts from Whipscribe — including ones uploaded via the web UI, not just MCP submissions. |  |
| `rename_transcript` | Set a short, human-readable title for one transcript. |  |
| `list_recipes` | List recipes the user can run. |  |
| `get_recipe` | Fetch one recipe by id, including the full prompt body so you can follow it. |  |
| `create_recipe` | Save a new private recipe (a prompt template) owned by the current user. |  |
| `update_recipe` | Modify a recipe the user owns. |  |
| `delete_recipe` | Delete a recipe the user owns. |  |
| `list_workflows` | List workflows visible to the caller — system / shared / mine. |  |
| `get_workflow` | Fetch one workflow — both the n8n graph (nodes + connections + settings) and the WhipScribe metadata (owner, visibility, tags, uses). |  |
| `create_workflow` | Create a workflow. |  |
| `update_workflow` | Update a workflow. |  |
| `delete_workflow` | Delete a workflow on n8n. |  |
| `run_workflow` | Trigger an execution of a workflow. |  |
| `request_upload_url` | Get a one-time presigned PUT URL to upload a file from the user's machine into the Whipscribe vault. |  |
| `clips_prepare` | Ensure clip-selection features are computed for a transcribed job. | key moments + Griot (kick feature index) |
| `clips_get_summary` | High-level orientation for a prepared job: total duration, sentence count, hook/question/number counts, energy stats, top 5 highest-energy seconds, speakers. |  |
| `clips_search_transcript` | Substring + token search across the transcript's sentences. | Griot /api/ask citations |
| `clips_get_sentences_in_range` | Pull every sentence in [start_s, end_s]. |  |
| `clips_get_high_signal` | Pre-flagged candidate sentences. | report key_moments |
| `clips_render` | Render a 9:16 vertical mp4 from [start_s, end_s] of the source video. |  |
| `list_my_clips` | List the caller's rendered clips, newest first. |  |
