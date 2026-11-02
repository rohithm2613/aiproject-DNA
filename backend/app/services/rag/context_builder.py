import re
from typing import List, Optional
from app.models.project import Project
from app.models.analysis import ProjectAnalysis
from app.schemas.validation import EvidenceItem

# Keywords / patterns to neutralize in untrusted external text
INJECTION_PATTERNS = [
    re.compile(r"ignore\s+(all\s+)?(previous|prior)\s+instructions?", re.IGNORECASE),
    re.compile(r"system\s*:\s*", re.IGNORECASE),
    re.compile(r"assistant\s*:\s*", re.IGNORECASE),
    re.compile(r"user\s*:\s*", re.IGNORECASE),
    re.compile(r"you\s+are\s+now\s+", re.IGNORECASE),
    re.compile(r"<\|im_start\|>", re.IGNORECASE),
    re.compile(r"<\|im_end\|>", re.IGNORECASE),
]

def sanitize_untrusted_text(text: Optional[str], max_len: int = 2000) -> str:
    """
    Sanitizes external untrusted text (paper abstracts, repository READMEs, descriptions)
    to prevent prompt injection while preserving semantic content.
    """
    if not text:
        return ""
    
    cleaned = text
    # Neutralize injection triggers
    for pat in INJECTION_PATTERNS:
        cleaned = pat.sub("[filtered_prompt_override]", cleaned)
    
    # Strip backticks to avoid breaking outer markdown fences
    cleaned = cleaned.replace("```", "'''")
    # Normalize excessive whitespaces
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    
    if len(cleaned) > max_len:
        cleaned = cleaned[:max_len] + "... [truncated]"
    return cleaned

