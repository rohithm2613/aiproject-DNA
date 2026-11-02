import re
from typing import List, Optional
from app.models.project import Project
from app.models.analysis import ProjectAnalysis
from app.services.github.base import clean_text

STOP_WORDS = {
    "a", "about", "above", "after", "again", "against", "all", "am", "an", "and",
    "any", "are", "as", "at", "be", "because", "been", "before", "being", "below",
    "between", "both", "but", "by", "can", "could", "did", "do", "does", "doing",
    "down", "during", "each", "few", "for", "from", "further", "had", "has", "have",
    "having", "he", "her", "here", "him", "his", "how", "i", "if", "in", "into",
    "is", "it", "its", "itself", "just", "me", "more", "most", "my", "no", "nor",
    "not", "now", "of", "off", "on", "once", "only", "or", "other", "our", "out",
    "over", "own", "same", "she", "should", "so", "some", "such", "than", "that",
    "the", "their", "them", "then", "there", "these", "they", "this", "those",
    "through", "to", "too", "under", "until", "up", "very", "was", "we", "were",
    "what", "when", "where", "which", "while", "who", "whom", "why", "with",
    "system", "platform", "project", "using", "based", "application", "tool", "solution"
}

def extract_meaningful_tokens(text: Optional[str], max_tokens: int = 5) -> List[str]:
    """Extracts distinctive technical terms while stripping punctuation and stop words."""
    if not text:
        return []
    words = re.findall(r"[A-Za-z0-9\-]+", str(text))
    tokens: List[str] = []
    for w in words:
        w_lower = w.lower()
        if w_lower not in STOP_WORDS and len(w_lower) > 2 and not w_lower.isnumeric():
            if w_lower not in [t.lower() for t in tokens]:
                tokens.append(w)
                if len(tokens) >= max_tokens:
                    break
    return tokens

def generate_github_queries(
    project: Project,
    analysis: Optional[ProjectAnalysis] = None,
    max_queries: int = 4
) -> List[str]:
    """
    Constructs focused GitHub repository search queries from the project title,
    problem statement, proposed solution, and Phase 3 analysis keywords/technologies.
    Returns 2 to 5 succinct, non-redundant queries.
    """
    queries: List[str] = []

    # 1. Query 1: Project Title Core Terms + Primary Domain Term
    title_tokens = extract_meaningful_tokens(project.title, max_tokens=4)
    domain = (analysis.primary_domain if analysis else project.domain) or ""
    domain_tokens = extract_meaningful_tokens(domain, max_tokens=2)

    primary_terms = list(dict.fromkeys(title_tokens + domain_tokens))
    if primary_terms:
        q1 = " ".join(primary_terms[:5])
        if q1:
            queries.append(q1)

    # 2. Query 2: Technical Keywords Focus
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
            q2 = " ".join(selected_kws)
            if q2 and q2 not in queries:
                queries.append(q2)

    # 3. Query 3: Problem/Solution Concepts + Primary Technology
    tech_candidates: List[str] = []
    if project.technologies and isinstance(project.technologies, list):
        tech_candidates.extend(project.technologies)
    if analysis and analysis.user_technologies and isinstance(analysis.user_technologies, list):
        tech_candidates.extend(analysis.user_technologies)
    if analysis and analysis.recommended_technologies and isinstance(analysis.recommended_technologies, dict):
        frameworks = analysis.recommended_technologies.get("frameworks") or []
        if isinstance(frameworks, list):
            tech_candidates.extend(frameworks)

    clean_techs = [clean_text(t) for t in tech_candidates if clean_text(t)]
    clean_techs = list(dict.fromkeys(clean_techs))  # deduplicate

    if analysis and (analysis.problem_statement or analysis.proposed_solution):
        concept_text = f"{analysis.problem_statement or ''} {analysis.proposed_solution or ''}"
        concept_tokens = extract_meaningful_tokens(concept_text, max_tokens=3)
        if concept_tokens:
            q3_terms = concept_tokens[:2]
            if clean_techs:
                q3_terms.append(clean_techs[0])
            q3 = " ".join(q3_terms)
            if q3 and q3 not in queries:
                queries.append(q3)

    # 4. Query 4: Primary Domain + Top Framework/Language
    if domain_tokens and clean_techs:
        q4 = f"{domain_tokens[0]} {' '.join(clean_techs[:2])}"
        if q4 and q4 not in queries:
            queries.append(q4)

    # Fallback if no queries could be constructed
    if not queries:
        fallback = " ".join(title_tokens)[:50].strip()
        queries.append(fallback if fallback else project.title)

    # Clean and deduplicate queries
    deduped: List[str] = []
    seen = set()
    for q in queries:
        norm = q.lower().strip()
        if norm and norm not in seen:
            seen.add(norm)
            deduped.append(q)
            if len(deduped) >= max_queries:
                break

    return deduped

