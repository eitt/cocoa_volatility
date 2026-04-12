#!/usr/bin/env python3
"""Generate the cocoa-specific literature-alignment outputs used by the manuscript.

This script does not run a new search. It writes a curated, audited corpus that was
retained after manual screening against the manuscript's methodological gap:
benchmark transmission, uneven supply-chain adjustment, and weather as contextual
vulnerability. The set is cocoa-led, with carefully labelled comparative support
from coffee where the manuscript uses a broader tropical tree-crop framing.
"""

from __future__ import annotations

import json
from pathlib import Path


RECORDS = [
    {
        "key": "TsowouGayi2019",
        "authors": "Tsowou and Gayi",
        "year": 2019,
        "journal": "Journal of African Trade",
        "title": "Trade Reforms and Integration of Cocoa Farmers into World Markets: Evidence from African and non-African Countries",
        "doi": "10.2991/jat.k.190916.001",
        "evidence_status": "pdf_audited",
        "retrieval": "papers/10.2991_jat.k.190916.001__Trade_Reforms_and_Integration_of_Cocoa_Farmers_into_World_Markets_Evidence_from_African_and_no.pdf",
        "gap_role": "benchmark transmission and producer exposure",
        "quote": "the reforms have increased the exposure of farmers to world cocoa markets",
        "interpretation": "The paper supports the claim that producer exposure rises when domestic cocoa markets are more tightly linked to world prices.",
        "manuscript_use": ["Introduction", "Literature Review", "Methods", "Discussion"],
    },
    {
        "key": "Jumah2001",
        "authors": "Jumah and Kunst",
        "year": 2001,
        "journal": "European Review of Agricultural Economics",
        "title": "The Effects of Dollar/Sterling Exchange Rate Volatility on Futures Markets for Coffee and Cocoa",
        "doi": "10.1093/erae/28.3.307",
        "evidence_status": "publisher_abstract_verified",
        "retrieval": "https://doi.org/10.1093/erae/28.3.307",
        "gap_role": "exchange-rate channel in cocoa price dynamics",
        "quote": "the exchange rate emerges as a main source of risk for the commodity futures price",
        "interpretation": "The article supports modelling exchange-rate conditions as a distinct source of cocoa-market risk rather than background noise.",
        "manuscript_use": ["Introduction", "Literature Review", "Methods"],
    },
    {
        "key": "talero_sarmiento_etal_2025",
        "authors": "Talero-Sarmiento et al.",
        "year": 2025,
        "journal": "Ecological Informatics",
        "title": "Optimizing Cocoa Biomass Density through Integrated Irrigation and Drainage Management under Water Stress: A Linear Programming Approach",
        "doi": "10.1016/j.ecoinf.2025.103262",
        "evidence_status": "abstract_verified",
        "retrieval": "https://doi.org/10.1016/j.ecoinf.2025.103262",
        "gap_role": "local weather architecture and variable selection",
        "quote": "Using data from the NASA POWER database and incorporating detailed climate, soil, and crop management variables specific to San Vicente del Chucuri, Colombia",
        "interpretation": "The paper supports the local choice of NASA POWER weather inputs and anchors the weather block in prior cocoa modelling for the same municipality.",
        "manuscript_use": ["Methods"],
    },
    {
        "key": "Mithofer2017",
        "authors": "Mithofer et al.",
        "year": 2017,
        "journal": "International Journal of Biodiversity Science, Ecosystem Services & Management",
        "title": "Unpacking 'sustainable' cocoa: do sustainability standards, development projects and policies address producer concerns in Indonesia, Cameroon and Peru?",
        "doi": "10.1080/21513732.2018.1432691",
        "evidence_status": "pdf_audited",
        "retrieval": "papers/cocoa_claim_support/Unpacking_sustainable_cocoa_do_sustainability_standards_development_projects_and_policies_address_producer_concerns_in_I.pdf",
        "gap_role": "producer constraints, weak market position, and institutional fit",
        "quote": "Producers in all three countries shared concerns of price volatility, weak farmer organizations and dependence on few buyers.",
        "interpretation": "This supports the manuscript's claim that cocoa vulnerability reflects both price instability and constrained producer capacity within the chain.",
        "manuscript_use": ["Introduction", "Literature Review", "Methods", "Discussion"],
    },
    {
        "key": "Morales2022",
        "authors": "Morales et al.",
        "year": 2022,
        "journal": "Frontiers in Climate",
        "title": "Planning for Adaptation: A System Approach to Understand the Value Chain's Role in Supporting Smallholder Coffee Farmers' Adaptive Capacity in Peru",
        "doi": "10.3389/fclim.2022.788369",
        "evidence_status": "pdf_audited",
        "retrieval": "papers/10.3389_fclim.2022.788369__Planning_for_Adaptation_A_System_Approach_to_Understand_the_Value_Chain_s_Role_in_Supporting_.pdf",
        "gap_role": "comparative tree-crop evidence on value-chain support",
        "quote": "this study is the first to develop indicators that assess the sensitivity and adaptive capacity of coffee value-chain actors",
        "interpretation": "Used carefully, this provides comparative evidence from a similar tropical tree-crop system that adaptive capacity depends on chain-level organization.",
        "manuscript_use": ["Introduction", "Literature Review", "Discussion"],
    },
    {
        "key": "Verburg2019",
        "authors": "Verburg et al.",
        "year": 2019,
        "journal": "Environmental Science & Policy",
        "title": "An innovation perspective to climate change adaptation in coffee systems",
        "doi": "10.1016/j.envsci.2019.03.017",
        "evidence_status": "pdf_audited",
        "retrieval": "papers/10.1016_j.envsci.2019.03.017__An_innovation_perspective_to_climate_change_adaptation_in_coffee_systems.pdf",
        "gap_role": "comparative tree-crop evidence on adaptation systems",
        "quote": "We identify climate change adaptation options, their scale of application, and the necessary implementation steps.",
        "interpretation": "The paper is used only as comparative evidence that adaptation in similar perennial crop systems extends beyond the farm to wider organizational arrangements.",
        "manuscript_use": ["Introduction", "Literature Review", "Discussion"],
    },
    {
        "key": "AkrofiAtitianti2018",
        "authors": "Akrofi-Atitianti et al.",
        "year": 2018,
        "journal": "Land",
        "title": "Assessing Climate Smart Agriculture and Its Determinants of Practice in Ghana: A Case of the Cocoa Production System",
        "doi": "10.3390/land7010030",
        "evidence_status": "pdf_audited",
        "retrieval": "papers/cocoa_claim_support/Assessing_Climate_Smart_Agriculture_and_Its_Determinants_of_Practice_in_Ghana_A_Case_of_the_Cocoa_Production_System.pdf",
        "gap_role": "climate vulnerability and adaptation in cocoa systems",
        "quote": "enhance production, mitigate and/or remove GHG emissions and build resilience",
        "interpretation": "The study supports treating resilience as an explicit analytical concern in cocoa systems rather than as an external framing device.",
        "manuscript_use": ["Introduction", "Methods", "Discussion"],
    },
    {
        "key": "Schroth2016",
        "authors": "Schroth et al.",
        "year": 2016,
        "journal": "Science of The Total Environment",
        "title": "Vulnerability to Climate Change of Cocoa in West Africa: Patterns, Opportunities and Limits to Adaptation",
        "doi": "10.1016/j.scitotenv.2016.03.024",
        "evidence_status": "abstract_verified",
        "retrieval": "https://doi.org/10.1016/j.scitotenv.2016.03.024",
        "gap_role": "climatic suitability, adaptation limits, and spatial vulnerability",
        "quote": "maximum dry season temperatures are projected to become as or more limiting for cocoa as dry season water availability",
        "interpretation": "The article supports the claim that cocoa climate vulnerability is structured by specific biophysical constraints, not by generic climate stress alone.",
        "manuscript_use": ["Introduction", "Literature Review", "Discussion"],
    },
    {
        "key": "Koh2020",
        "authors": "Koh et al.",
        "year": 2020,
        "journal": "Environmental Research Letters",
        "title": "Climate risks to Brazilian coffee production",
        "doi": "10.1088/1748-9326/aba471",
        "evidence_status": "pdf_audited",
        "retrieval": "papers/10.1088_1748-9326_aba471__Climate_risks_to_Brazilian_coffee_production.pdf",
        "gap_role": "comparative tree-crop climate-risk mapping",
        "quote": "Negative climate hazard and exposure impacts for coffee producing regions could be potentially offset by targeting climate adaptation support to these high-risk regions",
        "interpretation": "The paper is used only as comparative evidence that adaptation in similar perennial crop systems has a spatial risk dimension.",
        "manuscript_use": ["Introduction", "Discussion"],
    },
    {
        "key": "Laderach2016",
        "authors": "Laderach et al.",
        "year": 2016,
        "journal": "Climatic Change",
        "title": "Climate change adaptation of coffee production in space and time",
        "doi": "10.1007/s10584-016-1788-9",
        "evidence_status": "pdf_audited",
        "retrieval": "papers/10.1007_s10584-016-1788-9__Climate_change_adaptation_of_coffee_production_in_space_and_time.pdf",
        "gap_role": "comparative tree-crop adaptation planning",
        "quote": "to develop an adaptation framework across time and space to guide adaptation planning in Nicaraguan coffee systems",
        "interpretation": "The article is used only as comparative evidence on spatially differentiated adaptation planning in a similar tropical perennial crop.",
        "manuscript_use": ["Introduction", "Discussion"],
    },
    {
        "key": "Laderach2013",
        "authors": "Laderach et al.",
        "year": 2013,
        "journal": "Climatic Change",
        "title": "Predicting the Future Climatic Suitability for Cocoa Farming of the World's Leading Producer Countries, Ghana and Cote d'Ivoire",
        "doi": "10.1007/s10584-013-0774-8",
        "evidence_status": "abstract_verified",
        "retrieval": "https://doi.org/10.1007/s10584-013-0774-8",
        "gap_role": "future climatic suitability of cocoa-producing regions",
        "quote": "we predict changes in relative climatic suitability for cocoa for 2050",
        "interpretation": "The paper supports using climatic suitability as part of the vulnerability literature surrounding cocoa production.",
        "manuscript_use": ["Introduction"],
    },
    {
        "key": "Lahive2019",
        "authors": "Lahive et al.",
        "year": 2019,
        "journal": "Agronomy for Sustainable Development",
        "title": "The physiological responses of cacao to the environment and the implications for climate change resilience. A review",
        "doi": "10.1007/s13593-018-0552-0",
        "evidence_status": "pdf_audited",
        "retrieval": "papers/cocoa_claim_support/The_physiological_responses_of_cacao_to_the_environment_and_the_implications_for_climate_change_resilience._A_review.pdf",
        "gap_role": "physiological sensitivity to heat and water stress",
        "quote": "water limitation causes significant yield reduction in cacao",
        "interpretation": "The review supports incorporating weather as vulnerability context by showing clear physiological sensitivity to water stress.",
        "manuscript_use": ["Introduction", "Literature Review", "Methods", "Discussion"],
    },
    {
        "key": "Jacobi2013",
        "authors": "Jacobi et al.",
        "year": 2013,
        "journal": "Renewable Agriculture and Food Systems",
        "title": "Agroecosystem resilience and farmers' perceptions of climate change impacts on cocoa farms in Alto Beni, Bolivia",
        "doi": "10.1017/S174217051300029X",
        "evidence_status": "pdf_audited",
        "retrieval": "papers/10.1017_s174217051300029x__Agroecosystem_resilience_and_farmers_perceptions_of_climate_change_impacts_on_cocoa_farms_in_.pdf",
        "gap_role": "agroecosystem resilience and cocoa farming systems",
        "quote": "Agroecosystem resilience was higher under the two agroforestry systems than under common practice monoculture",
        "interpretation": "The paper supports the argument that ecological design changes the buffering capacity of cocoa systems.",
        "manuscript_use": ["Introduction", "Discussion"],
    },
    {
        "key": "Niether2020",
        "authors": "Niether et al.",
        "year": 2020,
        "journal": "Environmental Research Letters",
        "title": "Cocoa agroforestry systems versus monocultures: a multi-dimensional meta-analysis",
        "doi": "10.1088/1748-9326/abb053",
        "evidence_status": "pdf_audited",
        "retrieval": "papers/10.1088_1748-9326_abb053__Cocoa_agroforestry_systems_versus_monocultures_a_multi-dimensional_meta-analysis.pdf",
        "gap_role": "agroforestry as adaptation and buffering strategy",
        "quote": "Cocoa agroforestry contributed to climate change mitigation by storing 2.5 times more carbon and to adaptation by lowering mean temperatures",
        "interpretation": "This directly supports the manuscript's treatment of agroforestry as a buffering mechanism under cocoa climate stress.",
        "manuscript_use": ["Introduction", "Literature Review", "Discussion"],
    },
    {
        "key": "Vaast2014",
        "authors": "Vaast and Somarriba",
        "year": 2014,
        "journal": "Agroforestry Systems",
        "title": "Trade-offs between crop intensification and ecosystem services: the role of agroforestry in cocoa cultivation",
        "doi": "10.1007/s10457-014-9762-x",
        "evidence_status": "pdf_audited",
        "retrieval": "papers/cocoa_claim_support/Trade-offs_between_crop_intensification_and_ecosystem_services_the_role_of_agroforestry_in_cocoa_cultivation.pdf",
        "gap_role": "interaction of price volatility, climate change, and ecological buffering",
        "quote": "The removal of shade trees diminishes smallholders' ability to adapt to global change driven by demographic pressure, food insecurity, cocoa price volatility and climate change.",
        "interpretation": "The article directly supports the manuscript's core claim that vulnerability is produced by market shocks interacting with limited buffering capacity.",
        "manuscript_use": ["Introduction", "Literature Review", "Discussion"],
    },
]


