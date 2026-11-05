#!/usr/bin/env python3
"""Calm Move Kit build script.

Assembles each printable as (warm getting-started page + HTML/CSS sheet pages)
and renders one unbranded PDF per sheet into printables/.

Local-first: no network, no signups, no secrets. Renders with WeasyPrint when
available, falling back to headless Chrome.

Usage:
    python3 build.py                 # build every sheet
    python3 build.py --only box-labels
    python3 build.py --out /tmp/pdf  # custom output dir
    python3 build.py --list
"""

import argparse
import logging
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SOURCES = ROOT / "sources"
CSS_REL = "sources/css/kit.css"

# ---------------------------------------------------------------------------
# Sheet manifest
# ---------------------------------------------------------------------------
# `pages` is the number of .page divs in the sheet fragment itself; the build
# adds one warm getting-started page in front of every sheet.
SHEETS = [
    {
        "slug": "binder-spine-tabs",
        "file": "binder-spine-and-tabs",
        "title": "Binder Spine & Tab Sheet",
        "pages": 2,
        "check": ["movingbinder", "tabkey"],
        "gs": {
            "what": [
                "Any sturdy 3-ring binder (2 inch or wider feels calm, not cramped)",
                "A pair of scissors and a pen",
                "Tape or glue if the spine insert is floppy",
            ],
            "how": [
                "Print this PDF, then cut out the spine strip that matches your binder width.",
                "Write your move month and family name in the blanks, and slide the strip into the outside pocket of your binder spine.",
                "Cut the eight tabs along the dashed lines and hole-punch the wide end.",
                "File your sheets behind the matching tabs, and pencil in the tab key below so anyone in the house can find things.",
            ],
            "tip": "A binder you can find in the dark beats a pretty one you never open. Crayons, quarters for carts, and a pen live up front in the pocket.",
            "greet": "Let's make the binder first.",
        },
    },
    {
        "slug": "box-labels",
        "file": "box-labels",
        "title": "Room-by-Room Box Labels",
        "pages": 3,
        "check": ["kitchen", "garage"],
        "gs": {
            "what": [
                "This printout, a pen, and tape",
                "A marker that reads well in dim hallways (chisel tip is kind on tired eyes)",
            ],
            "how": [
                "Print at 100 percent scale (no fit-to-page shrinking, so the numbers stay roomy).",
                "Fill in the room name and the box number before taping, not after.",
                "Tape a label on the top AND on the side of each box, so it reads from any angle it might be stacked.",
                "Circle the priority: 3 means this gets unpacked in week one, 1 means it can ride in the truck a long while.",
            ],
            "tip": "Write the room on the box in the same big letters every time. Future-you, carrying a box and holding a door with one knee, will be grateful.",
            "greet": "Someday a box just says 'bedroom' and you believe it.",
        },
    },
    {
        "slug": "utility-calendar",
        "file": "utility-transfer-calendar",
        "title": "Utility Transfer Calendar",
        "pages": 2,
        "check": ["turnon", "shutoff"],
        "gs": {
            "what": [
                "Your current utility account numbers",
                "The lease or closing date, or a best guess while you wait",
            ],
            "how": [
                "On the transfer checklist, write the shut-off date at the OLD home and the turn-on date at the NEW home for each line.",
                "Call two weeks ahead if you can. Older water and trash companies often bill in cycles and cannot start mid-cycle.",
                "When a company confirms, copy the confirmation number into the box and mark the checkbox. That number is your umbrella on a rainy day.",
                "On the month grid, write shut-offs with one symbol and turn-ons with another, so overlaps and gaps pop out at one glance.",
            ],
            "tip": "Book the internet turn-on first. It is the slowest company in every town, and it schedules by availability, not by your welcome.",
            "greet": "This one page prevents the no-hot-water surprise.",
        },
    },
    {
        "slug": "change-of-address",
        "file": "change-of-address-master-list",
        "title": "Change-of-Address Master List",
        "pages": 2,
        "check": ["usps", "creditcard"],
        "gs": {
            "what": [
                "About twenty minutes with your mail pile",
                "Your new address and your start date, written at the top before you begin",
            ],
            "how": [
                "Start with the USPS line, then your bank and insurance. Everything else will follow, one coffee break at a time.",
                "Each time someone confirms, write the date in the 'Confirmed' column. The pencil date is what makes this a master list instead of a worry list.",
                "Let the mail keep flowing. Old senders keep sending mail for months, and each new letter is a free reminder of whom to update.",
            ],
            "tip": "You do not need to finish this before the move. Twenty addresses in ink, five in the notes column, is a great month.",
            "greet": "The quietest chore, done one checkbox at a time.",
        },
    },
    {
        "slug": "paint-dims",
        "file": "new-home-paint-and-dims",
        "title": "New-Home Paint & Dims Grid",
        "pages": 2,
        "check": ["gallons", "ceiling"],
        "gs": {
            "what": [
                "A tape measure and something to write with",
                "Paint chips taped during your first visit, if you already have them",
            ],
            "how": [
                "Walk the empty home room by room. Measure length and width, then jot the ceiling height you saw or asked for.",
                "On the dims grid, write window sizes too. Blinds and curtains get ordered faster than paint dries.",
                "On the paint grid, tape or write the color name, the finish (eggshell hides handprints best), and the gallons estimate.",
                "Buy one sample quart per room and paint a poster-board swatch. Live with it for a day before committing five gallons.",
            ],
            "tip": "Measure the stairs and the widest doorframe once and tape that number to the binder. It decides which couch goes through which door.",
            "greet": "Numbers in pencil buy you weeks of confidence.",
        },
    },
    {
        "slug": "fragile-cards",
        "file": "fragile-warning-cards",
        "title": "Fragile Warning Cards",
        "pages": 1,
        "check": ["fragile", "thissideup"],
        "gs": {
            "what": ["This printout, scissors, and tape", "A red or orange marker, if you have one"],
            "how": [
                "Cut along the dashed lines; each card is meant to be tossed in a box after unpacking and reused for the next one.",
                "Tape one card on two opposite faces of every fragile box, so it is visible on two of the four sides however it is stacked.",
                "Write the room name and the box number on each card, matching your box-label sheet.",
                "When you pack lamps and dishes, put them on the truck last so they come off first and never end up under camping gear.",
            ],
            "tip": "Words help movers; colors help everyone. A bold marker border around a card reads from across a garage.",
            "greet": "Small cards, real savings in dishware.",
        },
    },
    {
        "slug": "unpack-order",
        "file": "unpack-order-plan",
        "title": "Unpack-Order Plan",
        "pages": 2,
        "check": ["survival", "openfirst"],
        "gs": {
            "what": ["A pen", "Permission to let the garage stay full for two weeks"],
            "how": [
                "On the plan page, start only with the Day 1 row. Bed, nightstand kit, bathroom, and dishes. Nothing else counts yet.",
                "Cross out or reorder rows to match your real life. Morning people unpack kitchens, night people unpack bedrooms.",
                "On the first-boxes page, number your ten most important boxes and make sure each gets its own number on the box labels too.",
                "Leave one room the 'closed box room'. Boxes go there when they arrive, and items are pulled out only as needed. It stays honest.",
            ],
            "tip": "Empty tape guns and open scissors are how an unpacking day stalls. Yesterday's box gets taped before today's box gets opened.",
            "greet": "First a bed, then a barista, then a bookshelf.",
        },
    },
    {
        "slug": "dishes-in-a-day",
        "file": "dishes-in-a-day-arrival-card",
        "title": "Dishes in a Day Arrival Card",
        "pages": 1,
        "check": ["dishesinaday", "sinkkit"],
        "gs": {
            "what": ["This card, packed on top of the kitchen's first box", "Soap, two towels, and the kettle you packed last"],
            "how": [
                "When the boxes arrive, find the box labeled KITCHEN 1 first, even before the bed boxes. This card will be taped on top.",
                "Run the steps on the card in order. Each step takes minutes, not hours, because the point is dinner tonight, not a perfect kitchen.",
                "When the last checkbox on the card is filled, you get to eat off plates tonight. Write the date under it and tape it into the binder's boxes tab.",
            ],
            "tip": "If the day goes sideways, one plate, one cup, one pan is still a win. This card asks for a dinner, not a kitchen.",
            "greet": "The kindest box in the whole house.",
        },
    },
]

