# shimmy_cloud_agents/server.py

import asyncio
import logging
import os
import uuid
import time
from typing import Dict, AsyncIterable, Optional

import grpc
import uvicorn
from dotenv import find_dotenv, load_dotenv
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

# Import ADK core components
from google.adk.agents import Agent # Assuming root_agent is an LlmAgent or similar
from google.adk.runners import Runner
# Correct imports for InMemory services
from google.adk.sessions.in_memory_session_service import InMemorySessionService
from google.adk.artifacts.in_memory_artifact_service import InMemoryArtifactService
from google.adk.sessions import Session # For type hinting Session object
from google.genai import types as genai_types

# Import the gRPC context manager setter and resolver
from shimmy_cloud_agents.tools.grpc_context_manager import set_active_streams, resolve_pending_power_request

# --- Configuration & Logging (Your improved version) ---
env_path = find_dotenv(".env")
print(f"DEBUG: Attempting to load .env file from: {env_path}") # Print path
load_dotenv(env_path, override=True)
print(f"DEBUG: ROOT_AGENT_MODEL after load_dotenv in server.py: {os.getenv('ROOT_AGENT_MODEL')}") # Print value

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO").upper(),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Import generated gRPC files
try:
    from shimmy_cloud_agents.shared_grpc import shimmy_interface_pb2
    from shimmy_cloud_agents.shared_grpc import shimmy_interface_pb2_grpc
except ImportError as e:
    logger.exception(
        "ImportError: Failed to import gRPC modules. This could be due to issues with "
        "gRPC code generation (missing or incorrectly placed "
        "shimmy_interface_pb2.py or shimmy_interface_pb2_grpc.py). "
        "See traceback below for details."
    )
    exit(1)

# Import your ADK agents
try:
    from shimmy_cloud_agents.agents.stt_subscriber.agent import stt_subscriber_agent
    from shimmy_cloud_agents.agents.speech_processor.agent import speech_processor_agent
    root_agent = stt_subscriber_agent # Main agent for stt_subscriber_runner
except ImportError as e:
    logger.exception(
        "ImportError: Failed to import ADK agents. Check agent definitions and paths. "
        "See traceback below for details."
    )
    exit(1)

GRPC_HOST = os.getenv("GRPC_SERVER_HOST", "0.0.0.0")
GRPC_PORT = int(os.getenv("GRPC_SERVER_PORT", 50051))


# --- ADK Setup ---
session_service = InMemorySessionService()
artifact_service = InMemoryArtifactService()

speech_processor_runner = Runner(
    app_name="shimmy_speech_processor",
    agent=speech_processor_agent,
    session_service=session_service,
    artifact_service=artifact_service,
)

stt_subscriber_runner = Runner(
    app_name="shimmy_stt_subscriber",
    agent=root_agent,
    session_service=session_service,
    artifact_service=artifact_service,
)

# --- gRPC Connection Management ---
active_robot_streams: Dict[str, grpc.aio.ServicerContext] = {}
robot_audio_buffers: Dict[str, bytearray] = {}


