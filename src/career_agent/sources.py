"""Read-only sources. Network targets are fixed; board names are validated."""
import json
import re
import xml.etree.ElementTree as ET
from html.parser import HTMLParser
from urllib.request import Request, urlopen
from .models import Job


class TextExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts = []

    def handle_data(self, data):
        self.parts.append(data)


def plain(value):
    parser = TextExtractor()
    parser.feed(value or "")
    return " ".join(" ".join(parser.parts).split())


def fetch(url):
    request = Request(url, headers={"User-Agent": "RemoteCareerAgent/0.1 (personal job discovery)"})
    with urlopen(request, timeout=20) as response:
        content = response.read(5_000_001)
    if len(content) > 5_000_000:
        raise ValueError("Source response exceeds 5 MB")
    return content


def parse_wwr(content):
    if b"<!DOCTYPE" in content.upper() or b"<!ENTITY" in content.upper():
        raise ValueError("XML entities are not supported")
    result = []
    for item in ET.fromstring(content).findall("./channel/item"):
        title = item.findtext("title", "")
        company, separator, role = title.partition(":")
        url = item.findtext("link", "")
        result.append(Job(source="wwr", external_id=item.findtext("guid") or url,
                          title=role.strip() if separator else title, company=company.strip() if separator else "Unknown",
                          url=url, description=plain(item.findtext("description")) or title))
    return result


def discover(source, board=None):
    if source == "wwr":
        return parse_wwr(fetch("https://weworkremotely.com/remote-jobs.rss"))
    if source not in ("greenhouse", "lever"):
        raise ValueError("Supported sources: wwr, greenhouse, lever")
    if not board or not re.fullmatch(r"[A-Za-z0-9_-]{1,100}", board):
        raise ValueError("A valid company board slug is required")
    if source == "greenhouse":
        data = json.loads(fetch(f"https://boards-api.greenhouse.io/v1/boards/{board}/jobs?content=true"))
        return [Job(source=source, external_id=str(row["id"]), title=row["title"], company=board,
                    url=row["absolute_url"], description=plain(row.get("content")) or row["title"],
                    location=row.get("location", {}).get("name", "")) for row in data["jobs"]]
    data = json.loads(fetch(f"https://api.lever.co/v0/postings/{board}?mode=json"))
    return [Job(source=source, external_id=row["id"], title=row["text"], company=board,
                url=row["hostedUrl"], description=row.get("descriptionPlain") or plain(row.get("description")) or row["text"],
                location=row.get("categories", {}).get("location", "")) for row in data]
