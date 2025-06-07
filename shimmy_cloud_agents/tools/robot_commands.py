# shimmy_cloud_agents/tools/robot_commands.py

import logging
from typing import Optional, Dict, Any
import uuid
import asyncio

from google.adk.tools import ToolContext

# Import the new gRPC context manager
from shimmy_cloud_agents.tools import grpc_context_manager

# Import the generated protobuf message types
try:
    from shimmy_cloud_agents.shared_grpc import shimmy_interface_pb2
except ImportError:
    print("Error: Could not import generated shimmy_interface_pb2. Run protoc first.")
    shimmy_interface_pb2 = None # Avoid crashing the rest of the file

logger = logging.getLogger(__name__)

# --- Helper to get gRPC Context ---
def _get_grpc_context(tool_context: ToolContext) -> Optional[Any]:
    """Retrieves the gRPC context using the robot_id from the tool_context's invocation_context."""
    if not tool_context:
        logger.error("ToolContext is missing. Cannot determine robot_id.")
        return None
    
    invocation_ctx = getattr(tool_context, "_invocation_context", None)
    if not invocation_ctx:
        logger.error("ToolContext._invocation_context is missing. Cannot determine robot_id.")
        return None
        
    robot_id = getattr(invocation_ctx, "user_id", None)
    if not robot_id:
        logger.error("ToolContext._invocation_context.user_id is missing. Cannot determine robot_id.")
        return None
    
    logger.info(f"Attempting to get gRPC context for robot_id: {robot_id} (from tool_context._invocation_context.user_id)")
    
    grpc_ctx = grpc_context_manager.get_grpc_context_by_robot_id(robot_id)
    if not grpc_ctx:
        logger.error(
            f"gRPC context not found for robot_id '{robot_id}' via grpc_context_manager."
        )
    else:
        logger.info(f"gRPC context found for robot_id: {robot_id}")
    return grpc_ctx

# --- Tool Implementations (Placeholders) ---

async def move_shimmy_tool(
    target_linear_distance_meters: Optional[float] = None,
    target_angular_degrees: Optional[float] = None,
    tool_context: ToolContext = None,
) -> str:
    """
    Moves the robot forward/backward and/or turns it in place.
    Specify distance in meters (positive forward, negative backward) and/or
    angle in degrees (positive counter-clockwise, negative clockwise).
    """
    logger.info(
        f"move_shimmy_tool called with distance: {target_linear_distance_meters}, angle: {target_angular_degrees}"
    )
    invocation_ctx = getattr(tool_context, "_invocation_context", None)
    if not invocation_ctx:
        logger.error("move_shimmy_tool: ToolContext._invocation_context is missing.")
        return "Error: Invocation context missing, cannot execute move command."

    robot_id_for_context = getattr(invocation_ctx, "user_id", None)
    current_session_id = getattr(invocation_ctx.session, "id", None)

    if not robot_id_for_context or not current_session_id:
        logger.error("move_shimmy_tool: Robot ID or Session ID missing from invocation context.")
        return "Error: Robot/Session ID missing, cannot execute move command."

    grpc_context = _get_grpc_context(tool_context)
    if not grpc_context or shimmy_interface_pb2 is None:
        return "Error: Cannot send command (gRPC context or protobuf missing)."

    command_id = f"cmd_move_{uuid.uuid4().hex[:8]}"
    command_payload = shimmy_interface_pb2.MoveCommand(
        target_linear_distance_meters=target_linear_distance_meters,
        target_angular_degrees=target_angular_degrees,
    )
    robot_command_message = shimmy_interface_pb2.RobotCommand(
        command_id=command_id,
        move_command=command_payload
    )
    cloud_message = shimmy_interface_pb2.CloudToRobotMessage(
        session_id=current_session_id,
        robot_command=robot_command_message
    )

    logger.info(f"Prepared MoveCommand: {robot_command_message} for session {current_session_id} (Robot: {robot_id_for_context})")
    try:
        await grpc_context.write(cloud_message)
        logger.info(f"MoveCommand sent successfully to robot {robot_id_for_context} (CmdID: {command_id}).")
        return f"Move command (ID: {command_id}) sent."
    except Exception as e:
        logger.error(f"Failed to send MoveCommand to robot {robot_id_for_context} (CmdID: {command_id}): {e}")
        return f"Error sending move command (ID: {command_id}): {e}"

