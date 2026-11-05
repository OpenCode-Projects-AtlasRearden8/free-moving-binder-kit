"""Tests for the Calm Move Kit build.

Every sheet must build a valid, correctly-paged, unbranded PDF whose text can
be verified. The extractor is dependency-free: it inflates PDF streams and
decodes WeasyPrint's CID text through the embedded ToUnicode maps.
"""

import re
import subprocess
import sys
import zlib
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import build  # noqa: E402


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def inflate(raw):
    chunks = []
    for c in re.findall(rb"stream\r?\n(.*?)endstream", raw, re.S):
        try:
            chunks.append(zlib.decompress(c))
        except Exception:
            pass
    return chunks


def to_unicode_maps(chunks):
    cmap = {}
    for d in chunks:
        if b"CIDInit" not in d:
            continue
        for m in re.findall(rb"beginbfchar(.*?)endbfchar", d, re.S):
            for cid, uni in re.findall(rb"<([0-9A-Fa-f]+)> <([0-9A-Fa-f]+)>", m):
                cmap[int(cid, 16)] = int(uni, 16)
        for m in re.findall(rb"beginbfrange(.*?)endbfrange", d, re.S):
            for lo, hi, base in re.findall(rb"<([0-9A-Fa-f]+)> <([0-9A-Fa-f]+)> <([0-9A-Fa-f]+)>", m):
                lo, hi, base = int(lo, 16), int(hi, 16), int(base, 16)
                for cid in range(lo, hi + 1):
                    cmap[cid] = base + (cid - lo)
    return cmap


def pdf_text(path):
    """All text in a WeasyPrint PDF, keeping only ascii letters, lowercase."""
    raw = Path(path).read_bytes()
    chunks = inflate(raw)
    cmap = to_unicode_maps(chunks)
    text = ""
    for d in chunks:
        if b"CIDInit" in d or b"BT" not in d:
            continue
        for seg in re.findall(rb"BT(.*?)ET", d, re.S):
            hexes = re.findall(rb"<([0-9A-Fa-f]+)>", seg)
            h = "".join(x.decode() for x in hexes)
            b = bytes.fromhex(h[: (len(h) // 2) * 2])
            for i in range(0, len(b) - 1, 2):
                u = cmap.get(int.from_bytes(b[i : i + 2], "big"))
                if u:
                    text += chr(u)
    return re.sub(r"[^A-Za-z]", "", text).lower()


def page_count(path):
    raw = Path(path).read_bytes()
    blobs = [raw] + inflate(raw)
    return sum(
        len(re.findall(rb"/Type\s*/Page(?!\w)", blob))
        for blob in blobs
    )


# ---------------------------------------------------------------------------
# fixture: build everything once into a temp dir
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session")
def built(tmp_path_factory):
    out = tmp_path_factory.mktemp("printables")
    proc = subprocess.run(
        [sys.executable, str(ROOT / "build.py"), "--out", str(out)],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr
    return out


@pytest.mark.parametrize("sheet", build.SHEETS, ids=lambda s: s["slug"])
def test_sheet_builds_valid_pdf(built, sheet):
    path = built / f"{sheet['file']}.pdf"
    raw = path.read_bytes()
    assert raw.startswith(b"%PDF-"), path
    assert raw.rstrip().endswith(b"%%EOF"), path
    assert len(raw) > 1024, f"{path.name} suspiciously small"
    assert page_count(path) == sheet["pages"] + 1, (
        f"{path.name}: expected {sheet['pages'] + 1} pages (getting-started + sheet)"
    )


@pytest.mark.parametrize("sheet", build.SHEETS, ids=lambda s: s["slug"])
def test_sheet_contains_expected_text(built, sheet):
    text = pdf_text(built / f"{sheet['file']}.pdf")
    for kw in sheet["check"]:
        assert kw in text, f"{sheet['file']}.pdf is missing expected text '{kw}'"


@pytest.mark.parametrize("sheet", build.SHEETS, ids=lambda s: s["slug"])
def test_getting_started_page_present(built, sheet):
    """Every PDF opens on a warm getting-started page, not on a form."""
    text = pdf_text(built / f"{sheet['file']}.pdf")
    gs_markers = ["gettingstarted", "whatyouneed", "howtouseit"]
    for marker in gs_markers:
        assert marker in text, f"missing getting-started marker '{marker}'"


@pytest.mark.parametrize("sheet", build.SHEETS, ids=lambda s: s["slug"])
def test_pdfs_are_unbranded(built, sheet):
    raw = (built / f"{sheet['file']}.pdf").read_bytes()
    text = pdf_text(built / f"{sheet['file']}.pdf")
    for word in ["asdale", "dylan", "copyright"]:
        assert word not in text, f"{sheet['file']}.pdf contains branding '{word}'"
        assert word.encode() not in raw, f"{sheet['file']}.pdf contains branding '{word}'"


def test_build_regenerates_every_sheet_to_printables():
    """The committed printables/ folder holds one PDF per manifest sheet."""
    for sheet in build.SHEETS:
        path = ROOT / "printables" / f"{sheet['file']}.pdf"
        assert path.exists(), f"missing shipped artifact {path}"
        assert page_count(path) == sheet["pages"] + 1, path


def test_every_source_fragment_counts_pages(tmp_path):
    """Page promises in the manifest match the .page divs in sources/."""
    for sheet in build.SHEETS:
        frag = (ROOT / "sources" / f"{sheet['slug']}.html").read_text()
        n_pages = frag.count('class="page"')
        assert n_pages == sheet["pages"], f"{sheet['slug']}: expected {sheet['pages']} .page divs, found {n_pages}"
