#!/usr/bin/env python3

from __future__ import annotations

import argparse
from pathlib import Path
import pandas as pd


EVIDENCE_DIRECTIONS = ["supports", "opposes", "mixed", "neutral", "unclear"]


SUPPORT_TERMS = [
    "reduced",
    "decreased",
    "attenuated",
    "suppressed",
    "inhibited",
    "protected",
    "ameliorated",
    "lowered",
    "improved",
]

OPPOSE_TERMS = [
    "increased",
    "larger",
    "worsened",
    "accelerated",
    "exacerbated",
    "aggravated",
    "impaired",
    "harmful",
    "delayed",
]

MIXED_TERMS = [
    "however",
    "whereas",
    "although",
    "but",
    "stage-dependent",
    "dose-dependent",
    "context-dependent",
    "cell-type",
    "endpoint",
    "unchanged",
]

REVIEW_TERMS = [
    "review",
    "summarises",
    "summarizes",
    "does not present new primary data",
]


def read_papers(path: Path) -> pd.DataFrame:
    """Read a CSV or TSV file containing paper metadata and abstracts."""
    if not path.exists():
        raise FileNotFoundError(f"Input paper file not found: {path}")

    if path.suffix.lower() == ".csv":
        return pd.read_csv(path)

    if path.suffix.lower() in [".tsv", ".txt"]:
        return pd.read_csv(path, sep="\t")

    raise ValueError("Input file must be .csv, .tsv, or tab-delimited .txt")


def normalise_text(value: object) -> str:
    """Safely convert a table cell to lowercase text."""
    if pd.isna(value):
        return ""
    return str(value).lower()


def classify_evidence(title: str, abstract: str) -> tuple[str, str, str]:
    """
    Classify evidence direction using simple transparent keyword rules.

    Returns:
        evidence_direction, confidence, notes
    """
    text = f"{title} {abstract}".lower()

    support_hits = [term for term in SUPPORT_TERMS if term in text]
    oppose_hits = [term for term in OPPOSE_TERMS if term in text]
    mixed_hits = [term for term in MIXED_TERMS if term in text]
    review_hits = [term for term in REVIEW_TERMS if term in text]

    if review_hits:
        return "neutral", "low", "Review/background article; not treated as primary evidence."

    if support_hits and oppose_hits:
        return (
            "mixed",
            "moderate",
            f"Contains both support terms {support_hits} and opposition terms {oppose_hits}.",
        )

    if mixed_hits and (support_hits or oppose_hits):
        return (
            "mixed",
            "moderate",
            f"Contains context-dependence terms {mixed_hits}.",
        )

    if support_hits:
        return "supports", "moderate", f"Matched support terms: {support_hits}."

    if oppose_hits:
        return "opposes", "moderate", f"Matched opposition terms: {oppose_hits}."

    if len(text.strip()) < 50:
        return "unclear", "low", "Insufficient text available for classification."

    return "neutral", "low", "Topic discussed but no direct directional evidence detected."


def infer_study_type(title: str, abstract: str) -> str:
    """Infer broad study type from title/abstract text."""
    text = f"{title} {abstract}".lower()

    if "review" in text:
        return "review"
    if any(term in text for term in ["mouse", "mice", "rat", "animal"]):
        return "animal"
    if any(term in text for term in ["cultured", "cells", "cell", "in vitro"]):
        return "in vitro"
    if any(term in text for term in ["human", "patient", "clinical"]):
        return "human"
    if any(term in text for term in ["computational", "model"]):
        return "computational"

    return "not specified"


def infer_context(title: str, abstract: str) -> dict[str, str]:
    """Extract lightweight context fields using keyword rules."""
    text = f"{title} {abstract}".lower()

    species_or_model = "not specified"
    if "mouse" in text or "mice" in text:
        species_or_model = "mouse"
    elif "rat" in text:
        species_or_model = "rat"
    elif "human" in text:
        species_or_model = "human"
    elif "cultured" in text or "in vitro" in text:
        species_or_model = "in vitro"

    cell_type_or_tissue = "not specified"
    if "endothelial" in text:
        cell_type_or_tissue = "endothelial cells/vascular endothelium"
    elif "macrophage" in text:
        cell_type_or_tissue = "macrophages"
    elif "monocyte" in text:
        cell_type_or_tissue = "monocytes"
    elif "plaque" in text:
        cell_type_or_tissue = "atherosclerotic plaque"

    disease_context = "not specified"
    if "atherosclerosis" in text or "atherosclerotic" in text or "plaque" in text:
        disease_context = "atherosclerosis"

    intervention_or_exposure = "not specified"
    if "knockout" in text or "deficiency" in text:
        intervention_or_exposure = "genetic knockout/deficiency"
    elif "knockdown" in text:
        intervention_or_exposure = "gene knockdown"
    elif "inhibition" in text or "inhibitor" in text:
        intervention_or_exposure = "pharmacological inhibition"
    elif "expression" in text:
        intervention_or_exposure = "expression association"

    return {
        "species_or_model": species_or_model,
        "cell_type_or_tissue": cell_type_or_tissue,
        "disease_context": disease_context,
        "intervention_or_exposure": intervention_or_exposure,
    }


