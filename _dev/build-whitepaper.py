"""Build whitepaper.html from the whitepaper's Markdown.

    python _dev/build-whitepaper.py [path/to/WHITEPAPER.md]

Defaults to ../WHITEPAPER.md (the copy next to this site), keeps a copy of the source in
_dev/whitepaper.md, and writes whitepaper.html at the site root. It handles the Markdown the
whitepaper uses (headings, paragraphs, lists, tables, emphasis, code, links, rules) and nothing
more, so the site keeps its no-dependencies rule.
"""

import html
import os
import re
import shutil
import sys

SITE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = sys.argv[1] if len(sys.argv) > 1 else os.path.join(SITE, "..", "WHITEPAPER.md")


def slug(text):
    text = re.sub(r"<[^>]+>", "", text)
    text = re.sub(r"[^\w\s-]", "", text.lower())
    return re.sub(r"\s+", "-", text.strip())


def inline(text):
    """Escape, then apply code spans, links, bold, italics and bare URLs."""
    codes = []

    def keep_code(m):
        codes.append("<code>" + html.escape(m.group(1), quote=False) + "</code>")
        return "\x00%d\x00" % (len(codes) - 1)

    text = re.sub(r"`([^`]+)`", keep_code, text)
    text = html.escape(text, quote=False)
    links = []

    def keep_link(m):
        links.append('<a href="%s">%s</a>' % (html.escape(m.group(2)), m.group(1)))
        return "\x01%d\x01" % (len(links) - 1)

    text = re.sub(r"\[([^\]]+)\]\(([^)\s]+)\)", keep_link, text)
    text = re.sub(r"(https?://[^\s<)]+[^\s<).,;:])",
                  lambda m: '<a href="%s">%s</a>' % (m.group(1), m.group(1)), text)
    text = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"(?<![\w*])\*([^*\n]+)\*(?![\w*])", r"<em>\1</em>", text)
    text = re.sub("\x01(\\d+)\x01", lambda m: links[int(m.group(1))], text)
    text = re.sub("\x00(\\d+)\x00", lambda m: codes[int(m.group(1))], text)
    return text


def convert(md):
    lines = md.replace("\r\n", "\n").split("\n")
    out, toc, title = [], [], None
    i = 0

    def is_block_start(l):
        return bool(re.match(r"^(#{1,4}\s|-\s|\d+\.\s|\||---\s*$)", l))

    while i < len(lines):
        line = lines[i]
        if not line.strip():
            i += 1
            continue
        m = re.match(r"^(#{1,4})\s+(.*)$", line)
        if m:
            level, text = len(m.group(1)), m.group(2).strip()
            if level == 1 and title is None:
                title = text
                i += 1
                continue
            hid = slug(text)
            if level == 2:
                toc.append((hid, inline(text)))
            out.append('<h%d id="%s">%s</h%d>' % (level, hid, inline(text), level))
            i += 1
            continue
        if re.match(r"^---\s*$", line):
            out.append("<hr>")
            i += 1
            continue
        if line.startswith("|") and i + 1 < len(lines) and re.match(r"^\|[\s:|-]+\|\s*$", lines[i + 1]):
            cells = lambda l: [c.strip() for c in l.strip().strip("|").split("|")]
            head = "".join("<th>%s</th>" % inline(c) for c in cells(line))
            i += 2
            rows = []
            while i < len(lines) and lines[i].startswith("|"):
                rows.append("<tr>" + "".join("<td>%s</td>" % inline(c) for c in cells(lines[i])) + "</tr>")
                i += 1
            out.append('<div class="table-wrap"><table><thead><tr>%s</tr></thead><tbody>%s</tbody></table></div>'
                       % (head, "".join(rows)))
            continue
        lm = re.match(r"^(-|\d+\.)\s+", line)
        if lm:
            ordered = lm.group(1) != "-"
            items = []
            while i < len(lines) and re.match(r"^(-|\d+\.)\s+", lines[i]):
                items.append("<li>%s</li>" % inline(re.sub(r"^(-|\d+\.)\s+", "", lines[i])))
                i += 1
            tag = "ol" if ordered else "ul"
            out.append("<%s>%s</%s>" % (tag, "".join(items), tag))
            continue
        para = []
        while i < len(lines) and lines[i].strip() and not is_block_start(lines[i]):
            para.append(inline(lines[i].strip()))
            i += 1
        # A paragraph whose first line is all bold is a question with its answer under it.
        if len(para) > 1 and re.fullmatch(r"<strong>.*</strong>", para[0]):
            out.append('<div class="qa"><p class="q">%s</p><p>%s</p></div>'
                       % (para[0], "<br>".join(para[1:])))
        else:
            out.append("<p>%s</p>" % "<br>".join(para))
    return title, toc, "\n".join(out)


TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Whitepaper | hx+</title>
<meta name="description" content="The hx+ whitepaper: why we built hxc, how compatibility is kept, what hx+ adds, how the project is run, and where things stand.">
<link rel="canonical" href="https://hxplus.org/whitepaper.html">
<meta property="og:type" content="article">
<meta property="og:site_name" content="hx+">
<meta property="og:title" content="The hx+ whitepaper">
<meta property="og:description" content="A strict superset of Haxe 4.3, built on hxc, a faithful Haxe compiler written in Haxe.">
<meta property="og:url" content="https://hxplus.org/whitepaper.html">
<meta property="og:image" content="https://hxplus.org/assets/og-image.png">
<meta name="twitter:card" content="summary_large_image">
<meta name="theme-color" content="#0b0e14">
<link rel="icon" href="assets/favicon.svg" type="image/svg+xml">
<link rel="stylesheet" href="assets/style.css">
<script>
try {
  var t = localStorage.getItem('hxplus-theme');
  if (t !== 'light' && t !== 'dark') t = matchMedia('(prefers-color-scheme: light)').matches ? 'light' : 'dark';
  document.documentElement.setAttribute('data-theme', t);
} catch (e) {}
</script>
</head>
<body>

<a class="skip-link" href="#doc">Skip to content</a>

<header class="site-header">
  <div class="container header-inner">
    <a class="brand" href="./"><img class="logo" src="assets/logo.svg" alt="">hx<span class="plus">plus</span></a>
    <nav class="site-nav doc-nav">
      <a href="./">Home</a>
      <a class="nav-out" href="https://github.com/dimensionscape/hxc">GitHub <span aria-hidden="true">&#8599;</span></a>
    </nav>
    <button class="theme-toggle" id="themeToggle" aria-label="Toggle theme"><span class="tt-sun">&#9728;</span><span class="tt-moon">&#9790;</span></button>
  </div>
</header>

<main class="doc-page" id="doc">
  <div class="container doc-layout">
    <article class="doc">
      <p class="eyebrow"><span class="idx">hx+</span>Whitepaper</p>
      <h1>%(title)s</h1>
%(body)s
    </article>
    <aside class="doc-toc" aria-label="Contents">
      <p class="doc-toc-title">Contents</p>
      <ol>
%(toc)s
      </ol>
    </aside>
  </div>
</main>

<footer class="site-footer">
  <div class="container footer-inner">
    <div>
      <span class="brand brand-footer"><img class="logo" src="assets/logo.svg" alt="">hx<span class="plus">plus</span></span>
      <p class="footer-tag">A community superset of Haxe.</p>
    </div>
    <nav class="footer-links" aria-label="Elsewhere">
      <a href="./">Home</a>
      <a href="https://github.com/dimensionscape/hxc">GitHub</a>
      <a href="https://lib.haxe.org/p/hxc/">haxelib</a>
    </nav>
    <div class="footer-meta">
      <p>&copy; 2026 Dimensionscape LLC</p>
      <p>hx+ is an independent project. Haxe is a project of the Haxe Foundation.</p>
    </div>
  </div>
</footer>

<script>
document.getElementById('themeToggle').addEventListener('click', function () {
  var root = document.documentElement;
  var next = root.getAttribute('data-theme') === 'light' ? 'dark' : 'light';
  root.setAttribute('data-theme', next);
  try { localStorage.setItem('hxplus-theme', next); } catch (e) {}
});
</script>

</body>
</html>
"""


def main():
    md = open(SRC, encoding="utf-8").read()
    title, toc, body = convert(md)
    page = TEMPLATE % {
        "title": inline(title or "hx+ whitepaper"),
        "body": "\n".join("      " + l for l in body.split("\n")),
        "toc": "\n".join('        <li><a href="#%s">%s</a></li>' % (h, t) for h, t in toc),
    }
    open(os.path.join(SITE, "whitepaper.html"), "w", encoding="utf-8", newline="\n").write(page)
    keep = os.path.join(SITE, "_dev", "whitepaper.md")
    if os.path.abspath(SRC) != os.path.abspath(keep):
        shutil.copyfile(SRC, keep)
    print("whitepaper.html: %d sections, %d bytes" % (len(toc), len(page)))


main()
