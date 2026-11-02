import re
from typing import List, Optional, Set
from app.models.project import Project
from app.models.analysis import ProjectAnalysis
from app.models.github_repo import GitHubRepository
from app.schemas.repository_analysis import (
    TechnologyStackResponse,
    ExtractedFeatureResponse,
    SimilarityAnalysisResponse,
)

STOPWORDS: Set[str] = {
    "a", "an", "the", "and", "or", "in", "on", "at", "to", "for", "with", "by", "of",
    "from", "as", "is", "are", "was", "were", "it", "this", "that", "these", "those",
    "using", "used", "via", "based", "system", "project", "application", "tool", "solution",
}

def tokenize(text: Optional[str]) -> Set[str]:
    """Tokenizes text into lowercase alpha words excluding common stopwords."""
    if not text:
        return set()
    words = re.findall(r"\b[a-zA-Z0-9_\-\+]{2,}\b", text.lower())
    return {w for w in words if w not in STOPWORDS}

def calculate_jaccard(set_a: Set[str], set_b: Set[str]) -> float:
    """Calculates Jaccard similarity index between two sets."""
    if not set_a or not set_b:
        return 0.0
    intersection = set_a.intersection(set_b)
    union = set_a.union(set_b)
    return (len(intersection) / len(union)) if union else 0.0