GAP_QUESTIONS = [
    "How strongly are international cocoa shocks transmitted to Colombian producer-linked prices once exchange-rate and oil conditions are taken into account?",
    "Does the supply chain distribute adjustment unevenly, leaving producer-linked prices more exposed than downstream consumer prices?",
    "How should localized weather variability enter the analysis: as a direct price driver or as contextual vulnerability that intensifies exposure?",
]


def build_markdown() -> str:
    rows = [
        "# Cocoa Literature Alignment Review",
        "",
        "This review is restricted to papers that support the manuscript's actual methodological gap. The corpus is cocoa-led. Coffee papers are retained only where the manuscript explicitly uses them as comparative evidence for tropical perennial cash crops cultivated under similar climatic and organizational conditions.",
        "",
        "The Introduction motivates the paper as a study of resilience-relevant exposure in cocoa systems. The literature review carries that argument forward by showing that the gap is not a generic absence of climate or market research, but the absence of an empirical design that links benchmark transmission, uneven supply-chain adjustment, and localized environmental stress in one framework.",
        "",
        "The first gap question concerns transmission. Cocoa market studies show that tighter integration with world markets can raise farmer exposure to international cocoa volatility, while exchange-rate conditions alter cocoa price risk through commodity-market channels \\citep{TsowouGayi2019,Jumah2001}. That evidence supports the manuscript's decision to model world cocoa prices, COP/USD, and oil conditions as separate parts of the transmission environment rather than as one undifferentiated external shock.",
        "",
        "The second gap question concerns uneven adjustment across the chain. The retained cocoa value-chain literature shows that producer vulnerability is shaped by price volatility together with weak farmer organizations, dependence on few buyers, and incomplete alignment between interventions and producer concerns \\citep{Mithofer2017}. Comparative work on coffee value chains is used only at the level of general mechanism and indicates that adaptive capacity in similar tropical tree-crop systems depends on support and coordination across the chain \\citep{Morales2022,Verburg2019}. Those studies do not estimate benchmark, producer, and downstream prices in one system, but they justify the manuscript's hypothesis that producer-linked adjustment may be harsher than downstream adjustment.",
        "",
        "The third gap question concerns weather and resilience. Cocoa-specific climate studies show that vulnerability depends on climatic suitability, physiological sensitivity, and farm-system design, while agroforestry can buffer heat stress and improve adaptive capacity \\citep{Schroth2016,Laderach2013,Lahive2019,Jacobi2013,Niether2020,Vaast2014,AkrofiAtitianti2018}. Comparative coffee studies are used only to support broader cross-crop statements about spatial climate risk and adaptation planning \\citep{Koh2020,Laderach2016}. The local weather architecture is additionally anchored in prior cocoa modelling for San Vicente del Chucuri \\citep{talero_sarmiento_etal_2025}. This literature justifies adding localized weather indicators, but it does not support treating weather as the dominant short-run price mechanism. That distinction is central to the manuscript's methods.",
        "",
        "Taken together, the retained literature supports a narrow and defensible claim: this manuscript identifies one resilience-relevant exposure mechanism in cocoa systems, namely the transmission of external cocoa shocks into producer-linked prices under macroeconomic conditions and local environmental stress. It does not claim to estimate resilience in the abstract, and the review below is organized to preserve that discipline.",
        "",
        "| Gap question | Supporting paper | Verbatim extract | Strict interpretation | Fit with the manuscript |",
        "|---|---|---|---|---|",
    ]
    fit_map = {
        "benchmark transmission and producer exposure": "Supports the world-to-Colombia transmission block.",
        "exchange-rate channel in cocoa price dynamics": "Supports keeping exchange rate separate from the cocoa benchmark.",
        "local weather architecture and variable selection": "Supports the local NASA POWER weather block used in Methods.",
        "producer constraints, weak market position, and institutional fit": "Supports the argument that exposure depends on producer capacity and chain position.",
        "comparative tree-crop evidence on value-chain support": "Supports only cautious cross-crop statements about chain-level adaptive capacity.",
        "comparative tree-crop evidence on adaptation systems": "Supports only cautious cross-crop statements about adaptation beyond the farm.",
        "climate vulnerability and adaptation in cocoa systems": "Supports the resilience framing around cocoa adaptation.",
        "climatic suitability, adaptation limits, and spatial vulnerability": "Supports treating climatic suitability as part of cocoa vulnerability literature.",
        "comparative tree-crop climate-risk mapping": "Supports only cautious cross-crop statements about spatial climate risk.",
        "comparative tree-crop adaptation planning": "Supports only cautious cross-crop statements about adaptation planning in similar systems.",
        "future climatic suitability of cocoa-producing regions": "Supports the climate-suitability strand used in the Introduction.",
        "physiological sensitivity to heat and water stress": "Supports treating weather as contextual vulnerability rather than pure noise.",
        "agroecosystem resilience and cocoa farming systems": "Supports the buffering role of agroforestry.",
        "agroforestry as adaptation and buffering strategy": "Supports the interpretation of ecological buffering under climate stress.",
        "interaction of price volatility, climate change, and ecological buffering": "Supports the claim that market and climate stress interact.",
    }
    for record in RECORDS:
        article = f"`{record['key']}` ({record['authors']}, {record['year']}, {record['journal']})"
        rows.append(
            f"| {record['gap_role']} | {article} | \"{record['quote']}\" | {record['interpretation']} | {fit_map[record['gap_role']]} |"
        )
    rows.extend(
        [
            "",
            "## Retained Corpus",
            "",
            "| Key | DOI | Evidence status | Manuscript use |",
            "|---|---|---|---|",
        ]
    )
    for record in RECORDS:
        rows.append(
            f"| `{record['key']}` | `{record['doi']}` | {record['evidence_status']} | {', '.join(record['manuscript_use'])} |"
        )
    return "\n".join(rows) + "\n"


