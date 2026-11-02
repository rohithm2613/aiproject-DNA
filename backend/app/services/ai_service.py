import json
import logging
import os
from typing import Optional, List, Dict, Any
from fastapi import HTTPException, status
from google import genai
from google.genai import types

from app.core.config import settings
from app.schemas.analysis import ProjectAnalysisSchema

logger = logging.getLogger("uvicorn.error")

SYSTEM_INSTRUCTION = """You are a senior AI research advisor, systems architect, and technical project validator for the AI ProjectDNA platform.
Your objective is to provide a rigorous, objective, and structured engineering analysis of the proposed project idea.

CRITICAL INSTRUCTIONS & CONSTRAINTS:
1. Distinguish established facts in the user's proposal from your own technical assumptions.
2. DO NOT claim or imply that the project idea is novel, revolutionary, or unique.
3. DO NOT claim that similar projects do not exist.
4. Clearly distinguish user-specified technologies from AI-recommended technologies.
5. DO NOT invent fake research citations, papers, or arXiv IDs.
6. For datasets, list candidate datasets that might be relevant, but explicitly label them as potential candidates without claiming guaranteed public availability.
7. Provide realistic, sober technical feasibility assessments.
8. Extract 10 to 20 meaningful, high-specificity technical and domain keywords.
9. Formulate 4 to 6 measurable, unambiguous project objectives.
10. Return strictly valid structured JSON matching the requested response schema."""


