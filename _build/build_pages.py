"""sudokuportal 페이지 생성기.

index.html 을 원본으로 오늘의 스도쿠(daily.html)와 난이도별 페이지(level/*.html)를 만들고,
sitemap.xml / rss.xml 을 실제 파일 기준으로 다시 씁니다.

사용법 (리포 루트에서):  python _build/build_pages.py
- index.html 의 <!-- PAGE:HEAD/HEADER/CONTENT START·END --> 와 <!-- PAGE:PRESET --> 구간만 페이지별로 바꿉니다.
- 게임 코드·광고·스타일은 index.html 그대로 복사되므로, 게임을 고칠 때는 index.html 만 고치고 이 스크립트를 다시 실행하세요.
- 폴더 이름이 '_' 로 시작해서 GitHub Pages(Jekyll)는 이 스크립트를 공개하지 않습니다.
"""
import datetime as dt
import email.utils
import html
import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SITE = "https://sudokuportal.enjoy-onepage.com"
EN_SITE = "https://us-daily-sudoku-puzzle.enjoy-onepage.com"  # English twin with the same paths (reciprocal hreflang)
KST = dt.timezone(dt.timedelta(hours=9))

PAGES = [
    {
        "path": "daily.html", "preset": {"mode": "daily", "level": "normal"},
        "title": "오늘의 스도쿠 | 매일 새 문제·연속 기록 무료",
        "desc": "한국 시간 기준으로 매일 모두에게 같은 문제가 나오는 오늘의 스도쿠. 연속 기록을 쌓고 친구와 같은 문제로 겨뤄 보세요.",
        "h1": "오늘의 스도쿠", "sub": "매일 자정(한국 시간) 새 문제 · 난이도 4단계 · 연속 기록",
        "intro_h2": "📅 오늘의 스도쿠란?",
        "intro": "오늘의 스도쿠는 한국 시간 자정마다 바뀌는 하루 한 문제입니다. 같은 날 같은 난이도를 고르면 누구에게나 똑같은 문제가 나오기 때문에, 가족이나 친구와 누가 더 빨리 푸는지 겨루기 좋습니다. 기본은 '보통' 난이도이고, 위에서 쉬움·어려움·전문가로 바꾼 뒤 '📅 오늘의 스도쿠'를 누르면 같은 날짜의 다른 난이도 문제가 나옵니다.",
        "blocks": [
            ("연속 기록은 이렇게 쌓여요", [
                "오늘의 스도쿠를 하루에 한 문제라도 끝까지 풀면 그날이 기록됩니다. 난이도는 상관없습니다.",
                "어제에 이어 오늘도 풀면 연속 일수가 1씩 늘고, 하루를 건너뛰면 다시 1일부터 시작합니다.",
                "'해답 보기'를 누른 판은 기록되지 않습니다.",
                "기록은 이 기기의 브라우저에만 저장되므로, 다른 기기나 시크릿 창에서는 따로 쌓입니다.",
            ]),
            ("친구와 같은 문제로 대결하기", [
                "클리어 후 '📤 결과 공유하기'를 누르면 내 기록과 함께 같은 문제로 들어오는 링크가 공유·복사됩니다.",
                "링크에는 날짜와 난이도만 들어 있어 정답이 드러나지 않습니다.",
                "지난 날짜의 문제도 링크(예: ?date=2026-09-01&level=hard)로 다시 풀 수 있지만, 연속 기록은 그날의 오늘의 스도쿠만 인정됩니다.",
            ]),
        ],
        "faq": [
            ("오늘의 스도쿠는 몇 시에 바뀌나요?", "한국 시간 자정(00:00)에 바뀝니다. 해외에 있어도 한국 날짜를 기준으로 같은 문제가 나옵니다."),
            ("하루에 여러 번 풀 수 있나요?", "네. 같은 문제를 다시 풀 수 있고, 더 빠른 기록이 나오면 그 기록으로 바뀝니다. 연속 기록은 하루에 한 번만 늘어납니다."),
            ("자정이 지나면 풀던 문제는 어떻게 되나요?", "열어 둔 문제는 그대로 풀 수 있습니다. 다만 연속 기록은 문제를 끝낸 시점의 날짜가 문제 날짜와 같을 때만 인정됩니다."),
        ],
    },
    {
        "path": "level/easy.html", "preset": {"mode": "free", "level": "easy"},
        "title": "쉬운 스도쿠 | 초보자용 무료 퍼즐 무제한",
        "desc": "빈칸 36~40개, 싱글 기법만으로 풀리는 쉬운 스도쿠. 규칙만 알면 처음 하는 분도 끝까지 풀 수 있어요.",
        "h1": "쉬운 스도쿠", "sub": "빈칸 36~40개 · 싱글 기법만으로 풀리는 초보자용",
        "intro_h2": "🌱 쉬운 스도쿠는 이런 분께",
        "intro": "쉬운 스도쿠는 처음 시작하는 분, 오랜만에 퍼즐을 다시 해 보는 분, 아이와 함께 하는 분께 맞춘 난이도입니다. 81칸 중 빈칸은 36~40개로, 절반 이상이 이미 채워져 있습니다. 모든 문제는 한 칸에 들어갈 숫자가 하나로 좁혀지는 '싱글' 기법만으로 끝까지 풀리는지 검사를 통과한 것이라, 찍지 않아도 됩니다.",
        "blocks": [
            ("처음 푸는 분을 위한 순서", [
                "숫자가 가장 많이 채워진 줄이나 박스를 찾습니다. 빈칸이 한두 개뿐이면 빠진 숫자를 바로 알 수 있습니다.",
                "숫자 하나를 정해 판 전체를 훑습니다. 예를 들어 5가 이미 있는 줄과 열을 지우고 나면, 어떤 박스에서 5가 들어갈 자리가 한 곳만 남는 경우가 많습니다.",
                "헷갈리는 칸은 후보 숫자를 메모해 두세요. 숫자를 확정하면 같은 줄·열·박스의 메모는 자동으로 지워집니다.",
                "틀린 것 같으면 '오류 체크'로 확인할 수 있습니다. 익숙해지면 실수 0회로 풀어 보세요.",
            ]),
        ],
        "faq": [
            ("쉬움과 보통은 무엇이 다른가요?", "둘 다 싱글 기법만으로 풀리지만, 보통은 빈칸이 45~50개로 더 많아서 확정할 칸을 찾는 데 시간이 더 걸립니다."),
            ("아이도 할 수 있나요?", "1부터 9까지 숫자를 알고, 같은 줄·열·박스에 같은 숫자가 없어야 한다는 규칙을 이해하면 충분합니다. 처음에는 오류 체크를 쓰면서 함께 풀어 보세요."),
        ],
    },
    {
        "path": "level/normal.html", "preset": {"mode": "free", "level": "normal"},
        "title": "보통 스도쿠 | 중급 무료 퍼즐 무제한",
        "desc": "빈칸 45~50개의 보통 난이도 스도쿠. 히든 싱글과 후보 메모를 연습하기 좋은 무제한 무료 퍼즐입니다.",
        "h1": "보통 스도쿠", "sub": "빈칸 45~50개 · 히든 싱글과 메모 연습용",
        "intro_h2": "🙂 보통 스도쿠에서 달라지는 점",
        "intro": "보통 스도쿠는 규칙에 익숙해진 분이 한 단계 올라가기 좋은 난이도입니다. 빈칸이 45~50개로 늘어나, 눈에 바로 보이는 칸보다 '이 숫자가 들어갈 곳이 여기밖에 없다'를 찾아야 하는 순간이 많아집니다. 그래도 모든 문제는 싱글 기법만으로 풀리도록 검사했기 때문에 추측 없이 끝낼 수 있습니다.",
        "blocks": [
            ("보통 난이도에서 막힐 때", [
                "히든 싱글: 한 박스(또는 줄·열) 안에서 어떤 숫자가 들어갈 수 있는 칸이 하나뿐이면 그 칸이 답입니다. 박스마다 1부터 9까지 차례로 확인해 보세요.",
                "교차 확인: 가로줄과 세로줄을 동시에 보며 후보를 지우면 빈칸이 빠르게 줄어듭니다.",
                "메모는 적게, 정확하게: 모든 칸에 후보를 적기보다 후보가 두세 개인 칸만 적어 두면 판이 덜 복잡합니다.",
                "기록 줄이기: 같은 난이도를 여러 판 풀면 최고 기록이 이 기기에 저장됩니다.",
            ]),
        ],
        "faq": [
            ("보통 난이도에서 자주 막히는데 괜찮은 건가요?", "네. 빈칸이 많아지면 한동안 확정할 칸이 안 보이는 구간이 생깁니다. 이때는 숫자 하나를 정해 판 전체를 다시 훑는 히든 싱글 찾기가 가장 효과적입니다."),
            ("같은 문제를 다시 풀 수 있나요?", "주소창의 링크(문제 번호 포함)를 저장하거나 공유하면 언제든 같은 문제가 다시 나옵니다."),
        ],
    },
    {
        "path": "level/hard.html", "preset": {"mode": "free", "level": "hard"},
        "title": "어려운 스도쿠 | 고급 무료 퍼즐 무제한",
        "desc": "빈칸 51~55개의 어려운 스도쿠. 네이키드 페어와 포인팅 같은 후보 소거 기법이 필요할 수 있는 무료 퍼즐입니다.",
        "h1": "어려운 스도쿠", "sub": "빈칸 51~55개 · 후보 소거 기법이 필요할 수 있는 고급",
        "intro_h2": "🔥 어려운 스도쿠를 푸는 방법",
        "intro": "어려운 스도쿠는 빈칸이 51~55개로, 싱글만으로는 진행이 멈추는 문제가 섞여 나옵니다. 이때부터는 후보 숫자를 꼼꼼히 메모하고, 여러 칸의 후보를 한꺼번에 비교해 지워 나가는 기법이 필요합니다. 정답은 항상 하나뿐이므로 논리로 끝까지 풀 수 있습니다.",
        "blocks": [
            ("어려움 난이도에서 쓰는 기법", [
                "네이키드 페어: 같은 줄(또는 열·박스)의 두 칸에 후보가 똑같이 두 개(예: 3·7)만 남았다면, 그 두 숫자는 두 칸이 나눠 가집니다. 같은 줄의 다른 칸에서 3과 7을 지울 수 있습니다.",
                "포인팅: 한 박스 안에서 어떤 숫자의 후보가 한 줄에만 모여 있으면, 그 줄의 박스 밖 칸에서는 그 숫자를 지울 수 있습니다.",
                "박스·줄 줄이기: 반대로 어떤 줄에서 한 숫자의 후보가 한 박스 안에만 있으면, 그 박스의 나머지 칸에서 그 숫자를 지웁니다.",
                "숫자를 확정할 때마다 같은 줄·열·박스의 메모가 자동으로 지워지니, 후보가 하나만 남은 칸이 새로 생기지 않았는지 바로 확인하세요.",
            ]),
        ],
        "faq": [
            ("어려움과 전문가는 무엇이 다른가요?", "전문가는 빈칸이 56개 이상(주어진 숫자 25개 이하)이라 실마리가 더 적습니다. 어려움에서 페어와 포인팅에 익숙해진 뒤 넘어가길 권합니다."),
            ("찍어서 풀어도 되나요?", "틀리면 앞선 칸들까지 되돌려야 해서 오히려 오래 걸립니다. 후보가 두 개인 칸을 기준으로 두 경우를 차례로 따져 보는 편이 안전합니다."),
        ],
    },
    {
        "path": "level/expert.html", "preset": {"mode": "free", "level": "expert"},
        "title": "전문가 스도쿠 | 최고 난도 무료 퍼즐",
        "desc": "빈칸 56개 이상, 주어진 숫자 25개 이하의 전문가 스도쿠. X-Wing 같은 고급 기법까지 쓰는 최고 난도 퍼즐입니다.",
        "h1": "전문가 스도쿠", "sub": "빈칸 56개 이상 · 주어진 숫자 25개 이하 · 최고 난도",
        "intro_h2": "🧠 전문가 스도쿠 도전하기",
        "intro": "전문가 스도쿠는 이 사이트에서 가장 어려운 단계입니다. 주어진 숫자가 25개 이하(빈칸 56개 이상)라서 처음 몇 수를 찾는 것부터 쉽지 않습니다. 정답이 하나뿐인 문제만 나오므로 끝까지 논리로 풀 수 있지만, 후보 메모를 체계적으로 관리하지 않으면 중간에 길을 잃기 쉽습니다.",
        "blocks": [
            ("전문가 난이도 공략", [
                "먼저 모든 빈칸에 후보를 적습니다. 전문가 단계에서는 메모 없이 진행하기 어렵습니다.",
                "히든 페어: 한 줄에서 두 숫자가 들어갈 수 있는 칸이 같은 두 칸뿐이라면, 그 두 칸의 다른 후보는 모두 지웁니다.",
                "X-Wing: 어떤 숫자가 두 줄에서 각각 같은 두 열에만 후보로 남아 있으면, 그 두 열의 나머지 칸에서 그 숫자를 지울 수 있습니다.",
                "막히면 가장 최근에 확정한 칸 주변부터 다시 봅니다. 숫자 하나가 여러 칸의 후보를 한꺼번에 줄여 줍니다.",
            ]),
        ],
        "faq": [
            ("전문가 문제는 주어진 숫자가 몇 개인가요?", "대체로 23~25개입니다. 정답이 하나뿐인 9×9 스도쿠의 이론상 최소 힌트 수는 17개로 알려져 있습니다."),
            ("너무 어려우면 어떻게 하나요?", "'오류 체크'로 틀린 칸만 확인하거나, 어려움 단계에서 기법을 먼저 연습해 보세요. '해답 보기'를 누른 판은 기록되지 않습니다."),
        ],
    },
]