async def process_transcription_and_respond(
    transcription: str, session_id: str, robot_id: str,
    is_http_test: bool = False
) -> Optional[str]:
    logger.info(
        f"Starting sequential agent processing for robot {robot_id}, session"
        f" {session_id}. HTTP Test: {is_http_test}. Transcription: '{transcription[:100]}...'"
    )
    processing_start_time = time.time()

    grpc_context = None
    if not is_http_test:
        grpc_context = active_robot_streams.get(robot_id)
        if not grpc_context:
            logger.error(f"HTTP Test: False, but no active gRPC stream found for robot_id: {robot_id}")
            return "Error: Robot gRPC stream not found."

    current_session: Optional[Session] = None
    try:
        # Try to get an existing session
        current_session = session_service.get_session(
            app_name=stt_subscriber_runner.app_name, user_id=robot_id, session_id=session_id
        )
        logger.info(f"Existing session found: {session_id} for app {stt_subscriber_runner.app_name}")
        # Update state for existing session
        current_session.state["latest_transcription"] = transcription
        # Ensure grpc_context is NOT stored in ADK session state
        current_session.state.pop("grpc_context", None) 

    except AttributeError: # Session not found, create a new one
        logger.info(f"Creating new session: {session_id} for app {stt_subscriber_runner.app_name}")
        initial_state = {
            "robot_id": robot_id,
            "latest_transcription": transcription,
            # Ensure grpc_context is NOT stored in ADK session state
        }
        current_session = session_service.create_session(
            app_name=stt_subscriber_runner.app_name,
            user_id=robot_id,
            session_id=session_id,
            state=initial_state,
        )

    if not current_session:
        logger.error(f"Critical error: Failed to get or create session {session_id} for robot {robot_id}")
        return "Error: Session management failed critically."

    # Now current_session is guaranteed to be a Session object, and its state contains 'latest_transcription'

    speech_analysis_result = None
    try:
        logger.info(f"Preparing to run Speech Processor for session {session_id} (correlating with stt_subscriber session)...")

        # State needed by speech_processor_agent's callback
        speech_processor_session_state = {
            "robot_id": robot_id,
            "latest_transcription": transcription,
            # Ensure grpc_context is NOT stored in ADK session state for speech_processor_runner either
        }
        if not is_http_test and grpc_context: # Ensure grpc_context is available if needed
             speech_processor_session_state["grpc_context"] = grpc_context

        # Ensure a session exists for speech_processor_runner with its own app_name
        try:
            sp_session = session_service.get_session(
                app_name=speech_processor_runner.app_name,
                user_id=robot_id,
                session_id=session_id
            )
            sp_session.state.update(speech_processor_session_state)
            # Ensure grpc_context is NOT stored here either
            sp_session.state.pop("grpc_context", None) 
            logger.info(f"Updated existing session {session_id} for speech_processor_runner (app: {speech_processor_runner.app_name}).")
        except AttributeError: # Not found, create one for speech_processor_runner
            sp_session = session_service.create_session(
                app_name=speech_processor_runner.app_name,
                user_id=robot_id,
                session_id=session_id,
                state=speech_processor_session_state
            )
            logger.info(f"Created new session {session_id} for speech_processor_runner (app: {speech_processor_runner.app_name}).")

        logger.info(f"Running Speech Processor (app: {speech_processor_runner.app_name}) for session {sp_session.id}...")
        async for event in speech_processor_runner.run_async(
            session_id=sp_session.id, user_id=robot_id, new_message=None # Callback loads from sp_session.state
        ):
            logger.debug(f"Speech Processor Event for {sp_session.id}: {event.author}")
            # speech_analysis_result is expected to be put into sp_session.state by the speech_processor_agent
        
        if "speech_analysis_result" in sp_session.state:
            speech_analysis_result = sp_session.state["speech_analysis_result"]
            current_session.state["speech_analysis_result"] = speech_analysis_result # Copy to main session state
            logger.info(f"Speech analysis complete for {sp_session.id}: {speech_analysis_result}. Copied to main session.")
        else:
            logger.warning(f"Speech processor did not populate 'speech_analysis_result' in state for {sp_session.id} (app: {speech_processor_runner.app_name})")
            current_session.state.pop("speech_analysis_result", None) # Ensure it's not stale in main session

    except Exception as e:
        logger.exception(f"Error during Speech Processor run for session {session_id} (attempted for app {speech_processor_runner.app_name}): {e}")
        current_session.state.pop("speech_analysis_result", None) # Ensure it's not stale in main session state

    final_response_text = "Sorry, I couldn't process that request."
    try:
        logger.info(f"Running STT Subscriber Agent for session {current_session.id}...")
        user_content = genai_types.Content(
            role="user", parts=[genai_types.Part(text=transcription)]
        )
        async for event in stt_subscriber_runner.run_async(
            session_id=current_session.id, user_id=robot_id, new_message=user_content
        ):
            logger.debug(f"STT Subscriber Event for {current_session.id}: {event.author}")
            if event.is_final_response and event.content and event.content.parts:
                response_parts = [
                    part.text
                    for part in event.content.parts
                    if hasattr(part, "text") and part.text
                ]
                if response_parts:
                   final_response_text = " ".join(response_parts)
                   logger.info(f"STT Subscriber final response for {current_session.id}: {final_response_text}")
    except Exception as e:
        logger.exception(f"Error during STT Subscriber run for session {current_session.id}: {e}")
        final_response_text = f"An error occurred during main processing: {e}"

    processing_end_time = time.time()
    logger.info(
        f"Sequential agent processing complete for robot {robot_id}, session {current_session.id}."
        f" Duration: {processing_end_time - processing_start_time:.2f}s"
    )

    if is_http_test:
        return final_response_text
    elif grpc_context: # This implies not is_http_test
        try:
            response_message = shimmy_interface_pb2.CloudToRobotMessage(
                session_id=current_session.id, # Use current_session.id for consistency
                text_response=shimmy_interface_pb2.TextResponse(
                    text_to_speak=final_response_text
                ),
            )
            await grpc_context.write(response_message)
            logger.info(f"Sent final response to robot {robot_id} for session {current_session.id}")
        except Exception as e:
            logger.error(
                f"Failed to send final response to robot {robot_id} on session {current_session.id}: {e}"
            )
    return None


