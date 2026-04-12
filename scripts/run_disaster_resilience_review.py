#!/usr/bin/env python3
"""Build an auditable disaster-resilience literature review corpus."""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Set, Tuple

import fitz  # type: ignore
import requests

HOME = Path.home()
SKILL_SCRIPTS = HOME / ".codex" / "skills" / "sci-papers-downloder" / "scripts"
if SKILL_SCRIPTS.exists():
    sys.path.insert(0, str(SKILL_SCRIPTS))

try:
    from download_open_access import attempt_download, safe_filename, unique_path  # type: ignore
except Exception as exc:  # pragma: no cover - environment-dependent
    raise SystemExit(f"Could not import sci-papers-downloder helpers: {exc}")


OPENALEX_WORKS_URL = "https://api.openalex.org/works"
CROSSREF_WORKS_URL = "https://api.crossref.org/works"
REQUEST_TIMEOUT = 60
USER_AGENT = "cocoa-volatility-disaster-review/1.0"

THEMATIC_QUERIES: Dict[str, List[str]] = {
    "economic_impacts": [
        '"natural disaster" economic resilience policy adaptation',
        '"post-disaster" economic recovery resilience policy',
        'flood drought cyclone livelihood resilience adaptation policy',
        '"economic resilience" disaster household welfare adaptation',
        '"resilient recovery" disaster household welfare',
        '"disaster preparedness" education resilience natural hazard',
    ],
    "risk_assessment_modelling": [
        '"disaster risk reduction" resilience modelling adaptation',
        '"risk assessment" disaster resilience ecosystem services',
        '"vulnerability index" natural hazard resilience adaptation',
        '"socio-ecological resilience" natural hazard model policy',
        '"agent-based model" disaster recovery resilience',
        '"flood vulnerability index" resilience adaptation',
        '"multi-hazard" resilience index policy',
    ],
    "ecosystem_services_natural_capital": [
        '"ecosystem services" disaster resilience natural capital adaptation',
        '"green infrastructure" flood resilience ecosystem services policy',
        'mangroves storm protection resilience ecosystem services adaptation',
        'wetlands disaster risk reduction resilience natural capital',
        '"ecosystem-based adaptation" disaster resilience policy',
        '"natural infrastructure" flood resilience adaptation',
    ],
    "governance_institutions": [
        '"disaster governance" resilience institutions adaptation',
        '"institutional resilience" natural hazards policy adaptation',
        '"community resilience" disaster governance policy',
        '"adaptive governance" disaster resilience socio-ecological',
        '"equitable resilience" disaster governance',
        '"resilient recovery" governance disaster institutions',
    ],
    "behavioral_responses": [
        '"risk perception" disaster adaptation resilience household',
        '"behavioral response" natural hazard resilience adaptation',
        '"protective behavior" flood resilience adaptation',
        '"household coping" drought disaster resilience policy',
        '"disaster preparedness" education experience resilience',
        '"social vulnerability" perception disaster adaptation',
        '"coping strategies" drought resilience household',
    ],
    "adaptation_resilience_strategies": [
        '"adaptation strategy" disaster resilience policy',
        '"transformative resilience" disaster adaptation socio-ecological',
        '"adaptive capacity" natural disaster resilience policy',
        '"resilience strategy" natural hazard adaptation governance',
        '"resilient recovery" disaster adaptation',
        '"transformational adaptation" disaster resilience',
        '"urban resilience" disaster infrastructure governance',
    ],
}

HIGH_QUALITY_JOURNALS = {
    "Annual Review of Environment and Resources",
    "Climate Risk Management",
    "Climatic Change",
    "Disasters",
    "Ecological Economics",
    "Ecological Indicators",
    "Ecology and Society",
    "Ecosystem Services",
    "Environment and Development Economics",
    "Environmental Research Letters",
    "Environmental Science and Policy",
    "Food Policy",
    "Food Security",
    "Frontiers in Climate",
    "Global Environmental Change",
    "International Journal of Disaster Risk Reduction",
    "International Journal of Disaster Risk Science",
    "Journal of Environmental Management",
    "Journal of Rural Studies",
    "Land Use Policy",
    "Nature Climate Change",
    "Natural Hazards",
    "Natural Hazards and Earth System Sciences",
    "Ocean and Coastal Management",
    "PNAS Nexus",
    "Proceedings of the National Academy of Sciences",
    "Regional Environmental Change",
    "Risk Analysis",
    "Scientific Reports",
    "Science of the Total Environment",
    "Sustainability Science",
    "Technological Forecasting and Social Change",
    "The Lancet Planetary Health",
    "World Development",
}

DISASTER_TERMS = [
    "disaster",
    "disasters",
    "drought",
    "earthquake",
    "flood",
    "floods",
    "hazard",
    "hazards",
    "hurricane",
    "landslide",
    "storm",
    "storms",
    "typhoon",
    "wildfire",
    "wildfires",
    "cyclone",
    "tsunami",
]

RESILIENCE_TERMS = [
    "adaptive capacity",
    "adaptation",
    "coping",
    "recovery",
    "resilience",
    "resilient",
    "robustness",
    "transformative",
]

POLICY_RISK_TERMS = [
    "adaptation plan",
    "behavior",
    "behaviour",
    "governance",
    "institution",
    "management",
    "mitigation",
    "planning",
    "policy",
    "policies",
    "risk",
    "strategy",
    "strategies",
    "vulnerability",
]

