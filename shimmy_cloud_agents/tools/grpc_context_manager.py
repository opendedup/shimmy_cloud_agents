# shimmy_cloud_agents/tools/grpc_context_manager.py

import asyncio # Added asyncio for Futures
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

# This dictionary will be populated by server.py with the active gRPC streams.
_active_streams_map: Dict[str, Any] = {}

# Dictionary for pending power status requests: command_id -> asyncio.Future
_pending_power_requests: Dict[str, asyncio.Future] = {}

def set_active_streams(streams_map: Dict[str, Any]) -> None:
    """
    Sets the global dictionary of active robot_id to gRPC context mappings.
    This should be called by the server module once its stream map is initialized.
    """
    global _active_streams_map
    _active_streams_map = streams_map
    logger.info(f"grpc_context_manager: Active streams map has been set. Known robot_ids (keys): {list(_active_streams_map.keys()) if _active_streams_map else 'None'}")

def get_grpc_context_by_robot_id(robot_id: str) -> Optional[Any]:
    """
    Retrieves the gRPC context for a given robot_id.
    """
    if not _active_streams_map:
        logger.warning("grpc_context_manager: Attempted to get context, but active_streams_map is not set or empty.")
        return None
    
    context = _active_streams_map.get(robot_id)
    if not context:
        logger.error(f"grpc_context_manager: gRPC context not found for robot_id: {robot_id}. Available robot_ids: {list(_active_streams_map.keys())}")
    else:
        logger.debug(f"grpc_context_manager: Successfully retrieved gRPC context for robot_id: {robot_id}")
    return context

def get_all_active_robot_ids() -> list[str]:
    """Returns a list of all robot_ids with active gRPC contexts."""
    return list(_active_streams_map.keys())

# --- Functions for managing pending power requests ---

def add_pending_power_request(command_id: str, future: asyncio.Future) -> None:
    """Adds a future to the pending power requests dictionary."""
    _pending_power_requests[command_id] = future
    logger.debug(f"grpc_context_manager: Added pending power request for command_id: {command_id}")

def resolve_pending_power_request(command_id: str, result: Any) -> bool:
    """
    Resolves a pending power request future with the given result.
    Returns True if a future was found and resolved, False otherwise.
    """
    future = _pending_power_requests.pop(command_id, None)
    if future and not future.done():
        future.set_result(result)
        logger.debug(f"grpc_context_manager: Resolved pending power request for command_id: {command_id} with result: {result}")
        return True
    elif future and future.done():
        logger.warning(f"grpc_context_manager: Attempted to resolve already done future for command_id: {command_id}")
        return False # Or handle as an error, already resolved
    else:
        # This can happen if the command_ack is for a different, non-awaited command, which is normal.
        logger.debug(f"grpc_context_manager: No pending power request found for command_id to resolve: {command_id}")
        return False

def get_pending_power_request(command_id: str) -> Optional[asyncio.Future]:
    """Retrieves a pending power request future if it exists."""
    return _pending_power_requests.get(command_id) 