# ---------------------------------------------------------------------------
# Getting-started page (one warm page in front of every sheet)
# ---------------------------------------------------------------------------

GS_PAGE = """\
<div class="page gs">
  <p class="greet">{greet}</p>
  <p class="small" style="margin-top:0">{sheet_title} &middot; getting started</p>
  <div class="gs-box">
    <h2>Who this sheet is for</h2>
    <p style="margin:0">Anyone facing a move who would like it to feel a little calmer.
    Everything here is free, prints on plain letter paper, works offline, and asks
    nothing back &mdash; no account, no email, no app. Print it, tape it, scribble on
    it. That is the whole requirement.</p>
  </div>
  <div class="gs-box">
    <h2>What you need</h2>
    <ul>{what}</ul>
  </div>
  <div class="gs-box">
    <h2>How to use it</h2>
    <ol>{how}</ol>
  </div>
  <div class="hint">
    <strong>One warm tip:</strong> {tip}
  </div>
  <div class="gs-home">
    Companion to the <em>Moving Without Meltdown</em> guide &middot; this sheet is part
    of the Calm Move Kit, a set of free printables for a peaceful household move.
  </div>
  <div class="foot">Calm Move Kit &middot; print &middot; use freely &middot; no strings</div>
</div>
"""


def gs_html(sheet):
    emoji_free = lambda items: "".join(f"<li>{i}</li>" for i in items)
    return GS_PAGE.format(
        greet=sheet["gs"]["greet"],
        sheet_title=sheet["title"],
        what=emoji_free(sheet["gs"]["what"]),
        how=emoji_free(sheet["gs"]["how"]),
        tip=sheet["gs"]["tip"],
    )