def build_disaster_md() -> str:
    lines = [
        "# Cocoa-Focused Disaster and Resilience Review",
        "",
        "This file narrows the earlier broad disaster-resilience review to the subset of papers that actually fit the manuscript's empirical design. The retained set is cocoa-led. Coffee papers appear only where the manuscript explicitly uses them as comparative evidence for similar tropical perennial cash crops.",
        "",
        "The retained evidence supports three linked propositions. First, benchmark transmission matters because producer exposure increases when domestic cocoa markets are more tightly linked to world prices \\citep{TsowouGayi2019}. Second, vulnerability in cocoa systems is not reducible to prices alone because producers report price volatility together with weak organizations, buyer dependence, and climate-related constraints \\citep{Mithofer2017,AkrofiAtitianti2018}, while comparative coffee studies support broader cross-crop statements about value-chain organization and adaptation support \\citep{Morales2022,Verburg2019}. Third, cocoa climate studies justify weather as contextual vulnerability because climatic suitability, physiological sensitivity, and agroforestry buffering all shape how shocks are experienced \\citep{Schroth2016,Lahive2019,Jacobi2013,Niether2020,Vaast2014}, while prior local cocoa modelling supports the NASA POWER weather architecture used in Methods \\citep{talero_sarmiento_etal_2025}.",
        "",
        "The manuscript's contribution is therefore a linked design rather than a new abstract definition of resilience: it estimates price transmission, compares producer-linked and downstream adjustment, and then interprets localized weather as environmental stress layered onto that market exposure.",
        "",
        "| Paper | Role in the manuscript | Evidence status |",
        "|---|---|---|",
    ]
    for record in RECORDS:
        lines.append(f"| `{record['key']}` | {record['gap_role']} | {record['evidence_status']} |")
    return "\n".join(lines) + "\n"