def calculate_similarity(
    project: Project,
    analysis: Optional[ProjectAnalysis],
    repo: GitHubRepository,
    tech_stack: TechnologyStackResponse,
    features: List[ExtractedFeatureResponse],
    readme_text: Optional[str] = None,
) -> SimilarityAnalysisResponse:
    """
    Computes a transparent, configurable multi-factor similarity evaluation
    between the user's project idea and an analyzed GitHub repository.
    """
    # 1. Technology Overlap Score (0 - 100)
    user_tech_raw = set(project.technologies or [])
    if analysis and analysis.user_technologies:
        user_tech_raw.update(analysis.user_technologies)
    if analysis and analysis.recommended_technologies:
        # Include primary recommended tech in evaluation
        if isinstance(analysis.recommended_technologies, dict):
            for tech_list in analysis.recommended_technologies.values():
                if isinstance(tech_list, list):
                    user_tech_raw.update(tech_list)

    user_tech = {t.lower().strip() for t in user_tech_raw if t}

    repo_tech_raw: Set[str] = set()
    repo_tech_raw.update(tech_stack.programming_languages)
    repo_tech_raw.update(tech_stack.frontend_frameworks)
    repo_tech_raw.update(tech_stack.backend_frameworks)
    repo_tech_raw.update(tech_stack.databases)
    repo_tech_raw.update(tech_stack.ai_ml_libraries)
    repo_tech_raw.update(tech_stack.cloud_deployment)
    repo_tech_raw.update(tech_stack.devops_tools)
    repo_tech = {t.lower().strip() for t in repo_tech_raw if t}

    shared_tech = user_tech.intersection(repo_tech)
    if user_tech and repo_tech:
        # Proportion of user technologies present in repository
        tech_score = (len(shared_tech) / max(len(user_tech), 1)) * 100.0
        # Blend with Jaccard
        jaccard_tech = calculate_jaccard(user_tech, repo_tech) * 100.0
        tech_score = min(100.0, 0.7 * tech_score + 0.3 * jaccard_tech)
    elif repo.language and any(repo.language.lower() in t for t in user_tech):
        tech_score = 40.0
    else:
        tech_score = 0.0

    # 2. Domain Similarity Score (0 - 100)
    domain_tokens = tokenize(project.domain)
    if analysis:
        domain_tokens.update(tokenize(analysis.primary_domain))
        if analysis.secondary_domains and isinstance(analysis.secondary_domains, list):
            for sec in analysis.secondary_domains:
                domain_tokens.update(tokenize(sec))

    repo_domain_tokens = set(tokenize(repo.description))
    if repo.topics and isinstance(repo.topics, list):
        for top in repo.topics:
            repo_domain_tokens.update(tokenize(top))
    if repo.language:
        repo_domain_tokens.add(repo.language.lower())

    shared_domain = domain_tokens.intersection(repo_domain_tokens)
    if domain_tokens and repo_domain_tokens:
        domain_overlap = (len(shared_domain) / max(len(domain_tokens), 1)) * 100.0
        domain_score = min(100.0, domain_overlap * 1.5)  # slight scaling for focused domain tokens
    else:
        domain_score = 20.0 if shared_tech else 5.0

    # 3. Problem Similarity Score (0 - 100)
    problem_text = project.description or ""
    if analysis and analysis.problem_statement:
        problem_text += " " + analysis.problem_statement
    if analysis and analysis.keywords:
        problem_text += " " + " ".join(analysis.keywords)

    repo_problem_text = (repo.description or "") + " " + (repo.name or "")
    if readme_text:
        # Use first 1500 chars of README
        repo_problem_text += " " + readme_text[:1500]

    prob_user_tokens = tokenize(problem_text)
    prob_repo_tokens = tokenize(repo_problem_text)
    shared_problem_tokens = prob_user_tokens.intersection(prob_repo_tokens)

    if prob_user_tokens and prob_repo_tokens:
        overlap_ratio = len(shared_problem_tokens) / max(len(prob_user_tokens), 1)
        problem_score = min(100.0, overlap_ratio * 250.0)  # text overlap normalization
    else:
        problem_score = 10.0

    # 4. Feature Similarity Score (0 - 100)
    user_objectives: List[str] = []
    if project.objectives:
        user_objectives.extend(re.split(r"[\n;\.]+", project.objectives))
    if analysis and analysis.objectives and isinstance(analysis.objectives, list):
        user_objectives.extend(analysis.objectives)
    user_objectives = [o.strip() for o in user_objectives if len(o.strip()) > 5]

    repo_feature_names = [f.feature_name.lower() for f in features]
    repo_feature_text = " ".join([f"{f.feature_name} {f.description}" for f in features])
    repo_feature_tokens = tokenize(repo_feature_text)

    matched_features = 0
    if user_objectives and (features or repo_feature_tokens):
        for obj in user_objectives:
            obj_tokens = tokenize(obj)
            if obj_tokens.intersection(repo_feature_tokens):
                matched_features += 1
        feature_score = min(100.0, (matched_features / max(len(user_objectives), 1)) * 100.0)
    elif features:
        # Repository has documented features; calculate token overlap with project description
        feature_score = min(75.0, calculate_jaccard(prob_user_tokens, repo_feature_tokens) * 180.0)
    else:
        feature_score = 15.0

    # 5. Overall Weighted Composite Score
    # Weights: Problem 30%, Feature 30%, Technology 25%, Domain 15%
    overall_score = (
        0.30 * problem_score
        + 0.30 * feature_score
        + 0.25 * tech_score
        + 0.15 * domain_score
    )
    overall_score = round(max(0.0, min(100.0, overall_score)), 1)
    problem_score = round(max(0.0, min(100.0, problem_score)), 1)
    feature_score = round(max(0.0, min(100.0, feature_score)), 1)
    tech_score = round(max(0.0, min(100.0, tech_score)), 1)
    domain_score = round(max(0.0, min(100.0, domain_score)), 1)

    # 6. Transparent Rationale Explanation
    shared_tech_str = ", ".join(sorted([t.title() for t in shared_tech])) if shared_tech else "None"
    shared_domain_str = ", ".join(sorted(list(shared_domain)[:4])) if shared_domain else "Minimal"

    explanation = (
        f"Overall alignment of {overall_score}% is derived from: "
        f"Problem scope ({problem_score}%), Feature capability ({feature_score}%), "
        f"Technology stack ({tech_score}%, shared: {shared_tech_str}), "
        f"and Domain taxonomy ({domain_score}%, terms: {shared_domain_str}). "
        f"Note: This is a comparative heuristic evaluation for project differentiation."
    )

    return SimilarityAnalysisResponse(
        overall_score=overall_score,
        problem_similarity_score=problem_score,
        feature_similarity_score=feature_score,
        technology_overlap_score=tech_score,
        domain_similarity_score=domain_score,
        explanation=explanation,
    )