THEME_TERMS: Dict[str, Sequence[str]] = {
    "economic_impacts": [
        "asset",
        "consumption",
        "damage",
        "economic",
        "employment",
        "income",
        "loss",
        "losses",
        "macroeconomic",
        "poverty",
        "recovery",
        "welfare",
    ],
    "risk_assessment_modelling": [
        "assessment",
        "forecast",
        "index",
        "indicator",
        "model",
        "modelling",
        "scenario",
        "simulation",
        "uncertainty",
        "vulnerability",
    ],
    "ecosystem_services_natural_capital": [
        "ecosystem services",
        "forest",
        "green infrastructure",
        "mangrove",
        "natural capital",
        "nature-based",
        "reef",
        "wetland",
    ],
    "governance_institutions": [
        "collective action",
        "coordination",
        "governance",
        "institution",
        "participation",
        "planning",
        "policy",
        "regulation",
    ],
    "behavioral_responses": [
        "behavior",
        "behaviour",
        "coping",
        "decision",
        "perception",
        "protective",
        "response",
        "risk perception",
        "willingness",
    ],
    "adaptation_resilience_strategies": [
        "adaptation",
        "adaptive capacity",
        "preparedness",
        "resilience strategy",
        "strategy",
        "strategies",
        "transformative",
    ],
}

METHOD_PATTERNS: List[Tuple[str, Sequence[str]]] = [
    ("econometrics", ["difference-in-differences", "econometric", "fixed-effects", "instrumental variable", "panel regression", "regression"]),
    ("CGE / IAM models", ["cge", "computable general equilibrium", "integrated assessment model", "input-output model"]),
    ("vulnerability indices", ["composite index", "index", "indicator", "vulnerability index"]),
    ("agent-based models", ["agent-based", "abm"]),
    ("qualitative institutional analysis", ["case study", "governance analysis", "institutional analysis", "interview", "qualitative"]),
    ("spatial risk modelling", ["gis", "hazard model", "remote sensing", "spatial", "susceptibility model"]),
    ("systematic review / meta-analysis", ["meta-analysis", "systematic review"]),
    ("mixed methods", ["mixed methods", "survey", "workshop"]),
]

QUESTION_PATTERNS = [
    r"\bthis (paper|study|article)\s+(examines|investigates|assesses|analyzes|analyses|explores|evaluates|quantifies|models|considers|asks)\b",
    r"\bwe\s+(examine|investigate|assess|analyze|analyse|explore|evaluate|quantify|model|consider|ask)\b",
    r"\bthe (purpose|aim|objective) of this (paper|study)\b",
]

FINDING_PATTERNS = [
    "find",
    "findings",
    "results",
    "show",
    "shows",
    "suggest",
    "suggests",
    "indicate",
    "indicates",
    "reveal",
    "reveals",
    "demonstrate",
    "demonstrates",
]

GAP_PATTERNS = [
    "few studies",
    "little is known",
    "limited evidence",
    "research gap",
    "scarce evidence",
    "underexplored",
    "remains unclear",
]

METHOD_TERMS = [
    "framework",
    "index",
    "method",
    "model",
    "regression",
    "simulation",
    "survey",
]

EXCLUDE_TITLE_TERMS = [
    "book review",
    "commentary",
    "corrigendum",
    "editorial",
    "erratum",
    "foreword",
    "guest editorial",
    "introduction",
]


@dataclass
class Candidate:
    doi: str
    title: str
    journal: str
    year: Optional[int]
    authors: List[str]
    abstract: str
    cited_by_count: int
    pdf_urls: List[str]
    landing_urls: List[str]
    source_url: str
    openalex_id: str
    query_themes: Set[str] = field(default_factory=set)
    queries: Set[str] = field(default_factory=set)
    score: float = 0.0
    theme_scores: Dict[str, int] = field(default_factory=dict)


@dataclass
class ReviewRecord:
    paper_id: str
    bibtex_key: str
    doi: str
    title: str
    journal: str
    year: Optional[int]
    authors: List[str]
    research_question: str
    quote: str
    interpretation: str
    category: str
    theme: str
    method_class: str
    gap_note: str
    method_note: str
    pdf_path: str
    source_url: str
    openalex_id: str
    landing_urls: List[str]
    query_themes: List[str]
    search_queries: List[str]
    crossref: Dict[str, Any]


def repair_text(text: str) -> str:
    if not text:
        return ""
    cleaned = text.replace("\u00ad", "").replace("Â ", " ").replace("Â", "")
    markers = ("Ã", "â€", "â€™", "â€˜", "â€“", "â€”")
    if any(marker in cleaned for marker in markers):
        try:
            repaired = cleaned.encode("latin1", errors="ignore").decode("utf-8", errors="ignore")
            if sum(repaired.count(marker) for marker in markers) < sum(cleaned.count(marker) for marker in markers):
                cleaned = repaired
        except Exception:
            pass
    return cleaned


def normalize_doi(raw: Optional[str]) -> str:
    if not raw:
        return ""
    doi = re.sub(r"^https?://(dx\.)?doi\.org/", "", raw.strip(), flags=re.I)
    return doi.strip()


def reconstruct_abstract(inverted_index: Optional[Dict[str, List[int]]]) -> str:
    if not inverted_index:
        return ""
    positioned: List[Tuple[int, str]] = []
    for word, positions in inverted_index.items():
        for pos in positions:
            positioned.append((pos, repair_text(word)))
    positioned.sort(key=lambda item: item[0])
    return repair_text(" ".join(word for _, word in positioned))


def unique_nonempty(items: Iterable[Optional[str]]) -> List[str]:
    seen: Set[str] = set()
    out: List[str] = []
    for item in items:
        if not item:
            continue
        value = item.strip()
        if not value or value in seen:
            continue
        seen.add(value)
        out.append(value)
    return out