def build_rag_context(
    project: Project,
    analysis: Optional[ProjectAnalysis],
    evidence_items: List[EvidenceItem],
    max_chars: int = 40000,
) -> str:
    """
    Constructs a structured, character-budgeted prompt context containing:
    1. The user's project idea details.
    2. Discrete tagged evidence blocks with traceable IDs (EVID-PAP-xx, EVID-REP-xx, EVID-GAP-xx).
    3. Clear grounding instructions for the RAG synthesis engine.
    """
    sections: List[str] = []
    
    # -------------------------------------------------------------------------
    # Header: Target Project Idea
    # -------------------------------------------------------------------------
    idea_header = [
        "================================================================================",
        "TARGET PROJECT UNDER VALIDATION",
        "================================================================================",
        f"Project Title: {project.title}",
        f"Project Description: {project.description or 'No description provided'}",
    ]
    if project.domain:
        idea_header.append(f"Primary Domain: {project.domain}")
    
    if analysis:
        if analysis.problem_statement:
            idea_header.append(f"Problem Statement: {analysis.problem_statement}")
        if analysis.proposed_solution:
            idea_header.append(f"Proposed Solution: {analysis.proposed_solution}")
        if getattr(analysis, "target_users", None):
            users = ", ".join(analysis.target_users) if isinstance(analysis.target_users, list) else str(analysis.target_users)
            idea_header.append(f"Target Users: {users}")
        if getattr(analysis, "keywords", None):
            kw = ", ".join(analysis.keywords) if isinstance(analysis.keywords, list) else str(analysis.keywords)
            idea_header.append(f"Keywords: {kw}")
        if getattr(analysis, "objectives", None):
            objs = ", ".join(analysis.objectives) if isinstance(analysis.objectives, list) else str(analysis.objectives)
            idea_header.append(f"Objectives: {objs}")
            
    sections.append("\n".join(idea_header))
    
    # -------------------------------------------------------------------------
    # Evidence Items Split by Type
    # -------------------------------------------------------------------------
    paper_evids = [e for e in evidence_items if e.source_type == "research_paper"]
    repo_evids = [e for e in evidence_items if e.source_type in ("github_repository", "repository_analysis")]
    gap_evids = [e for e in evidence_items if e.source_type == "innovation_gap"]
    patent_evids = [e for e in evidence_items if e.source_type == "patent"]
    
    # Papers
    if paper_evids:
        p_lines = [
            "\n================================================================================",
            f"RETRIEVED ACADEMIC RESEARCH EVIDENCE ({len(paper_evids)} sources)",
            "================================================================================",
        ]
        for e in paper_evids:
            p_lines.append(f"\n--- EVIDENCE BLOCK [{e.evidence_id}] ---")
            p_lines.append(f"Title: {e.source_title}")
            if e.source_author:
                p_lines.append(f"Authors: {e.source_author}")
            if e.publication_year:
                p_lines.append(f"Year: {e.publication_year}")
            if e.source_url:
                p_lines.append(f"URL: {e.source_url}")
            if e.similarity_score is not None:
                p_lines.append(f"Semantic Similarity: {e.similarity_score:.4f}")
            p_lines.append(f"Evidence Strength: {e.evidence_strength}")
            p_lines.append(f"Nature: {e.documented_or_inferred}")
            sanitized_content = sanitize_untrusted_text(e.evidence_content, max_len=1500)
            p_lines.append(f"Excerpt & Findings:\n{sanitized_content}")
            p_lines.append(f"--- END [{e.evidence_id}] ---")
        sections.append("\n".join(p_lines))
        
    # Repositories
    if repo_evids:
        r_lines = [
            "\n================================================================================",
            f"RETRIEVED GITHUB IMPLEMENTATION EVIDENCE ({len(repo_evids)} sources)",
            "================================================================================",
        ]
        for e in repo_evids:
            r_lines.append(f"\n--- EVIDENCE BLOCK [{e.evidence_id}] ---")
            r_lines.append(f"Repository: {e.source_title}")
            if e.source_url:
                r_lines.append(f"URL: {e.source_url}")
            if e.similarity_score is not None:
                r_lines.append(f"Semantic Similarity: {e.similarity_score:.4f}")
            r_lines.append(f"Evidence Strength: {e.evidence_strength}")
            r_lines.append(f"Nature: {e.documented_or_inferred}")
            sanitized_content = sanitize_untrusted_text(e.evidence_content, max_len=1800)
            r_lines.append(f"Features, Architecture & Findings:\n{sanitized_content}")
            r_lines.append(f"--- END [{e.evidence_id}] ---")
        sections.append("\n".join(r_lines))

    # Patents & Prior Art (Phase 4.6)
    if patent_evids:
        pat_lines = [
            "\n================================================================================",
            f"RETRIEVED PATENT & PRIOR-ART EVIDENCE ({len(patent_evids)} sources)",
            "================================================================================",
        ]
        for e in patent_evids:
            pat_lines.append(f"\n--- EVIDENCE BLOCK [{e.evidence_id}] ---")
            pat_lines.append(f"Publication / Title: {e.source_title}")
            if e.source_author:
                pat_lines.append(f"Assignee / Applicant: {e.source_author}")
            if e.publication_year:
                pat_lines.append(f"Publication Year: {e.publication_year}")
            if e.source_url:
                pat_lines.append(f"Google Patents URL: {e.source_url}")
            if e.similarity_score is not None:
                pat_lines.append(f"Semantic Similarity: {e.similarity_score:.4f}")
            pat_lines.append(f"Evidence Strength: {e.evidence_strength}")
            pat_lines.append(f"Nature: {e.documented_or_inferred}")
            sanitized_content = sanitize_untrusted_text(e.evidence_content, max_len=1500)
            pat_lines.append(f"Disclosed Architecture & Claims Excerpts:\n{sanitized_content}")
            pat_lines.append(f"--- END [{e.evidence_id}] ---")
        sections.append("\n".join(pat_lines))
        
    # Innovation Gap Candidates
    if gap_evids:
        g_lines = [
            "\n================================================================================",
            f"CANDIDATE INNOVATION GAPS TO VALIDATE ({len(gap_evids)} items)",
            "================================================================================",
        ]
        for e in gap_evids:
            g_lines.append(f"\n--- EVIDENCE BLOCK [{e.evidence_id}] ---")
            g_lines.append(f"Gap Candidate: {e.source_title}")
            g_lines.append(f"Category: {e.evidence_category}")
            g_lines.append(f"Details:\n{sanitize_untrusted_text(e.evidence_content, max_len=800)}")
            g_lines.append(f"--- END [{e.evidence_id}] ---")
        sections.append("\n".join(g_lines))
        
    # -------------------------------------------------------------------------
    # Synthesis & Grounding Guardrails Instructions
    # -------------------------------------------------------------------------
    instructions = [
        "\n================================================================================",
        "STRICT GROUNDING & CITATION RULES FOR VALIDATION REPORT",
        "================================================================================",
        "1. Every factual assertion, capability claim, or gap validation MUST cite one or more Evidence IDs (e.g. EVID-PAP-01, EVID-REP-02, EVID-PAT-01).",
        "2. DO NOT hallucinate evidence IDs. ONLY cite IDs listed above.",
        "3. Evaluate each candidate innovation gap into one of: 'supported_gap', 'partially_supported_gap', 'not_supported_gap', 'insufficient_evidence'.",
        "4. If a capability or feature is missing in the analyzed repos/papers/patents, use precise phrasing like 'not found in the analyzed sources' rather than claiming it does not exist worldwide.",
        "5. Remember: Absence of evidence is NOT evidence of absence (e.g., an unmentioned feature in a README or patent abstract does not prove absence).",
        "6. Do NOT certify global novelty or provide legal patentability opinions. Provide objective preliminary research validation only.",
        "7. Fill all 10 required report sections completely according to the output schema.",
    ]
    sections.append("\n".join(instructions))
    
    full_text = "\n".join(sections)
    
    # Enforce character budget if exceeded
    if len(full_text) > max_chars:
        full_text = full_text[:max_chars - 200] + "\n\n[CONTEXT BUDGET REACHED: Remaining sources truncated for token budget preservation]"
        
    return full_text
