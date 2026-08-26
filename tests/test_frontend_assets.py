"""Static invariants for the markdown/code styling in app/static/app.css.

Two constraints have to hold at the same time, and fixing either one naively
breaks the other:

1. The editor's internals must stay untouched. CodeMirror renders *every* line
   of the editor as a ``<pre>`` inside ``.ex-body``, so a bare ``.ex-body pre``
   selector styles the editor itself. It only looks acceptable while
   CodeMirror's own stylesheet wins on specificity, which stops being true as
   soon as that CDN file is slow, blocked, or version-bumped.

2. Because the styling is scoped to an explicit list of prose containers, any
   container that renders markdown or code snippets must appear in that list.
   ``.sol-card`` (community solutions) is the easy one to miss: it lives inside
   ``.ex-body``, so it was silently dropped when the rules were narrowed.

These tests parse the shipped CSS/JS rather than a browser, so they are fast and
deterministic in CI. They cannot prove the styling *looks* right, only that the
selector contract between markup and stylesheet is intact.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
STATIC = ROOT / "app" / "static"

# Containers whose markdown/snippet <pre> blocks must get the dark padded box.
PRE_CONTAINERS = (
    ".instructions",
    ".refresher-body",
    ".local-only",
    ".ivq-body",
    ".ivq-answer",
    ".lesson-body",
    ".panel",
    ".sol-card",
)

# Containers whose inline/block <code> must get the mono font + accent colour.
# .local-only is deliberately absent: its only snippet is a <pre class="launch-block">
# with no <code> child, and that class carries its own styling.
CODE_CONTAINERS = tuple(c for c in PRE_CONTAINERS if c != ".local-only")

_COMMENT_RE = re.compile(r"/\*.*?\*/", re.DOTALL)
_RULE_RE = re.compile(r"([^{}]+)\{([^{}]*)\}", re.DOTALL)


def _read(name: str) -> str:
    return (STATIC / name).read_text(encoding="utf-8")


def _rules(css: str) -> list[tuple[frozenset[str], str]]:
    """Return (selector set, declaration block) pairs, comments stripped.

    Nested at-rules (``@media`` and friends) leave a stray fragment behind for
    this flat regex; that fragment has no declarations, so it is harmless for
    the selector-presence assertions below.
    """
    stripped = _COMMENT_RE.sub("", css)
    rules: list[tuple[frozenset[str], str]] = []
    for selector_text, body in _RULE_RE.findall(stripped):
        selectors = frozenset(
            " ".join(sel.split()) for sel in selector_text.split(",") if sel.strip()
        )
        rules.append((selectors, body))
    return rules


def _rule_containing(
    rules: list[tuple[frozenset[str], str]], selector: str
) -> tuple[frozenset[str], str]:
    matches = [rule for rule in rules if selector in rule[0]]
    assert matches, f"no CSS rule declares {selector!r}"
    assert len(matches) == 1, f"{selector!r} is declared in {len(matches)} rules; expected one"
    return matches[0]


@pytest.fixture(scope="module")
def css_rules() -> list[tuple[frozenset[str], str]]:
    return _rules(_read("app.css"))


def test_pre_rule_covers_every_prose_container(css_rules):
    selectors, body = _rule_containing(css_rules, ".instructions pre")
    missing = [f"{c} pre" for c in PRE_CONTAINERS if f"{c} pre" not in selectors]
    assert not missing, f"markdown <pre> styling misses: {missing}"
    normalized = " ".join(body.split())
    for declaration in ("background: #0a0e16", "overflow-x: auto", "padding: 12px 14px"):
        assert declaration in normalized, f"markdown <pre> box lost {declaration!r}"


def test_code_rules_cover_every_prose_container(css_rules):
    inline, _ = _rule_containing(css_rules, ".instructions code")
    block, _ = _rule_containing(css_rules, ".instructions pre code")
    missing_inline = [f"{c} code" for c in CODE_CONTAINERS if f"{c} code" not in inline]
    missing_block = [f"{c} pre code" for c in CODE_CONTAINERS if f"{c} pre code" not in block]
    assert not missing_inline, f"inline <code> styling misses: {missing_inline}"
    assert not missing_block, f"block <code> styling misses: {missing_block}"


def test_no_selector_styles_the_editor_container_generically(css_rules):
    """`.ex-body pre|code` would reach into CodeMirror's own line elements."""
    offenders = sorted(
        sel
        for selectors, _ in css_rules
        for sel in selectors
        if re.search(r"\.ex-body\s+(pre|code)\b", sel)
    )
    assert not offenders, f"selectors leak into the editor's internals: {offenders}"


def test_codemirror_line_reset_is_present(css_rules):
    """Defence in depth for the case above, if a broad selector sneaks back in."""
    _, body = _rule_containing(css_rules, ".CodeMirror pre.CodeMirror-line")
    normalized = " ".join(body.split())
    for declaration in ("background: transparent", "border: 0", "margin: 0"):
        assert declaration in normalized, f"CodeMirror line reset lost {declaration!r}"


def test_community_solutions_markup_matches_the_styled_selector():
    """The CSS above is only useful if solutions still render <pre><code> in .sol-card."""
    js = _read("features.js")
    block = re.search(r'<div class="sol-card">.*?</div>', js, re.DOTALL)
    assert block, "community solutions no longer render a .sol-card block"
    assert "<pre><code>" in block.group(0), (
        ".sol-card stopped emitting <pre><code>; update app.css scoping to match"
    )


def test_solutions_are_rendered_inside_the_exercise_body():
    """Documents why .sol-card cannot rely on any selector scoped outside .ex-body."""
    app_js = _read("app.js")
    ex_body = app_js.split('<div class="ex-body">', 1)
    assert len(ex_body) == 2, "exercise markup no longer contains .ex-body"
    assert "solutionsSlotHtml(ex)" in ex_body[1], "solutions slot moved out of .ex-body"
