
import re
import urllib.request
from urllib.parse import urljoin

BASE = "https://pminternship.mca.gov.in/_next/static/chunks/"

CHUNKS = [
    "3s8k7vo_s4xze.js",
    "2to95sz9nc7l0.js",
    "0sbz0r0iwpaq4.js",
    "0r-yhzch002b1.js",
    "14__1i89rd559.js",
    "1ovez-th-i_ud.js",
    "1p2pnk_9dd7zu.js",
    "0xbcr0luqpxoh.js",
    "3xk8zqf7e4fun.js",
    "2tts5lx0bw_wx.js",
    "0soiag1zxzfjy.js",
    "2d3ksom0n1lv-.js",
    "1u798hil5lw-8.js",
    "2b6qy2w9hyqfv.js",
    "143x2lqw1q4lr.js",
    "427mcejumvtvt.js",
    "2i1g5vxcj77lv.js",
    "0s2wkxhvimhqg.js",
    "03a7msqrx1v-c.js",
    "0l3zby4-lzx5m.js",
    "27v8g87x3-4q1.js",
    "01pmjx6i7l-8o.js",
    "134prgfqvoel8.js",
    "0op6dfn3haq60.js",
    "0jwuwgmcqhtk_.js",
    "0rzytlihws3fc.js",
    "27r5xmk55wf03.js",
    "41918mwvey8rh.js",
    "1r96xmhlg0cod.js",
    "0ywmay8s41jwn.js",
    "0zpx0t-_lh2cx.js",
    "3tjcs0on49s8b.js",
    "05po5j13pgfn1.js",
    "0lm_9bvl9cu2q.js",
]

PATTERNS = [
    re.compile(r"""["'`](\/[^"'`\s]{1,180})["'`]"""),
    re.compile(r"""(?:fetch|axios|baseURL)\s*\([^)]{0,250}""", re.I),
]

INTERESTING = re.compile(
    r"api|graphql|intern|opportun|job|listing|search|vacanc|company",
    re.I
)

print("=" * 60)
print("PMIS - FOCUSED API REFERENCE SCAN")
print("=" * 60)

total = 0

for filename in CHUNKS:
    try:
        request = urllib.request.Request(
            urljoin(BASE, filename),
            headers={"User-Agent": "Mozilla/5.0"}
        )

        with urllib.request.urlopen(request, timeout=20) as response:
            content = response.read(2 * 1024 * 1024).decode(
                "utf-8", errors="ignore"
            )

        found = set()

        for pattern in PATTERNS:
            for match in pattern.finditer(content):
                value = match.group(1) if match.lastindex else match.group(0)

                if INTERESTING.search(value):
                    found.add(value[:220])

        if found:
            print(f"\nFILE: {filename}")

            for item in sorted(found)[:15]:
                print(" ", item)
                total += 1

    except Exception as error:
        print(f"\n{filename}: {error}")

print("\n" + "=" * 60)
print("TOTAL RELEVANT REFERENCES:", total)
print("Static JavaScript inspection only.")
print("No API endpoints called. No database changes.")
print("=" * 60)