def build_tex() -> str:
    return (
        "\\section{Literature Review}\n\n"
        "The literature relevant to this manuscript is narrower than the broader disaster-resilience field. The unresolved issue is not simply whether climate stress, institutions, or adaptation matter for rural livelihoods. The specific gap is whether international cocoa shocks are transmitted into producer-linked prices under macroeconomic conditions, whether that adjustment is distributed unevenly across the supply chain, and how local weather should be incorporated without being overstated as the dominant short-run price mechanism. The retained evidence is cocoa-led, with coffee studies used only where the manuscript explicitly invokes broader comparisons across tropical perennial cash crops cultivated under similar conditions. In that sense, the literature review extends the Introduction's argument rather than repeating it.\n\n"
        "Evidence from cocoa-market integration shows that tighter integration with world markets can increase producer exposure to international volatility, while exchange-rate conditions shape cocoa price risk through distinct financial channels \\citep{TsowouGayi2019,Jumah2001}. These studies justify modelling world cocoa prices and the COP/USD rate separately in the present manuscript. They do not, however, follow those shocks through producer-linked and downstream price layers in one empirical system.\n\n"
        "The cocoa value-chain literature identifies a second missing piece. Producer concerns include price volatility, weak farmer organizations, dependence on few buyers, and incomplete alignment between interventions and producer priorities \\citep{Mithofer2017}. Comparative work on coffee should not be read as direct cocoa evidence, but it reinforces the broader mechanism that adaptive capacity in similar tropical tree-crop systems depends on support and coordination across the chain \\citep{Morales2022,Verburg2019}. This combined evidence supports the idea that chain position matters for exposure, but it stops short of measuring whether downstream prices adjust differently from producer-linked cocoa prices in one aligned monthly design.\n\n"
        "Climate-oriented cocoa studies identify the third component of the gap. Cocoa vulnerability has been analysed through climatic suitability, physiological sensitivity, and adaptation options \\citep{Schroth2016,Laderach2013,Lahive2019}. Farm-system studies further show that agroforestry can strengthen buffering capacity and adaptation under cocoa climate stress \\citep{Jacobi2013,Niether2020,Vaast2014}. Comparative coffee studies are used only to support broader cross-crop statements about spatial climate risk and adaptation planning \\citep{Koh2020,Laderach2016}. Prior local cocoa modelling additionally supports the NASA POWER weather architecture used in the Methods section \\citep{talero_sarmiento_etal_2025}. These papers justify using localized weather indicators as contextual vulnerability, yet they do not show that weather should replace benchmark transmission as the core short-run adjustment mechanism.\n\n"
        "The manuscript therefore fills a specific gap left open across these strands. It combines international cocoa benchmarks, Colombian producer-linked prices, a European downstream chocolate price index, exchange-rate and oil controls, and localized weather indicators in one transparent empirical framework. The analytical gain comes from keeping those layers distinct: prices and macro controls identify transmission, downstream prices reveal how adjustment is distributed across the chain, and weather clarifies the local stress context in which transmitted shocks are experienced.\n"
    )


def build_manifest() -> dict:
    return {
        "paper_count": len(RECORDS),
        "scope": "Cocoa-led retained corpus aligned to manuscript gap and methods, with carefully labelled comparative coffee support",
        "gap_questions": GAP_QUESTIONS,
        "papers": RECORDS,
    }


def write_file(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    write_file(root / "output" / "literature_review.md", build_markdown())
    write_file(
        root / "output" / "disaster_resilience_review" / "disaster_resilience_review.md",
        build_disaster_md(),
    )
    write_file(
        root / "output" / "disaster_resilience_review" / "literature_review_disaster_resilience.tex",
        build_tex(),
    )
    write_file(
        root / "output" / "literature_review_manifest.json",
        json.dumps(build_manifest(), ensure_ascii=False, indent=2) + "\n",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
