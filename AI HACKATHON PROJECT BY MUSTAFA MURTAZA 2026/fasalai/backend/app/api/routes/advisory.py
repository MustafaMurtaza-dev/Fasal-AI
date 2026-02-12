"""
Advisory API Routes
"""
from fastapi import APIRouter, HTTPException
from loguru import logger
from app.services.agent_orchestrator_service import orchestrator_service
from app.models.schemas import AdvisoryRequest, AdvisoryResponse

router = APIRouter()


@router.post("/advisory/ask")
async def ask(request: AdvisoryRequest):
    try:
        query = request.query.strip()
        if not query:
            raise HTTPException(400, "Please enter a question / سوال لکھیں!")
        if len(query) > 2000:
            raise HTTPException(400, "Question too long. Keep under 2000 characters.")

        response = await orchestrator_service.process_query(
            query=query,
            crop_type=request.crop_type,
            location=request.location,
            language=request.language.value,
            context=request.context,
        )

        # ─── Serialize to clean dict ───
        # This ensures frontend gets exactly what it expects
        result = {
            "answer": response.answer or "No response generated.",
            "answer_urdu": response.answer_urdu or "",
            "confidence": float(response.confidence) if response.confidence else 0.8,
            "agents_used": list(response.agents_used) if response.agents_used else [],
            "follow_up_questions": list(response.follow_up_questions) if response.follow_up_questions else [],
            "reasoning_chain": response.reasoning_chain or "",
            "sources": [],
        }

        # Convert SourceReference objects to simple dicts
        if response.sources:
            for src in response.sources:
                try:
                    if hasattr(src, "source"):
                        # It's a SourceReference object
                        result["sources"].append({
                            "source": str(src.source) if src.source else "FasalAI",
                            "relevance_score": float(src.relevance_score) if src.relevance_score else 0.8,
                            "excerpt": str(src.excerpt) if src.excerpt else None,
                        })
                    elif isinstance(src, dict):
                        result["sources"].append({
                            "source": str(src.get("source", "FasalAI")),
                            "relevance_score": float(src.get("relevance_score", 0.8)),
                            "excerpt": src.get("excerpt"),
                        })
                    elif isinstance(src, str):
                        result["sources"].append({
                            "source": src,
                            "relevance_score": 0.8,
                            "excerpt": None,
                        })
                except Exception as e:
                    logger.debug(f"Source serialization skip: {e}")

        # Debug log
        logger.info(
            f"📤 Response: answer={len(result['answer'])}ch, "
            f"urdu={len(result['answer_urdu'])}ch, "
            f"sources={len(result['sources'])}, "
            f"follow_up={len(result['follow_up_questions'])}"
        )

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Advisory error: {e}", exc_info=True)
        # Return error as JSON, not 500
        return {
            "answer": f"**Server Error**\n\nSomething went wrong: {str(e)[:200]}\n\nPlease try again.",
            "answer_urdu": "سرور میں خرابی۔ دوبارہ کوشش کریں۔",
            "confidence": 0.0,
            "agents_used": ["Error"],
            "follow_up_questions": [],
            "sources": [],
            "reasoning_chain": f"Error: {str(e)[:200]}",
        }


@router.get("/advisory/quick/{crop}/{topic}")
async def quick(crop: str, topic: str):
    queries = {
        "fertilizer": f"{crop} ke liye konsi khad kitni miqdar mein dalni chahiye?",
        "irrigation": f"{crop} ko kitna pani kab kab dena chahiye? Schedule batayein.",
        "pest": f"{crop} par konse keede lagte hain aur unka ilaj kya hai?",
        "disease": f"{crop} ki aam bimariyan konsi hain aur unka spray/ilaj batayein?",
        "harvest": f"{crop} ki katai ka sahi waqt aur tareeqa kya hai?",
        "sowing": f"{crop} ki bijai ka sahi waqt aur tareeqa batayein, best varieties?",
    }
    q = queries.get(topic, f"{crop} ke baare mein {topic} ki maloomat dijiye")

    try:
        response = await orchestrator_service.process_query(
            query=q, crop_type=crop, language="ur"
        )

        result = {
            "answer": response.answer or "",
            "answer_urdu": response.answer_urdu or "",
            "confidence": float(response.confidence),
            "agents_used": list(response.agents_used) if response.agents_used else [],
            "follow_up_questions": list(response.follow_up_questions) if response.follow_up_questions else [],
            "sources": [],
        }

        if response.sources:
            for src in response.sources:
                if hasattr(src, "source"):
                    result["sources"].append({
                        "source": str(src.source),
                        "relevance_score": float(getattr(src, "relevance_score", 0.8)),
                    })
                elif isinstance(src, str):
                    result["sources"].append({"source": src, "relevance_score": 0.8})

        return result

    except Exception as e:
        logger.error(f"Quick advisory error: {e}")
        return {
            "answer": f"Error getting {topic} info for {crop}. Please try again.",
            "answer_urdu": "معلومات دستیاب نہیں۔ دوبارہ کوشش کریں۔",
            "confidence": 0.0,
            "sources": [],
            "agents_used": [],
            "follow_up_questions": [],
        }


@router.get("/advisory/stats")
async def rag_stats():
    from app.services.rag_service import rag_service
    return rag_service.get_stats()