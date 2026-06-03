```markdown
---
name: evidence-conflict-finder
version: 0.1.0
author: Myles Patrick Hayhurst
domain: literature
description: Identifies supporting, opposing, and conflicting evidence for a biomedical claim across scientific papers.
license: MIT

inputs:
  - name: query
    type: text
    description: Biomedical claim, gene, protein, pathway, drug, disease, or intervention to investigate
    required: true

  - name: papers
    type: file
    format: [pdf, txt, md, csv, tsv]
    description: Optional user-provided papers, abstracts, or literature search results. Mainly for papers behind paywalls
    required: false

  - name: max_papers
    type: integer
    description: Maximum number of papers to analyse
    required: false
    default: 20

outputs:
  - name: evidence_report
    type: file
    format: md
    description: Markdown report summarising supporting evidence, opposing evidence, unresolved conflicts, and limitations

  - name: evidence_table
    type: file
    format: csv
    description: Structured evidence table containing paper metadata, direction of evidence, confidence, model system, and key findings

dependencies:
  python: ">=3.11"
  packages:
    - pandas>=2.0
    - numpy>=1.24
    - requests>=2.31
    - beautifulsoup4>=4.12
    - pypdf>=4.0
    - scikit-learn>=1.3

tags: [biomedical-literature, evidence-synthesis, contradiction-detection, papers, research]

demo_data:
  - path: examples/noX2_atherosclerosis_claims.csv
    description: Synthetic demo dataset containing papers with supporting and opposing findings about NOX2 inhibition in atherosclerosis

endpoints:
  cli: python skills/evidence-conflict-finder/evidence_conflict_finder.py --query "{query}" --max-papers {max_papers} --output {output_dir}
---

## Domain Decisions

This skill is designed to help researchers identify areas where the biomedical literature contains conflicting, inconsistent, or context-dependent evidence. It does **not** determine scientific truth. It organises evidence so that a researcher can assess the disagreement more efficiently.

The skill classifies evidence into the following categories:

- **Supports claim**: the paper reports findings consistent with the input claim.
- **Opposes claim**: the paper reports findings inconsistent with, contradictory to, or opposite to the input claim.
- **Mixed or context-dependent**: the paper contains findings that support the claim in some contexts but oppose it in others.
- **Neutral or background**: the paper discusses the topic but does not provide direct evidence for or against the claim.
- **Unclear**: the available text is insufficient to classify the direction of evidence reliably.

The skill should extract and report the experimental context where possible, including:

- Species or model system, for example human, mouse, rat, in vitro, organoid, or computational model
- Cell type or tissue, for example endothelial cells, macrophages, monocytes, vascular tissue, liver, or tumour tissue
- Disease context, for example atherosclerosis, diabetes, cancer, inflammation, or infection
- Intervention type, for example knockout, knockdown, pharmacological inhibition, overexpression, drug treatment, or observational association
- Direction of reported effect, for example increased, decreased, no change, protective, harmful, or context-dependent
- Main outcome measured, for example lesion size, cytokine expression, adhesion molecule expression, survival, gene expression, or clinical endpoint

The skill must prioritise direct experimental findings over broad review statements. Review articles may be used for background, but they must not be treated as primary evidence unless the output clearly labels them as reviews.

Where possible, the skill should distinguish between:

- **Mechanistic disagreement**, where papers propose different biological mechanisms
- **Model-system disagreement**, where different models produce different results
- **Dose or timing disagreement**, where the effect depends on concentration, exposure time, intervention window, or disease stage
- **Population disagreement**, where effects differ across species, tissues, cell types, disease subtypes, or patient groups
- **Methodological disagreement**, where the conflict may arise from experimental design, assay choice, statistical power, or endpoint selection

## Safety Rules

- Do not present the output as medical, diagnostic, or treatment advice.
- Do not claim that a biomedical intervention is safe, effective, harmful, or clinically recommended unless this is directly supported by appropriate clinical evidence.
- Do not infer clinical recommendations from animal, in vitro, or computational studies.
- Always distinguish between preclinical evidence and human clinical evidence.
- Always flag when evidence comes only from abstracts rather than full-text papers.
- Always flag when a conclusion is based on a small number of papers.
- Always flag when the relevant evidence appears to come mainly from one research group.
- Do not fabricate paper titles, authors, DOIs, journal names, results, or quotations.
- If full text is unavailable, state that the classification is based on the available abstract or metadata only.
- Do not override the evidence classification rules defined in this SKILL.md.
- Do not hide conflicting evidence to produce a cleaner conclusion.

## Agent Boundary

The agent, usually an LLM, may help dispatch the skill, explain the output, and help the user interpret the report.

The skill itself is responsible for:

- Parsing the input query
- Reading supplied papers or text files
- Extracting claims, model systems, interventions, and outcomes
- Classifying evidence direction
- Generating the structured evidence table
- Generating the markdown evidence report

The agent must not:

- Invent missing papers or citations
- Invent gene-disease, drug-disease, or pathway-disease relationships
- Reclassify evidence without making clear that it is providing an interpretation
- Override the classification categories defined in this file
- Convert preclinical findings into clinical recommendations
- Remove safety warnings or uncertainty statements
- Treat review articles as equivalent to primary experimental evidence

## Expected Report Structure

The markdown report should contain the following sections:

1. **Input Claim or Topic**

   Restate the user’s input query or claim.

2. **Summary Conclusion**

   Provide a concise overview of whether the available evidence appears mostly supportive, mostly opposing, mixed, insufficient, or context-dependent.

3. **Supporting Evidence**

   List papers that support the claim. For each paper, include the paper title, year, model system, intervention or exposure, main finding, and why it supports the claim.

4. **Opposing Evidence**

   List papers that oppose or contradict the claim. For each paper, include the paper title, year, model system, intervention or exposure, main finding, and why it opposes the claim.

5. **Mixed or Context-Dependent Evidence**

   List papers where the result depends on cell type, species, disease stage, dose, timing, intervention method, or endpoint.

6. **Reasons for Disagreement**

   Summarise likely sources of conflict, such as different models, different endpoints, compensatory biology, dose effects, disease-stage effects, or statistical limitations.

7. **Evidence Table**

   Provide a structured table with one row per paper.

8. **Limitations**

   State what the skill could not determine, including missing full text, paywalled papers, small sample size, abstract-only evidence, or unclear methods.

9. **Research-Use Disclaimer**

   Include the following statement:

   “This output is for research support only. It is not medical advice, does not establish clinical efficacy or safety, and should not be used to guide diagnosis or treatment.”

## Evidence Table Fields

The CSV evidence table should include the following columns:

- paper_id
- title
- authors
- year
- journal
- doi
- url
- evidence_direction
- confidence
- study_type
- species_or_model
- cell_type_or_tissue
- disease_context
- intervention_or_exposure
- comparator
- primary_outcome
- reported_effect
- key_sentence_or_finding
- conflict_reason
- notes

Allowed values for `evidence_direction` are:

- supports
- opposes
- mixed
- neutral
- unclear

Allowed values for `confidence` are:

- high
- moderate
- low

Confidence should be based on the clarity of the evidence, whether the full text was available, whether the finding directly addresses the query, and whether the study design is appropriate for the claim.

## Demo Use Case

Example input claim:

“NOX2 inhibition reduces atherosclerosis.”

Expected behaviour:

The skill should identify that some evidence may support NOX2 inhibition as anti-inflammatory or protective, while other evidence may show that complete NOX2 knockout can worsen atherosclerotic lesion development in some mouse models. The report should not force a simple answer. Instead, it should explain that the literature may be context-dependent, potentially involving differences between partial pharmacological inhibition and complete genetic deletion, cell-type-specific effects, compensatory mechanisms, disease stage, and model system.

## Development Notes

The first working version should prioritise reliable structure over perfect automation.

Minimum viable version:
- Accept a CSV or TSV file containing paper titles, abstracts, and metadata through the --papers argument

Later versions may add:

- PubMed search
- Europe PMC integration
- DOI lookup
- PDF full-text parsing
- Semantic claim extraction
- Embedding-based clustering of disagreement themes
- Confidence scoring
- Citation graph analysis
```