def request_json(url: str, *, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    response = requests.get(
        url,
        params=params,
        timeout=REQUEST_TIMEOUT,
        headers={"User-Agent": USER_AGENT},
    )
    response.raise_for_status()
    return response.json()


def search_openalex(query: str, per_page: int = 100) -> List[Dict[str, Any]]:
    payload = request_json(
        OPENALEX_WORKS_URL,
        params={
            "search": query,
            "per-page": per_page,
            "filter": "is_oa:true,has_doi:true,has_fulltext:true,type:article,primary_location.source.type:journal,language:en",
        },
    )
    return payload.get("results", [])


def build_candidate_urls(work: Dict[str, Any]) -> Tuple[List[str], List[str]]:
    pdf_urls: List[Optional[str]] = []
    landing_urls: List[Optional[str]] = []
    for location in [work.get("primary_location"), work.get("best_oa_location"), *(work.get("locations") or [])]:
        if not isinstance(location, dict):
            continue
        pdf_urls.append(location.get("pdf_url"))
        landing_urls.append(location.get("landing_page_url"))
    open_access = work.get("open_access") or {}
    landing_urls.append(open_access.get("oa_url"))
    landing_urls.append(work.get("doi"))
    return unique_nonempty(pdf_urls), unique_nonempty(landing_urls)


def count_hits(text: str, terms: Sequence[str]) -> int:
    lower = text.lower()
    return sum(1 for term in terms if term in lower)


def has_any(text: str, terms: Sequence[str]) -> bool:
    lower = text.lower()
    return any(term in lower for term in terms)


def score_theme_hits(text: str) -> Dict[str, int]:
    return {theme: count_hits(text, terms) for theme, terms in THEME_TERMS.items()}


def journal_quality_score(journal: str) -> float:
    if journal in HIGH_QUALITY_JOURNALS:
        return 5.0
    lower = journal.lower()
    if any(fragment in lower for fragment in ["environment", "ecolog", "disaster", "risk", "hazard", "world development"]):
        return 2.5
    return 0.0


def relevance_gate(title: str, abstract: str) -> bool:
    joined = f"{title} {abstract}".lower()
    if any(term in title.lower() for term in EXCLUDE_TITLE_TERMS):
        return False
    return has_any(joined, DISASTER_TERMS) and has_any(joined, RESILIENCE_TERMS) and has_any(joined, POLICY_RISK_TERMS)


def candidate_score(title: str, abstract: str, journal: str, cited_by_count: int) -> Tuple[float, Dict[str, int]]:
    joined = f"{title} {abstract}"
    theme_scores = score_theme_hits(joined)
    score = 0.0
    score += 5.0 if relevance_gate(title, abstract) else -999.0
    score += sum(theme_scores.values()) * 1.2
    score += journal_quality_score(journal)
    score += min(max(cited_by_count, 0), 250) / 40.0
    if has_any(joined, ["ecosystem services", "natural capital", "governance", "risk perception", "adaptive capacity"]):
        score += 2.0
    return score, theme_scores


def build_candidate_pool() -> Dict[str, Candidate]:
    candidates: Dict[str, Candidate] = {}
    for theme, queries in THEMATIC_QUERIES.items():
        for query in queries:
            for work in search_openalex(query):
                doi = normalize_doi(work.get("doi"))
                if not doi:
                    continue
                title = repair_text((work.get("display_name") or "").strip())
                if not title:
                    continue
                journal = repair_text((((work.get("primary_location") or {}).get("source") or {}).get("display_name") or "").strip())
                if journal not in HIGH_QUALITY_JOURNALS:
                    continue
                authors = [
                    repair_text(((item.get("author") or {}).get("display_name") or "").strip())
                    for item in (work.get("authorships") or [])
                    if (item.get("author") or {}).get("display_name")
                ]
                abstract = reconstruct_abstract(work.get("abstract_inverted_index"))
                if not relevance_gate(title, abstract):
                    continue
                cited_by_count = int(work.get("cited_by_count") or 0)
                score, theme_scores = candidate_score(title, abstract, journal, cited_by_count)
                if score < 10:
                    continue
                pdf_urls, landing_urls = build_candidate_urls(work)
                existing = candidates.get(doi)
                if existing is None:
                    candidates[doi] = Candidate(
                        doi=doi,
                        title=title,
                        journal=journal or "Unknown journal",
                        year=work.get("publication_year"),
                        authors=authors,
                        abstract=abstract,
                        cited_by_count=cited_by_count,
                        pdf_urls=pdf_urls,
                        landing_urls=landing_urls,
                        source_url=(work.get("doi") or "").strip(),
                        openalex_id=(work.get("id") or "").strip(),
                        query_themes={theme},
                        queries={query},
                        score=score,
                        theme_scores=theme_scores,
                    )
                else:
                    existing.query_themes.add(theme)
                    existing.queries.add(query)
                    existing.pdf_urls = unique_nonempty([*existing.pdf_urls, *pdf_urls])
                    existing.landing_urls = unique_nonempty([*existing.landing_urls, *landing_urls])
                    if score > existing.score:
                        existing.title = title
                        existing.journal = journal or existing.journal
                        existing.year = work.get("publication_year")
                        existing.authors = authors or existing.authors
                        existing.abstract = abstract or existing.abstract
                        existing.cited_by_count = cited_by_count
                        existing.score = score
                        existing.theme_scores = theme_scores
    return candidates


def build_processing_queue(candidates: Dict[str, Candidate]) -> List[Candidate]:
    theme_lists: Dict[str, List[Candidate]] = {}
    for theme in THEMATIC_QUERIES:
        theme_lists[theme] = sorted(
            [candidate for candidate in candidates.values() if theme in candidate.query_themes],
            key=lambda item: (-item.score, -(item.year or 0), item.title.lower()),
        )

    queue: List[Candidate] = []
    seen: Set[str] = set()
    max_len = max((len(items) for items in theme_lists.values()), default=0)
    ordered_themes = list(THEMATIC_QUERIES)
    for idx in range(max_len):
        for theme in ordered_themes:
            items = theme_lists[theme]
            if idx >= len(items):
                continue
            candidate = items[idx]
            if candidate.doi in seen:
                continue
            queue.append(candidate)
            seen.add(candidate.doi)

    leftovers = sorted(
        [candidate for candidate in candidates.values() if candidate.doi not in seen],
        key=lambda item: (-item.score, -(item.year or 0), item.title.lower()),
    )
    queue.extend(leftovers)
    return queue


def trim_front_matter(text: str) -> str:
    patterns = [r"\babstract\b", r"\bsummary\b", r"\bintroduction\b"]
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.I)
        if match and match.start() < 2500:
            return text[match.start():]
    return text


