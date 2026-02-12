from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from loguru import logger
from app.services.agent_orchestrator_service import orchestrator_service
from app.models.schemas import AdvisoryRequest, AdvisoryResponse

router = APIRouter()


@router.post("/advisory/ask", response_model=AdvisoryResponse)
async def ask(request: AdvisoryRequest):
    try:
        query = request.query.strip()
        if not query:
            raise HTTPException(400, "Please enter a question / سوال لکھیں!")
        if len(query) > 2000:
            raise HTTPException(
                400, "Question too long. Keep under 2000 characters."
            )

        response = await orchestrator_service.process_query(
            query=query,
            crop_type=request.crop_type,
            location=request.location,
            language=request.language.value,
            context=request.context,
        )

        # Serialize properly — ensure sources are dicts not objects
        result = {
            "answer": response.answer or "No response generated.",
            "answer_urdu": response.answer_urdu or "",
            "confidence": response.confidence,
            "agents_used": response.agents_used or [],
            "follow_up_questions": response.follow_up_questions or [],
            "reasoning_chain": response.reasoning_chain or "",
            "sources": [],
        }

        # Convert SourceReference objects to clean dicts
        if response.sources:
            for src in response.sources:
                if hasattr(src, "source"):
                    result["sources"].append({
                        "source": str(src.source),
                        "relevance_score": float(
                            src.relevance_score
                            if src.relevance_score
                            else 0.8
                        ),
                        "excerpt": str(src.excerpt) if src.excerpt else None,
                    })
                elif isinstance(src, dict):
                    result["sources"].append({
                        "source": str(src.get("source", "FasalAI")),
                        "relevance_score": float(
                            src.get("relevance_score", 0.8)
                        ),
                        "excerpt": src.get("excerpt"),
                    })
                elif isinstance(src, str):
                    result["sources"].append({
                        "source": src,
                        "relevance_score": 0.8,
                        "excerpt": None,
                    })

        return JSONResponse(content=result)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Advisory error: {e}")
        raise HTTPException(500, "Server error. Please try again.")


@router.get("/advisory/quick/{crop}/{topic}")
async def quick(crop: str, topic: str):
    queries = {
        "fertilizer": (
            f"{crop} ke liye konsi khad kitni miqdar mein "
            f"dalni chahiye?"
        ),
        "irrigation": (
            f"{crop} ko kitna pani kab kab dena chahiye? "
            f"Schedule batayein."
        ),
        "pest": (
            f"{crop} par konse keede lagte hain aur unka "
            f"ilaj kya hai?"
        ),
        "disease": (
            f"{crop} ki aam bimariyan konsi hain aur unka "
            f"spray/ilaj batayein?"
        ),
        "harvest": (
            f"{crop} ki katai ka sahi waqt aur tareeqa "
            f"kya hai?"
        ),
        "sowing": (
            f"{crop} ki bijai ka sahi waqt aur tareeqa "
            f"batayein, best varieties?"
        ),
    }
    q = queries.get(
        topic,
        f"{crop} ke baare mein {topic} ki maloomat dijiye",
    )

    response = await orchestrator_service.process_query(
        query=q, crop_type=crop, language="ur"
    )

    # Same serialization
    result = {
        "answer": response.answer or "",
        "answer_urdu": response.answer_urdu or "",
        "confidence": response.confidence,
        "agents_used": response.agents_used or [],
        "follow_up_questions": response.follow_up_questions or [],
        "sources": [],
    }

    if response.sources:
        for src in response.sources:
            if hasattr(src, "source"):
                result["sources"].append({
                    "source": str(src.source),
                    "relevance_score": float(
                        getattr(src, "relevance_score", 0.8)
                    ),
                })
            elif isinstance(src, str):
                result["sources"].append({
                    "source": src,
                    "relevance_score": 0.8,
                })

    return JSONResponse(content=result)


@router.get("/advisory/stats")
async def rag_stats():
    """Returns RAG knowledge base statistics"""
    from app.services.rag_service import rag_service
    return rag_service.get_stats()