# --- gRPC Servicer Implementation ---
class ShimmyCloudServiceServicer(
    shimmy_interface_pb2_grpc.ShimmyCloudServiceServicer
):
    async def Communicate(
        self,
        request_iterator: AsyncIterable[shimmy_interface_pb2.RobotToCloudMessage],
        context: grpc.aio.ServicerContext,
    ) -> AsyncIterable[shimmy_interface_pb2.CloudToRobotMessage]:
        peer = context.peer()
        # Ensure robot_id is generated and logged immediately
        robot_id = f"robot_{peer}_{uuid.uuid4().hex[:6]}"
        session_id_for_this_connection = f"grpc_conn_session_{robot_id}_{uuid.uuid4().hex[:8]}"
        logger.info(f"[{robot_id}] Communicate: Method ENTERED. Peer: {peer}, Assigned RobotID: {robot_id}, Connection Session: {session_id_for_this_connection}")

        # Initialize stream and buffer storage immediately
        active_robot_streams[robot_id] = context
        robot_audio_buffers[robot_id] = bytearray()
        logger.info(f"[{robot_id}] Communicate: Added to active_robot_streams and initialized buffer.")

        async def cleanup():
            logger.info(f"[{robot_id}] Communicate: Cleanup task STARTED for RobotID: {robot_id}, Peer: {peer}.")
            active_robot_streams.pop(robot_id, None)
            robot_audio_buffers.pop(robot_id, None)
            logger.info(f"[{robot_id}] Communicate: Cleanup task COMPLETED for RobotID: {robot_id}.")

        context.add_done_callback(lambda _: asyncio.create_task(cleanup()))
        logger.info(f"[{robot_id}] Communicate: Added done_callback.")

        try:
            logger.info(f"[{robot_id}] Communicate: Entering TRY block, about to start 'async for message in request_iterator' loop.")
            message_count = 0
            async for message in request_iterator:
                message_count += 1
                client_msg_payload_type = message.WhichOneof("robot_payload")
                client_msg_session_id = message.session_id
                logger.info(f"[{robot_id}] Communicate: MSG #{message_count} RECEIVED from client. Type: {client_msg_payload_type}, ClientSession: {client_msg_session_id}")

                current_process_session_id = client_msg_session_id or session_id_for_this_connection

                if client_msg_payload_type == "audio_chunk":
                    robot_audio_buffers[robot_id].extend(message.audio_chunk.audio_data)
                    BUFFER_THRESHOLD = 16000 * 2 # Example threshold
                    logger.debug(f"[{robot_id}] Communicate: Audio chunk received. Buffer size: {len(robot_audio_buffers[robot_id])}")
                    if len(robot_audio_buffers[robot_id]) >= BUFFER_THRESHOLD:
                        audio_data = bytes(robot_audio_buffers[robot_id])
                        robot_audio_buffers[robot_id] = bytearray() # Clear buffer
                        logger.info(f"[{robot_id}] Communicate: Audio buffer threshold reached. Processing {len(audio_data)} bytes.")
                        # Simulate STT and further processing
                        transcription = f"Simulated transcription for {robot_id} at {time.time()} from audio chunk"
                        logger.info(f"[{robot_id}] Communicate: STT Result from audio: {transcription}. Creating task for process_transcription_and_respond.")
                        asyncio.create_task(
                            process_transcription_and_respond(
                                transcription, current_process_session_id, robot_id, is_http_test=False
                            )
                        )
                elif client_msg_payload_type == "status_update":
                    status_payload = message.status_update
                    status_data_type = status_payload.WhichOneof("status_data")
                    logger.info(f"[{robot_id}] Communicate: Status update RECEIVED: type '{status_data_type}'. Details: {status_payload}")
                    
                    # Check for special interactive shell command
                    if status_data_type == "command_ack":
                        command_ack = status_payload.command_ack
                        logger.info(f"[{robot_id}] Communicate: Received CommandAcknowledgement for command_id: {command_ack.command_id}, message: '{command_ack.message}'")
                        
                        # Attempt to resolve a pending power status request
                        was_power_request_resolved = resolve_pending_power_request(command_ack.command_id, command_ack.message)
                        
                        if was_power_request_resolved:
                            logger.info(f"[{robot_id}] Communicate: Successfully resolved pending power status request for command_id: {command_ack.command_id}.")
                            # The ack has been consumed by the power status request, no further processing for this specific ack here.
                        elif command_ack.command_id == "interactive_shell_command":
                            interactive_text = command_ack.message
                            logger.info(f"[{robot_id}] Communicate: Interactive shell command RECEIVED: '{interactive_text}'. Creating task for process_transcription_and_respond.")
                            asyncio.create_task(
                                process_transcription_and_respond(
                                    interactive_text, current_process_session_id, robot_id, is_http_test=False
                                )
                            )
                        # else: regular command acknowledgement, just log (already done by general log above)
                    # else: other status update types, just log (already done by general log above)

                else:
                    logger.warning(f"[{robot_id}] Communicate: Unknown payload type RECEIVED: {client_msg_payload_type}")
            
            logger.info(f"[{robot_id}] Communicate: FINISHED 'async for message in request_iterator' loop. Total messages received: {message_count}.")
            # If client stream closed, but RPC context not done, keep handler alive for pending writes.
            if not context.done():
                logger.info(f"[{robot_id}] Communicate: Client stream closed. Server keeping send-stream open for pending writes or until RPC termination.")
                while not context.done():
                    try:
                        await asyncio.sleep(0.5) # Check periodically if context is done.
                    except asyncio.CancelledError:
                        logger.info(f"[{robot_id}] Communicate: Main handler task cancelled while waiting for context to complete.")
                        # Propagate cancellation to ensure cleanup.
                        raise
                logger.info(f"[{robot_id}] Communicate: Context is now done or handler is exiting after client stream closure.")

        except grpc.aio.AioRpcError as e:
            if e.code() == grpc.StatusCode.CANCELLED:
                logger.info(f"[{robot_id}] Communicate: Stream CANCELLED (likely client disconnected or server shutdown): {e.details()}")
            else:
                logger.error(f"[{robot_id}] Communicate: grpc.aio.AioRpcError in stream: Code {e.code()}, Details: {e.details()}")
        except Exception as e:
            logger.exception(f"[{robot_id}] Communicate: UNHANDLED EXCEPTION in stream for RobotID {robot_id}:")
        finally:
            logger.info(f"[{robot_id}] Communicate: Method EXITING (finally block). Peer: {peer}")
        
        if False:
            yield