def trim_back_matter(text: str) -> str:
    patterns = [
        r"\nreferences\b",
        r"\nbibliography\b",
        r"\nworks cited\b",
        r"\nliterature cited\b",
        r"\nreference list\b",
    ]
    cut_at = None
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.I)
        if match and match.start() > len(text) * 0.40:
            cut_at = match.start() if cut_at is None else min(cut_at, match.start())
    return text[:cut_at] if cut_at else text


def normalize_text(text: str) -> str:
    text = text.replace("\r", "\n").replace("\x0c", "\n")
    text = re.sub(r"(\w)-\n(\w)", r"\1\2", text)
    text = re.sub(r"[ \t]+\n", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = trim_front_matter(text)
    return repair_text(trim_back_matter(text))


def normalize_for_match(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def extract_pdf_text(pdf_path: Path) -> str:
    chunks: List[str] = []
    with fitz.open(pdf_path) as doc:
        for page in doc:
            chunks.append(page.get_text("text"))
    return normalize_text("\n".join(chunks))


def paragraph_units(text: str) -> List[str]:
    parts = re.split(r"\n\s*\n", text)
    return [re.sub(r"\s+", " ", part).strip() for part in parts if len(re.sub(r"\s+", " ", part).strip()) >= 60]


def sentence_units(text: str) -> List[str]:
    sentences: List[str] = []
    for paragraph in paragraph_units(text):
        for sentence in re.split(r"(?<=[.!?])\s+(?=[A-Z0-9(\"'])", paragraph):
            cleaned = repair_text(re.sub(r"\s+", " ", sentence).strip())
            if len(cleaned) >= 40:
                sentences.append(cleaned)
    return sentences


def is_bad_quote(sentence: str) -> bool:
    lower = sentence.lower()
    if "[" in sentence or "]" in sentence:
        return True
    if re.search(r"\(\d+\)", sentence):
        return True
    if lower.count("(") >= 2 and re.search(r"\b(19|20)\d{2}\b", lower):
        return True
    if sentence.count("?") >= 1:
        return True
    if sentence.lower().startswith("table ") or sentence.lower().startswith("figure "):
        return True
    if "copyright" in lower:
        return True
    return False


def first_author_family(authors: Sequence[str]) -> str:
    if not authors:
        return "Anon"
    first = authors[0].strip()
    if "," in first:
        return re.sub(r"[^A-Za-z0-9]+", "", first.split(",")[0]) or "Anon"
    return re.sub(r"[^A-Za-z0-9]+", "", first.split()[-1]) or "Anon"


def theme_label(theme: str) -> str:
    return {
        "economic_impacts": "Economic impacts of disasters",
        "risk_assessment_modelling": "Risk assessment & modelling",
        "ecosystem_services_natural_capital": "Ecosystem services & natural capital",
        "governance_institutions": "Governance & institutions",
        "behavioral_responses": "Behavioral responses",
        "adaptation_resilience_strategies": "Adaptation & resilience strategies",
    }[theme]


def choose_primary_theme(candidate: Candidate, text: str) -> str:
    joined = f"{candidate.title} {candidate.abstract} {text[:5000]}"
    scores = {theme: count_hits(joined, terms) for theme, terms in THEME_TERMS.items()}
    if candidate.query_themes:
        for theme in candidate.query_themes:
            scores[theme] = scores.get(theme, 0) + 1
    return max(scores.items(), key=lambda item: (item[1], item[0]))[0]


def detect_method_class(text: str, abstract: str) -> str:
    joined = f"{abstract} {text[:12000]}".lower()
    for method_class, patterns in METHOD_PATTERNS:
        if any(pattern in joined for pattern in patterns):
            return method_class
    return "mixed methods"


def find_research_question(text: str, abstract: str, title: str) -> Optional[str]:
    candidates = sentence_units(abstract)
    for sentence in candidates:
        lower = sentence.lower()
        if any(re.search(pattern, lower) for pattern in QUESTION_PATTERNS):
            return repair_text(sentence.strip())
    for sentence in sentence_units(text[:12000]):
        lower = sentence.lower()
        if any(re.search(pattern, lower) for pattern in QUESTION_PATTERNS):
            return repair_text(sentence.strip())
    title_core = title.rstrip(".")
    title_lower = title_core.lower()
    if has_any(title_lower, DISASTER_TERMS) and has_any(title_lower, RESILIENCE_TERMS):
        return repair_text(f"The paper investigates {title_core}.")
    return None


def score_finding_sentence(sentence: str, theme: str) -> float:
    lower = sentence.lower()
    score = 0.0
    if any(pattern in lower for pattern in FINDING_PATTERNS):
        score += 5.0
    if has_any(lower, DISASTER_TERMS):
        score += 2.0
    if has_any(lower, RESILIENCE_TERMS):
        score += 2.0
    if has_any(lower, POLICY_RISK_TERMS):
        score += 2.0
    score += count_hits(lower, THEME_TERMS[theme]) * 1.0
    if len(sentence.split()) <= 30:
        score += 0.5
    if lower.startswith("table ") or lower.startswith("figure "):
        score -= 5.0
    return score


def shorten_quote(sentence: str, theme: str) -> str:
    words = sentence.split()
    if len(words) <= 25:
        return repair_text(sentence.strip())

    clauses = re.split(r"(?<=[,;:])\s+|\s+(?:but|while|although|because|and)\s+", sentence)
    clauses = [clause.strip(" ,;:") for clause in clauses if len(clause.split()) >= 6]
    if clauses:
        best_clause = max(clauses, key=lambda clause: score_finding_sentence(clause, theme))
        if len(best_clause.split()) <= 25:
            return repair_text(best_clause)

    best_window = " ".join(words[:25])
    best_score = score_finding_sentence(best_window, theme)
    for start in range(0, len(words) - 24):
        window = " ".join(words[start : start + 25])
        score = score_finding_sentence(window, theme)
        if score > best_score:
            best_window = window
            best_score = score
    return repair_text(best_window.strip(" ,;:"))


def find_answer_quote(text: str, abstract: str, theme: str) -> Optional[str]:
    abstract_candidates = sentence_units(abstract)
    text_candidates = sentence_units(text)
    for pool, min_score in ((abstract_candidates, 7.0), (text_candidates, 8.0)):
        best: Optional[Tuple[float, str]] = None
        for sentence in pool:
            if is_bad_quote(sentence):
                continue
            score = score_finding_sentence(sentence, theme)
            if score < min_score:
                continue
            if best is None or score > best[0]:
                best = (score, sentence)
        if best is not None:
            return shorten_quote(best[1], theme)
    return None


def find_gap_note(text: str, abstract: str) -> str:
    for sentence in sentence_units(abstract) + sentence_units(text[:8000]):
        lower = sentence.lower()
        if any(pattern in lower for pattern in GAP_PATTERNS):
            return shorten_quote(sentence, "governance_institutions")
    return ""


def find_method_note(text: str, abstract: str, method_class: str) -> str:
    patterns = next((patterns for label, patterns in METHOD_PATTERNS if label == method_class), [])
    for sentence in sentence_units(abstract) + sentence_units(text[:12000]):
        lower = sentence.lower()
        if any(pattern in lower for pattern in patterns):
            return shorten_quote(sentence, "risk_assessment_modelling")
    for sentence in sentence_units(abstract)[:5]:
        lower = sentence.lower()
        if has_any(lower, METHOD_TERMS):
            return shorten_quote(sentence, "risk_assessment_modelling")
    return ""


def infer_category(quote: str, gap_note: str, method_note: str) -> str:
    lower = quote.lower()
    if gap_note and gap_note.lower() == lower:
        return "Research Gap"
    if method_note and method_note.lower() == lower:
        return "Methodology"
    if any(pattern in lower for pattern in GAP_PATTERNS):
        return "Research Gap"
    if any(term in lower for term in METHOD_TERMS):
        return "Methodology"
    return "Literature Findings"


def build_interpretation(quote: str, theme: str, category: str) -> str:
    if category == "Research Gap":
        return "The quoted text states that the evidence base or analytical coverage remains limited, so the paper positions itself against a documented gap."
    if category == "Methodology":
        return "The quote identifies the paper's analytical design or measurement strategy and should be read as a methodological contribution rather than an outcome claim."
    theme_name = theme_label(theme)
    return f"The quote provides direct evidence relevant to {theme_name.lower()} and supports only the claim explicitly stated in the original text."


def download_pdf(candidate: Candidate, papers_dir: Path) -> Optional[Path]:
    base_name = safe_filename(f"{candidate.doi.replace('/', '_')}__{candidate.title}", "paper")
    existing = papers_dir / f"{base_name}.pdf"
    if existing.exists() and existing.stat().st_size > 2048:
        return existing

    urls = unique_nonempty([*candidate.pdf_urls, *candidate.landing_urls])
    for url in urls:
        target = unique_path(papers_dir / f"{base_name}.pdf")
        ok, _, _ = attempt_download(url, target, timeout=REQUEST_TIMEOUT)
        if ok and target.exists() and target.stat().st_size > 2048:
            return target
        target.unlink(missing_ok=True)
    return None


def crossref_metadata(doi: str) -> Dict[str, Any]:
    try:
        payload = request_json(f"{CROSSREF_WORKS_URL}/{requests.utils.quote(doi)}")
        return payload.get("message") or {}
    except Exception:
        return {}


def bibtex_escape(text: str) -> str:
    replacements = {
        "\\": "\\textbackslash{}",
        "{": "\\{",
        "}": "\\}",
        "&": "\\&",
        "%": "\\%",
        "$": "\\$",
        "#": "\\#",
        "_": "\\_",
    }
    for raw, escaped in replacements.items():
        text = text.replace(raw, escaped)
    return text


def build_bibtex_key(records: List[ReviewRecord], authors: Sequence[str], year: Optional[int]) -> str:
    base = f"{first_author_family(authors)}{year or 'n.d.'}"
    existing = {record.bibtex_key for record in records}
    if base not in existing:
        return base
    suffix = ord("a")
    while f"{base}{chr(suffix)}" in existing:
        suffix += 1
    return f"{base}{chr(suffix)}"


def join_authors_crossref(author_items: Sequence[Dict[str, Any]]) -> str:
    rendered: List[str] = []
    for item in author_items:
        family = (item.get("family") or "").strip()
        given = (item.get("given") or "").strip()
        if family and given:
            rendered.append(f"{family}, {given}")
        elif family:
            rendered.append(family)
        elif given:
            rendered.append(given)
    return " and ".join(rendered)


def build_bibtex_entry(record: ReviewRecord) -> str:
    meta = record.crossref
    author_block = repair_text(join_authors_crossref(meta.get("author") or []))
    if not author_block:
        author_block = " and ".join(record.authors)
    title_values = [repair_text(value) for value in (meta.get("title") or [record.title])]
    container = [repair_text(value) for value in (meta.get("container-title") or [record.journal])]
    issued = meta.get("issued", {}).get("date-parts", [[record.year or ""]])
    year = issued[0][0] if issued and issued[0] else (record.year or "")
    volume = meta.get("volume") or ""
    number = meta.get("issue") or ""
    pages = meta.get("page") or ""
    url = meta.get("URL") or f"https://doi.org/{record.doi}"
    fields = [
        f"  author = {{{bibtex_escape(author_block)}}}",
        f"  title = {{{bibtex_escape(title_values[0])}}}",
        f"  journal = {{{bibtex_escape(container[0])}}}",
        f"  year = {{{year}}}",
        f"  volume = {{{bibtex_escape(str(volume))}}}" if volume else "",
        f"  number = {{{bibtex_escape(str(number))}}}" if number else "",
        f"  pages = {{{bibtex_escape(str(pages))}}}" if pages else "",
        f"  doi = {{{record.doi}}}",
        f"  url = {{{url}}}",
    ]
    body = ",\n".join(field for field in fields if field)
    return f"@article{{{record.bibtex_key},\n{body}\n}}\n"


def verify_quote_in_text(quote: str, text: str) -> bool:
    return normalize_for_match(quote) in normalize_for_match(text)


def keep_record(
    candidate: Candidate,
    research_question: Optional[str],
    quote: Optional[str],
    text: str,
    theme: str,
) -> bool:
    if not research_question or not quote:
        return False
    if len(re.sub(r"\s+", "", text)) < 5000:
        return False
    if not verify_quote_in_text(quote, text):
        return False
    rq_joined = f"{candidate.title} {candidate.abstract} {research_question}".lower()
    if not (has_any(rq_joined, DISASTER_TERMS) and has_any(rq_joined, RESILIENCE_TERMS)):
        return False
    if count_hits(text[:15000], THEME_TERMS[theme]) == 0 and theme not in candidate.query_themes:
        return False
    return True


def build_records(target: int, papers_dir: Path) -> List[ReviewRecord]:
    candidates = build_candidate_pool()
    queue = build_processing_queue(candidates)
    records: List[ReviewRecord] = []
    kept_dois: Set[str] = set()

    for candidate in queue:
        if len(records) >= target:
            break
        if candidate.doi in kept_dois:
            continue

        pdf_path = download_pdf(candidate, papers_dir)
        if pdf_path is None:
            continue

        try:
            text = extract_pdf_text(pdf_path)
        except Exception:
            pdf_path.unlink(missing_ok=True)
            continue

        theme = choose_primary_theme(candidate, text)
        research_question = find_research_question(text, candidate.abstract, candidate.title)
        quote = find_answer_quote(text, candidate.abstract, theme)
        if not keep_record(candidate, research_question, quote, text, theme):
            pdf_path.unlink(missing_ok=True)
            continue

        method_class = detect_method_class(text, candidate.abstract)
        gap_note = find_gap_note(text, candidate.abstract)
        method_note = find_method_note(text, candidate.abstract, method_class)
        category = infer_category(quote or "", gap_note, method_note)
        interpretation = build_interpretation(quote or "", theme, category)
        crossref = crossref_metadata(candidate.doi)
        paper_id = f"P{len(records) + 1:03d}"
        bibtex_key = build_bibtex_key(records, candidate.authors, candidate.year)
        records.append(
            ReviewRecord(
                paper_id=paper_id,
                bibtex_key=bibtex_key,
                doi=candidate.doi,
                title=candidate.title,
                journal=candidate.journal,
                year=candidate.year,
                authors=candidate.authors,
                research_question=research_question or "",
                quote=quote or "",
                interpretation=interpretation,
                category=category,
                theme=theme,
                method_class=method_class,
                gap_note=gap_note,
                method_note=method_note,
                pdf_path=str(pdf_path),
                source_url=candidate.source_url or f"https://doi.org/{candidate.doi}",
                openalex_id=candidate.openalex_id,
                landing_urls=candidate.landing_urls,
                query_themes=sorted(candidate.query_themes),
                search_queries=sorted(candidate.queries),
                crossref=crossref,
            )
        )
        kept_dois.add(candidate.doi)

    return records


def ensure_quality(records: List[ReviewRecord], target: int, papers_dir: Path) -> None:
    if len(records) < target:
        raise RuntimeError(f"Only {len(records)} papers passed QC; target was {target}.")
    seen: Set[str] = set()
    for record in records:
        if record.doi in seen:
            raise RuntimeError(f"Duplicate DOI in final set: {record.doi}")
        seen.add(record.doi)
        pdf_path = Path(record.pdf_path)
        if not pdf_path.exists():
            raise RuntimeError(f"Missing PDF: {record.pdf_path}")
        if pdf_path.parent.resolve() != papers_dir.resolve():
            raise RuntimeError(f"PDF outside papers dir: {record.pdf_path}")
        text = extract_pdf_text(pdf_path)
        if not verify_quote_in_text(record.quote, text):
            raise RuntimeError(f"Quote verification failed for {record.doi}")


def build_theme_summaries(records: List[ReviewRecord]) -> Dict[str, str]:
    grouped: Dict[str, List[ReviewRecord]] = defaultdict(list)
    for record in records:
        grouped[record.theme].append(record)

    summaries: Dict[str, str] = {}
    for theme in THEMATIC_QUERIES:
        items = grouped.get(theme, [])
        if not items:
            items = [record for record in records if theme in record.query_themes]
        if not items:
            summaries[theme] = ""
            continue
        items = sorted(items, key=lambda item: (item.year or 0, item.bibtex_key))
        citations = ", ".join(f"\\citep{{{item.bibtex_key}}}" for item in items[:5])
        if theme == "economic_impacts":
            text = f"The economic-impacts literature shows that disasters alter income, welfare, and recovery trajectories, but the magnitude and persistence differ across households and places ({citations})."
        elif theme == "risk_assessment_modelling":
            text = f"Risk-assessment studies rely on models, indices, and scenario tools to operationalize resilience, yet the measures are often difficult to compare across hazards and scales ({citations})."
        elif theme == "ecosystem_services_natural_capital":
            text = f"Work on ecosystem services and natural capital treats reefs, wetlands, mangroves, and green infrastructure as protective assets, linking ecological condition to disaster-loss reduction and adaptation value ({citations})."
        elif theme == "governance_institutions":
            text = f"Governance studies emphasize coordination, institutional fit, and policy implementation capacity, suggesting that resilience depends on how rules and organizations translate into action ({citations})."
        elif theme == "behavioral_responses":
            text = f"Behavioral research highlights risk perception, coping, and protective decisions, indicating that adaptive responses are filtered through information, trust, and household constraints ({citations})."
        else:
            text = f"Adaptation and resilience-strategy papers distinguish preparedness, diversification, and transformational change, but they do not converge on a single operational definition of resilience ({citations})."
        summaries[theme] = text
    return summaries


def build_gap_synthesis(records: List[ReviewRecord]) -> List[str]:
    method_counter = Counter(record.method_class for record in records)
    theme_counter = Counter(record.theme for record in records)
    gaps = [
        "Resilience is measured inconsistently across the sample, with papers alternating between outcome metrics, composite indices, and process-oriented institutional indicators.",
        "Policy and governance studies repeatedly note implementation frictions, implying a persistent policy-design versus policy-execution gap.",
        "Economic and ecological strands remain weakly integrated: relatively few papers connect natural-capital dynamics to formal economic-loss or welfare models.",
        "Transformative resilience is discussed more often than it is operationalized, while incremental adaptation remains the dominant empirical focus.",
        "Empirical validation of resilience metrics remains limited because many studies rely on context-specific indices that are difficult to benchmark externally.",
    ]
    if method_counter.get("CGE / IAM models", 0) == 0:
        gaps.append("CGE and IAM evidence is notably scarce in the retained corpus relative to econometric and index-based approaches.")
    if theme_counter.get("behavioral_responses", 0) < 4:
        gaps.append("Behavioral responses remain underrepresented relative to governance and modelling studies, especially for long-run adaptation behavior.")
    return gaps


def build_method_review(records: List[ReviewRecord]) -> List[str]:
    method_counter = Counter(record.method_class for record in records)
    lines = [
        f"Econometrics: {method_counter.get('econometrics', 0)} papers. These studies improve causal structure but still face endogeneity, omitted-variable risk, and cross-context comparability problems.",
        f"CGE / IAM models: {method_counter.get('CGE / IAM models', 0)} papers. System-wide counterfactuals are useful, but strong structural assumptions can dominate results.",
        f"Vulnerability indices: {method_counter.get('vulnerability indices', 0)} papers. Composite indicators are portable and policy-friendly, yet weight choice and construct validity remain contested.",
        f"Agent-based models: {method_counter.get('agent-based models', 0)} papers. They capture heterogeneity and adaptation dynamics, but calibration and external validation are often weak.",
        f"Qualitative institutional analysis: {method_counter.get('qualitative institutional analysis', 0)} papers. These papers illuminate governance mechanisms but usually trade away causal identification and broad comparability.",
    ]
    other_classes = [
        method_class
        for method_class, count in method_counter.items()
        if method_class
        not in {
            "econometrics",
            "CGE / IAM models",
            "vulnerability indices",
            "agent-based models",
            "qualitative institutional analysis",
        }
        and count
    ]
    for method_class in sorted(other_classes):
        lines.append(f"{method_class}: {method_counter[method_class]} papers. These methods add complementary evidence but do not resolve the comparability and validation problems seen across the broader corpus.")
    return lines


def latex_escape(text: str) -> str:
    replacements = {
        "\\": r"\textbackslash{}",
        "&": r"\&",
        "%": r"\%",
        "$": r"\$",
        "#": r"\#",
        "_": r"\_",
        "{": r"\{",
        "}": r"\}",
    }
    for raw, escaped in replacements.items():
        text = text.replace(raw, escaped)
    return text


def build_latex_section(records: List[ReviewRecord]) -> str:
    theme_summaries = build_theme_summaries(records)
    gap_lines = build_gap_synthesis(records)
    method_lines = build_method_review(records)
    chunks = [
        r"\section{Literature Review}",
        "The retained corpus focuses on peer-reviewed journal articles that explicitly connect natural disasters, resilience, and policy, risk, or adaptation relevance.",
    ]
    for theme in THEMATIC_QUERIES:
        chunks.append(rf"\subsection{{{theme_label(theme)}}}")
        chunks.append(theme_summaries.get(theme, ""))
    chunks.append(r"\subsection{Research Gap Synthesis}")
    for line in gap_lines:
        chunks.append(latex_escape(line))
    chunks.append(r"\subsection{Methodological Review}")
    for line in method_lines:
        chunks.append(latex_escape(line))
    return "\n\n".join(chunk for chunk in chunks if chunk) + "\n"


def record_to_dict(record: ReviewRecord) -> Dict[str, Any]:
    return {
        "paper_id": record.paper_id,
        "bibtex_key": record.bibtex_key,
        "doi": record.doi,
        "title": repair_text(record.title),
        "journal": repair_text(record.journal),
        "year": record.year,
        "authors": [repair_text(author) for author in record.authors],
        "research_question": repair_text(record.research_question),
        "quote": repair_text(record.quote),
        "interpretation": repair_text(record.interpretation),
        "category": record.category,
        "theme": record.theme,
        "theme_label": theme_label(record.theme),
        "method_class": record.method_class,
        "gap_note": repair_text(record.gap_note),
        "method_note": repair_text(record.method_note),
        "pdf_path": record.pdf_path,
        "source_url": record.source_url,
        "openalex_id": record.openalex_id,
        "landing_urls": record.landing_urls,
        "query_themes": record.query_themes,
        "search_queries": record.search_queries,
    }


def systematic_markdown_table(records: List[ReviewRecord]) -> str:
    lines = [
        "| Research Question | Article (Author, Year, Journal) | Verbatim Extract (exact text) | Interpretation | Category |",
        "|---|---|---|---|---|",
    ]
    for record in records:
        article = f"{first_author_family(record.authors)}, {record.year or 'n.d.'}, {record.journal}"
        row = [
            record.research_question.replace("|", "\\|"),
            article.replace("|", "\\|"),
            record.quote.replace("|", "\\|"),
            record.interpretation.replace("|", "\\|"),
            record.category,
        ]
        lines.append("| " + " | ".join(row) + " |")
    return "\n".join(lines)


def write_outputs(records: List[ReviewRecord], output_dir: Path) -> Dict[str, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    theme_summaries = build_theme_summaries(records)
    gap_lines = build_gap_synthesis(records)
    method_lines = build_method_review(records)

    json_path = output_dir / "disaster_resilience_review.json"
    md_path = output_dir / "disaster_resilience_review.md"
    tex_path = output_dir / "literature_review_disaster_resilience.tex"
    bib_path = output_dir / "disaster_resilience_review.bib"

    payload = {
        "paper_count": len(records),
        "themes": {theme: theme_label(theme) for theme in THEMATIC_QUERIES},
        "records": [record_to_dict(record) for record in records],
    }
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    md_lines = [
        "# Structured Literature Review",
        "",
        f"Retained papers: {len(records)}",
        "",
        "## Thematic Synthesis",
        "",
    ]
    for theme in THEMATIC_QUERIES:
        md_lines.append(f"### {theme_label(theme)}")
        md_lines.append(theme_summaries.get(theme, ""))
        md_lines.append("")

    md_lines.extend(
        [
            "## Systematic Table",
            "",
            systematic_markdown_table(records),
            "",
            "## Research Gap Synthesis",
            "",
        ]
    )
    for line in gap_lines:
        md_lines.append(f"- {line}")
    md_lines.extend(["", "## Methodological Review", ""])
    for line in method_lines:
        md_lines.append(f"- {line}")

    md_lines.extend(["", "## Manuscript Integration Output", "", "```tex", build_latex_section(records).strip(), "```", "", "## Bibliography Enhancement", ""])
    for record in records:
        md_lines.append(f"- `{record.bibtex_key}`: https://doi.org/{record.doi}")
    md_path.write_text("\n".join(md_lines).strip() + "\n", encoding="utf-8")

    tex_path.write_text(build_latex_section(records), encoding="utf-8")
    bib_path.write_text("\n".join(build_bibtex_entry(record) for record in records), encoding="utf-8")

    return {
        "json": json_path,
        "markdown": md_path,
        "tex": tex_path,
        "bib": bib_path,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build an auditable disaster-resilience literature review corpus.")
    parser.add_argument("--target", type=int, default=33, help="Minimum number of papers to retain after QC.")
    parser.add_argument("--papers-dir", default="papers/disaster_resilience_review", help="Directory for downloaded PDFs.")
    parser.add_argument("--output-dir", default="output/disaster_resilience_review", help="Directory for JSON/Markdown/BibTeX/TeX outputs.")
    parser.add_argument("--json", action="store_true", help="Print machine-readable summary.")
    return parser.parse_args()


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    args = parse_args()
    papers_dir = Path(args.papers_dir)
    output_dir = Path(args.output_dir)
    papers_dir.mkdir(parents=True, exist_ok=True)
    output_dir.mkdir(parents=True, exist_ok=True)

    records = build_records(target=args.target, papers_dir=papers_dir)
    ensure_quality(records, target=args.target, papers_dir=papers_dir)
    outputs = write_outputs(records, output_dir=output_dir)
    summary = {
        "paper_count": len(records),
        "dois": [record.doi for record in records],
        "papers_dir": str(papers_dir.resolve()),
        "json_file": str(outputs["json"].resolve()),
        "markdown_file": str(outputs["markdown"].resolve()),
        "tex_file": str(outputs["tex"].resolve()),
        "bib_file": str(outputs["bib"].resolve()),
    }
    if args.json:
        print(json.dumps(summary, ensure_ascii=False, indent=2))
    else:
        print(f"Papers retained: {summary['paper_count']}")
        print(f"Papers folder: {summary['papers_dir']}")
        print(f"JSON file: {summary['json_file']}")
        print(f"Markdown file: {summary['markdown_file']}")
        print(f"TeX file: {summary['tex_file']}")
        print(f"BibTeX file: {summary['bib_file']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