def build_evidence_table(df: pd.DataFrame, query: str, max_papers: int) -> pd.DataFrame:
    """Create a structured evidence table from input paper rows."""
    required_columns = {"title", "abstract"}
    missing = required_columns - set(df.columns)

    if missing:
        raise ValueError(f"Input file is missing required columns: {sorted(missing)}")

    df = df.head(max_papers).copy()
    rows = []

    for index, row in df.iterrows():
        title = normalise_text(row.get("title"))
        abstract = normalise_text(row.get("abstract"))

        evidence_direction, confidence, notes = classify_evidence(title, abstract)
        context = infer_context(title, abstract)

        rows.append(
            {
                "paper_id": row.get("paper_id", index + 1),
                "title": row.get("title", ""),
                "authors": row.get("authors", ""),
                "year": row.get("year", ""),
                "journal": row.get("journal", ""),
                "doi": row.get("doi", ""),
                "url": row.get("url", ""),
                "evidence_direction": evidence_direction,
                "confidence": confidence,
                "study_type": infer_study_type(title, abstract),
                "species_or_model": context["species_or_model"],
                "cell_type_or_tissue": context["cell_type_or_tissue"],
                "disease_context": context["disease_context"],
                "intervention_or_exposure": context["intervention_or_exposure"],
                "comparator": "",
                "primary_outcome": "",
                "reported_effect": "",
                "key_sentence_or_finding": row.get("abstract", ""),
                "conflict_reason": "",
                "notes": notes,
            }
        )

    return pd.DataFrame(rows)


def write_report(query: str, evidence_table: pd.DataFrame, output_path: Path) -> None:
    """Write a markdown evidence conflict report."""
    counts = evidence_table["evidence_direction"].value_counts().to_dict()

    supports = evidence_table[evidence_table["evidence_direction"] == "supports"]
    opposes = evidence_table[evidence_table["evidence_direction"] == "opposes"]
    mixed = evidence_table[evidence_table["evidence_direction"] == "mixed"]
    neutral = evidence_table[evidence_table["evidence_direction"] == "neutral"]
    unclear = evidence_table[evidence_table["evidence_direction"] == "unclear"]

    if len(mixed) > 0 or (len(supports) > 0 and len(opposes) > 0):
        conclusion = "The available evidence appears mixed or context-dependent."
    elif len(supports) > 0 and len(opposes) == 0:
        conclusion = "The available evidence appears mostly supportive."
    elif len(opposes) > 0 and len(supports) == 0:
        conclusion = "The available evidence appears mostly opposing."
    else:
        conclusion = "The available evidence is insufficient or mostly neutral."

    lines = [
        "# Evidence Conflict Report",
        "",
        "## Input Claim or Topic",
        "",
        query,
        "",
        "## Summary Conclusion",
        "",
        conclusion,
        "",
        "### Evidence direction counts",
        "",
    ]

    for direction in EVIDENCE_DIRECTIONS:
        lines.append(f"- {direction}: {counts.get(direction, 0)}")

    def add_section(title: str, subset: pd.DataFrame) -> None:
        lines.extend(["", f"## {title}", ""])

        if subset.empty:
            lines.append("No papers classified in this category.")
            return

        for _, row in subset.iterrows():
            lines.extend(
                [
                    f"### {row['title']}",
                    "",
                    f"- Year: {row['year']}",
                    f"- Journal: {row['journal']}",
                    f"- Study type: {row['study_type']}",
                    f"- Model/context: {row['species_or_model']}; {row['cell_type_or_tissue']}",
                    f"- Intervention/exposure: {row['intervention_or_exposure']}",
                    f"- Confidence: {row['confidence']}",
                    f"- Classification note: {row['notes']}",
                    "",
                ]
            )

    add_section("Supporting Evidence", supports)
    add_section("Opposing Evidence", opposes)
    add_section("Mixed or Context-Dependent Evidence", mixed)
    add_section("Neutral or Background Evidence", neutral)
    add_section("Unclear Evidence", unclear)

    lines.extend(
        [
            "",
            "## Reasons for Disagreement",
            "",
            "Potential sources of disagreement include differences in model system, intervention type, disease stage, endpoint measured, and whether the evidence concerns partial inhibition, complete genetic loss, or observational association.",
            "",
            "## Limitations",
            "",
            "- This MVP uses transparent keyword-based classification.",
            "- Classifications are based only on the supplied title and abstract text.",
            "- The output should be treated as evidence triage, not a systematic review.",
            "- Full-text review is required before drawing firm biological conclusions.",
            "",
            "## Research-Use Disclaimer",
            "",
            "This output is for research support only. It is not medical advice, does not establish clinical efficacy or safety, and should not be used to guide diagnosis or treatment.",
            "",
        ]
    )

    output_path.write_text("\n".join(lines), encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Classify supporting, opposing, mixed, neutral, and unclear evidence for a biomedical claim."
    )
    parser.add_argument("--query", required=True, help="Biomedical claim or topic to investigate.")
    parser.add_argument("--papers", required=True, help="CSV/TSV file containing paper titles and abstracts.")
    parser.add_argument("--output", required=True, help="Output directory.")
    parser.add_argument("--max-papers", type=int, default=20, help="Maximum number of papers to analyse.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    papers_path = Path(args.papers)
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    papers = read_papers(papers_path)
    evidence_table = build_evidence_table(
        df=papers,
        query=args.query,
        max_papers=args.max_papers,
    )

    evidence_table_path = output_dir / "evidence_table.csv"
    evidence_report_path = output_dir / "evidence_report.md"

    evidence_table.to_csv(evidence_table_path, index=False)
    write_report(args.query, evidence_table, evidence_report_path)

    print(f"Wrote evidence table: {evidence_table_path}")
    print(f"Wrote evidence report: {evidence_report_path}")


if __name__ == "__main__":
    main()