#!/usr/bin/env python3
"""Search, download, parse, and summarize a literature corpus for the review."""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Set, Tuple

import pandas as pd
import requests

try:
    import fitz  # type: ignore
except Exception as exc:  # pragma: no cover - environment-dependent import
    raise SystemExit(f"PyMuPDF is required for PDF parsing in this environment: {exc}")


HOME = Path.home()
SKILL_SCRIPTS = HOME / ".codex" / "skills" / "sci-papers-downloder" / "scripts"
if SKILL_SCRIPTS.exists():
    sys.path.insert(0, str(SKILL_SCRIPTS))

try:
    from download_open_access import attempt_download, safe_filename, unique_path  # type: ignore
except Exception as exc:  # pragma: no cover - defensive fallback
    raise SystemExit(f"Could not import sci-papers-downloder helpers: {exc}")


OPENALEX_WORKS_URL = "https://api.openalex.org/works"
REQUEST_TIMEOUT = 60
USER_AGENT = "cocoa-volatility-literature-review/1.0"

PREFERRED_JOURNALS = {
    "Agricultural Economics",
    "Agriculture and Human Values",
    "Annual Review of Environment and Resources",
    "Annual Review of Resource Economics",
    "Australian Journal of Agricultural and Resource Economics",
    "Climatic Change",
    "Conservation Biology",
    "Current Opinion in Environmental Sustainability",
    "Ecological Economics",
    "Ecology and Society",
    "Environmental Research Letters",
    "Food Policy",
    "Food Security",
    "Global Environmental Change",
    "Journal of Agricultural Economics",
    "Journal of Peasant Studies",
    "Journal of Rural Studies",
    "Nature Food",
    "Proceedings of the National Academy of Sciences",
    "World Development",
}

OTHER_COMMODITY_TERMS = {
    "aquaculture",
    "avocado",
    "biofuel",
    "cotton",
    "dairy",
    "fish",
    "oil palm",
    "papaya",
    "patchouli",
    "poultry",
    "rice",
    "soy",
    "soybean",
    "teff",
}

SEARCH_BUCKETS: Dict[str, List[str]] = {
    "price": [
        '"asymmetric price transmission" cocoa',
        '"asymmetric price transmission" coffee',
        '"price transmission" cocoa',
        '"price transmission" coffee',
        '"asymmetric exchange rate pass-through" cocoa',
        '"market integration" cocoa farmers',
        '"world price" coffee farm household income',
        '"price shocks" cocoa coffee transmission',
    ],
    "vulnerability": [
        "smallholder climate vulnerability cocoa",
        "smallholder climate vulnerability coffee",
        "cocoa farmers resilience climate",
        "coffee climate adaptation smallholder",
        "coffee rust smallholder resilience",
        "cocoa agroforestry resilience smallholder climate",
    ],
    "justice": [
        "living income smallholder tree crop commodity farmers",
        "coffee certification small scale growers globalization",
        "cocoa value chain living income farmers",
        "telecoupling sustainability smallholder commodity",
        '"fair trade" coffee farmers economics',
        "sustainability standards coffee cocoa value chain smallholder",
    ],
}

THEME_TERMS: Dict[str, Sequence[str]] = {
    "price": [
        "asymmetric price transmission",
        "exchange rate pass-through",
        "farmgate",
        "market integration",
        "marketing margin",
        "pass through",
        "pass-through",
        "price shock",
        "price transmission",
        "producer price",
        "retail price",
        "threshold price transmission",
        "world price",
    ],
    "distribution": [
        "asymmetric",
        "asymmetry",
        "certification",
        "distribution",
        "fair trade",
        "globalization",
        "inequal",
        "inequality",
        "living income",
        "margin",
        "market power",
        "price spread",
        "rent",
        "value share",
    ],
    "vulnerability": [
        "adaptive capacity",
        "exposure",
        "farm household",
        "food security",
        "livelihood",
        "producer",
        "resilience",
        "risk",
        "small-scale",
        "smallholder",
        "vulnerability",
    ],
    "climate": [
        "adaptation",
        "agroforestry",
        "biodiversity",
        "climate",
        "deforestation",
        "drought",
        "ecological",
        "environmental",
        "rainfall",
        "rust",
        "temperature",
        "weather",
    ],
    "anchor": [
        "certification",
        "cocoa",
        "coffee",
        "commodity",
        "farmer",
        "farm household",
        "smallholder",
        "supply chain",
        "telecoupling",
        "value chain",
    ],
    "core_anchor": [
        "certification",
        "cocoa",
        "coffee",
        "fair trade",
        "farm household",
        "living income",
        "smallholder",
        "supply chain",
        "telecoupling",
        "value chain",
    ],
    "support_anchor": [
        "commodity",
        "farmer",
        "livelihood",
        "producer",
    ],
    "policy": [
        "certification",
        "governance",
        "implication",
        "intervention",
        "living income",
        "policy",
        "recommend",
        "regulation",
        "sustainab",
    ],
}