# ---------------------------------------------------------------------------
# Renderer
# ---------------------------------------------------------------------------

def full_html(sheet, fragment):
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>{sheet['title']}</title>
<link rel="stylesheet" href="{CSS_REL}">
</head>
<body>
{gs_html(sheet)}
{fragment}
</body>
</html>
"""


def render_weasyprint(html, target):
    from weasyprint import HTML

    HTML(string=html, base_url=str(ROOT)).write_pdf(str(target))


def render_chrome(html, target):
    chrome = shutil.which("google-chrome") or shutil.which("chromium") or shutil.which("chromium-browser")
    if not chrome:
        raise RuntimeError("no PDF renderer available (need weasyprint or chrome)")
    tmp = target.with_suffix(".print.html")
    tmp.write_text(html)
    subprocess_run = [
        chrome, "--headless", "--disable-gpu", "--no-sandbox",
        "--print-to-pdf=" + str(target), "--no-pdf-header-footer",
        "--print-to-pdf-no-header", str(tmp),
    ]
    import subprocess

    subprocess.run(subprocess_run, check=True, capture_output=True)
    tmp.unlink(missing_ok=True)


def render(html, target):
    try:
        render_weasyprint(html, target)
        return "weasyprint"
    except ImportError:
        pass
    render_chrome(html, target)
    return "chrome"


def build_sheet(sheet, out_dir, force=True):
    src = SOURCES / f"{sheet['slug']}.html"
    fragment = src.read_text()
    html = full_html(sheet, fragment)
    target = out_dir / f"{sheet['file']}.pdf"
    engine = render(html, target)
    return target, engine


def main(argv=None):
    ap = argparse.ArgumentParser(description="Build the Calm Move Kit printables")
    ap.add_argument("--out", default=str(ROOT / "printables"))
    ap.add_argument("--only", help="build a single sheet by slug")
    ap.add_argument("--list", action="store_true")
    args = ap.parse_args(argv)

    sheets = SHEETS
    if args.list:
        for s in sheets:
            print(f"{s['slug']:>20}  {s['file']}.pdf  ({s['pages'] + 1} pages)")
        return 0
    if args.only:
        sheets = [s for s in sheets if s["slug"] == args.only]
        if not sheets:
            print(f"unknown sheet slug: {args.only}", file=sys.stderr)
            return 1

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    logging.getLogger("weasyprint").setLevel(logging.ERROR)
    ok = True
    for s in sheets:
        target, engine = build_sheet(s, out_dir)
        size = target.stat().st_size
        expected = s["pages"] + 1
        print(f"built {target.name:<42} {expected} pages  {size / 1024:7.1f} KB  ({engine})")
        if size < 1000:
            ok = False
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