async def turn_shimmy_tool(
    target_angular_degrees: float, tool_context: ToolContext = None
) -> str:
    """Turns the robot in place by the specified angle in degrees."""
    logger.info(f"turn_shimmy_tool called with angle: {target_angular_degrees}. Will call move_shimmy_tool.")
    
    return await move_shimmy_tool(
        target_linear_distance_meters=None,
        target_angular_degrees=target_angular_degrees,
        tool_context=tool_context,
    )

async def set_led_tool(
    color_hex: Optional[str] = None,
    brightness: Optional[float] = None,
    pattern: Optional[str] = None,
    turn_off: Optional[bool] = False,
    tool_context: ToolContext = None,
) -> str:
    """Controls the robot's LEDs."""
    logger.info(
        f"set_led_tool called with color: {color_hex}, brightness: {brightness}, pattern: {pattern}, turn_off: {turn_off}"
    )
    invocation_ctx = getattr(tool_context, "_invocation_context", None)
    if not invocation_ctx:
        logger.error("set_led_tool: ToolContext._invocation_context is missing.")
        return "Error: Invocation context missing, cannot execute LED command."

    robot_id_for_context = getattr(invocation_ctx, "user_id", None)
    current_session_id = getattr(invocation_ctx.session, "id", None)

    if not robot_id_for_context or not current_session_id:
        logger.error("set_led_tool: Robot ID or Session ID missing from invocation context.")
        return "Error: Robot/Session ID missing, cannot execute LED command."

    grpc_context = _get_grpc_context(tool_context)
    if not grpc_context or shimmy_interface_pb2 is None:
        return "Error: Cannot send command (gRPC context or protobuf missing)."

    command_id = f"cmd_led_{uuid.uuid4().hex[:8]}"
    command_payload = shimmy_interface_pb2.LEDCommand(
        color_hex=color_hex,
        brightness=brightness,
        pattern=pattern,
        turn_off=turn_off,
    )
    robot_command_message = shimmy_interface_pb2.RobotCommand(
        command_id=command_id,
        led_command=command_payload
    )
    cloud_message = shimmy_interface_pb2.CloudToRobotMessage(
        session_id=current_session_id,
        robot_command=robot_command_message
    )

    logger.info(f"Prepared LEDCommand: {robot_command_message} for session {current_session_id} (Robot: {robot_id_for_context})")
    try:
        await grpc_context.write(cloud_message)
        logger.info(f"LEDCommand sent successfully to robot {robot_id_for_context} (CmdID: {command_id}).")
        return f"LED command (ID: {command_id}) sent."
    except Exception as e:
        logger.error(f"Failed to send LEDCommand to robot {robot_id_for_context} (CmdID: {command_id}): {e}")
        return f"Error sending LED command (ID: {command_id}): {e}"


