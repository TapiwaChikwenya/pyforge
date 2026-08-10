"""One-shot helper: split app/static/index.html into app.css + app.js."""

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HTML = ROOT / "app" / "static" / "index.html"
text = HTML.read_text(encoding="utf-8")

if '<link rel="stylesheet" href="/static/app.css">' in text:
    print("already split")
    raise SystemExit(0)

s0 = text.index("<style>") + len("<style>")
s1 = text.index("</style>")
css = text[s0:s1].strip() + "\n"

marker = "<script>\n/* ============================================================"
j0 = text.index(marker) + len("<script>")
j1 = text.rindex("</script>")
js = text[j0:j1].strip() + "\n"

(ROOT / "app" / "static" / "app.css").write_text(css, encoding="utf-8")
(ROOT / "app" / "static" / "app.js").write_text(js, encoding="utf-8")

head = text[: text.index("<style>")]
head = head.replace(
    "</head>",
    '  <link rel="stylesheet" href="/static/app.css">\n</head>',
)
body = text[s1 + len("</style>") : text.index(marker)]
new = head + body + '<script src="/static/app.js"></script>\n</body>\n</html>\n'
HTML.write_text(new, encoding="utf-8")
print(f"wrote app.css ({len(css)} chars), app.js ({len(js)} chars)")
