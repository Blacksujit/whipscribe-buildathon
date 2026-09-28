# WhipScribe Buildathon

**A hiring challenge, open now.** Show us what you have built, find what is
wrong with a live product, build something on it if you want — and the best
person gets a founding engineer job. Immediate hire, fully remote.

## Who we are looking for

Four kinds of people, in this order:

| | Who | We see it in |
|---|---|---|
| 1 | Someone with a real eye for **UI and UX** | Track 1, Challenge 01, every screen you ship |
| 2 | Someone who **builds well with AI tools** | Your commits and README: what you kept, what you dropped |
| 3 | Someone who **takes a feature all the way to a customer** | Finishing; apps you have shipped; someone else using your work |
| 4 | Someone who **sees what a user needs and puts it in their hands** | Track 4, and the vision you write for it |

Above all: **huge self-drive.** You saw this, you started, nobody had to ask.

## What WhipScribe is

WhipScribe turns recordings into things people can use. Upload a file,
paste a link (YouTube, podcast, Drive, Dropbox) or record in the browser, and
get back:

- **Transcripts** in 100+ languages, with speaker labels and timestamps, in
  every export format.
- **Summaries, topics and key quotes** for every recording.
- **AI chat over your recordings:** ask a question of one file or of the whole
  library and get the answer with its evidence — the speaker, the recording,
  the exact second — and click to hear it.
- **Audio intelligence:** search across everything you have transcribed by
  what was actually said, quizzes and study help from lectures and videos,
  insights pulled from meetings, interviews and calls.
- **A library** of everything you have transcribed, organised in folders, that
  you own and can delete any time.

