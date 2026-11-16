
import re
import urllib.request
from urllib.parse import urljoin, urlparse

BASE_URL = "https://pminternship.mca.gov.in/"

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
    "turbopack-2i9vt_0kucrsw.js",
]

KEYWORDS = re.compile(
    r"internship|opportunit|api/|graphql|fetch\(|axios|"
    r"baseURL|job-details|explore-internships|company",
    re.IGNORECASE
)

print("=" * 65)
print("INTERNMATCH AI - PMIS CHUNK INSPECTION")
print("=" * 65)

for filename in CHUNKS:
    url = urljoin(BASE_URL, "_next/static/chunks/" + filename)

    print(f"\nChecking: {filename}")

    try:
        request = urllib.request.Request(
            url,
            headers={"User-Agent": "Mozilla/5.0"}
        )

        with urllib.request.urlopen(request, timeout=20) as response:
            if response.status != 200:
                print("HTTP status:", response.status)
                continue

            content = response.read(2 * 1024 * 1024).decode(
                "utf-8", errors="ignore"
            )

        matches = list(KEYWORDS.finditer(content))

        if not matches:
            print("No relevant keywords.")
            continue

        print("Relevant matches:", len(matches))

        shown = 0
        seen = set()

        for match in matches:
            start = max(0, match.start() - 180)
            end = min(len(content), match.end() + 250)
            context = content[start:end].replace("\n", " ")

            if context in seen:
                continue

            seen.add(context)
            print("\nMATCH:")
            print(context[:450])

            shown += 1
            if shown >= 5:
                print("\nFurther matches omitted for this file.")
                break

    except Exception as error:
        print("Could not inspect:", error)

print("\n" + "=" * 65)
print("INSPECTION COMPLETED")
print("No API endpoints were called.")
print("No database records were changed.")
print("=" * 65)