async def capture_image_tool(
    capture_type: str = "RGB_IMAGE", tool_context: ToolContext = None
) -> str:
    """
    Requests the robot to capture an image (RGB or DEPTH).
    The robot will send the image data back via the status update stream.
    """
    logger.info(f"capture_image_tool called with type: {capture_type}")
    invocation_ctx = getattr(tool_context, "_invocation_context", None)
    if not invocation_ctx:
        logger.error("capture_image_tool: ToolContext._invocation_context is missing.")
        return "Error: Invocation context missing, cannot execute camera command."

    robot_id_for_context = getattr(invocation_ctx, "user_id", None)
    current_session_id = getattr(invocation_ctx.session, "id", None)

    if not robot_id_for_context or not current_session_id:
        logger.error("capture_image_tool: Robot ID or Session ID missing from invocation context.")
        return "Error: Robot/Session ID missing, cannot execute camera command."

    grpc_context = _get_grpc_context(tool_context)
    if not grpc_context or shimmy_interface_pb2 is None:
        return "Error: Cannot send command (gRPC context or protobuf missing)."

    try:
        capture_enum = shimmy_interface_pb2.CameraCommand.CaptureType.Value(capture_type.upper())
    except ValueError:
        logger.error(f"Invalid capture_type: {capture_type}. Use RGB_IMAGE or DEPTH_IMAGE.")
        return "Error: Invalid capture type specified."

    command_id = f"cmd_camera_{uuid.uuid4().hex[:8]}"
    command_payload = shimmy_interface_pb2.CameraCommand(capture_type=capture_enum)
    robot_command_message = shimmy_interface_pb2.RobotCommand(
        command_id=command_id,
        camera_command=command_payload
    )
    cloud_message = shimmy_interface_pb2.CloudToRobotMessage(
        session_id=current_session_id,
        robot_command=robot_command_message
    )

    logger.info(f"Prepared CameraCommand: {robot_command_message} for session {current_session_id} (Robot: {robot_id_for_context})")
    try:
        await grpc_context.write(cloud_message)
        logger.info(f"CameraCommand sent successfully to robot {robot_id_for_context} (CmdID: {command_id}).")
        return f"Camera capture command (ID: {command_id}) sent. Waiting for image data..."
    except Exception as e:
        logger.error(f"Failed to send CameraCommand to robot {robot_id_for_context} (CmdID: {command_id}): {e}")
        return f"Error sending camera command (ID: {command_id}): {e}"


async def get_power_status_tool(tool_context: ToolContext = None) -> str:
    """Requests the robot's current power status and waits for the actual status."""
    logger.info("get_power_status_tool called, will wait for actual status update.")
    
    invocation_ctx = getattr(tool_context, "_invocation_context", None)
    if not invocation_ctx: 
        logger.error("get_power_status_tool: ToolContext._invocation_context is missing.")
        return "Error: Invocation context missing, cannot get power status."

    robot_id_for_context = getattr(invocation_ctx, "user_id", None)
    current_session_id = getattr(invocation_ctx.session, "id", None)

    if not robot_id_for_context or not current_session_id:
        logger.error("get_power_status_tool: Robot ID or Session ID missing from invocation context.")
        return "Error: Robot/Session ID missing, cannot get power status."

    grpc_context = _get_grpc_context(tool_context)
    if not grpc_context or shimmy_interface_pb2 is None:
        return "Error: Cannot send command (gRPC context or protobuf missing)."

    command_id = f"cmd_sysinfo_power_{uuid.uuid4().hex[:8]}"
    command_payload = shimmy_interface_pb2.SystemInfoCommand(
        info_request=shimmy_interface_pb2.SystemInfoCommand.InfoRequest.GET_POWER_STATUS
    )
    robot_command_message = shimmy_interface_pb2.RobotCommand(
        command_id=command_id,
        system_info_command=command_payload
    )
    cloud_message = shimmy_interface_pb2.CloudToRobotMessage(
        session_id=current_session_id, 
        robot_command=robot_command_message
    )

    power_status_future = asyncio.Future()
    grpc_context_manager.add_pending_power_request(command_id, power_status_future)

    logger.info(f"Prepared SystemInfoCommand (Power): {robot_command_message} for session {current_session_id}. Command_id: {command_id}")
    try:
        await grpc_context.write(cloud_message)
        logger.info(f"SystemInfoCommand (Power) sent successfully to robot {robot_id_for_context} (CmdID: {command_id}). Waiting for response...")
        
        try:
            power_status_result = await asyncio.wait_for(power_status_future, timeout=10.0) 
            logger.info(f"Received power status for {command_id}: '{power_status_result}'")
            return str(power_status_result) 
        except asyncio.TimeoutError:
            logger.error(f"Timeout waiting for power status response for command_id: {command_id}")
            grpc_context_manager.resolve_pending_power_request(command_id, "Error: Timeout waiting for power status.") 
            return "Error: Timeout waiting for power status update from robot."
        except Exception as e_await:
            logger.error(f"Error awaiting power status future for {command_id}: {e_await}")
            if grpc_context_manager.get_pending_power_request(command_id):
                 grpc_context_manager.resolve_pending_power_request(command_id, f"Error: {e_await}")
            return f"Error processing power status response: {e_await}"

    except Exception as e_send:
        logger.error(f"Failed to send SystemInfoCommand (Power) to robot {robot_id_for_context} (CmdID: {command_id}): {e_send}")
        grpc_context_manager.resolve_pending_power_request(command_id, f"Error: Failed to send command: {e_send}") 
        return f"Error sending power status request (ID: {command_id}): {e_send}"


