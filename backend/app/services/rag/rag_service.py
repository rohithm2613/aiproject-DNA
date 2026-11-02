import uuid
import logging
from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import func
from fastapi import HTTPException, status
from google.genai import types

from app.core.config import settings
from app.models.project import Project
from app.models.analysis import ProjectAnalysis
from app.models.validation_report import ProjectValidationReport
from app.schemas.validation import (
    EvidenceItem,
    ProjectValidationReportSchema,
    ValidationGenerateRequest,
    ValidationReportResponse,
    ValidationReportSummary,
    ValidationHistoryResponse,
    EvidenceManifestResponse,
)
from app.services.ai_service import AIService
from app.services.rag.evidence_retrieval_service import EvidenceRetrievalService
from app.services.rag.context_builder import build_rag_context
from app.services.rag.citation_service import CitationService
from app.services.rag.heuristic_synthesizer import synthesize_deterministic_report

logger = logging.getLogger("uvicorn.error")

RAG_SYSTEM_INSTRUCTION = """You are a senior AI research advisor, empirical systems evaluator, and research gap validator for AI ProjectDNA.
Your objective is to generate an evidence-backed Research Gap Validation Dossier evaluating the proposed project against retrieved academic papers and GitHub repositories.

CRITICAL CONSTRAINTS & GROUNDING RULES:
1. Every claim regarding existing capabilities or research gaps MUST cite one or more valid Evidence IDs from the prompt (e.g., EVID-PAP-01, EVID-REP-02, EVID-PAT-01).
2. DO NOT invent or hallucinate evidence IDs. Only cite IDs present in the provided evidence blocks.
3. Categorize candidate innovation gaps into:
   - 'supported_gap': confirmed limitation in research/code, not solved in sample repos.
   - 'partially_supported_gap': partial implementations exist, but key challenges remain.
   - 'not_supported_gap': already fully solved in existing repositories.
   - 'insufficient_evidence': insufficient retrieved sources to confirm or refute.
4. When a feature was not found in the sample, use precise wording such as 'not found in the analyzed sources' rather than claiming universal absence.
5. Remember: Absence of evidence is NOT evidence of absence.
6. DO NOT claim the project is globally novel or certified unique. This preliminary research report does not constitute a legal patentability opinion or formal freedom-to-operate search.
7. Return strictly valid structured JSON adhering to the ProjectValidationReportSchema."""

