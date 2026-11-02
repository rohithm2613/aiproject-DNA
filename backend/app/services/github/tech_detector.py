import re
import json
from typing import Dict, List, Optional, Set, Tuple, Any
from app.schemas.repository_analysis import TechnologyStackResponse

# 7 Standardized Technology Signatures with canonical naming
TECH_SIGNATURES: Dict[str, Dict[str, List[str]]] = {
    "programming_languages": {
        "Python": ["python", "py", "requirements.txt", "pyproject.toml", "setup.py"],
        "TypeScript": ["typescript", "ts", "tsconfig.json"],
        "JavaScript": ["javascript", "js", "package.json"],
        "C++": ["c++", "cpp", "cxx", "cmake", "cmakelists.txt"],
        "C": ["\\bc\\b", "c99", "c11"],
        "C#": ["c#", "csharp", ".net", "dotnet", ".csproj"],
        "Java": ["java", "pom.xml", "build.gradle"],
        "Go": ["golang", "\\bgo\\b", "go.mod", "go.sum"],
        "Rust": ["rust", "cargo.toml", "cargo.lock"],
        "Ruby": ["ruby", "gemfile", "gem"],
        "PHP": ["php", "composer.json"],
        "Swift": ["swift", "package.swift"],
        "Kotlin": ["kotlin", "build.gradle.kts"],
        "Shell": ["bash", "sh", "shell", "zsh"],
        "R": ["\\br\\b", "rscript", "cran"],
    },
    "frontend_frameworks": {
        "React": ["react", "reactjs", "react-dom"],
        "Next.js": ["next.js", "nextjs", "\\bnext\\b"],
        "Vue.js": ["vue", "vuejs", "vue3", "vuex", "pinia", "nuxt"],
        "Angular": ["angular", "@angular/core"],
        "Svelte": ["svelte", "sveltekit"],
        "Tailwind CSS": ["tailwindcss", "tailwind"],
        "Bootstrap": ["bootstrap"],
        "Electron": ["electron"],
        "Flutter": ["flutter", "dart"],
        "React Native": ["react-native"],
        "Vite": ["vite"],
    },
    "backend_frameworks": {
        "FastAPI": ["fastapi"],
        "Flask": ["flask"],
        "Django": ["django"],
        "Express": ["express", "expressjs"],
        "NestJS": ["nestjs", "@nestjs/core"],
        "Spring Boot": ["spring-boot", "org.springframework.boot"],
        "Gin": ["gin-gonic/gin", "github.com/gin-gonic/gin"],
        "Actix": ["actix-web", "actix"],
        "Ruby on Rails": ["rails"],
        "ASP.NET": ["aspnetcore", "microsoft.aspnetcore"],
        "Tornado": ["tornado"],
    },
    "databases": {
        "PostgreSQL": ["postgresql", "postgres", "psycopg2", "asyncpg"],
        "MySQL": ["mysql", "pymysql"],
        "SQLite": ["sqlite", "sqlite3"],
        "MongoDB": ["mongodb", "pymongo", "mongoose"],
        "Redis": ["redis", "aioredis"],
        "Cassandra": ["cassandra"],
        "Elasticsearch": ["elasticsearch"],
        "Neo4j": ["neo4j"],
        "Pinecone": ["pinecone", "pinecone-client"],
        "Chroma": ["chromadb", "chroma"],
        "Qdrant": ["qdrant-client", "qdrant"],
        "Supabase": ["@supabase/supabase-js", "supabase"],
    },
    "ai_ml_libraries": {
        "PyTorch": ["torch", "pytorch", "torchvision", "torchaudio"],
        "TensorFlow": ["tensorflow", "keras"],
        "Scikit-learn": ["scikit-learn", "sklearn"],
        "HuggingFace Transformers": ["transformers", "huggingface"],
        "OpenCV": ["opencv", "cv2", "opencv-python"],
        "LangChain": ["langchain", "langchain-core"],
        "LlamaIndex": ["llama-index", "llamaindex"],
        "Pandas": ["pandas"],
        "NumPy": ["numpy"],
        "ROS / ROS 2": ["ros2", "rclpy", "rclcpp", "\\bros\\b"],
        "Diffusers": ["diffusers"],
        "spaCy": ["spacy"],
        "Ray": ["ray[tune]", "ray"],
    },
    "cloud_deployment": {
        "Docker": ["docker", "dockerfile", "docker-compose"],
        "Kubernetes": ["kubernetes", "k8s", "kubectl", "helm"],
        "AWS": ["aws", "boto3", "aws-sdk"],
        "Google Cloud Platform": ["gcp", "google-cloud"],
        "Microsoft Azure": ["azure", "azure-storage"],
        "Terraform": ["terraform"],
        "Nginx": ["nginx"],
        "Vercel": ["vercel"],
        "Netlify": ["netlify"],
    },
    "devops_tools": {
        "GitHub Actions": ["github-actions", ".github/workflows", "actions/checkout"],
        "GitLab CI": [".gitlab-ci.yml"],
        "Jenkins": ["jenkinsfile", "jenkins"],
        "Prometheus": ["prometheus"],
        "Grafana": ["grafana"],
        "Pytest": ["pytest"],
        "Jest": ["jest"],
        "ESLint": ["eslint"],
        "Poetry": ["poetry.lock", "poetry"],
    },
}