LINKS = [
    ("/daily.html", "📅 오늘의 스도쿠"), ("/level/easy.html", "🌱 쉬운 스도쿠"), ("/level/normal.html", "🙂 보통 스도쿠"),
    ("/level/hard.html", "🔥 어려운 스도쿠"), ("/level/expert.html", "🧠 전문가 스도쿠"), ("/", "🏠 스도쿠 홈"), ("/guides/", "📚 스도쿠 가이드"),
]


def esc(s):
    return html.escape(s, quote=True)


def page_url(path):
    return f"{SITE}/{path}"


def head_block(p):
    url = page_url(p["path"])
    ld = {"@context": "https://schema.org", "@graph": [
        {"@type": "WebApplication", "@id": url + "#webapp", "name": p["h1"], "url": url, "applicationCategory": "GameApplication",
         "operatingSystem": "All", "inLanguage": "ko", "description": p["desc"], "image": f"{SITE}/og-image.png",
         "isPartOf": {"@type": "WebSite", "name": "스도쿠 무제한 퍼즐", "url": SITE + "/"},
         "offers": {"@type": "Offer", "price": "0", "priceCurrency": "KRW"}},
        {"@type": "FAQPage", "@id": url + "#faq", "mainEntity": [
            {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in p["faq"]]},
    ]}
    t, d = esc(p["title"]), esc(p["desc"])
    return "\n".join([
        "<!-- PAGE:HEAD START -->",
        f"<title>{html.escape(p['title'], quote=False)}</title>",
        f'<meta name="description" content="{d}">',
        '<meta name="robots" content="index, follow">',
        f'<link rel="canonical" href="{url}">',
        f'<link rel="alternate" hreflang="ko" href="{url}">',
        f'<link rel="alternate" hreflang="en" href="{EN_SITE}/{p["path"]}">',
        f'<link rel="alternate" hreflang="x-default" href="{EN_SITE}/{p["path"]}">',
        '<meta name="theme-color" content="#f97316">',
        '<link rel="icon" href="/favicon.ico">',
        '<link rel="apple-touch-icon" sizes="180x180" href="/apple-touch-icon.png">',
        '<link rel="manifest" href="/manifest.json">',
        '<meta name="apple-mobile-web-app-capable" content="yes">',
        '<meta property="og:locale" content="ko_KR">',
        '<meta property="og:type" content="website">',
        '<meta property="og:site_name" content="즐겨요 원페이지">',
        f'<meta property="og:title" content="{t}">',
        f'<meta property="og:description" content="{d}">',
        f'<meta property="og:url" content="{url}">',
        f'<meta property="og:image" content="{SITE}/og-image.png">',
        '<meta name="twitter:card" content="summary_large_image">',
        f'<meta name="twitter:title" content="{t}">',
        f'<meta name="twitter:description" content="{d}">',
        f'<meta name="twitter:image" content="{SITE}/og-image.png">',
        f'<link rel="alternate" type="application/rss+xml" title="스도쿠 무제한 퍼즐 RSS" href="{SITE}/rss.xml">',
        f'<link rel="sitemap" type="application/xml" href="{SITE}/sitemap.xml">',
        '<script type="application/ld+json">',
        json.dumps(ld, ensure_ascii=False, indent=2),
        "</script>",
        "<!-- PAGE:HEAD END -->",
    ])


def header_block(p):
    return "\n".join(["<!-- PAGE:HEADER START -->", '<header class="header">', f"  <h1>{esc(p['h1'])}</h1>",
                      f"  <div class=\"header-sub\">{esc(p['sub'])}</div>", "</header>", "<!-- PAGE:HEADER END -->"])


def content_block(p):
    out = ["<!-- PAGE:CONTENT START -->", '<section class="section">', f"  <h2>{esc(p['intro_h2'])}</h2>", '  <div class="content-card">',
           f"    <p>{esc(p['intro'])}</p>"]
    for title, items in p["blocks"]:
        out.append(f"    <h3>{esc(title)}</h3>")
        out.append("    <ul>" + "".join(f"<li>{esc(i)}</li>" for i in items) + "</ul>")
    out += ["  </div>", "</section>", "", '<section class="section" id="faq">', "  <h2>❓ 자주 묻는 질문</h2>"]
    for q, a in p["faq"]:
        out.append(f'  <div class="faq-item"><h3>Q. {esc(q)}</h3><p>{esc(a)}</p></div>')
    out += ["</section>", "", '<section class="section">', "  <h2>🧩 다른 난이도와 가이드</h2>", '  <div class="link-grid">']
    self_href = "/" + p["path"]
    for href, label in LINKS:
        if href != self_href:
            out.append(f'    <a class="link-card" href="{href}">{esc(label)}</a>')
    out += ["  </div>", "</section>", "<!-- PAGE:CONTENT END -->"]
    return "\n".join(out)


def swap(text, name, block):
    pat = re.compile(r"<!-- PAGE:%s START -->.*?<!-- PAGE:%s END -->" % (name, name), re.S)
    new, n = pat.subn(lambda _: block, text)
    if n != 1:
        raise SystemExit(f"marker PAGE:{name} not found exactly once")
    return new


def build_page(src, p):
    text = swap(src, "HEAD", head_block(p))
    text = swap(text, "HEADER", header_block(p))
    text = swap(text, "CONTENT", content_block(p))
    preset = json.dumps(p["preset"], ensure_ascii=False)
    if text.count("<!-- PAGE:PRESET -->") != 1:
        raise SystemExit("marker PAGE:PRESET missing")
    text = text.replace("<!-- PAGE:PRESET -->", f"<!-- PAGE:PRESET -->\n<script>window.SUDOKU_PRESET = {preset};</script>")
    return text


def title_desc(path):
    h = path.read_text(encoding="utf-8", errors="replace")
    t = re.search(r"<title[^>]*>(.*?)</title>", h, re.S)
    d = re.search(r'<meta[^>]+name=["\']description["\'][^>]*content=["\']([^"\']*)', h, re.I) or \
        re.search(r'<meta[^>]+content=["\']([^"\']*)["\'][^>]*name=["\']description', h, re.I)
    noindex = bool(re.search(r'<meta[^>]+name=["\']robots["\'][^>]+noindex', h, re.I))
    return (html.unescape(re.sub(r"\s+", " ", t.group(1))).strip() if t else path.name,
            html.unescape(d.group(1)).strip() if d else "", noindex)


def git_date(rel, first=False):
    out = subprocess.run(["git", "log", "--format=%cI", "--", rel], cwd=ROOT, capture_output=True, text=True).stdout.split()
    if not out:
        return dt.datetime.now(KST)
    return dt.datetime.fromisoformat(out[-1] if first else out[0])


def site_pages():
    """사이트맵·RSS에 넣을 공개 페이지 (noindex 제외, 순서 고정)."""
    rels = ["index.html", "daily.html"] + [f"level/{k}.html" for k in ("easy", "normal", "hard", "expert")]
    guides = ROOT / "guides"
    if (guides / "index.html").exists():
        rels.append("guides/index.html")
    rels += sorted(p.relative_to(ROOT).as_posix() for p in guides.glob("*.html") if p.name != "index.html") if guides.exists() else []
    rels += [r for r in ("about.html", "privacy.html", "terms.html") if (ROOT / r).exists()]
    return [r for r in rels if (ROOT / r).exists() and not title_desc(ROOT / r)[2]]


def loc(rel):
    if rel == "index.html":
        return SITE + "/"
    if rel.endswith("/index.html"):
        return f"{SITE}/{rel[:-10]}"
    return f"{SITE}/{rel}"


def write_sitemap(rels, changed):
    today = dt.datetime.now(KST).date().isoformat()
    lines = ['<?xml version="1.0" encoding="UTF-8"?>', '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for rel in rels:
        pr = "1.0" if rel == "index.html" else "0.9" if rel in ("daily.html",) else "0.8" if rel.startswith(("level/", "guides/")) else "0.5"
        lm = today if rel in changed else git_date(rel).date().isoformat()
        lines += ["  <url>", f"    <loc>{esc(loc(rel))}</loc>", f"    <lastmod>{lm}</lastmod>", "    <changefreq>weekly</changefreq>",
                  f"    <priority>{pr}</priority>", "  </url>"]
    lines.append("</urlset>")
    (ROOT / "sitemap.xml").write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")


def write_rss(rels):
    now = dt.datetime.now(dt.timezone.utc)
    t, d, _ = title_desc(ROOT / "index.html")
    out = ['<?xml version="1.0" encoding="UTF-8"?>', '<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">', "<channel>",
           f"  <title>{esc(t)}</title>", f"  <link>{SITE}/</link>", f"  <description>{esc(d)}</description>", "  <language>ko-kr</language>",
           f'  <atom:link href="{SITE}/rss.xml" rel="self" type="application/rss+xml" />',
           f"  <lastBuildDate>{email.utils.format_datetime(now)}</lastBuildDate>"]
    items = []
    for rel in rels:
        if rel == "index.html":
            continue
        it, idesc, _ = title_desc(ROOT / rel)
        items.append((git_date(rel, first=True), rel, it, idesc))
    for when, rel, it, idesc in sorted(items, key=lambda x: x[0], reverse=True):
        out += ["  <item>", f"    <title>{esc(it)}</title>", f"    <link>{esc(loc(rel))}</link>", f'    <guid isPermaLink="true">{esc(loc(rel))}</guid>',
                f"    <description>{esc(idesc or it)}</description>", f"    <pubDate>{email.utils.format_datetime(when)}</pubDate>", "  </item>"]
    out += ["</channel>", "</rss>"]
    (ROOT / "rss.xml").write_text("\n".join(out) + "\n", encoding="utf-8", newline="\n")


GUIDE_ORDER = ["rules.html", "guide1.html", "advanced.html", "guide2.html"]


def guides_index(src):
    """guides/index.html: 색인 허용 가이드만 모은 목차 페이지 (광고·스크립트 없음). 스타일은 index.html 의 가장 큰 <style> 을 그대로 쓴다."""
    gdir = ROOT / "guides"
    items = []
    for p in sorted(gdir.glob("*.html")):
        if p.name == "index.html":
            continue
        gt, gd, noindex = title_desc(p)
        if not noindex:
            items.append((p.name, gt, gd))
    items.sort(key=lambda x: (GUIDE_ORDER.index(x[0]) if x[0] in GUIDE_ORDER else len(GUIDE_ORDER), x[0]))
    url = f"{SITE}/guides/"
    title = "스도쿠 가이드 모음 | 규칙부터 고급 기법까지"
    desc = "스도쿠 규칙, 초보자 소거법, 네이키드 페어와 X-Wing 같은 고급 기법 가이드를 한곳에 모았습니다."
    if len(title) > 40 or len(desc) > 80:
        raise SystemExit("guides/index.html title/desc over the 40/80 limit")
    styles = re.findall(r"<style[^>]*>.*?</style>", src, re.S)
    ld = {"@context": "https://schema.org", "@type": "CollectionPage", "@id": url + "#page", "name": "스도쿠 가이드 모음", "url": url,
          "inLanguage": "ko", "description": desc, "isPartOf": {"@type": "WebSite", "name": "스도쿠 무제한 퍼즐", "url": SITE + "/"},
          "mainEntity": {"@type": "ItemList", "itemListElement": [
              {"@type": "ListItem", "position": i + 1, "url": f"{SITE}/guides/{f}", "name": gt} for i, (f, gt, _) in enumerate(items)]}}
    t, d = esc(title), esc(desc)
    cards = "\n".join(f'    <a class="link-card" href="/guides/{f}"><strong>{esc(gt)}</strong><br><span>{esc(gd)}</span></a>'
                      for f, gt, gd in items)
    page = "\n".join([
        "<!DOCTYPE html>", '<html lang="ko">', "<head>", '<meta charset="UTF-8">',
        '<meta name="viewport" content="width=device-width, initial-scale=1">',
        f"<title>{html.escape(title, quote=False)}</title>", f'<meta name="description" content="{d}">',
        '<meta name="robots" content="index, follow">', f'<link rel="canonical" href="{url}">',
        '<meta name="theme-color" content="#f97316">', '<link rel="icon" href="/favicon.ico">',
        '<meta property="og:locale" content="ko_KR">', '<meta property="og:type" content="website">',
        '<meta property="og:site_name" content="즐겨요 원페이지">', f'<meta property="og:title" content="{t}">',
        f'<meta property="og:description" content="{d}">', f'<meta property="og:url" content="{url}">',
        f'<meta property="og:image" content="{SITE}/og-image.png">', '<meta name="twitter:card" content="summary_large_image">',
        f'<meta name="twitter:title" content="{t}">', f'<meta name="twitter:description" content="{d}">',
        f'<meta name="twitter:image" content="{SITE}/og-image.png">',
        f'<link rel="alternate" type="application/rss+xml" title="스도쿠 무제한 퍼즐 RSS" href="{SITE}/rss.xml">',
        f'<link rel="sitemap" type="application/xml" href="{SITE}/sitemap.xml">',
        '<script type="application/ld+json">', json.dumps(ld, ensure_ascii=False, indent=2), "</script>",
        max(styles, key=len) if styles else "", "</head>", "<body>",
        '<header class="header">', "  <h1>스도쿠 가이드 모음</h1>",
        '  <div class="header-sub">규칙부터 고급 기법까지, 필요한 글만 골라 읽으세요</div>', "</header>",
        "<main>", '<section class="section">', "  <h2>📚 가이드 목록</h2>", '  <div class="link-grid">', cards, "  </div>", "</section>",
        '<section class="section">', "  <h2>🧩 바로 풀어보기</h2>", '  <div class="link-grid">',
        '    <a class="link-card" href="/daily.html">📅 오늘의 스도쿠</a>',
        '    <a class="link-card" href="/level/easy.html">🌱 쉬운 스도쿠</a>',
        '    <a class="link-card" href="/level/hard.html">🔥 어려운 스도쿠</a>',
        '    <a class="link-card" href="/">🏠 스도쿠 홈</a>', "  </div>", "</section>", "</main>",
        '<footer class="footer"><p><a href="/about.html">사이트 소개</a> | <a href="/privacy.html">개인정보처리방침</a> | '
        '<a href="/terms.html">이용약관</a></p></footer>', "</body>", "</html>", ""])
    out = gdir / "index.html"
    if not out.exists() or out.read_text(encoding="utf-8") != page:
        out.write_text(page, encoding="utf-8", newline="\n")
        return True
    return False



def main():
    src = (ROOT / "index.html").read_text(encoding="utf-8")
    changed = {"index.html"}
    for p in PAGES:
        if len(p["title"]) > 40 or len(p["desc"]) > 80:
            raise SystemExit(f"{p['path']}: title {len(p['title'])} / desc {len(p['desc'])} over the 40/80 limit")
        out = ROOT / p["path"]
        out.parent.mkdir(parents=True, exist_ok=True)
        text = build_page(src, p)
        for block in re.findall(r'<script type="application/ld\+json">(.*?)</script>', text, re.S):
            json.loads(block)
        if not out.exists() or out.read_text(encoding="utf-8") != text:
            out.write_text(text, encoding="utf-8", newline="\n")
            changed.add(p["path"])
    if guides_index(src):
        changed.add("guides/index.html")
    rels = site_pages()
    write_sitemap(rels, changed)
    write_rss(rels)
    print(f"built {len(PAGES)} pages; sitemap/rss entries: {len(rels)}")


if __name__ == "__main__":
    main()