async def set_voice_volume_tool(
    volume_level: float, tool_context: ToolContext = None
) -> str:
    """Adjusts the robot's synthesized voice volume (0.0 to 1.0)."""
    logger.info(f"set_voice_volume_tool called with level: {volume_level}")
    invocation_ctx = getattr(tool_context, "_invocation_context", None)
    if not invocation_ctx:
        logger.error("set_voice_volume_tool: ToolContext._invocation_context is missing.")
        return "Error: Invocation context missing, cannot execute volume command."

    robot_id_for_context = getattr(invocation_ctx, "user_id", None)
    current_session_id = getattr(invocation_ctx.session, "id", None)

    if not robot_id_for_context or not current_session_id:
        logger.error("set_voice_volume_tool: Robot ID or Session ID missing from invocation context.")
        return "Error: Robot/Session ID missing, cannot execute volume command."

    grpc_context = _get_grpc_context(tool_context)
    if not grpc_context or shimmy_interface_pb2 is None:
        return "Error: Cannot send command (gRPC context or protobuf missing)."

    volume_level = max(0.0, min(1.0, volume_level)) # Clamp volume level

    command_id = f"cmd_voice_{uuid.uuid4().hex[:8]}"
    command_payload = shimmy_interface_pb2.VoiceSettingsCommand(volume_level=volume_level)
    robot_command_message = shimmy_interface_pb2.RobotCommand(
        command_id=command_id,
        voice_settings_command=command_payload
    )
    cloud_message = shimmy_interface_pb2.CloudToRobotMessage(
        session_id=current_session_id,
        robot_command=robot_command_message
    )

    logger.info(f"Prepared VoiceSettingsCommand: {robot_command_message} for session {current_session_id} (Robot: {robot_id_for_context})")
    try:
        await grpc_context.write(cloud_message)
        logger.info(f"VoiceSettingsCommand sent successfully to robot {robot_id_for_context} (CmdID: {command_id}).")
        return f"Voice volume adjustment command (ID: {command_id}, Level: {volume_level}) sent."
    except Exception as e:
        logger.error(f"Failed to send VoiceSettingsCommand to robot {robot_id_for_context} (CmdID: {command_id}): {e}")
        return f"Error sending voice volume command (ID: {command_id}): {e}"


