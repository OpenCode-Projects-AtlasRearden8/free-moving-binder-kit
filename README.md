# free-moving-binder-kit — Calm Move Kit

Free printable kits for a calm move. Everything here prints on plain letter
paper, works fully offline, and asks for nothing: no account, no email, no
tracking. Print it, tape it, scribble on it.

The kit pairs with the *Moving Without Meltdown* guide — the book explains
the calm-move approach in plain English; these sheets are the binders-and-boxes
component you can print and write on.

## What's inside

Ready-to-print PDFs live in `printables/` (unbranded — no logos, no company
names, safe to hand out at shelters, libraries, and housewarming parties).

| PDF | What it's for |
| --- | --- |
| `binder-spine-and-tabs.pdf` | Spine inserts for 2" and 3" binders, plus eight section tabs and a tab key |
| `box-labels.pdf` | Eighteen cut-out labels, room by room, with box numbers and unpack priority |
| `utility-transfer-calendar.pdf` | One checklist for shut-offs and turn-ons, plus a month grid to see gaps |
| `change-of-address-master-list.pdf` | Everything to tell — USPS, banks, DMV, doctors, subscriptions — two pages |
| `new-home-paint-and-dims.pdf` | A paint grid and a dims grid for your first walkthrough of the empty house |
| `fragile-warning-cards.pdf` | Eight reusable FRAGILE cards to cut, write, and tape |
| `unpack-order-plan.pdf` | Days 1 through week 3, in kind-to-future-you order, plus a first-boxes page |
| `dishes-in-a-day-arrival-card.pdf` | The kindest box in the house — dinner on real plates on night one |

Every PDF opens on a warm **getting-started page**: what you need, how to use
it, and one tip that earns its place.

## Building the PDFs yourself

The PDFs are generated from plain HTML/CSS in `sources/` by one local build
script. All you need is Python 3 and WeasyPrint (or, as a fallback, a local
Chrome/Chromium binary):

```bash
python3 build.py               # build every sheet into printables/
python3 build.py --list        # see the sheet manifest
python3 build.py --only box-labels
python3 build.py --out /tmp/pdf
```

No network is used, ever. Nothing leaves your machine.

## Tests

`pytest` verifies that every sheet builds a valid PDF with the right number of
pages, a getting-started page, expected content, and zero branding:

```bash
python3 -m pytest tests/
```

## Repository layout

```
build.py                  one build script: manifest + getting-started pages + renderer
sources/*.html            one HTML fragment per sheet (the sheet pages)
sources/css/kit.css       shared print stylesheet (Letter, print-safe)
printables/*.pdf          the shipped, unbranded PDFs
tests/test_pdfs.py        builds fresh PDFs and verifies every sheet
```

## Design notes

- US Letter (8.5in x 11in), 100% scale, grayscale-friendly with one warm accent.
- Muted colors degrades gracefully to black-and-white printers; every cut line
  is a dashed line so scissors stay honest.
- Forms are pencil-first: fill lines are oversized on purpose.

## License

MIT — see `LICENSE`.

Copyright (c) 2026 Asdale Dynamics, LLC. Built as part of Asdale Dynamics' line
of free, beginner-friendly, privacy-respecting household tools; from the same
studio as *The Massive AI Manual* and dylanasdale.github.io, where AI is
explained like a friend would.