QUESTION_RULES: Dict[str, Dict[str, Any]] = {
    "Q1": {
        "weights": {
            "price transmission": 6,
            "pass-through": 6,
            "pass through": 6,
            "market integration": 5,
            "producer price": 4,
            "farmgate": 4,
            "retail price": 4,
            "marketing margin": 4,
            "world price": 3,
            "price shock": 3,
            "cointegration": 2,
        },
        "required_any": ["price transmission", "pass-through", "pass through", "market integration"],
        "min_score": 6,
    },
    "Q2": {
        "weights": {
            "asymmetric": 6,
            "asymmetry": 6,
            "unequal": 5,
            "inequal": 5,
            "distribution": 4,
            "market power": 4,
            "price spread": 4,
            "margin": 3,
            "living income": 3,
            "fair trade": 3,
            "value share": 3,
        },
        "required_any": ["asymmetric", "asymmetry", "unequal", "distribution", "market power", "price spread"],
        "min_score": 5,
    },
    "Q3": {
        "weights": {
            "vulnerability": 6,
            "smallholder": 5,
            "farm household": 5,
            "adaptive capacity": 4,
            "exposure": 4,
            "livelihood": 4,
            "food security": 4,
            "resilience": 4,
            "risk": 3,
            "producer": 2,
        },
        "required_any": ["vulnerability", "smallholder", "farm household", "adaptive capacity", "exposure", "livelihood"],
        "min_score": 6,
    },
    "Q4": {
        "weights": {
            "climate": 5,
            "weather": 4,
            "rainfall": 4,
            "temperature": 4,
            "drought": 4,
            "environmental": 3,
            "ecological": 3,
            "deforestation": 3,
            "rust": 3,
            "agroforestry": 2,
        },
        "required_any": ["climate", "weather", "rainfall", "temperature", "drought", "environmental", "ecological"],
        "min_score": 5,
    },
    "Q5": {
        "weights": {
            "policy": 5,
            "policies": 5,
            "implication": 4,
            "recommend": 4,
            "governance": 4,
            "sustainab": 4,
            "regulation": 4,
            "certification": 3,
            "living income": 3,
            "support": 2,
        },
        "required_any": ["policy", "policies", "implication", "recommend", "governance", "sustainab", "regulation", "certification", "living income"],
        "min_score": 5,
    },
}


@dataclass
class Candidate:
    doi: str
    title: str
    journal: str
    year: Optional[int]
    authors: List[str]
    abstract: str
    cited_by_count: int
    score: float
    pdf_urls: List[str]
    landing_urls: List[str]
    queries: List[str] = field(default_factory=list)
    buckets: Set[str] = field(default_factory=set)
    matched_terms: Dict[str, List[str]] = field(default_factory=dict)


@dataclass
class Answer:
    question_id: str
    extracted_text: str
    interpretation: str
    score: float


@dataclass
class PaperRecord:
    paper_id: str
    title: str
    doi: str
    journal: str
    year: Optional[int]
    authors: List[str]
    pdf_path: str
    summary: str
    matched_buckets: List[str]
    search_queries: List[str]
    answers: List[Answer]


def normalize_doi(raw: Optional[str]) -> str:
    if not raw:
        return ""
    doi = raw.strip()
    doi = re.sub(r"^https?://(dx\.)?doi\.org/", "", doi, flags=re.I)
    return doi.strip()


