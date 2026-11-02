import re
import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger("uvicorn.error")

# Domain to CPC classification code mappings for intelligent patent classification search
DOMAIN_CPC_MAP: Dict[str, List[str]] = {
    "artificial intelligence": ["G06N", "G06F"],
    "machine learning": ["G06N", "G06F"],
    "deep learning": ["G06N"],
    "computer vision": ["G06T", "G06V"],
    "natural language processing": ["G06F40", "G10L"],
    "speech recognition": ["G10L"],
    "healthcare": ["G16H", "A61B"],
    "biomedical": ["G16H", "A61B"],
    "cybersecurity": ["H04L9", "G06F21"],
    "security": ["H04L9", "G06F21"],
    "blockchain": ["H04L9", "G06Q20"],
    "fintech": ["G06Q20", "G06Q40"],
    "finance": ["G06Q40", "G06Q20"],
    "robotics": ["B25J", "G05D"],
    "autonomous systems": ["G05D", "B60W"],
    "iot": ["H04W", "H04L", "G16Y"],
    "internet of things": ["H04W", "H04L", "G16Y"],
    "cloud computing": ["G06F9", "H04L67"],
    "data science": ["G06F16", "G06N"],
    "big data": ["G06F16", "G06F17"],
    "telecommunications": ["H04W", "H04B", "H04L"],
    "networking": ["H04L", "H04W"],
}

STOP_WORDS = {
    "a", "about", "above", "after", "again", "against", "all", "am", "an", "and",
    "any", "are", "aren't", "as", "at", "be", "because", "been", "before", "being",
    "below", "between", "both", "but", "by", "can't", "cannot", "could", "couldn't",
    "did", "didn't", "do", "does", "doesn't", "doing", "don't", "down", "during",
    "each", "few", "for", "from", "further", "had", "hadn't", "has", "hasn't",
    "have", "haven't", "having", "he", "he'd", "he'll", "he's", "her", "here",
    "here's", "hers", "herself", "him", "himself", "his", "how", "how's", "i",
    "i'd", "i'll", "i'm", "i've", "if", "in", "into", "is", "isn't", "it", "it's",
    "its", "itself", "let's", "me", "more", "most", "mustn't", "my", "myself",
    "no", "nor", "not", "of", "off", "on", "once", "only", "or", "other", "ought",
    "our", "ours", "ourselves", "out", "over", "own", "same", "shan't", "she",
    "she'd", "she'll", "she's", "should", "shouldn't", "so", "some", "such",
    "than", "that", "that's", "the", "their", "theirs", "them", "themselves",
    "then", "there", "there's", "these", "they", "they'd", "they'll", "they're",
    "they've", "this", "those", "through", "to", "too", "under", "until", "up",
    "very", "was", "wasn't", "we", "we'd", "we'll", "we're", "we've", "were",
    "weren't", "what", "what's", "when", "when's", "where", "where's", "which",
    "while", "who", "who's", "whom", "why", "why's", "with", "won't", "would",
    "wouldn't", "you", "you'd", "you'll", "you're", "you've", "your", "yours",
    "yourself", "yourselves", "system", "platform", "tool", "using", "based",
    "project", "application", "method", "apparatus", "novel", "new", "improved"
}

def clean_term(term: str) -> str:
    """Cleans a single search keyword term."""
    return re.sub(r"[^\w\s-]", "", term).strip().lower()

class PatentQueryGenerator:
    """
    Generates targeted keyword queries and classification filters for patent discovery
    from the user's project idea and Phase 3 structured analysis.
    """

    @classmethod
    def infer_cpc_classifications(cls, primary_domain: str, secondary_domains: List[str], keywords: List[str]) -> List[str]:
        """Infers relevant CPC patent classification subclasses based on domain and keywords."""
        detected_cpc: List[str] = []
        text_corpus = f"{primary_domain} {' '.join(secondary_domains)} {' '.join(keywords)}".lower()

        for domain_key, cpc_list in DOMAIN_CPC_MAP.items():
            if domain_key in text_corpus:
                for cpc in cpc_list:
                    if cpc not in detected_cpc:
                        detected_cpc.append(cpc)

        # Default fallback to digital processing / software if none identified
        if not detected_cpc:
            detected_cpc = ["G06F", "G06N"]

        return detected_cpc[:4]

    @classmethod
    def generate_queries(
        cls,
        analysis_data: Dict[str, Any],
        query_override: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Builds patent search queries and classifications from structured analysis.
        Returns:
            {
                "primary_keywords": List[str],
                "cpc_codes": List[str],
                "search_queries": List[str],
            }
        """
        if query_override and query_override.strip():
            raw_override = query_override.strip()
            terms = [clean_term(w) for w in raw_override.split() if len(w) > 2 and clean_term(w) not in STOP_WORDS]
            return {
                "primary_keywords": terms[:6],
                "cpc_codes": ["G06F", "G06N"],
                "search_queries": [raw_override]
            }

        keywords: List[str] = analysis_data.get("keywords") or []
        primary_domain = str(analysis_data.get("primary_domain") or "").strip().lower()
        secondary_domains: List[str] = [str(d).lower() for d in (analysis_data.get("secondary_domains") or [])]
        user_technologies: List[str] = [str(t).lower() for t in (analysis_data.get("user_technologies") or [])]
        project_title = str(analysis_data.get("project_title") or "").strip()

        # Clean keywords
        valid_keywords: List[str] = []
        for kw in keywords:
            cleaned = clean_term(kw)
            if cleaned and cleaned not in STOP_WORDS and len(cleaned) > 2:
                valid_keywords.append(cleaned)

        # Clean technologies
        valid_tech: List[str] = []
        for tech in user_technologies:
            cleaned = clean_term(tech)
            if cleaned and cleaned not in STOP_WORDS and len(cleaned) > 2:
                valid_tech.append(cleaned)

        # CPC classifications
        cpc_codes = cls.infer_cpc_classifications(primary_domain, secondary_domains, valid_keywords)

        # Formulate combinations
        queries: List[str] = []

        # 1. Primary domain + top keywords
        if valid_keywords:
            top_kws = " ".join(valid_keywords[:3])
            queries.append(f"{top_kws}")

        # 2. Project domain + top 2 keywords
        if primary_domain and valid_keywords:
            queries.append(f"{primary_domain} {valid_keywords[0]}")

        # 3. Technologies + top keyword
        if valid_tech and valid_keywords:
            queries.append(f"{valid_tech[0]} {valid_keywords[0]}")

        # 4. Fallback if empty
        if not queries and project_title:
            title_words = [clean_term(w) for w in project_title.split() if clean_term(w) not in STOP_WORDS]
            queries.append(" ".join(title_words[:4]))

        if not queries:
            queries = ["artificial intelligence machine learning"]

        return {
            "primary_keywords": valid_keywords[:8],
            "cpc_codes": cpc_codes,
            "search_queries": queries[:3]
        }

