import re
import hashlib
from typing import Dict, Any, List, Optional
from app.models.project import Project
from app.models.analysis import ProjectAnalysis
from app.models.research_paper import ResearchPaper
from app.models.github_repo import GitHubRepository
from app.models.repository_analysis import RepositoryAnalysis

def compute_content_hash(text: str) -> str:
    """Computes a deterministic SHA-256 hexadecimal hash of cleaned text."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()

def clean_text(text: Optional[str]) -> str:
    """
    Cleans raw text by stripping markdown headers, excessive whitespace,
    and special characters while preserving technical identifiers.
    """
    if not text:
        return ""
    # Remove markdown link formatting [text](url) -> text
    cleaned = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', text)
    # Remove code blocks ```...```
    cleaned = re.sub(r'```[\s\S]*?```', '', cleaned)
    # Remove inline code ticks
    cleaned = re.sub(r'`([^`]+)`', r'\1', cleaned)
    # Remove markdown headers (#, ##, etc.)
    cleaned = re.sub(r'#+\s*', '', cleaned)
    # Replace multiple newlines or tabs with a single space
    cleaned = re.sub(r'\s+', ' ', cleaned)
    return cleaned.strip()

class TextPreprocessor:
    """
    Standardized text preparation for dense semantic embedding across
    project ideas, academic research papers, and GitHub repositories.
    """

    MAX_PROJECT_CHARS = 3500
    MAX_PAPER_CHARS = 3000
    MAX_REPO_CHARS = 3500
    MAX_PATENT_CHARS = 3500

    @classmethod
    def prepare_project_text(
        cls,
        project: Project,
        analysis: Optional[ProjectAnalysis] = None,
    ) -> Dict[str, Any]:
        """
        Synthesizes project representation from Project and ProjectAnalysis.
        Returns: {'text': str, 'content_hash': str, 'metadata': dict}
        """
        parts: List[str] = [f"Project: {project.title.strip()}"]

        if project.domain:
            parts.append(f"Domain: {project.domain.strip()}")

        if analysis:
            if analysis.project_summary:
                parts.append(f"Summary: {clean_text(analysis.project_summary)}")
            if analysis.problem_statement:
                parts.append(f"Problem: {clean_text(analysis.problem_statement)}")
            if analysis.proposed_solution:
                parts.append(f"Solution: {clean_text(analysis.proposed_solution)}")
            if analysis.primary_domain and analysis.primary_domain != project.domain:
                parts.append(f"Primary Domain: {analysis.primary_domain.strip()}")
            if analysis.secondary_domains:
                parts.append(f"Secondary Domains: {', '.join(analysis.secondary_domains)}")
            if analysis.keywords:
                parts.append(f"Keywords: {', '.join(analysis.keywords)}")
            if analysis.objectives:
                clean_objs = [clean_text(o) for o in analysis.objectives if clean_text(o)]
                if clean_objs:
                    parts.append(f"Objectives: {' | '.join(clean_objs)}")
        else:
            if project.description:
                parts.append(f"Description: {clean_text(project.description)}")
            if project.technologies:
                parts.append(f"Technologies: {', '.join(project.technologies)}")
            if project.objectives:
                parts.append(f"Objectives: {clean_text(project.objectives)}")

        full_text = "\n".join(parts)
        if len(full_text) > cls.MAX_PROJECT_CHARS:
            full_text = full_text[:cls.MAX_PROJECT_CHARS].rsplit(' ', 1)[0]

        content_hash = compute_content_hash(full_text)
        metadata = {
            "title": project.title,
            "domain": project.domain,
            "preview": (analysis.project_summary if analysis and analysis.project_summary else project.description)[:240],
            "analysis_version": analysis.version if analysis else None,
        }

        return {
            "text": full_text,
            "content_hash": content_hash,
            "metadata": metadata,
        }

    @classmethod
    def prepare_paper_text(cls, paper: ResearchPaper) -> Dict[str, Any]:
        """
        Synthesizes text representation for an academic research paper.
        """
        parts: List[str] = [f"Academic Paper: {paper.title.strip()}"]

        venue = getattr(paper, "venue", None)
        if venue:
            parts.append(f"Venue/Journal: {clean_text(venue)}")
        
        year = getattr(paper, "publication_year", None) or getattr(paper, "year", None)
        if year:
            parts.append(f"Year: {year}")

        fields = getattr(paper, "fields_of_study", None)
        if not fields and getattr(paper, "primary_category", None):
            fields = [paper.primary_category]
        if fields:
            parts.append(f"Fields: {', '.join(fields)}")

        if getattr(paper, "abstract", None):
            parts.append(f"Abstract: {clean_text(paper.abstract)}")

        full_text = "\n".join(parts)
        if len(full_text) > cls.MAX_PAPER_CHARS:
            full_text = full_text[:cls.MAX_PAPER_CHARS].rsplit(' ', 1)[0]

        content_hash = compute_content_hash(full_text)
        paper_url = getattr(paper, "paper_url", None) or getattr(paper, "primary_url", None)
        if not paper_url and getattr(paper, "doi", None):
            paper_url = f"https://doi.org/{paper.doi}"

        abstract_val = getattr(paper, "abstract", None)
        metadata = {
            "title": paper.title,
            "provider": getattr(paper, "provider", "unknown"),
            "url": paper_url,
            "venue": venue,
            "year": year,
            "open_access": getattr(paper, "open_access", None),
            "preview": (abstract_val[:240] + "...") if abstract_val else "No abstract provided.",
        }

        return {
            "text": full_text,
            "content_hash": content_hash,
            "metadata": metadata,
        }

    @classmethod
    def prepare_repo_text(
        cls,
        repo: GitHubRepository,
        analysis: Optional[RepositoryAnalysis] = None,
    ) -> Dict[str, Any]:
        """
        Synthesizes text representation for a GitHub repository using
        metadata and Phase 4.3 deep analysis if available.
        """
        parts: List[str] = [f"Repository: {repo.full_name}"]

        if repo.description:
            parts.append(f"Description: {clean_text(repo.description)}")
        if repo.language:
            parts.append(f"Primary Language: {repo.language}")
        if repo.topics:
            parts.append(f"Topics: {', '.join(repo.topics)}")

        if analysis:
            if analysis.summary and analysis.summary != repo.description:
                parts.append(f"Analysis Summary: {clean_text(analysis.summary)}")
            if analysis.problem_statement:
                parts.append(f"Problem Addressed: {clean_text(analysis.problem_statement)}")

            # Extract tech stack
            techs = analysis.detected_technologies or {}
            tech_items = []
            for cat, val in techs.items():
                if isinstance(val, list) and cat != "evidence_sources":
                    tech_items.extend(val)
            if tech_items:
                parts.append(f"Detected Stack: {', '.join(sorted(set(tech_items))[:15])}")

            # Extract features
            feats = analysis.features or []
            feat_summaries = []
            for f in feats[:6]:
                fname = f.get("feature_name") if isinstance(f, dict) else getattr(f, "feature_name", None)
                fdesc = f.get("description") if isinstance(f, dict) else getattr(f, "description", None)
                if fname:
                    feat_summaries.append(f"{fname}: {clean_text(fdesc or '')}")
            if feat_summaries:
                parts.append(f"Key Features: {' | '.join(feat_summaries)}")

        full_text = "\n".join(parts)
        if len(full_text) > cls.MAX_REPO_CHARS:
            full_text = full_text[:cls.MAX_REPO_CHARS].rsplit(' ', 1)[0]

        content_hash = compute_content_hash(full_text)
        stars = getattr(repo, "stargazers_count", None)
        if stars is None:
            stars = getattr(repo, "stars_count", 0)

        metadata = {
            "title": repo.full_name,
            "url": getattr(repo, "html_url", None),
            "language": getattr(repo, "language", None),
            "stargazers_count": stars,
            "preview": (repo.description[:240] + "...") if getattr(repo, "description", None) else (analysis.summary[:240] if analysis and analysis.summary else "No description provided."),
            "has_deep_analysis": analysis is not None,
        }

        return {
            "text": full_text,
            "content_hash": content_hash,
            "metadata": metadata,
        }

    @classmethod
    def prepare_patent_text(cls, patent: Any) -> Dict[str, Any]:
        """
        Synthesizes text representation for a patent publication.
        """
        pub_num = getattr(patent, "publication_number", "Unknown")
        title = getattr(patent, "title", "Untitled Patent")
        parts: List[str] = [f"Patent Publication: {pub_num} - {title.strip()}"]

        jurisdiction = getattr(patent, "jurisdiction", None)
        if jurisdiction:
            parts.append(f"Jurisdiction: {jurisdiction}")

        assignees = getattr(patent, "assignees", None) or []
        if assignees:
            parts.append(f"Assignees/Applicants: {', '.join(assignees[:5])}")

        cpc = getattr(patent, "cpc_classifications", None) or []
        if cpc:
            parts.append(f"CPC Classifications: {', '.join(cpc[:6])}")

        abstract_val = getattr(patent, "abstract", None)
        if abstract_val:
            parts.append(f"Abstract: {clean_text(abstract_val)}")

        claims = getattr(patent, "claims", None) or []
        if claims:
            clean_claims = [clean_text(c) for c in claims[:3] if clean_text(c)]
            if clean_claims:
                parts.append(f"Key Claims: {' | '.join(clean_claims)}")

        full_text = "\n".join(parts)
        if len(full_text) > cls.MAX_PATENT_CHARS:
            full_text = full_text[:cls.MAX_PATENT_CHARS].rsplit(' ', 1)[0]

        content_hash = compute_content_hash(full_text)
        metadata = {
            "title": title,
            "publication_number": pub_num,
            "jurisdiction": jurisdiction,
            "assignees": assignees[:3],
            "url": getattr(patent, "source_url", None),
            "preview": (abstract_val[:240] + "...") if abstract_val else f"Patent {pub_num}",
        }

        return {
            "text": full_text,
            "content_hash": content_hash,
            "metadata": metadata,
        }


def prepare_project_text(project: Project, analysis: Optional[ProjectAnalysis] = None) -> str:
    """Convenience helper returning prepared project text representation."""
    return TextPreprocessor.prepare_project_text(project, analysis)["text"]


def prepare_research_paper_text(paper: ResearchPaper) -> str:
    """Convenience helper returning prepared research paper text representation."""
    return TextPreprocessor.prepare_paper_text(paper)["text"]


def prepare_github_repo_text(repo: GitHubRepository, analysis: Optional[RepositoryAnalysis] = None) -> str:
    """Convenience helper returning prepared GitHub repository text representation."""
    return TextPreprocessor.prepare_repo_text(repo, analysis)["text"]


def prepare_patent_text(patent: Any) -> str:
    """Convenience helper returning prepared patent text representation."""
    return TextPreprocessor.prepare_patent_text(patent)["text"]