def reconstruct_abstract(inverted_index: Optional[Dict[str, List[int]]]) -> str:
    if not inverted_index:
        return ""
    positioned: List[Tuple[int, str]] = []
    for word, positions in inverted_index.items():
        for pos in positions:
            positioned.append((pos, word))
    positioned.sort(key=lambda item: item[0])
    return " ".join(word for _, word in positioned)


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


def lowercase_hits(text: str, terms: Sequence[str]) -> List[str]:
    lower = text.lower()
    return sorted({term for term in terms if term in lower})


def candidate_score(title: str, abstract: str, journal: str, cited_by_count: int, has_pdf_url: bool) -> Tuple[float, Dict[str, List[str]]]:
    joined = " ".join([title, abstract, journal])
    hits = {name: lowercase_hits(joined, terms) for name, terms in THEME_TERMS.items()}
    hits["focus"] = lowercase_hits(
        joined,
        ["cocoa", "coffee", "smallholder", "farm household", "certification", "living income", "telecoupling", "fair trade"],
    )

    if not hits["core_anchor"] and not (hits["price"] and hits["support_anchor"]):
        return -999.0, hits
    if not hits["focus"] and not hits["price"]:
        return -999.0, hits

    if any(term in joined.lower() for term in OTHER_COMMODITY_TERMS) and not ({"cocoa", "coffee"} & set(hits["anchor"])):
        penalty = 15.0
    else:
        penalty = 0.0

    theme_total = len(hits["price"]) + len(hits["distribution"]) + len(hits["vulnerability"]) + len(hits["climate"])
    score = 0.0
    score += 5.0 * len(hits["price"])
    score += 4.0 * len(hits["distribution"])
    score += 4.0 * len(hits["vulnerability"])
    score += 3.0 * len(hits["climate"])
    score += 2.0 * len(hits["anchor"])
    score += 3.0 * len(hits["core_anchor"])
    if {"cocoa", "coffee"} & set(hits["anchor"]):
        score += 4.0
    if {"smallholder", "farm household"} & set(hits["anchor"]):
        score += 3.0
    if journal in PREFERRED_JOURNALS:
        score += 3.0
    if has_pdf_url:
        score += 1.0
    score += min(max(cited_by_count, 0), 150) / 75.0
    if theme_total < 2:
        score -= 5.0
    score -= penalty
    return score, hits


def search_openalex(query: str, per_page: int = 20) -> List[Dict[str, Any]]:
    params = {
        "search": query,
        "per-page": per_page,
        "filter": "is_oa:true,has_doi:true,has_fulltext:true,type:article,primary_location.source.type:journal,language:en",
    }
    response = requests.get(
        OPENALEX_WORKS_URL,
        params=params,
        timeout=REQUEST_TIMEOUT,
        headers={"User-Agent": USER_AGENT},
    )
    response.raise_for_status()
    payload = response.json()
    return payload.get("results", [])


def build_candidate_pool() -> Dict[str, Candidate]:
    candidates: Dict[str, Candidate] = {}

    for bucket, queries in SEARCH_BUCKETS.items():
        for query in queries:
            works = search_openalex(query)
            for work in works:
                doi = normalize_doi(work.get("doi"))
                if not doi:
                    continue
                title = (work.get("display_name") or "").strip()
                if not title:
                    continue
                journal = (((work.get("primary_location") or {}).get("source") or {}).get("display_name") or "").strip()
                authors = [
                    ((item.get("author") or {}).get("display_name") or "").strip()
                    for item in (work.get("authorships") or [])
                    if (item.get("author") or {}).get("display_name")
                ]
                abstract = reconstruct_abstract(work.get("abstract_inverted_index"))
                cited_by_count = int(work.get("cited_by_count") or 0)
                pdf_urls, landing_urls = build_candidate_urls(work)
                score, matched_terms = candidate_score(
                    title=title,
                    abstract=abstract,
                    journal=journal,
                    cited_by_count=cited_by_count,
                    has_pdf_url=bool(pdf_urls),
                )
                if score < 4:
                    continue

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
                        score=score,
                        pdf_urls=pdf_urls,
                        landing_urls=landing_urls,
                        queries=[query],
                        buckets={bucket},
                        matched_terms=matched_terms,
                    )
                else:
                    existing.queries.append(query)
                    existing.buckets.add(bucket)
                    existing.pdf_urls = unique_nonempty([*existing.pdf_urls, *pdf_urls])
                    existing.landing_urls = unique_nonempty([*existing.landing_urls, *landing_urls])
                    if score > existing.score:
                        existing.score = score
                        existing.title = title
                        existing.journal = journal or existing.journal
                        existing.year = work.get("publication_year")
                        existing.authors = authors or existing.authors
                        existing.abstract = abstract or existing.abstract
                        existing.cited_by_count = cited_by_count
                        existing.matched_terms = matched_terms

    return candidates