# --- FastAPI App Setup ---
app = FastAPI(title="Shimmy Cloud Agent Service")
grpc_server: Optional[grpc.aio.Server] = None

@app.on_event("startup")
async def startup_event():
    global grpc_server
    grpc_server = grpc.aio.server()
    shimmy_interface_pb2_grpc.add_ShimmyCloudServiceServicer_to_server(
        ShimmyCloudServiceServicer(), grpc_server
    )
    listen_addr = f"{GRPC_HOST}:{GRPC_PORT}"
    grpc_server.add_insecure_port(listen_addr)
    logger.info(f"Starting gRPC server on {listen_addr}")
    await grpc_server.start()
    logger.info("gRPC server started.")
    
    # Pass the active_robot_streams dictionary to the context manager
    set_active_streams(active_robot_streams)
    logger.info("gRPC context manager initialized with active_robot_streams.")

    asyncio.create_task(grpc_server.wait_for_termination())

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Stopping gRPC server...")
    if grpc_server:
        await grpc_server.stop(grace=1)
    logger.info("gRPC server stopped.")

@app.get("/")
async def read_root():
    return {"message": "Shimmy Cloud Agent Service is running."}

# --- Pydantic Model for HTTP Test Request ---
class AgentTestRequest(BaseModel):
    transcription: str
    robot_id: str = "http_test_robot"
    session_id: Optional[str] = None

# --- HTTP Endpoint for Testing Agents ---
@app.post("/test_agent") # Removed response_model=str for more flexibility
async def test_agent_endpoint(request: AgentTestRequest):
    session_id = request.session_id or f"http_session_{uuid.uuid4().hex[:8]}"
    logger.info(
        f"Received /test_agent request: transcription='{request.transcription}',"
        f" robot_id='{request.robot_id}', session_id='{session_id}'"
    )
    try:
        final_response = await process_transcription_and_respond(
            transcription=request.transcription,
            session_id=session_id,
            robot_id=request.robot_id,
            is_http_test=True,
        )
        if final_response is None:
            error_detail = "Agent processing failed to return text."
            logger.error(f"{error_detail} for session {session_id} via HTTP.")
            raise HTTPException(status_code=500, detail={"error": error_detail, "session_id": session_id})
        return {"response": final_response, "session_id": session_id}
    except HTTPException as http_exc:
        # Re-raise HTTPException to let FastAPI handle it, assuming detail might already include session_id or is structured.
        raise http_exc
    except Exception as e:
        error_detail = str(e)
        logger.exception(f"Error processing /test_agent request for session {session_id}: {e}")
        raise HTTPException(status_code=500, detail={"error": error_detail, "session_id": session_id})


# --- Main Execution ---
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)