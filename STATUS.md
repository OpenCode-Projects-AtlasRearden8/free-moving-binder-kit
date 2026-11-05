# STATUS — free-moving-binder-kit (Calm Move Kit)

Last updated: 2026-11-05

## What was built

A free, local-first printable kit for a calm household move: eight print-ready
PDF "sheets", each opening on a warm getting-started page (what you need, how
to use it, one good tip). Built from plain HTML/CSS in `sources/` by a single
local build script, rendered with WeasyPrint. The PDFs in `printables/` are
unbranded — no logos, no company names — so they can be handed out freely.

Sheets (manifest lives in `build.py`):

1. `binder-spine-and-tabs.pdf` — 2"/3" spine inserts (rotated type), 8 tab cards, tab key (3 pages)
2. `box-labels.pdf` — 18 room-by-room cut-out labels with box numbers + priority circles (4)
3. `utility-transfer-calendar.pdf` — shut-off/turn-on checklist with confirmation numbers + month grid (3)
4. `change-of-address-master-list.pdf` — USPS/banks/DMV/health/school subscriptions list (3)
5. `new-home-paint-and-dims.pdf` — paint grid + dims/appliance-doorway grid (3)
6. `fragile-warning-cards.pdf` — 8 reusable FRAGILE cards (2)
7. `unpack-order-plan.pdf` — day-1→week-3 order plan + first-boxes page (3)
8. `dishes-in-a-day-arrival-card.pdf` — the arrival card for the KITCHEN 1 box (2)

Companion to the *Moving Without Meltdown* guide (referenced on every
getting-started page); that guide is separate and not in this repo.

## How to run

```bash
python3 build.py              # build all sheets into printables/
python3 build.py --list       # show the manifest
python3 build.py --only box-labels
python3 build.py --out DIR
python3 -m pytest tests/      # build fresh PDFs + verify every sheet
```

Requirements: Python 3.13 and WeasyPrint (installed here at v70). If
WeasyPrint is missing, `build.py` falls back to headless Chrome
(`google-chrome/chromium` on PATH). No network, no signups, no secrets.

## Verification results

- `python3 build.py` — all 8 sheets build; page counts match the manifest.
- `python3 -m pytest tests/` — **34 tests pass**, covering per sheet:
  - valid PDF (starts `%PDF-`, ends `%%EOF`, non-trivial size)
  - exact page count = manifest sheet pages + 1 getting-started page
  - expected content keywords found in the page text (goes through a small
    dependency-free CID/ToUnicode text extractor written for the tests)
  - getting-started markers present ("what you need", "how to use it")
  - unbranded: no "Asdale", "Dylan", or "Copyright" text anywhere in the PDF
- Plus repo-level checks: shipped `printables/` artifacts exist with correct
  page counts, and every `sources/*.html` fragment declares exactly the number
  of `.page` divs the manifest promises.
- Visual QA: every page rendered to PNG at build time reviewed for overflow,
  cut lines, and rotated spine text (page counts + `pdftoppm`).

All PDFs were rebuilt from source and committed (23 pages total).

## Known gaps / nice next steps

- Calendar grid is month-agnostic (users write in day numbers); a dated,
  move-month-aware version could be a separate sheet.
- Spine insert is sized for standard 10.5-inch spines; mini binders are out of
  scope for now.
- Small-format labels (e.g. Avery 5160) are not provided; the printed labels
  are meant for scissors, not a label printer.
- No dark-room/photocopy-only version; the accent color is muted but a pure
  B/W rebuild could be added as `--ink` mode.
- Tests deliberately don't depend on poppler; extra PDF assertions could add
  (optional, skip-if-missing) checks like outline/metadata validation.