class RAGService:
    def __init__(self, db: Session):
        self.db = db

    def _verify_project_ownership(self, project_id: str, user_id: str) -> Project:
        project = self.db.query(Project).filter(Project.id == project_id).first()
        if not project:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
        if project.user_id != user_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You do not have access to this project")
        return project

    def generate_validation_report(
        self,
        project_id: str,
        user_id: str,
        request: ValidationGenerateRequest,
    ) -> ValidationReportResponse:
        """
        Orchestrates RAG evidence retrieval, Gemini LLM synthesis (with heuristic fallback),
        citation sanitization, version tracking, and report persistence.
        """
        project = self._verify_project_ownership(project_id, user_id)

        # If force_regenerate is False, return latest existing report if available
        if not request.force_regenerate:
            existing = (
                self.db.query(ProjectValidationReport)
                .filter(ProjectValidationReport.project_id == project_id)
                .order_by(ProjectValidationReport.version.desc())
                .first()
            )
            if existing:
                logger.info(f"Returning cached validation report v{existing.version} for project {project_id}")
                return self._to_response(existing)

        # 1. Retrieve latest analysis record
        analysis = (
            self.db.query(ProjectAnalysis)
            .filter(ProjectAnalysis.project_id == project_id)
            .order_by(ProjectAnalysis.created_at.desc())
            .first()
        )

        # 2. Gather Evidence Manifest
        retriever = EvidenceRetrievalService(self.db)
        evidence_items, retrieval_metadata = retriever.retrieve_evidence_manifest(
            project=project,
            max_papers=request.max_papers,
            max_repos=request.max_repos,
            max_gaps=request.max_gaps,
            include_embeddings=request.include_embeddings,
        )

        # 3. Attempt Gemini Structured RAG Synthesis
        report_schema: Optional[ProjectValidationReportSchema] = None
        model_name = settings.GEMINI_MODEL or "gemini-2.5-flash"
        api_key_configured = bool(settings.GEMINI_API_KEY and settings.GEMINI_API_KEY.strip() != "your_gemini_api_key_here")

        if api_key_configured:
            try:
                context_prompt = build_rag_context(
                    project=project,
                    analysis=analysis,
                    evidence_items=evidence_items,
                    max_chars=settings.RAG_CONTEXT_MAX_CHARS,
                )
                client = AIService.get_client()
                candidates = [model_name]
                for fallback in ["gemini-3-flash-preview", "gemini-2.5-flash", "gemini-flash-latest"]:
                    if fallback not in candidates:
                        candidates.append(fallback)

                for idx, m_name in enumerate(candidates):
                    try:
                        logger.info(f"Submitting RAG validation prompt for project '{project.title}' to Gemini model: {m_name}...")
                        response = client.models.generate_content(
                            model=m_name,
                            contents=context_prompt,
                            config=types.GenerateContentConfig(
                                response_mime_type="application/json",
                                response_schema=ProjectValidationReportSchema,
                                system_instruction=RAG_SYSTEM_INSTRUCTION,
                                temperature=0.2,
                            ),
                        )
                        if response and response.text:
                            report_schema = ProjectValidationReportSchema.model_validate_json(response.text)
                            model_name = m_name
                            logger.info(f"Successfully received structured RAG validation report from Gemini ({m_name}).")
                            break
                    except Exception as candidate_err:
                        err_str = str(candidate_err)
                        if ("404" in err_str or "NOT_FOUND" in err_str or "no longer available" in err_str.lower()) and idx < len(candidates) - 1:
                            logger.warning(f"RAG model '{m_name}' unavailable ({err_str[:100]}). Retrying with '{candidates[idx + 1]}'...")
                            continue
                        raise candidate_err
            except Exception as e:
                logger.warning(f"Gemini RAG generation failed: {e}. Falling back to deterministic heuristic synthesis.")
                report_schema = None

        # 4. Fallback if Gemini unavailable or failed
        if report_schema is None:
            model_name = "deterministic-rag-synthesizer"
            logger.info("Executing deterministic grounded report synthesis...")
            report_schema = synthesize_deterministic_report(
                project=project,
                analysis=analysis,
                evidence_items=evidence_items,
                retrieval_metadata=retrieval_metadata,
            )

        # 5. Validate and Sanitize Citations
        report_schema, citation_stats = CitationService.validate_and_sanitize_report(
            report=report_schema,
            evidence_manifest=evidence_items,
        )
        retrieval_metadata["citation_stats"] = citation_stats

        # 6. Calculate Version
        max_version = (
            self.db.query(func.max(ProjectValidationReport.version))
            .filter(ProjectValidationReport.project_id == project_id)
            .scalar()
        )
        next_version = (max_version or 0) + 1

        # 7. Persist Report Record
        report_id = str(uuid.uuid4())
        record = ProjectValidationReport(
            id=report_id,
            project_id=project.id,
            analysis_id=analysis.id if analysis else None,
            user_id=user_id,
            version=next_version,
            report_status="completed",
            report_json=report_schema.model_dump(),
            evidence_manifest=[item.model_dump() for item in evidence_items],
            model_name=model_name,
            retrieval_metadata=retrieval_metadata,
        )
        self.db.add(record)
        self.db.commit()
        self.db.refresh(record)

        logger.info(f"Persisted ProjectValidationReport {record.id} v{record.version} for project {project_id}")
        return self._to_response(record)

    def get_latest_report(self, project_id: str, user_id: str) -> ValidationReportResponse:
        self._verify_project_ownership(project_id, user_id)
        report = (
            self.db.query(ProjectValidationReport)
            .filter(ProjectValidationReport.project_id == project_id)
            .order_by(ProjectValidationReport.version.desc())
            .first()
        )
        if not report:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No validation report generated yet for this project",
            )
        return self._to_response(report)

    def get_report_history(self, project_id: str, user_id: str) -> ValidationHistoryResponse:
        self._verify_project_ownership(project_id, user_id)
        reports = (
            self.db.query(ProjectValidationReport)
            .filter(ProjectValidationReport.project_id == project_id)
            .order_by(ProjectValidationReport.version.desc())
            .all()
        )
        summaries: List[ValidationReportSummary] = []
        for r in reports:
            manifest_len = len(r.evidence_manifest) if isinstance(r.evidence_manifest, list) else 0
            rep_dict = r.report_json or {}
            val_gaps = rep_dict.get("validated_research_gaps", {}).get("validated_gaps", [])
            sup_cnt = sum(1 for g in val_gaps if g.get("validation_status") == "supported_gap")
            cov = rep_dict.get("final_assessment", {}).get("overall_evidence_coverage", "adequate")
            summaries.append(
                ValidationReportSummary(
                    id=r.id,
                    project_id=r.project_id,
                    analysis_id=r.analysis_id,
                    version=r.version,
                    report_status=r.report_status,
                    model_name=r.model_name,
                    total_evidence_items=manifest_len,
                    supported_gaps_count=sup_cnt,
                    overall_evidence_coverage=cov,
                    created_at=r.created_at,
                )
            )
        return ValidationHistoryResponse(
            project_id=project_id,
            total_reports=len(summaries),
            reports=summaries,
        )

    def get_report_by_id(self, project_id: str, report_id: str, user_id: str) -> ValidationReportResponse:
        self._verify_project_ownership(project_id, user_id)
        report = (
            self.db.query(ProjectValidationReport)
            .filter(
                ProjectValidationReport.id == report_id,
                ProjectValidationReport.project_id == project_id,
            )
            .first()
        )
        if not report:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Validation report not found")
        return self._to_response(report)

    def get_evidence_manifest(
        self,
        project_id: str,
        user_id: str,
        report_id: Optional[str] = None,
    ) -> EvidenceManifestResponse:
        self._verify_project_ownership(project_id, user_id)
        query = self.db.query(ProjectValidationReport).filter(ProjectValidationReport.project_id == project_id)
        if report_id:
            report = query.filter(ProjectValidationReport.id == report_id).first()
        else:
            report = query.order_by(ProjectValidationReport.version.desc()).first()

        if not report:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No validation report found to retrieve evidence manifest",
            )

        items_raw = report.evidence_manifest or []
        evidence_items = [EvidenceItem.model_validate(item) for item in items_raw]

        counts: dict = {}
        for it in evidence_items:
            counts[it.source_type] = counts.get(it.source_type, 0) + 1

        return EvidenceManifestResponse(
            project_id=project_id,
            report_id=report.id,
            version=report.version,
            total_evidence_items=len(evidence_items),
            evidence_items=evidence_items,
            counts_by_source=counts,
            retrieval_metadata=report.retrieval_metadata or {},
        )

    @staticmethod
    def _to_response(record: ProjectValidationReport) -> ValidationReportResponse:
        raw_manifest = record.evidence_manifest or []
        evidence_items = [EvidenceItem.model_validate(item) for item in raw_manifest]
        report_schema = ProjectValidationReportSchema.model_validate(record.report_json)

        return ValidationReportResponse(
            id=record.id,
            project_id=record.project_id,
            analysis_id=record.analysis_id,
            user_id=record.user_id,
            version=record.version,
            report_status=record.report_status,
            model_name=record.model_name,
            report=report_schema,
            evidence_manifest=evidence_items,
            retrieval_metadata=record.retrieval_metadata or {},
            created_at=record.created_at,
            updated_at=record.updated_at,
        )