Try it at [whipscribe.com](https://whipscribe.com). The same abilities are
open to builders through the public [API](https://whipscribe.com/docs) and
the [MCP server](https://whipscribe.com/claude), which gives any AI assistant
(Claude, Cursor, Perplexity and others) the full set of tools: transcribe,
summarise, ask, search, manage the library.

We are a small team, moving fast, with real customers. The next person in
will own real parts of this product from their first weeks.

## What you win

**A full-time job. Immediate hire — we make the offer as soon as we see the
right person.**

| | |
|---|---|
| Role | **Founding Software Engineer** at WhipScribe / Neugence — a core member of a small team, not employee number two hundred |
| Where | **Fully remote** |
| Pay | **₹6–10 LPA, negotiable** with what you bring and what you take on |
| Day one | You ship to real customers in your first weeks; what you build is yours to own |

## The ladder

| Step | What you do | What happens |
|---|---|---|
| 1 | **Track 0** — open a pull request with your track record: LinkedIn, repos, shipped apps, wins, teams | You are on the [leaderboard](https://whipscribe.com/buildathon); we check every link; you get the 7-day API credit coupon |
| 2 | **Track 1** — use whipscribe.com on your phone and laptop, file what is wrong, propose fixes | Reviewers score it; your rank appears |
| 3 | **Pick a build track** (2, 3 or 4), or more than one | Same: reviewed, scored, ranked |
| 4 | Stand out | We invite you to work with us for a few weeks on the real product — **paid** — so both sides see the fit |
| 5 | Fit | **The offer.** |

Steps 1 and 2 are required. Step 3 is where you choose. You can stop at any
step; say why.

## The tracks

| | Track | |
|---|---|---|
| 0 | [Show us what you already have](#track-0--show-us-what-you-already-have) — a pull request with your LinkedIn, repos, shipped apps, wins and teams | **required, first** |
| 1 | [Find what is wrong](#track-1--find-what-is-wrong) — UI bugs and proposals on the live product | **required** |
| 2 | [Build the desktop app](#track-2--build-the-desktop-app) | pick one or more |
| 3 | [Google Drive, bulk upload, search](#track-3--google-drive-bulk-upload-search) | pick one or more |
| 4 | [Invent a workflow](#track-4--invent-a-workflow) on the API and MCP | pick one or more |

### Track 0 — Show us what you already have

Before anything else, open a pull request that shows us your current work,
with links: your LinkedIn, the repos you have built, the apps you have
shipped, the thing you are proudest of, hackathons you won, teams you led.
The pull request template has a **Track record** block; fill in every line
that is true.

That pull request is your entry. It is how you get the credit coupon, and it
is what we read first. We check it, not just read it: in every repo you link
we count your commits against everyone else's, whether you owned something
complex from start to finish, and how you worked with others — reviews you
gave, issues you answered, work you did alongside a team. Store links are
checked live, Devpost pages are read for the winner mark, and your LinkedIn
is matched against the one on your GitHub profile. It tells us how you work
before you have written a line for us.

### Track 1 — Find what is wrong

Use [whipscribe.com](https://whipscribe.com) on your phone and on your laptop.
Sign in, upload a file, read the transcript, use the library, look at credits
and pricing. It is the live product.

- File each problem as an issue here, using the **UI bug** template.
- Label it `mobile` or `desktop`.
- For the ones that matter, add a **Proposal**: what you would change, why, and
  a mockup or before/after.

We read proposals before code. A small fix for a real problem beats a long
list. Every participant does this track: it is the quickest way for us to
see your eye, and for you to see the product you would be working on.

**Start here:** [UI challenge 01 — the transcript reader on a phone](challenges/01-mobile-transcript/README.md).
Our current design, every state on screen; show us the next version.

### Track 2 — Build the desktop app

A desktop app that:

1. Connects to your calendar (Google first; others are a bonus) and shows
   what is coming up.
2. Records the meeting — system audio, microphone, or both — and keeps the
   recording if the app closes mid-call.
3. Sends it to WhipScribe through the API and shows the transcript with
   speakers.
4. Manages your recordings through the MCP server: folders, search, rename,
   delete.

The bar is the best meeting-recording app you can find on the market — not a
demo. Look at what people already use, work out what they get right and where
they fall short, then design something better, from scratch if you need to.
Tell us what you looked at and what you chose to do differently.

Any stack; say why you chose yours. Guidance, not rules:

- **Windows:** Tauri 2 if you want Windows and macOS from one build with a
  web UI. Electron is fine if it is what you ship fastest.
- **macOS:** the same Tauri 2 or Electron build. Recording system audio needs
  ScreenCaptureKit permissions — the hardest part of the app.

Desktop only for this track: Windows first, macOS welcome. WhipScribe already
has an iOS app, so a phone app is not part of the challenge.

One platform done well beats two done badly.

Build in order: calendar → recording → transcript → library → polish. Stop
where you like and say why.

### Track 3 — Google Drive, bulk upload, search

A web app that:

1. Connects to Google Drive and lets you pick folders.
2. Transcribes everything in them, with progress per file, and picks up new
   files later.
3. Lists what was transcribed by folder, and searches the words inside the
   transcripts. Results jump to the moment in the recording.
4. Stretch: ask a question across a folder.

A thorough design on its own is a valid entry for this track. The UI is most
of the problem.

### Track 4 — Invent a workflow

Pick a real person with a real problem that recordings can solve, and build
the workflow that solves it, on the WhipScribe API, the MCP server, or both.
This track is open-ended on purpose. It shows us two things the others
cannot: what you can see that we have not, and what you can actually put in
a user's hands.

**Who the users are.** Anyone whose day produces audio they never get back
to: a student with a term of lectures, a journalist with forty interviews, a
sales rep with calls and a CRM to fill in, a researcher coding interviews by
theme, a podcaster who needs show notes and chapters, a support lead who
wants every call checked against a script, a founder with investor calls, a
teacher giving spoken feedback, someone who sends themselves voice notes all
day, a person who is deaf or hard of hearing and gets sent audio. Pick one.
Be specific: not "students", but "a medical student revising from six hours
of lectures a week".

**What a workflow is.** The steps that go from the recording to the thing
the person actually wanted, with the person doing as little as possible in
between. Some shapes, to start you thinking; yours does not have to be on
this list:

- A meeting ends and the decisions and action items are already in Linear,
  Jira, Notion or Todoist, each linked to the moment it was said.
- A voice note sent to a bot on WhatsApp or Telegram comes back as text and
  a summary, and lands in the library, filed.
- Forty interviews become a theme-by-interview matrix a researcher can
  defend, with every cell pointing at a quote.
- A sales call becomes CRM notes with objections, commitments and next steps,
  in the fields the CRM already has.
- A term of lectures becomes study cards and a weekly quiz, with the weak
  spots weighted.
- A podcast episode becomes chapters, show notes, pull quotes and three
  social posts, in the host's voice.
- An assistant skill: connect the MCP server to Claude, ChatGPT or Cursor and
  make "what did we agree with the vendor last month?" answerable from the
  whole library, with sources.
- A node for Zapier, Make or n8n, or a GitHub Action, so the workflow exists
  for people who do not code.

**What we want from you.**

1. **The problem, in one page.** Who the person is, what they do today, what
   it costs them in time or mistakes, and why recordings are the way in.
   Talk to one such person if you can; say what they said.
2. **The workflow, drawn.** The steps, what the API or MCP does in each, what
   the person sees, and what they never have to do again.
3. **A working prototype.** Real API calls, your own recordings, one flow
   end to end. Read the [docs](https://whipscribe.com/docs) for what the API
   returns; do not build on behaviour it does not have. A prototype that
   works for one person beats a platform that works for nobody yet.
4. **A two-minute recording** of the workflow doing its job, start to finish.
5. **The vision.** What this looks like a year on if it works: who else it
   serves, what it would need from us, what you would build next. This is
   where we learn how far you can see.

Any language, any framework, any integration you can reach. Build in
`apps/your-name/` in your fork, with the problem page and the vision in its
README.

**How we read this track.** Is the problem real and specific? Does the
workflow remove steps, not add a dashboard? Are the API and MCP used
correctly and honestly? Did someone other than you try it? And does the
vision hold up: can you see past the prototype to the product?

## How to take part

1. Fork this repo.
2. **Track 0:** open a pull request with the **Track record** block in the
   template filled in, and which tracks you plan to do. (An issue with the
   **Introduction** template works if you are not ready for a pull request
   yet.)
3. **Track 1:** file UI bugs and proposals as issues here.
4. Tracks 2, 3 and 4: build in `apps/your-name/` in your fork, with a README
   that says how to run it and what works. Open a pull request when you want
   us to look. Small and early beats big and late.

## What you need

- Your own WhipScribe account. Get an API key under *Account → API key*.
- The API docs: [whipscribe.com/docs](https://whipscribe.com/docs).
- The MCP server: [whipscribe.com/claude](https://whipscribe.com/claude).
- For tracks 2 and 3: a Google Cloud project with the Calendar or Drive API
  and an OAuth client. Keep the client secret out of the repo.
- Credits for testing: introduce yourself (below) and we send you a 7-day
  coupon for API credits.

AI tools are expected. `AGENTS.md` is the brief for them, `ai/prompts/` has a
starter prompt for each track, and `TOOLS.md` sets up the MCP servers that
speed you up: WhipScribe, Playwright, Context7, GitHub.

## Leaderboard

> **Reviews finish by Sunday 27 September 2026.** Every pull request open today
> is scored, ranked on the board and answered with written feedback within 48
> hours. Keep building; anything you open after that joins the next review pass.

Live standings for every track and challenge: [whipscribe.com/buildathon](https://whipscribe.com/buildathon).
You appear there as soon as your Track 0 pull request is open; your rank
appears once reviewers have scored you. Click any name for the
profile: GitHub facts, the **Track record** you wrote in your introduction
(LinkedIn, shipped apps, hackathon wins, teams led, team projects), and every
score. What you claim is checked, not just read: for every repo you link we
count your commits against everyone else's, store links are checked live,
Devpost pages are read for the winner mark, and your LinkedIn is matched
against the one on your GitHub profile. Reviews are ours; the board is
everyone's.

## How we judge

Check yourself first with [`CHECKLIST.md`](CHECKLIST.md) — what we look for, as a
tickable list that is already in the Introduction and pull request templates.

1. **UI and UX.** Does it feel right? Are empty, loading, error and done
   states designed? Would a non-technical person get it?
2. **Building with AI, well.** Did you understand what the tool produced,
   keep the good and drop the rest? Your commits and README show this.
3. **Finishing.** One thing that works for a real user beats three that
   nearly do.
4. **Learning.** Say what was new to you and how it went.
5. **Self-drive.** Did you open Track 0 before anyone asked, show what you
   have already built, and keep moving without being chased?
6. **Ownership and teamwork.** In the repos you link: did you own a complex
   project end to end, and did you work well with others — reviews, issues,
   shared work? Hackathons you won, teams you led, and team projects you
   shipped all count here; link them and say what your part was.
7. **Shipped apps.** iOS or Android apps you built that are live in a store
   with real users count. Paste the links in your introduction.
8. **Vision.** Track 4 especially: did you pick a real problem, see the
   whole workflow, and describe where it goes next in a way we believe?

## Rules

- Your own account and your own recordings. Never record someone who did not
  agree.
- No keys, secrets or tokens in commits.
- Be specific and kind. We read everything.
- Your app in your fork stays yours.

Questions: open an issue with the **Question** template.
