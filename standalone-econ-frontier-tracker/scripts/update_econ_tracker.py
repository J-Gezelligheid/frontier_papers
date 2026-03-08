#!/usr/bin/env python3
"""Build expanded economics frontier tracker data into data/econ_tracker.json."""

from __future__ import annotations

import json
import os
import re
import time
from datetime import datetime, timezone
from html import unescape
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import requests
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "data" / "econ_tracker.json"

HEADERS = {
    "User-Agent": "econ-frontier-tracker-bot/1.0 (mailto:jincaiqi@ucass.edu.cn)",
    "Accept": "application/json, text/html;q=0.9, */*;q=0.8",
}
TIMEOUT = int(os.getenv("ECON_TRACKER_TIMEOUT_SECONDS", "25"))

KIMI_API_BASE = os.getenv("KIMI_API_BASE", "https://api.moonshot.cn/v1").rstrip("/")
KIMI_API_KEY = os.getenv("KIMI_API_KEY", "").strip()
KIMI_MODEL = os.getenv("KIMI_MODEL", "moonshot-v1-8k")
KIMI_MIN_INTERVAL_SECONDS = float(os.getenv("KIMI_MIN_INTERVAL_SECONDS", "3.2"))
MAX_ABSTRACT_TRANSLATE_CHARS = int(os.getenv("MAX_ABSTRACT_TRANSLATE_CHARS", "2500"))
MAX_ECON_PAPERS_PER_JOURNAL = int(os.getenv("MAX_ECON_PAPERS_PER_JOURNAL", "12"))

ECON_JOURNALS = [
    {"name": "American Economic Review", "issn": "0002-8282", "issue_url": "https://www.aeaweb.org/journals/aer"},
    {"name": "Quarterly Journal of Economics", "issn": "0033-5533", "issue_url": "https://academic.oup.com/qje"},
    {"name": "Journal of Political Economy", "issn": "0022-3808", "issue_url": "https://www.journals.uchicago.edu/journals/jpe"},
    {"name": "Econometrica", "issn": "0012-9682", "issue_url": "https://onlinelibrary.wiley.com/journal/14680262"},
    {"name": "Review of Economic Studies", "issn": "0034-6527", "issue_url": "https://academic.oup.com/restud"},
    {"name": "American Economic Journal: Applied Economics", "issn": "1945-7782", "issue_url": "https://www.aeaweb.org/journals/app"},
    {"name": "American Economic Journal: Economic Policy", "issn": "1945-7731", "issue_url": "https://www.aeaweb.org/journals/pol"},
    {"name": "Journal of International Economics", "issn": "0022-1996", "issue_url": "https://www.sciencedirect.com/journal/journal-of-international-economics"},
    {"name": "Journal of Development Economics", "issn": "0304-3878", "issue_url": "https://www.sciencedirect.com/journal/journal-of-development-economics"},
    {"name": "Review of International Economics", "issn": "0965-7576", "issue_url": "https://onlinelibrary.wiley.com/journal/14679396"},
    {"name": "Journal of Industrial Economics", "issn": "0022-1821", "issue_url": "https://onlinelibrary.wiley.com/journal/14676451"},
    {"name": "RAND Journal of Economics", "issn": "0741-6261", "issue_url": "https://onlinelibrary.wiley.com/journal/17562171"},
    {"name": "International Journal of Industrial Organization", "issn": "0167-7187", "issue_url": "https://www.sciencedirect.com/journal/international-journal-of-industrial-organization"},
    {"name": "Research Policy", "issn": "0048-7333", "issue_url": "https://www.sciencedirect.com/journal/research-policy"},
    {"name": "Strategic Management Journal", "issn": "0143-2095", "issue_url": "https://onlinelibrary.wiley.com/journal/10970266"},
    {"name": "Management Science", "issn": "0025-1909", "issue_url": "https://pubsonline.informs.org/journal/mnsc"},
    {"name": "Journal of Business Venturing", "issn": "0883-9026", "issue_url": "https://www.sciencedirect.com/journal/journal-of-business-venturing"},
    {"name": "Technovation", "issn": "0166-4972", "issue_url": "https://www.sciencedirect.com/journal/technovation"},
    {"name": "Industrial and Corporate Change", "issn": "0960-6491", "issue_url": "https://academic.oup.com/icc"},
    {"name": "Journal of Health Economics", "issn": "0167-6296", "issue_url": "https://www.sciencedirect.com/journal/journal-of-health-economics"},
    {"name": "Health Economics", "issn": "1057-9230", "issue_url": "https://onlinelibrary.wiley.com/journal/10991050"},
    {"name": "PharmacoEconomics", "issn": "1170-7690", "issue_url": "https://link.springer.com/journal/40273"},
    {"name": "Value in Health", "issn": "1098-3015", "issue_url": "https://www.valueinhealthjournal.com/"},
    {"name": "Health Affairs", "issn": "0278-2715", "issue_url": "https://www.healthaffairs.org/journal/hlthaff"},
]

