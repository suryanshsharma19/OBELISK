from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
import json
import asyncio
from typing import AsyncGenerator

from app.db.neo4j_client import neo4j_client
from app.db.redis_client import RedisClient
from app.core.logging import setup_logger

logger = setup_logger(__name__)
router = APIRouter()

async def stream_blast_radius(pkg_name: str) -> AsyncGenerator[str, None]:
    redis = RedisClient()
    redis.connect()
    
    cache_key = f"blast_radius:{pkg_name}"
    cached_data = None
    if redis.client:
        cached_data = redis.client.get(cache_key)

    if cached_data:
        data = json.loads(cached_data)
        for layer in data:
            yield f"data: {json.dumps({'event': 'layer', 'data': layer})}\n\n"
            await asyncio.sleep(0.8)
        yield f"data: {json.dumps({'event': 'done', 'data': []})}\n\n"
        return

    try:
        results = neo4j_client.get_blast_radius(pkg_name)
    except Exception as e:
        logger.error("Error querying Neo4j for blast radius: %s", str(e))
        yield f"data: {json.dumps({'event': 'error', 'data': str(e)})}\n\n"
        return

    layers = {}
    for row in results:
        depth = row.get("depth", 1)
        if depth not in layers:
            layers[depth] = []
        layers[depth].append({
            "name": row.get("name"),
            "path": row.get("path_nodes", []),
            "risk_score": row.get("risk_score")
        })

    sorted_layers = [layers[k] for k in sorted(layers.keys())]
    if redis.client:
        redis.client.setex(cache_key, 3600, json.dumps(sorted_layers))
    
    for layer_data in sorted_layers:
        yield f"data: {json.dumps({'event': 'layer', 'data': layer_data})}\n\n"
        await asyncio.sleep(0.8)

    yield f"data: {json.dumps({'event': 'done', 'data': []})}\n\n"

@router.get("/blast-radius/{pkg_name}")
async def blast_radius_sse(pkg_name: str):
    return StreamingResponse(
        stream_blast_radius(pkg_name),
        media_type="text/event-stream"
    )


