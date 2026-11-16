
import urllib.request
import re

url = (
    "https://pminternship.mca.gov.in/"
    "_next/static/chunks/14__1i89rd559.js"
)

try:
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "Mozilla/5.0"}
    )

    with urllib.request.urlopen(request, timeout=40) as response:
        content = response.read(2 * 1024 * 1024).decode(
            "utf-8", errors="ignore"
        )

    print("Downloaded successfully.")
    print("Searching API references...\n")

    patterns = [
        r'["\']\/api\/[^"\']{1,180}',
        r'baseURL.{0,250}',
        r'\/api\/.{0,180}',
    ]

    found = set()

    for pattern in patterns:
        for match in re.finditer(pattern, content, re.I):
            found.add(match.group(0))

    if found:
        for item in sorted(found):
            print("--------------------------------")
            print(item)
    else:
        print("No specific API path found.")

except Exception as error:
    print("Inspection error:", error)

print("\nInspection only. No API requests or database changes.")