ECON_TOPIC_KEYWORDS = {
    "国际贸易": [
        "trade",
        "export",
        "import",
        "tariff",
        "customs",
        "wto",
        "trade agreement",
        "free trade agreement",
        "fta",
        "anti-dumping",
        "global value chain",
        "gvc",
        "supply chain",
        "贸易",
        "出口",
        "进口",
        "关税",
        "自贸协定",
        "全球价值链",
    ],
    "国际经济": [
        "international economics",
        "open economy",
        "exchange rate",
        "balance of payments",
        "capital flow",
        "cross-border",
        "foreign direct investment",
        "fdi",
        "international finance",
        "external shock",
        "global macro",
        "international monetary",
        "国际经济",
        "汇率",
        "国际金融",
        "跨境资本",
        "国际收支",
        "外商直接投资",
    ],
    "产业经济": [
        "industrial organization",
        "industry dynamics",
        "market power",
        "competition policy",
        "antitrust",
        "pricing",
        "platform economy",
        "merger",
        "vertical integration",
        "firm entry",
        "产业经济",
        "产业组织",
        "反垄断",
        "竞争政策",
        "并购",
        "平台经济",
        "市场势力",
    ],
    "企业创新": [
        "innovation",
        "research and development",
        "r&d",
        "patent",
        "technology adoption",
        "entrepreneurship",
        "startup",
        "knowledge spillover",
        "invention",
        "企业创新",
        "创新",
        "研发",
        "专利",
        "创业",
        "技术扩散",
    ],
    "医药产业": [
        "pharmaceutical industry",
        "pharma",
        "biotech",
        "drug market",
        "drug pricing",
        "reimbursement",
        "biosimilar",
        "generic drug",
        "pipeline",
        "医药产业",
        "制药",
        "药企",
        "药品市场",
        "药品定价",
        "仿制药",
        "生物类似药",
    ],
    "医疗创新": [
        "medical innovation",
        "healthcare innovation",
        "health technology",
        "medical device",
        "digital health",
        "telemedicine",
        "hospital innovation",
        "healthcare delivery",
        "医疗创新",
        "医疗技术",
        "数字医疗",
        "远程医疗",
        "医疗器械",
        "医院创新",
    ],
    "创新药": [
        "innovative drug",
        "first-in-class",
        "novel drug",
        "new molecular entity",
        "nme",
        "clinical trial",
        "fda approval",
        "nmpa approval",
        "nda",
        "bla",
        "oncology drug",
        "gene therapy",
        "biologic",
        "创新药",
        "新药",
        "临床试验",
        "药物审批",
        "肿瘤药",
        "基因治疗",
    ],
}


def normalize_text(text: Any) -> str:
    return re.sub(r"\s+", " ", str(text or "")).strip()


def normalize_name_key(text: str) -> str:
    s = normalize_text(text).lower()
    s = re.sub(r"[^0-9a-z\u4e00-\u9fff]+", " ", s)
    return normalize_text(s)