def build_processing_queue(candidates: Dict[str, Candidate]) -> List[Candidate]:
    bucket_lists: Dict[str, List[Candidate]] = {}
    for bucket in SEARCH_BUCKETS:
        bucket_lists[bucket] = sorted(
            [candidate for candidate in candidates.values() if bucket in candidate.buckets],
            key=lambda item: (-item.score, -(item.year or 0), item.title.lower()),
        )

    queue: List[Candidate] = []
    seen: Set[str] = set()
    max_len = max((len(items) for items in bucket_lists.values()), default=0)
    for idx in range(max_len):
        for bucket in ("price", "vulnerability", "justice"):
            items = bucket_lists[bucket]
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


def is_reference_like(text: str) -> bool:
    lower = text.lower()
    if lower.startswith("keywords") or lower.startswith("key words"):
        return True
    if lower.startswith("acknowledg"):
        return True
    if "department of" in lower or "university" in lower or "e-mail" in lower or "supplementary material" in lower:
        return True
    if lower.count("(") >= 2 and lower.count(")") >= 2 and re.search(r"\b\d{4}[a-z]?\b", lower):
        return True
    if "doi.org/" in lower or lower.startswith("http"):
        return True
    return False


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
        if not match:
            continue
        if match.start() > len(text) * 0.45:
            cut_at = match.start() if cut_at is None else min(cut_at, match.start())
    return text[:cut_at] if cut_at else text


def trim_front_matter(text: str) -> str:
    patterns = [r"\babstract\b", r"\bsummary\b", r"\bintroduction\b"]
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.I)
        if match and match.start() < 2500:
            return text[match.start():]
    return text


