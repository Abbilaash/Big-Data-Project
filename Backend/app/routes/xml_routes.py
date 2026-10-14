"""
xml_routes.py

PURPOSE:
    FastAPI router exposing three endpoints that return XML output.
    Each endpoint demonstrates the Neo4j + MongoDB integration:
    - Neo4j supplies relationship/graph data
    - MongoDB supplies content/profile data
    - Python merges them and returns XML

ENDPOINTS:
    GET /api/xml/feed/{user_id}           → personalized feed as XML
    GET /api/xml/suggestions/{user_id}    → friend suggestions as XML
    GET /api/xml/profile/{user_id}        → user profile as XML

USAGE (open in browser or Swagger at /docs):
    http://localhost:8000/api/xml/feed/USR_abc123
    http://localhost:8000/api/xml/suggestions/USR_abc123
    http://localhost:8000/api/xml/profile/USR_abc123
"""

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import Response

from app.services.xml_integration_service import (
    get_feed_as_xml,
    get_suggestions_as_xml,
    get_user_profile_as_xml,
)

router = APIRouter(prefix="/api/xml", tags=["XML Integration (Neo4j + MongoDB)"])


@router.get(
    "/feed/{user_id}",
    summary="Personalized feed — Neo4j (relationships) + MongoDB (event content)",
    response_class=Response,
    responses={
        200: {
            "content": {"application/xml": {}},
            "description": "XML feed ranked by friends' interactions",
        }
    },
)
async def xml_feed(
    user_id: str,
    limit: int = Query(default=10, ge=1, le=50, description="Max events to return"),
):
    """
    Returns a user's personalized event feed as XML.

    **How integration works:**
    1. Neo4j (Cypher): Find events liked/registered/shared/viewed by this user's connections
    2. MongoDB: Fetch full event documents + friend display names using those IDs
    3. Python: Score events by action weight (REGISTERED=4, SHARED=3, LIKED=2, VIEWED=1)
    4. Output: XML with `source_databases="Neo4j + MongoDB"` attribute
    """
    try:
        xml_content = await get_feed_as_xml(user_id, limit=limit)
        return Response(content=xml_content, media_type="application/xml")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/suggestions/{user_id}",
    summary="Friend suggestions — Neo4j (mutual connections) + MongoDB (profiles)",
    response_class=Response,
    responses={
        200: {
            "content": {"application/xml": {}},
            "description": "XML list of suggested users to follow",
        }
    },
)
async def xml_suggestions(
    user_id: str,
    limit: int = Query(default=10, ge=1, le=50, description="Max suggestions to return"),
):
    """
    Returns friend/connection suggestions as XML.

    **How integration works:**
    1. Neo4j (Cypher): Friends-of-friends ranked by mutual connection count
    2. MongoDB: Department-based fallback when graph is sparse; hydrate full profiles
    3. Output: Each `<Person>` tagged with `source="graph"` or `source="department_fallback"`
    """
    try:
        xml_content = await get_suggestions_as_xml(user_id, limit=limit)
        return Response(content=xml_content, media_type="application/xml")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/profile/{user_id}",
    summary="User profile — MongoDB (content) + Neo4j (graph stats)",
    response_class=Response,
    responses={
        200: {
            "content": {"application/xml": {}},
            "description": "XML user profile combining both databases",
        }
    },
)
async def xml_profile(
    user_id: str,
    viewer_id: str = Query(
        default=None,
        description="Optional: viewer's user_id to include is_following status",
    ),
):
    """
    Returns a user's full profile as XML combining both databases.

    **How integration works:**
    - `<BasicInfo source="MongoDB">` — name, department, year, role, picture
    - `<GraphStats source="Neo4j">` — follower count, following count, events registered/liked
    """
    try:
        xml_content = await get_user_profile_as_xml(user_id, viewer_id=viewer_id)
        return Response(content=xml_content, media_type="application/xml")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
