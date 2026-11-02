import re
from typing import List, Optional
from app.models.analysis import ProjectAnalysis
from app.models.project import Project
from app.services.research.base import clean_text

# Common academic and conversational stop words to strip from queries
STOP_WORDS = {
    "a", "about", "above", "after", "again", "against", "all", "am", "an", "and",
    "any", "are", "aren't", "as", "at", "be", "because", "been", "before", "being",
    "below", "between", "both", "but", "by", "can", "cannot", "could", "did", "do",
    "does", "doing", "don't", "down", "during", "each", "few", "for", "from", "further",
    "had", "has", "have", "having", "he", "her", "here", "hers", "herself", "him",
    "himself", "his", "how", "i", "if", "in", "into", "is", "it", "its", "itself",
    "just", "me", "more", "most", "my", "myself", "no", "nor", "not", "now", "of",
    "off", "on", "once", "only", "or", "other", "our", "ours", "ourselves", "out",
    "over", "own", "same", "she", "should", "so", "some", "such", "than", "that",
    "the", "their", "theirs", "them", "themselves", "then", "there", "these", "they",
    "this", "those", "through", "to", "too", "under", "until", "up", "very", "was",
    "wasn't", "we", "were", "weren't", "what", "when", "where", "which", "while",
    "who", "whom", "why", "with", "would", "you", "your", "yours", "yourself",
    "using", "based", "system", "platform", "project", "approach", "novel", "new"
}

def extract_meaningful_tokens(text: str, max_tokens: int = 5) -> List[str]:
    """Extracts distinctive technical keywords by stripping stop words and punctuation."""
    if not text:
        return []
    words = re.findall(r"[A-Za-z0-9\-]+", text)
    tokens: List[str] = []
    for w in words:
        w_lower = w.lower()
        if w_lower not in STOP_WORDS and len(w_lower) > 2 and not w_lower.isnumeric():
            if w_lower not in [t.lower() for t in tokens]:
                tokens.append(w)
                if len(tokens) >= max_tokens:
                    break
    return tokens

def generate_research_queries(
    project: Project,
    analysis: Optional[ProjectAnalysis] = None,
    max_queries: int = 3
) -> List[str]:
    """
    Constructs 1-3 targeted academic search queries derived from the project description
    and Phase 3 analysis dossier (if available).
    Ensures queries are succinct, non-redundant, and fit API length constraints.
    """
    queries: List[str] = []

    # 1. Primary Query: Cleaned Project Title + Primary Domain
    title_tokens = extract_meaningful_tokens(project.title, max_tokens=5)
    domain = (analysis.primary_domain if analysis else project.domain) or ""
    domain_tokens = extract_meaningful_tokens(domain, max_tokens=2)

    primary_terms = list(dict.fromkeys(title_tokens + domain_tokens))
    if primary_terms:
        primary_query = " ".join(primary_terms[:6])
        if primary_query:
            queries.append(primary_query)

    # 2. Secondary Query: Technical Keywords & Domain
    if analysis and analysis.keywords:
        kw_list = analysis.keywords if isinstance(analysis.keywords, list) else []
        selected_kws: List[str] = []
        for kw in kw_list:
            if isinstance(kw, str):
                cleaned_kw = clean_text(kw)
                if cleaned_kw and cleaned_kw.lower() not in [q.lower() for q in queries]:
                    selected_kws.append(cleaned_kw)
            if len(selected_kws) >= 3:
                break
        
        if selected_kws:
            kw_query = " ".join(selected_kws)
            if domain_tokens:
                kw_query = f"{domain_tokens[0]} {kw_query}"
            if kw_query and kw_query not in queries:
                queries.append(kw_query)

    # 3. Tertiary Query: Problem statement / Proposed solution core tokens
    if analysis and (analysis.problem_statement or analysis.proposed_solution):
        combined = f"{analysis.problem_statement or ''} {analysis.proposed_solution or ''}"
        concept_tokens = extract_meaningful_tokens(combined, max_tokens=4)
        if concept_tokens:
            concept_query = " ".join(concept_tokens[:4])
            if concept_query and concept_query not in queries:
                queries.append(concept_query)

    # Fallback if no analysis available or queries list is empty
    if not queries:
        desc_tokens = extract_meaningful_tokens(project.description, max_tokens=4)
        fallback = " ".join(title_tokens + desc_tokens)[:60].strip()
        queries.append(fallback if fallback else project.title)

    # Deduplicate while preserving order and apply max limit
    seen = set()
    deduped_queries = []
    for q in queries:
        norm = q.lower().strip()
        if norm and norm not in seen:
            seen.add(norm)
            deduped_queries.append(q)
            if len(deduped_queries) >= max_queries:
                break

    return deduped_queries