def normalize_text(text: str) -> str:
    text = text.replace("\r", "\n").replace("\x0c", "\n")
    text = re.sub(r"(\w)-\n(\w)", r"\1\2", text)
    text = re.sub(r"[ \t]+\n", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = trim_front_matter(text)
    return trim_back_matter(text)


def normalize_for_match(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def excel_safe(value: Any) -> Any:
    if not isinstance(value, str):
        return value
    return re.sub(r"[\x00-\x08\x0B-\x0C\x0E-\x1F]", "", value)


def extract_pdf_text(pdf_path: Path) -> str:
    chunks: List[str] = []
    with fitz.open(pdf_path) as doc:
        for page in doc:
            chunks.append(page.get_text("text"))
    return normalize_text("\n".join(chunks))


def paragraph_units(text: str) -> List[Tuple[str, float]]:
    units: List[Tuple[str, float]] = []
    parts = re.split(r"\n\s*\n", text)
    total = max(1, len(parts))
    for idx, raw in enumerate(parts):
        cleaned = re.sub(r"\s+", " ", raw).strip()
        if len(cleaned) < 60:
            continue
        units.append((cleaned, idx / total))
    return units


def sentence_units(text: str) -> List[Tuple[str, float]]:
    units: List[Tuple[str, float]] = []
    paragraphs = paragraph_units(text)
    total = max(1, len(paragraphs))
    for idx, (paragraph, _) in enumerate(paragraphs):
        sentences = re.split(r"(?<=[.!?])\s+(?=[A-Z0-9(“\"'])", paragraph)
        for sentence in sentences:
            cleaned = re.sub(r"\s+", " ", sentence).strip()
            if len(cleaned) < 45:
                continue
            units.append((cleaned, idx / total))
    return units


def score_unit(question_id: str, text: str, relative_position: float) -> float:
    lower = text.lower()
    if is_reference_like(text):
        return -10.0
    if len(text) > 1200:
        return -2.0
    if lower.startswith("table ") or lower.startswith("figure "):
        return -6.0
    if lower.count(";") >= 6:
        return -4.0

    rule = QUESTION_RULES[question_id]
    score = 0.0
    for term, weight in rule["weights"].items():
        if term in lower:
            score += float(weight)

    if question_id in {"Q1", "Q2"} and relative_position < 0.45:
        score += 0.5
    if question_id == "Q5" and relative_position > 0.55:
        score += 1.0
    if question_id in {"Q3", "Q4"} and ("smallholder" in lower or "farm" in lower or "coffee" in lower or "cocoa" in lower):
        score += 0.5
    if question_id == "Q5" and any(
        term in lower for term in ["acknowledg", "funded by", "grant", "research program", "cgiar", "ifpri"]
    ):
        score -= 8.0
    return score


def passes_question_gate(question_id: str, lower: str) -> bool:
    price_terms = ["price transmission", "pass-through", "pass through", "market integration"]
    chain_terms = ["coffee", "cocoa", "producer", "retail", "farmgate", "value chain", "supply chain", "market"]
    asymmetry_terms = ["asymmetric", "asymmetry", "unequal", "distribution", "market power", "price spread"]
    subject_terms = ["smallholder", "farm household", "farmer", "producer", "livelihood", "food security", "adaptive capacity"]
    vulnerability_terms = ["vulnerability", "exposure", "resilience", "risk", "adaptive capacity"]
    climate_terms = ["climate", "weather", "rainfall", "temperature", "drought", "environmental", "ecological"]
    policy_terms = ["policy", "policies", "implication", "recommend", "governance", "sustainab", "regulation", "support"]

    if question_id == "Q1":
        return any(term in lower for term in price_terms) and any(term in lower for term in chain_terms)
    if question_id == "Q2":
        return any(term in lower for term in asymmetry_terms) and any(
            term in lower for term in ["price", "value", "market", "farmer", "producer", "coffee", "cocoa", "chain", "income"]
        )
    if question_id == "Q3":
        return any(term in lower for term in subject_terms) and any(term in lower for term in vulnerability_terms)
    if question_id == "Q4":
        return any(term in lower for term in climate_terms) and any(
            term in lower for term in ["smallholder", "farmer", "producer", "coffee", "cocoa", "farm", "livelihood", "agroforestry", "crop"]
        )
    return any(term in lower for term in policy_terms) and any(
        term in lower for term in ["smallholder", "farmer", "producer", "coffee", "cocoa", "value chain", "supply chain", "income", "certification", "market"]
    )


def build_interpretation(question_id: str, extracted_text: str) -> str:
    lower = extracted_text.lower()
    if question_id == "Q1":
        return "This passage shows how the paper frames transmission across market nodes, usually by linking world, producer, farm-gate, or retail prices."
    if question_id == "Q2":
        if "asym" in lower:
            return "This excerpt explicitly points to asymmetric pass-through, meaning positive and negative shocks are not transmitted in the same way."
        return "This excerpt highlights unequal value distribution or market power rather than a symmetric sharing of shocks and returns."
    if question_id == "Q3":
        return "This passage identifies who is vulnerable and the dimensions used to describe exposure, sensitivity, or adaptive capacity among smallholders."
    if question_id == "Q4":
        return "This excerpt ties the argument to climate or environmental stress by naming the production risks that amplify livelihood exposure."
    return "This passage states a policy, governance, or sustainability implication and shows how the paper moves from evidence to action."


def select_answer_for_question(question_id: str, text: str) -> Optional[Answer]:
    rule = QUESTION_RULES[question_id]
    candidates = sentence_units(text) + paragraph_units(text)
    best: Optional[Tuple[float, str]] = None
    for unit, relative_position in candidates:
        score = score_unit(question_id, unit, relative_position)
        if score < rule["min_score"]:
            continue
        lower = unit.lower()
        if not any(term in lower for term in rule["required_any"]):
            continue
        if not passes_question_gate(question_id, lower):
            continue
        if best is None or score > best[0]:
            best = (score, unit)

    if best is None:
        return None

    extracted_text = best[1]
    interpretation = build_interpretation(question_id, extracted_text)
    return Answer(
        question_id=question_id,
        extracted_text=extracted_text,
        interpretation=interpretation,
        score=best[0],
    )


def summarize_paper(candidate: Candidate, answers: List[Answer]) -> str:
    parts = [f"This {candidate.year or 'n.d.'} paper in {candidate.journal} examines {candidate.title}."]
    answered = {answer.question_id for answer in answers}
    if "Q1" in answered:
        parts.append("It contributes direct evidence on price transmission or market integration.")
    if "Q2" in answered:
        parts.append("It discusses asymmetry, unequal value distribution, or market power in the chain.")
    if "Q3" in answered:
        parts.append("It characterizes smallholder vulnerability, exposure, or adaptive capacity.")
    if "Q4" in answered:
        parts.append("It incorporates climate or environmental stress into the analysis.")
    if "Q5" in answered:
        parts.append("It closes with policy or sustainability implications relevant to resilience and justice.")
    return " ".join(parts[:5])


def download_pdf(candidate: Candidate, papers_dir: Path) -> Optional[Path]:
    base_name = safe_filename(f"{candidate.doi.replace('/', '_')}__{candidate.title}", "paper")
    existing = papers_dir / f"{base_name}.pdf"
    if existing.exists() and existing.stat().st_size > 1024:
        return existing
    urls = unique_nonempty([*candidate.pdf_urls, *candidate.landing_urls])
    for url in urls:
        target = unique_path(papers_dir / f"{base_name}.pdf")
        ok, _, _ = attempt_download(url, target, timeout=REQUEST_TIMEOUT)
        if ok and target.exists() and target.stat().st_size > 1024:
            return target
        if target.exists():
            target.unlink(missing_ok=True)
    return None


def paper_answers(text: str) -> List[Answer]:
    answers: List[Answer] = []
    for question_id in ("Q1", "Q2", "Q3", "Q4", "Q5"):
        answer = select_answer_for_question(question_id, text)
        if answer is not None:
            answers.append(answer)
    return answers


def keep_paper(candidate: Candidate, answers: List[Answer]) -> bool:
    answered = {answer.question_id for answer in answers}
    if not answered:
        return False
    if "price" in candidate.buckets and not ({"Q1", "Q2"} & answered):
        return False
    if "vulnerability" in candidate.buckets and not ({"Q3", "Q4"} & answered):
        return False
    if "justice" in candidate.buckets and not ({"Q2", "Q5"} & answered):
        return False
    return True


def write_outputs(records: List[PaperRecord], output_dir: Path) -> Dict[str, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    excel_path = output_dir / "literature_review.xlsx"
    markdown_path = output_dir / "literature_review.md"
    manifest_path = output_dir / "literature_review_manifest.json"

    rows: List[Dict[str, Any]] = []
    for record in records:
        for answer in record.answers:
            rows.append(
                {
                    "paper_id": record.paper_id,
                    "title": record.title,
                    "DOI": record.doi,
                    "journal": record.journal,
                    "question_id": answer.question_id,
                    "extracted_text": answer.extracted_text,
                    "interpretation": answer.interpretation,
                }
            )

    dataframe = pd.DataFrame(
        rows,
        columns=["paper_id", "title", "DOI", "journal", "question_id", "extracted_text", "interpretation"],
    )
    for column in dataframe.columns:
        dataframe[column] = dataframe[column].map(excel_safe)
    with pd.ExcelWriter(excel_path, engine="openpyxl") as writer:
        dataframe.to_excel(writer, sheet_name="literature_review", index=False)

    markdown_chunks: List[str] = []
    for record in records:
        markdown_chunks.append(f"## {record.title}\n")
        markdown_chunks.append(f"- DOI: {record.doi}")
        markdown_chunks.append(f"- Journal: {record.journal}")
        markdown_chunks.append("")
        markdown_chunks.append("### Summary")
        markdown_chunks.append(record.summary)
        markdown_chunks.append("")
        markdown_chunks.append("### Answers")
        markdown_chunks.append("")
        answers_by_question = {answer.question_id: answer for answer in record.answers}
        for question_id in ("Q1", "Q2", "Q3", "Q4", "Q5"):
            answer = answers_by_question.get(question_id)
            if answer is None:
                continue
            quote = answer.extracted_text.replace("\"", "\\\"")
            markdown_chunks.append(f"{question_id}:")
            markdown_chunks.append(f"- Text: \"{quote}\"")
            markdown_chunks.append(f"- Interpretation: {answer.interpretation}")
            markdown_chunks.append("")

    markdown_path.write_text("\n".join(markdown_chunks).strip() + "\n", encoding="utf-8")
    manifest_path.write_text(
        json.dumps(
            {
                "paper_count": len(records),
                "papers": [
                    {
                        "paper_id": record.paper_id,
                        "title": record.title,
                        "doi": record.doi,
                        "journal": record.journal,
                        "year": record.year,
                        "authors": record.authors,
                        "pdf_path": record.pdf_path,
                        "matched_buckets": record.matched_buckets,
                        "search_queries": record.search_queries,
                        "answer_count": len(record.answers),
                    }
                    for record in records
                ],
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    return {
        "excel": excel_path,
        "markdown": markdown_path,
        "manifest": manifest_path,
    }


def ensure_quality(records: List[PaperRecord], target: int, papers_dir: Path) -> None:
    if len(records) < target:
        raise RuntimeError(f"Only {len(records)} papers passed QC; target was {target}.")
    dois = [record.doi for record in records]
    if len(dois) != len(set(dois)):
        raise RuntimeError("Duplicate DOI detected in final records.")
    for record in records:
        pdf_path = Path(record.pdf_path)
        if not pdf_path.exists():
            raise RuntimeError(f"Missing PDF file for {record.doi}: {pdf_path}")
        if pdf_path.parent.resolve() != papers_dir.resolve():
            raise RuntimeError(f"PDF path outside papers directory: {pdf_path}")
        text = normalize_for_match(extract_pdf_text(pdf_path))
        for answer in record.answers:
            if normalize_for_match(answer.extracted_text) not in text:
                raise RuntimeError(f"Verbatim text check failed for {record.doi} {answer.question_id}")


def build_records(target: int, papers_dir: Path) -> List[PaperRecord]:
    candidates = build_candidate_pool()
    queue = build_processing_queue(candidates)
    records: List[PaperRecord] = []
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

        if len(re.sub(r"\s+", "", text)) < 4000:
            pdf_path.unlink(missing_ok=True)
            continue

        answers = paper_answers(text)
        if not keep_paper(candidate, answers):
            pdf_path.unlink(missing_ok=True)
            continue

        paper_id = f"P{len(records) + 1:03d}"
        record = PaperRecord(
            paper_id=paper_id,
            title=candidate.title,
            doi=candidate.doi,
            journal=candidate.journal,
            year=candidate.year,
            authors=candidate.authors,
            pdf_path=str(pdf_path),
            summary=summarize_paper(candidate, answers),
            matched_buckets=sorted(candidate.buckets),
            search_queries=sorted(set(candidate.queries)),
            answers=sorted(answers, key=lambda item: item.question_id),
        )
        records.append(record)
        kept_dois.add(candidate.doi)

    return records


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the literature review search/download/extraction pipeline.")
    parser.add_argument("--target", type=int, default=25, help="Minimum number of papers to keep after QC.")
    parser.add_argument("--papers-dir", default="papers", help="Directory for downloaded PDFs.")
    parser.add_argument("--output-dir", default="output", help="Directory for Excel/Markdown outputs.")
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
        "excel_file": str(outputs["excel"].resolve()),
        "markdown_file": str(outputs["markdown"].resolve()),
        "manifest_file": str(outputs["manifest"].resolve()),
    }

    if args.json:
        print(json.dumps(summary, ensure_ascii=False, indent=2))
    else:
        print(f"Papers downloaded: {summary['paper_count']}")
        print("DOIs:")
        for doi in summary["dois"]:
            print(doi)
        print(f"Papers folder: {summary['papers_dir']}")
        print(f"Excel file: {summary['excel_file']}")
        print(f"Markdown file: {summary['markdown_file']}")
        print(f"Manifest file: {summary['manifest_file']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
