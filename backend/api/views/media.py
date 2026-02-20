"""Media routes - proxy for external video content.

Provides a proxy endpoint to fetch videos from MuscleWiki API
with proper authentication headers.
"""

import os
from urllib.parse import unquote

import httpx
from fastapi import APIRouter, HTTPException, status
from fastapi.responses import StreamingResponse

router = APIRouter(
    prefix="/media",
    tags=["Media"],
)


def _get_rapidapi_headers() -> dict[str, str]:
    """Get RapidAPI headers for MuscleWiki."""
    api_key = os.getenv("RAPIDAPI_KEY", "")
    return {
        "x-rapidapi-host": "musclewiki-api.p.rapidapi.com",
        "x-rapidapi-key": api_key,
    }


@router.get(
    "/video",
    summary="Proxy video from MuscleWiki",
    description="""
Proxies video content from MuscleWiki API with proper authentication.

The video URL should be passed as a query parameter. This endpoint
fetches the video with RapidAPI headers and streams it to the client.
    """,
    responses={
        200: {
            "description": "Video stream",
            "content": {"video/mp4": {}},
        },
        400: {"description": "Missing or invalid URL"},
        502: {"description": "Failed to fetch video from source"},
    },
)
async def proxy_video(url: str):
    """Proxy video content from MuscleWiki.

    Args:
        url: The original video URL from MuscleWiki API

    Returns:
        Streaming video response
    """
    if not url:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="URL parameter is required",
        )

    # Decode URL if encoded
    video_url = unquote(url)

    # Validate it's a MuscleWiki URL
    if "musclewiki" not in video_url.lower() and "media.musclewiki" not in video_url.lower():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only MuscleWiki video URLs are allowed",
        )

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.get(
                video_url,
                headers=_get_rapidapi_headers(),
                follow_redirects=True,
            )
            response.raise_for_status()

            # Get content type from response or default to mp4
            content_type = response.headers.get("content-type", "video/mp4")

            async def stream_content():
                yield response.content

            return StreamingResponse(
                stream_content(),
                media_type=content_type,
                headers={
                    "Accept-Ranges": "bytes",
                    "Cache-Control": "public, max-age=86400",
                },
            )

    except httpx.HTTPStatusError as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Failed to fetch video: {e.response.status_code}",
        )
    except httpx.RequestError as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Failed to connect to video source: {str(e)}",
        )
