
import re
import ssl
from html.parser import HTMLParser
from urllib.parse import urljoin, urlsplit
from urllib.request import Request, urlopen


BASE_URL = "https://pminternship.mca.gov.in/"
MAX_SIZE = 2 * 1024 * 1024

SEARCH_TERMS = [
    "featured-internships",
    "internship-details",
    "get-sectors",
    "get-field",
    "get-internship-for-company",
    "get-districts-by-state-id",
    "baseURL",
    "baseUrl",
    "axios.create",
    "fetch(",
    "NEXT_PUBLIC",
    "internship",
    "opportunities",
]


class ScriptParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.scripts = []

    def handle_starttag(self, tag, attrs):
        if tag == "script":
            attributes = dict(attrs)
            src = attributes.get("src")

            if src:
                self.scripts.append(src)


def fetch(url):
    request = Request(
        url,
        headers={
            "User-Agent": "InternMatchAI-Research/1.0",
            "Accept": "*/*",
        },
    )

    context = ssl.create_default_context()

    with urlopen(
        request,
        timeout=20,
        context=context,
    ) as response:

        final_url = response.geturl()
        host = (urlsplit(final_url).hostname or "").lower()

        if host != "pminternship.mca.gov.in":
            raise ValueError("Unexpected external redirect.")

        data = response.read(MAX_SIZE + 1)

        if len(data) > MAX_SIZE:
            raise ValueError("File exceeds size limit.")

        return data.decode("utf-8", errors="replace")


def inspect_homepage():
    print("\nSTEP 1: INSPECTING OFFICIAL HOMEPAGE")

    html = fetch(BASE_URL)

    parser = ScriptParser()
    parser.feed(html)

    scripts = list(dict.fromkeys(
        urljoin(BASE_URL, item)
        for item in parser.scripts
    ))

    print("JavaScript files found:", len(scripts))

    return scripts


def inspect_script(url):
    print("\n" + "=" * 70)
    print("SCRIPT:", urlsplit(url).path)
    print("=" * 70)

    try:
        content = fetch(url)

    except Exception as error:
        print("Could not read script:", error)
        return

    found = 0
    printed_positions = set()

    for term in SEARCH_TERMS:
        start = 0

        while True:
            position = content.lower().find(term.lower(), start)

            if position == -1:
                break

            start = position + len(term)

            # Avoid printing the same section repeatedly.
            bucket = position // 250

            if bucket in printed_positions:
                continue

            printed_positions.add(bucket)
            found += 1

            left = max(0, position - 250)
            right = min(len(content), position + 450)

            snippet = content[left:right]

            print("\nMATCH:", term)
            print("Context:")
            print(snippet[:700])

            if found >= 15:
                print("\nSnippet limit reached for this file.")
                return

    if found == 0:
        print("No relevant API configuration found in this file.")


def main():
    print("=" * 70)
    print("INTERNMATCH AI - PMIS API CONFIGURATION INSPECTOR")
    print("=" * 70)

    print("Official website:", BASE_URL)
    print("Request method: GET")
    print("Login: Not used")
    print("Database: Not modified")

    try:
        scripts = inspect_homepage()

        # Inspect the first 39 scripts or fewer.
        for script in scripts[:39]:
            inspect_script(script)

    except Exception as error:
        print("Investigation error:", error)

    print("\n" + "=" * 70)
    print("INSPECTION COMPLETED")
    print("No API endpoints were called.")
    print("No database records were changed.")
    print("=" * 70)


if __name__ == "__main__":
    main()
