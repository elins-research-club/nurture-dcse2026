from collections import deque
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional
from dateutil.parser import isoparse
import asyncio
import logging

logger = logging.getLogger(__name__)

# Master Ring Buffer: holds up to 8000 raw telemetry points in RAM per node
_master_buffers: Dict[str, deque] = {}
_seeded_nodes: set = set()

# Async Mutex Lock to serialize Cold Path requests to ThingSpeak to guarantee no HTTP 429
thingspeak_cold_lock = asyncio.Lock()

def get_node_buffer(node_id: str) -> deque:
    if node_id not in _master_buffers:
        _master_buffers[node_id] = deque(maxlen=8000)
    return _master_buffers[node_id]

def append_node_telemetry(node_id: str, entry: Dict[str, Any]):
    """Appends a new live telemetry point to the ring buffer (FIFO: auto-evicts oldest if >8000)."""
    buf = get_node_buffer(node_id)
    if buf and buf[-1].get("created_at") == entry.get("created_at"):
        buf[-1].update(entry)
    else:
        buf.append(dict(entry))

def set_initial_history(node_id: str, feeds: List[Dict[str, Any]]):
    """Initializes the ring buffer with historical feeds fetched from ThingSpeak."""
    buf = get_node_buffer(node_id)
    existing_items = list(buf)
    buf.clear()
    for f in feeds:
        buf.append(dict(f))
    # Re-append any newer live items that were received while fetching history
    if existing_items:
        last_feed_ts = feeds[-1].get("created_at") if feeds else None
        for item in existing_items:
            if not last_feed_ts or item.get("created_at", "") > last_feed_ts:
                buf.append(item)
    _seeded_nodes.add(node_id)
    logger.info(f"[TelemetryBuffer] Initialized & seeded ring buffer for {node_id} with {len(buf)} points.")

def get_hot_path_history(node_id: str, duration_hours: float = 24.0) -> Optional[List[Dict[str, Any]]]:
    """
    Returns data points from the in-memory ring buffer within the last duration_hours.
    Returns None if the buffer has not yet been seeded with historical data (triggering initial fetch).
    """
    if node_id not in _seeded_nodes:
        return None
        
    buf = get_node_buffer(node_id)
    if not buf:
        return None
    
    now_utc = datetime.now(timezone.utc)
    cutoff_time = now_utc - timedelta(hours=duration_hours)
    
    result = []
    for item in buf:
        ts_str = item.get("created_at")
        if ts_str:
            try:
                dt = isoparse(ts_str)
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
                if dt >= cutoff_time:
                    result.append(item)
            except Exception:
                result.append(item)
        else:
            result.append(item)
            
    return result if result else list(buf)