class AIService:
    @classmethod
    def get_api_key(cls) -> str:
        """Retrieves and validates the Google Gemini API key from settings."""
        if hasattr(settings, "GEMINI_API_KEY"):
            return (settings.GEMINI_API_KEY or "").strip()
        return os.environ.get("GEMINI_API_KEY", "").strip()

    @classmethod
    def is_configured(cls) -> bool:
        """Checks if a valid, non-placeholder Gemini API key is present."""
        api_key = cls.get_api_key()
        return bool(api_key and api_key != "your_gemini_api_key_here")

    @classmethod
    def get_diagnostics(cls) -> Dict[str, Any]:
        """
        Safe diagnostic check for Gemini API configuration.
        NEVER prints or exposes the actual secret key.
        """
        api_key = cls.get_api_key()
        is_placeholder = (api_key == "your_gemini_api_key_here")
        detected = bool(api_key)
        configured = bool(detected and not is_placeholder)
        
        client_initialized = False
        init_error: Optional[str] = None
        if configured:
            try:
                # Instantiate client to verify local configuration
                genai.Client(api_key=api_key)
                client_initialized = True
            except Exception as e:
                init_error = str(e).replace(api_key, "[REDACTED]")

        if configured and client_initialized:
            status_str = "ready"
        elif not detected:
            status_str = "missing_key"
        elif is_placeholder:
            status_str = "placeholder_key"
        else:
            status_str = "client_init_failed"

        return {
            "status": status_str,
            "detected": detected,
            "configured": configured,
            "client_initialized": client_initialized,
            "configured_model": settings.GEMINI_MODEL or "gemini-2.5-flash",
            "key_length": len(api_key) if detected else 0,
            "init_error": init_error,
        }

    @classmethod
    def get_client(cls) -> genai.Client:
        """Instantiate Google GenAI Client with validation of API key."""
        api_key = cls.get_api_key()
        if not api_key or api_key == "your_gemini_api_key_here":
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Google Gemini API key is not configured. Please set a valid GEMINI_API_KEY in the backend environment variables."
            )
        try:
            return genai.Client(api_key=api_key)
        except Exception as exc:
            sanitized_exc = str(exc).replace(api_key, "[REDACTED]")
            logger.error(f"Failed to initialize Gemini Client: {sanitized_exc}")
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Failed to initialize Gemini Client: {sanitized_exc}"
            )

    @classmethod
    def analyze_project_idea(
        cls,
        title: str,
        description: str,
        domain: str,
        user_technologies: List[str],
        objectives: Optional[str] = None
    ) -> ProjectAnalysisSchema:
        """
        Submits project details to Google Gemini API with structured JSON schema output enforcement.
        Validates model response against Pydantic ProjectAnalysisSchema.
        """
        client = cls.get_client()
        api_key = cls.get_api_key()

        user_prompt = f"""Please analyze the following project idea submitted to AI ProjectDNA:

PROJECT TITLE:
{title}

PRIMARY DOMAIN CATEGORY:
{domain}

PROJECT IDEA DESCRIPTION:
{description}

USER-SPECIFIED TECHNOLOGIES:
{', '.join(user_technologies) if user_technologies else 'None specified'}

USER-SPECIFIED OBJECTIVES:
{objectives if objectives else 'None specified'}

Generate a thorough, structured, and realistic analysis complying strictly with the defined schema."""

        primary_model = settings.GEMINI_MODEL or "gemini-2.5-flash"
        # Candidate models to try in priority order: configured model first, followed by compatible flash models
        candidates = [primary_model]
        for fallback in ["gemini-3-flash-preview", "gemini-2.5-flash", "gemini-flash-latest"]:
            if fallback not in candidates:
                candidates.append(fallback)

        last_exception: Optional[Exception] = None

        for idx, model_name in enumerate(candidates):
            logger.info(f"Submitting project '{title}' to Gemini model: {model_name}...")

            try:
                response = client.models.generate_content(
                    model=model_name,
                    contents=user_prompt,
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json",
                        response_schema=ProjectAnalysisSchema,
                        system_instruction=SYSTEM_INSTRUCTION,
                        temperature=0.2,
                    )
                )

                if not response.text:
                    raise HTTPException(
                        status_code=status.HTTP_502_BAD_GATEWAY,
                        detail="Gemini API returned an empty response."
                    )

                # Validate structured output via Pydantic
                try:
                    analysis_data = ProjectAnalysisSchema.model_validate_json(response.text)
                    cls.last_model_used = model_name
                    logger.info(f"Successfully received and validated structured analysis for '{title}' using {model_name}.")
                    return analysis_data
                except Exception as parse_err:
                    logger.error(f"JSON validation failed on model response: {parse_err}. Raw: {response.text[:300]}")
                    raise HTTPException(
                        status_code=status.HTTP_502_BAD_GATEWAY,
                        detail=f"Model output did not match expected structured schema: {str(parse_err)}"
                    )

            except HTTPException:
                raise
            except Exception as exc:
                err_msg = str(exc).replace(api_key, "[REDACTED]")
                last_exception = exc

                # If this model returns 404 (e.g. model deprecated or not available for this project/account),
                # and another candidate is available, attempt the next candidate
                if ("404" in err_msg or "NOT_FOUND" in err_msg or "no longer available" in err_msg.lower()) and idx < len(candidates) - 1:
                    logger.warning(
                        f"Gemini model '{model_name}' returned 404/unavailable: {err_msg[:120]}. "
                        f"Retrying with next compatible model '{candidates[idx + 1]}'..."
                    )
                    continue

                logger.error(f"Gemini API execution error with {model_name}: {err_msg}", exc_info=True)

                if "429" in err_msg or "RESOURCE_EXHAUSTED" in err_msg or "quota" in err_msg.lower():
                    raise HTTPException(
                        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                        detail="Gemini API quota exceeded or rate limited. Please verify your Google AI Studio quota or try again shortly."
                    )
                if "API_KEY_INVALID" in err_msg or "400" in err_msg or "unregistered" in err_msg.lower() or "PERMISSION_DENIED" in err_msg:
                    raise HTTPException(
                        status_code=status.HTTP_502_BAD_GATEWAY,
                        detail="Invalid, expired, or rejected Google Gemini API key. Please check your credentials in Google AI Studio."
                    )
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail=f"Error communicating with Google Gemini API: {err_msg}"
                )

        # If all candidates failed without raising a specific HTTPException
        final_err = str(last_exception).replace(api_key, "[REDACTED]") if last_exception else "Unknown error"
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"All attempted Gemini models failed: {final_err}"
        )