def parse_requirements_txt(content: str) -> List[str]:
    """Extracts package names from requirements.txt."""
    packages = []
    for line in content.splitlines():
        line = line.strip()
        if not line or line.startswith("#") or line.startswith("-"):
            continue
        # Extract package name before ==, >=, <=, ~=, <, >, ;
        pkg = re.split(r"[><=~;\[\s]", line)[0].strip()
        if pkg:
            packages.append(pkg.lower())
    return packages

def parse_package_json(content: str) -> List[str]:
    """Extracts dependency names from package.json."""
    packages = []
    try:
        data = json.loads(content)
        deps = data.get("dependencies", {})
        dev_deps = data.get("devDependencies", {})
        packages.extend(list(deps.keys()))
        packages.extend(list(dev_deps.keys()))
    except Exception:
        pass
    return [p.lower() for p in packages]

def parse_pyproject_toml(content: str) -> List[str]:
    """Extracts dependencies from pyproject.toml."""
    packages = []
    for line in content.splitlines():
        line = line.strip()
        if "=" in line and not line.startswith("["):
            parts = line.split("=", 1)
            name = parts[0].strip().strip('"').strip("'")
            if name and not name.startswith("python"):
                packages.append(name.lower())
    return packages

def detect_technologies(
    repo_meta: Dict[str, Any],
    readme_text: Optional[str] = None,
    dependency_files: Optional[Dict[str, str]] = None,
) -> TechnologyStackResponse:
    """
    Scans repository metadata, dependency files, and README text
    to extract evidence-grounded technology stack categorizations.
    """
    dependency_files = dependency_files or {}
    evidence: Dict[str, List[str]] = {}
    categorized: Dict[str, Set[str]] = {cat: set() for cat in TECH_SIGNATURES}

    # 1. Primary language and language metadata from GitHub
    primary_lang = repo_meta.get("language")
    if primary_lang:
        for canonical, aliases in TECH_SIGNATURES["programming_languages"].items():
            if primary_lang.lower() == canonical.lower() or any(a == primary_lang.lower() for a in aliases):
                categorized["programming_languages"].add(canonical)
                evidence.setdefault(canonical, []).append(f"GitHub repository primary language: '{primary_lang}'")

    # 2. Languages JSON breakdown
    languages_dict = repo_meta.get("languages") or {}
    if isinstance(languages_dict, dict):
        for lang in languages_dict.keys():
            for canonical, aliases in TECH_SIGNATURES["programming_languages"].items():
                if lang.lower() == canonical.lower() or any(a == lang.lower() for a in aliases):
                    categorized["programming_languages"].add(canonical)
                    if f"GitHub languages: '{lang}'" not in evidence.get(canonical, []):
                        evidence.setdefault(canonical, []).append(f"GitHub language breakdown contains: '{lang}'")

    # 3. Topics / tags
    topics = repo_meta.get("topics") or []
    for topic in topics:
        topic_lower = topic.lower()
        for cat, mapping in TECH_SIGNATURES.items():
            for canonical, aliases in mapping.items():
                if any(alias in topic_lower for alias in aliases):
                    categorized[cat].add(canonical)
                    evidence.setdefault(canonical, []).append(f"Repository topic tag: '{topic}'")

    # 4. Dependency file inspection
    for filename, content in dependency_files.items():
        extracted_pkgs: List[str] = []
        if filename.endswith("requirements.txt"):
            extracted_pkgs = parse_requirements_txt(content)
        elif filename.endswith("package.json"):
            extracted_pkgs = parse_package_json(content)
        elif filename.endswith("pyproject.toml"):
            extracted_pkgs = parse_pyproject_toml(content)

        for pkg in extracted_pkgs:
            for cat, mapping in TECH_SIGNATURES.items():
                for canonical, aliases in mapping.items():
                    if any(alias == pkg or pkg in alias for alias in aliases):
                        categorized[cat].add(canonical)
                        evidence.setdefault(canonical, []).append(f"Declared in {filename}: '{pkg}'")

    # 5. README text scanning (only if README is present)
    if readme_text:
        readme_lower = readme_text.lower()
        for cat, mapping in TECH_SIGNATURES.items():
            for canonical, aliases in mapping.items():
                if canonical in categorized[cat]:
                    continue  # already verified by metadata or deps
                for alias in aliases:
                    pattern = rf"\b{re.escape(alias)}\b"
                    match = re.search(pattern, readme_lower)
                    if match:
                        categorized[cat].add(canonical)
                        # Extract excerpt around match
                        start = max(0, match.start() - 30)
                        end = min(len(readme_text), match.end() + 30)
                        excerpt = readme_text[start:end].replace("\n", " ").strip()
                        evidence.setdefault(canonical, []).append(f"Documented in README: '...{excerpt}...'")
                        break

    return TechnologyStackResponse(
        programming_languages=sorted(list(categorized["programming_languages"])),
        frontend_frameworks=sorted(list(categorized["frontend_frameworks"])),
        backend_frameworks=sorted(list(categorized["backend_frameworks"])),
        databases=sorted(list(categorized["databases"])),
        ai_ml_libraries=sorted(list(categorized["ai_ml_libraries"])),
        cloud_deployment=sorted(list(categorized["cloud_deployment"])),
        devops_tools=sorted(list(categorized["devops_tools"])),
        evidence={k: list(set(v)) for k, v in evidence.items()},
    )
