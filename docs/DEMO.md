# Demo — recording the walkthrough GIF

The README embeds `docs/demo.gif`. Here's how to (re)record it so it always
reflects the current project.

## What to capture (60–90 seconds)

Keep it tight and in this order:

1. **Log in** with the demo account (`demo@citegraph.dev` / `demo1234`).
2. **Upload** two or three research-paper PDFs by dragging them onto the sidebar;
   wait for them to appear with page/chunk counts.
3. **Ask a real question**, e.g. _"What methods do these papers use to reduce
   false positives?"_ Let the answer render.
4. **Show the citations** — point out the confidence ring, the "verified" badge,
   and the exact section/page each one cites.
5. **Ask an unanswerable question**, e.g. _"What is the capital of France?"_ and
   show it refusing instead of guessing.
6. **Open the Evaluation tab** to show the real baseline-vs-classifier numbers
   and the cannot-answer rate.

## How to record

Any free recorder works:

- **Windows:** Xbox Game Bar (`Win+G`) or the built-in Snipping Tool video mode.
- **macOS:** `Shift+Cmd+5`.
- **Cross-platform:** [OBS Studio](https://obsproject.com/) (free).

Record at a modest window size (around 1280×800) so the text stays readable when
converted to a GIF.

## Convert to GIF

Using ffmpeg (free):

```bash
# from an mp4/mov recording -> an optimized gif
ffmpeg -i walkthrough.mp4 -vf "fps=12,scale=1000:-1:flags=lanczos" \
  -c:v gif docs/demo.gif
```

If the GIF is too large for GitHub to render inline (keep it under ~10 MB), lower
the fps (e.g. `fps=8`) or the width (`scale=800:-1`).

## Re-recording later

If the UI or flow changes, just re-record following the checklist above and
overwrite `docs/demo.gif` — the README references it by path, so nothing else
needs to change.

## Tip: seed a couple of papers first

The demo reads best with 2–3 real papers loaded. Upload them once with the demo
account before recording; they persist in the Postgres volume between restarts
(until you run `docker compose down -v`).