async def find_object_tool(object_name: str, tool_context: ToolContext = None) -> str:
    """Requests the robot to locate a specific object in its view."""
    logger.info(f"find_object_tool called for object: {object_name}")
    invocation_ctx = getattr(tool_context, "_invocation_context", None)
    if not invocation_ctx:
        logger.error("find_object_tool: ToolContext._invocation_context is missing.")
        return "Error: Invocation context missing, cannot execute find_object command."

    robot_id_for_context = getattr(invocation_ctx, "user_id", None)
    current_session_id = getattr(invocation_ctx.session, "id", None)

    if not robot_id_for_context or not current_session_id:
        logger.error("find_object_tool: Robot ID or Session ID missing from invocation context.")
        return "Error: Robot/Session ID missing, cannot execute find_object command."

    grpc_context = _get_grpc_context(tool_context)
    if not grpc_context or shimmy_interface_pb2 is None:
        return "Error: Cannot send command (gRPC context or protobuf missing)."

    command_id = f"cmd_find_{uuid.uuid4().hex[:8]}"
    command_payload = shimmy_interface_pb2.FindObjectCommand(object_name=object_name)
    robot_command_message = shimmy_interface_pb2.RobotCommand(
        command_id=command_id,
        find_object_command=command_payload
    )
    cloud_message = shimmy_interface_pb2.CloudToRobotMessage(
        session_id=current_session_id,
        robot_command=robot_command_message
    )

    logger.info(f"Prepared FindObjectCommand: {robot_command_message} for session {current_session_id} (Robot: {robot_id_for_context})")
    try:
        await grpc_context.write(cloud_message)
        logger.info(f"FindObjectCommand sent successfully to robot {robot_id_for_context} (CmdID: {command_id}).")
        return f"Find object command (ID: {command_id}) for '{object_name}' sent. Waiting for result..."
    except Exception as e:
        logger.error(f"Failed to send FindObjectCommand to robot {robot_id_for_context} (CmdID: {command_id}): {e}")
        return f"Error sending find object command (ID: {command_id}): {e}"


async def cancel_movement_tool(
    command_id_to_cancel: Optional[str] = None, tool_context: ToolContext = None
) -> str:
    """Requests the robot to cancel ongoing movements."""
    log_msg = "cancel_movement_tool called"
    if command_id_to_cancel:
        log_msg += f" for command_id: {command_id_to_cancel}"
    else:
        log_msg += " (canceling all)"
    logger.info(log_msg)

    invocation_ctx = getattr(tool_context, "_invocation_context", None)
    if not invocation_ctx:
        logger.error("cancel_movement_tool: ToolContext._invocation_context is missing.")
        return "Error: Invocation context missing, cannot execute cancel command."

    robot_id_for_context = getattr(invocation_ctx, "user_id", None)
    current_session_id = getattr(invocation_ctx.session, "id", None)

    if not robot_id_for_context or not current_session_id:
        logger.error("cancel_movement_tool: Robot ID or Session ID missing from invocation context.")
        return "Error: Robot/Session ID missing, cannot execute cancel command."

    grpc_context = _get_grpc_context(tool_context)
    if not grpc_context or shimmy_interface_pb2 is None:
        return "Error: Cannot send command (gRPC context or protobuf missing)."

    command_id = f"cmd_cancel_{uuid.uuid4().hex[:8]}" # This is the ID of the cancel command itself
    command_payload = shimmy_interface_pb2.CancelCommand(command_id_to_cancel=command_id_to_cancel)
    robot_command_message = shimmy_interface_pb2.RobotCommand(
        command_id=command_id,
        cancel_command=command_payload
    )
    cloud_message = shimmy_interface_pb2.CloudToRobotMessage(
        session_id=current_session_id,
        robot_command=robot_command_message
    )

    logger.info(f"Prepared CancelCommand: {robot_command_message} for session {current_session_id} (Robot: {robot_id_for_context})")
    try:
        await grpc_context.write(cloud_message)
        logger.info(f"CancelCommand sent successfully to robot {robot_id_for_context} (CmdID: {command_id}).")
        return f"Cancel movement command (ID: {command_id}) sent."
    except Exception as e:
        logger.error(f"Failed to send CancelCommand to robot {robot_id_for_context} (CmdID: {command_id}): {e}")
        return f"Error sending cancel command (ID: {command_id}): {e}"