def strip_html_text(text: str) -> str:
    if not text:
        return ""
    content = unescape(text)
    soup = BeautifulSoup(content, "lxml")
    return normalize_text(soup.get_text(" ", strip=True))


def trim_for_translation(text: str, max_chars: int = MAX_ABSTRACT_TRANSLATE_CHARS) -> str:
    if not text:
        return ""
    s = normalize_text(text)
    if len(s) <= max_chars:
        return s
    return s[:max_chars].rsplit(" ", 1)[0] + " ..."


def fetch_json(url: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    last_error: Optional[Exception] = None
    for attempt in range(1, 4):
        try:
            resp = requests.get(url, params=params, headers=HEADERS, timeout=TIMEOUT)
            resp.raise_for_status()
            return resp.json()
        except Exception as exc:
            last_error = exc
            if attempt < 3:
                time.sleep(1.2 * attempt)
    raise RuntimeError(f"GET failed for {url}: {last_error}")


def safe_title(item: Dict[str, Any]) -> str:
    title = item.get("title", "")
    if isinstance(title, list):
        return normalize_text(title[0] if title else "")
    return normalize_text(title)


def extract_doi_from_url(url: str) -> str:
    m = re.search(r"https?://doi\.org/(.+)", url, flags=re.I)
    return m.group(1).strip() if m else ""


def openalex_abstract_from_doi_url(doi_url: str) -> str:
    doi = extract_doi_from_url(doi_url)
    if not doi:
        return ""

    api_url = f"https://api.openalex.org/works/https://doi.org/{doi}"
    try:
        payload = fetch_json(api_url)
    except Exception:
        return ""

    inverted = payload.get("abstract_inverted_index")
    if not inverted:
        return ""

    words: Dict[int, str] = {}
    max_pos = -1
    for token, positions in inverted.items():
        if not isinstance(positions, list):
            continue
        for p in positions:
            try:
                pi = int(p)
            except Exception:
                continue
            words[pi] = token
            max_pos = max(max_pos, pi)

    if max_pos < 0:
        return ""

    sentence = " ".join(words.get(i, "") for i in range(max_pos + 1))
    return normalize_text(sentence)


def clean_translation_output(text: str) -> str:
    s = normalize_text(text)
    if not s:
        return ""

    s = re.sub(r"^type\s*:\s*.*?text\s*:\s*", "", s, flags=re.I)
    s = re.sub(r"^(translation|译文|翻译)\s*:\s*", "", s, flags=re.I)
    s = s.strip("\"'` ")
    return normalize_text(s)


def date_tuple_from_crossref(item: Dict[str, Any]) -> Tuple[int, int, int]:
    fields = [
        "published-print",
        "published-online",
        "published",
        "issued",
        "created",
        "deposited",
    ]
    for key in fields:
        node = item.get(key, {})
        if not isinstance(node, dict):
            continue
        date_parts = node.get("date-parts")
        if not isinstance(date_parts, list) or not date_parts:
            continue
        first = date_parts[0]
        if not isinstance(first, list) or not first:
            continue
        try:
            y = int(first[0])
            m = int(first[1]) if len(first) > 1 else 1
            d = int(first[2]) if len(first) > 2 else 1
            return (y, m, d)
        except Exception:
            continue
    return (0, 0, 0)


def score_journal_candidate(query_name: str, candidate_title: str) -> int:
    q = normalize_name_key(query_name)
    c = normalize_name_key(candidate_title)
    if not q or not c:
        return -1
    if q == c:
        return 1000

    score = 0
    if q in c or c in q:
        score += 500

    q_tokens = set(q.split())
    c_tokens = set(c.split())
    overlap = len(q_tokens & c_tokens)
    score += overlap * 80
    score -= abs(len(q_tokens) - len(c_tokens)) * 6
    return score


def resolve_crossref_journal(journal: Dict[str, Any]) -> Tuple[str, str, Optional[str]]:
    query_name = normalize_text(journal.get("query_name") or journal.get("name"))
    issn_hint = normalize_text(journal.get("issn"))
    issn_lookup_error = ""
    if issn_hint:
        try:
            payload = fetch_json(f"https://api.crossref.org/journals/{issn_hint}")
            message = payload.get("message", {}) if isinstance(payload, dict) else {}
            title = normalize_text(message.get("title")) or query_name
            return issn_hint, title, None
        except Exception as exc:
            issn_lookup_error = str(exc)

    if query_name and any(ord(ch) > 127 for ch in query_name):
        if issn_lookup_error:
            return "", query_name, f"ISSN lookup failed: {issn_lookup_error}"
        return "", query_name, "Non-ASCII journal title is not supported by Crossref title search."

    try:
        payload = fetch_json(
            "https://api.crossref.org/journals",
            params={"query.title": query_name, "rows": 8},
        )
    except Exception as exc:
        return "", query_name, str(exc)

    items = payload.get("message", {}).get("items", [])
    if not items:
        return "", query_name, "No Crossref journal match found."

    best = None
    best_score = -1
    for row in items:
        title = normalize_text(row.get("title", ""))
        score = score_journal_candidate(query_name, title)
        if score > best_score:
            best = row
            best_score = score

    if not best:
        return "", query_name, "No Crossref journal match found."

    issn_list = best.get("ISSN", [])
    if not isinstance(issn_list, list):
        issn_list = []
    resolved_issn = normalize_text(issn_list[0] if issn_list else "")
    resolved_title = normalize_text(best.get("title")) or query_name
    if not resolved_issn:
        return "", resolved_title, "Crossref result has no ISSN."
    return resolved_issn, resolved_title, None


def determine_latest_issue(items: List[Dict[str, Any]]) -> Tuple[str, str, Tuple[int, int, int]]:
    article_items = [it for it in items if it.get("type") == "journal-article"]
    if not article_items:
        return "", "", (0, 0, 0)

    candidates: List[Tuple[Tuple[int, int, int], str, str]] = []
    for it in article_items:
        volume = normalize_text(it.get("volume"))
        issue = normalize_text(it.get("issue"))
        if not volume or not issue:
            continue
        date_key = date_tuple_from_crossref(it)
        candidates.append((date_key, volume, issue))

    if candidates:
        date_key, volume, issue = max(candidates, key=lambda x: (x[0], x[1], x[2]))
        return volume, issue, date_key

    latest_date = max((date_tuple_from_crossref(it) for it in article_items), default=(0, 0, 0))
    return "", "", latest_date


def in_latest_issue(
    item: Dict[str, Any],
    latest_volume: str,
    latest_issue: str,
    latest_date: Tuple[int, int, int],
) -> bool:
    if latest_volume and latest_issue:
        return (
            normalize_text(item.get("volume")) == latest_volume
            and normalize_text(item.get("issue")) == latest_issue
        )

    y, m, _ = latest_date
    if y <= 0:
        return True

    iy, im, _ = date_tuple_from_crossref(item)
    if iy <= 0:
        return False
    return iy == y and im == m


def detect_econ_topics(title: str, abstract: str) -> List[str]:
    haystack = normalize_text(f"{title} {abstract}").lower()
    if not haystack:
        return []

    matched: List[str] = []
    for topic, terms in ECON_TOPIC_KEYWORDS.items():
        if any(term in haystack for term in terms):
            matched.append(topic)
    return matched


class KimiTranslator:
    def __init__(self, api_key: str, model: str):
        self.api_key = api_key
        self.model = model
        self.enabled = bool(api_key)
        self.cache: Dict[str, str] = {}
        self.success_count = 0
        self.fail_count = 0
        self.fail_samples: List[str] = []
        self._last_call_ts = 0.0

    def warmup_cache(self, old_data: Dict[str, Any]) -> None:
        if not old_data:
            return

        for journal in old_data.get("econ_tracker", {}).get("journals", []):
            for paper in journal.get("papers", []):
                title_en = normalize_text(paper.get("title_en") or paper.get("title"))
                title_zh = normalize_text(paper.get("title_zh"))
                if title_en and title_zh:
                    self.cache[title_en] = title_zh

                abstract_en = normalize_text(paper.get("abstract_en"))
                abstract_zh = normalize_text(paper.get("abstract_zh"))
                if abstract_en and abstract_zh:
                    self.cache[abstract_en] = abstract_zh

    def _record_failure(self, source: str, msg: str) -> None:
        self.fail_count += 1
        if len(self.fail_samples) < 6:
            self.fail_samples.append(f"{source[:80]} :: {msg[:160]}")

    def _respect_rate_limit(self) -> None:
        if KIMI_MIN_INTERVAL_SECONDS <= 0:
            return
        now = time.time()
        wait_s = KIMI_MIN_INTERVAL_SECONDS - (now - self._last_call_ts)
        if wait_s > 0:
            time.sleep(wait_s)

    def translate(self, text: str, kind: str = "text") -> str:
        source = normalize_text(text)
        if not source:
            return ""

        if source in self.cache:
            return self.cache[source]

        if not self.enabled:
            return ""

        user_prompt = (
            "Translate the following English content into Simplified Chinese. "
            "Keep economics and innovation terminology precise. Output translation only.\n\n"
            f"Type: {kind}\n"
            f"Text:\n{source}"
        )

        payload = {
            "model": self.model,
            "temperature": 0,
            "messages": [
                {"role": "system", "content": "You are a professional translator for economics and innovation studies."},
                {"role": "user", "content": user_prompt},
            ],
        }

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        for attempt in range(4):
            try:
                self._respect_rate_limit()
                resp = requests.post(
                    f"{KIMI_API_BASE}/chat/completions",
                    headers=headers,
                    json=payload,
                    timeout=90,
                )
                self._last_call_ts = time.time()

                if resp.status_code >= 400:
                    raise requests.HTTPError(f"HTTP {resp.status_code}: {resp.text[:200]}")

                data = resp.json()
                translated = clean_translation_output(data["choices"][0]["message"]["content"])
                if not translated:
                    raise ValueError("Empty translation")

                self.cache[source] = translated
                self.success_count += 1
                return translated
            except Exception as exc:
                if attempt < 3:
                    time.sleep(2 * (attempt + 1))
                else:
                    self.cache[source] = ""
                    self._record_failure(source, str(exc))
                    return ""

        return ""


def build_econ_journal_block(journal: Dict[str, Any], translator: KimiTranslator) -> Dict[str, Any]:
    result: Dict[str, Any] = {
        "name": journal.get("name"),
        "query_name": journal.get("query_name") or journal.get("name"),
        "issn": normalize_text(journal.get("issn")),
        "resolved_name": journal.get("name"),
        "issue_title": "Latest issue (Crossref)",
        "issue_url": journal.get("issue_url", ""),
        "matched_count": 0,
        "total_in_issue": 0,
        "papers": [],
        "error": None,
    }

    resolved_issn, resolved_name, resolve_error = resolve_crossref_journal(journal)
    if resolved_name:
        result["resolved_name"] = resolved_name
    if resolved_issn:
        result["issn"] = resolved_issn

    if not resolved_issn:
        result["error"] = resolve_error or "Unable to resolve journal ISSN from Crossref."
        return result

    api = f"https://api.crossref.org/journals/{resolved_issn}/works"

    try:
        payload = fetch_json(
            api,
            params={
                "sort": "published",
                "order": "desc",
                "rows": 220,
                "select": (
                    "title,URL,volume,issue,type,abstract,"
                    "published-print,published-online,published,issued"
                ),
            },
        )
        items = payload.get("message", {}).get("items", [])
        latest_volume, latest_issue, latest_date = determine_latest_issue(items)

        if latest_volume and latest_issue:
            result["issue_title"] = f"Volume {latest_volume}, Issue {latest_issue}"
        elif latest_date[0] > 0:
            result["issue_title"] = f"Published {latest_date[0]:04d}-{latest_date[1]:02d}"

        picked: List[Dict[str, Any]] = []
        total_in_issue = 0

        for it in items:
            if it.get("type") != "journal-article":
                continue

            title_en = safe_title(it)
            url = normalize_text(it.get("URL", ""))
            if not title_en or not url:
                continue

            if not in_latest_issue(it, latest_volume, latest_issue, latest_date):
                continue

            total_in_issue += 1

            abstract_en = strip_html_text(it.get("abstract", ""))
            if not abstract_en:
                abstract_en = openalex_abstract_from_doi_url(url)
            abstract_en = normalize_text(abstract_en)

            matched_topics = detect_econ_topics(title_en, abstract_en)
            if not matched_topics:
                continue

            title_zh = translator.translate(title_en, kind="title")
            abstract_zh = (
                translator.translate(trim_for_translation(abstract_en), kind="abstract")
                if abstract_en
                else ""
            )

            picked.append(
                {
                    "title_en": title_en,
                    "title_zh": title_zh,
                    "url": url,
                    "abstract_en": abstract_en,
                    "abstract_zh": abstract_zh,
                    "matched_topics": matched_topics,
                }
            )

            if len(picked) >= MAX_ECON_PAPERS_PER_JOURNAL:
                break

        result["papers"] = picked
        result["matched_count"] = len(picked)
        result["total_in_issue"] = total_in_issue
        if resolve_error:
            result["error"] = f"ISSN fallback used: {resolve_error}"

    except Exception as exc:
        result["error"] = str(exc)

    return result


def build_econ_tracker_block(translator: KimiTranslator) -> Dict[str, Any]:
    journals = [build_econ_journal_block(j, translator) for j in ECON_JOURNALS]
    return {
        "topics": list(ECON_TOPIC_KEYWORDS.keys()),
        "topic_keywords": ECON_TOPIC_KEYWORDS,
        "max_papers_per_journal": MAX_ECON_PAPERS_PER_JOURNAL,
        "journals": journals,
        "note": (
            "Filter by title/abstract keywords for international trade, international economics, "
            "industrial economics, firm innovation, pharmaceutical industry, healthcare innovation, "
            "and innovative drugs in latest issue TOCs."
        ),
    }


def load_previous_data() -> Dict[str, Any]:
    if not OUTPUT.exists():
        return {}
    try:
        return json.loads(OUTPUT.read_text(encoding="utf-8"))
    except Exception:
        return {}


def main() -> None:
    previous = load_previous_data()
    translator = KimiTranslator(api_key=KIMI_API_KEY, model=KIMI_MODEL)
    translator.warmup_cache(previous)
    econ_tracker = build_econ_tracker_block(translator)

    payload = {
        "updated_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"),
        "translation": {
            "engine": "kimi",
            "model": KIMI_MODEL,
            "enabled": translator.enabled,
            "success_count": translator.success_count,
            "fail_count": translator.fail_count,
            "failed_examples": translator.fail_samples,
            "note": "Set KIMI_API_KEY to enable Chinese translation.",
        },
        "econ_tracker": econ_tracker,
    }

    if translator.enabled and translator.success_count == 0:
        print(
            "Warning: Kimi translation is enabled but no translation succeeded. "
            f"Failures: {translator.fail_samples[:2]}"
        )

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    total_matches = sum(len(j.get("papers", [])) for j in econ_tracker.get("journals", []))
    print(f"Wrote: {OUTPUT}")
    print(
        "Translation stats: "
        f"enabled={translator.enabled}, success={translator.success_count}, fail={translator.fail_count}"
    )
    print(
        "Journals tracked: "
        f"{len(econ_tracker.get('journals', []))}, total matched papers={total_matches}"
    )


if __name__ == "__main__":
    main()
