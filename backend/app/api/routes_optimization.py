"""API routes for description optimization rounds and diffs."""

from fastapi import APIRouter

router = APIRouter(prefix="/optimization", tags=["optimization"])

@router.get("/")
def get_optimization_placeholder():
    """Placeholder endpoint for optimization rounds."""
    return {
        "status": "placeholder",
        "message": "Optimization endpoints will be activated in future phases."
    }
