import asyncio
import logging
import uuid
import time
import random

import grpc

# Assuming your generated gRPC files are in a 'shared_grpc' directory
# and accessible from this path. Adjust if necessary.
try:
    from shared_grpc import shimmy_interface_pb2
    from shared_grpc import shimmy_interface_pb2_grpc
except ImportError:
    print("Error: Could not import generated shimmy_interface_pb2 or shimmy_interface_pb2_grpc.")
    print("Ensure these files are generated from your .proto file and are in the PYTHONPATH.")
    print("You might need to run: python -m grpc_tools.protoc -I./protos --python_out=./shimmy_cloud_agents/shared_grpc --grpc_python_out=./shimmy_cloud_agents/shared_grpc ./protos/shimmy_interface.proto")
    shimmy_interface_pb2 = None
    shimmy_interface_pb2_grpc = None
    exit(1)


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

GRPC_SERVER_HOST = "localhost"
GRPC_SERVER_PORT = 50051
ROBOT_ID = f"mock_robot_{uuid.uuid4().hex[:6]}"
# This session ID is generated once when the mock client starts.
# The server logic might also generate/manage session IDs per connection.
# For robust session resumption, this mock client might need to store and reuse
# a session ID provided by the server or persist its own.
MOCK_CLIENT_SESSION_ID = f"mock_client_session_{uuid.uuid4().hex[:8]}"

# Global shutdown event
shutdown_event = asyncio.Event()

async def send_initial_status(robot_id: str, session_id: str):
    """Sends an initial status update to the server."""
    logger.info(f"[{robot_id}] Sending initial presence status. Session: {session_id}")
    # RobotStatusUpdate itself does not have robot_id or timestamp fields as per the .proto.
    # These would be part of the individual status messages if defined there, or on the wrapper RobotToCloudMessage.
    # The RobotToCloudMessage has session_id, but no robot_id in the provided .proto
    status_payload = shimmy_interface_pb2.RobotStatusUpdate(
        power_status=shimmy_interface_pb2.PowerStatus(battery_voltage=4.1),
        # If you had other fields in RobotStatusUpdate for generic timestamp or ID, they'd go here.
        # But based on the .proto, it's a oneof status_data.
    )
    # The ROBOT_ID for the client is used for client-side logging and would be set on RobotToCloudMessage
    # if that message type had a robot_id field in the .proto.
    return shimmy_interface_pb2.RobotToCloudMessage(
        session_id=session_id, # session_id is on RobotToCloudMessage
        status_update=status_payload
    )

async def interactive_input_loop(robot_id: str, outgoing_message_queue: asyncio.Queue, session_id: str):
    """Handles interactive user input and sends it as commands."""
    logger.info(f"[{robot_id}] Interactive shell started. Type 'quit' or 'exit' to stop.")
    
    # Create a separate thread for input handling
    def input_thread():
        while not shutdown_event.is_set():
            try:
                # Clear the line and show prompt
                print("\r\033[K", end='', flush=True)  # Clear current line
                prompt = f"[{robot_id}@{session_id}] Enter command: "
                print(prompt, end='', flush=True)
                text = input()
                if text:
                    return text
            except EOFError:
                return None
            except Exception as e:
                logger.error(f"[{robot_id}] Error in input thread: {e}")
                return None
        return None

    # Wait a brief moment to ensure all initial logging is complete
    await asyncio.sleep(0.1)

    while not shutdown_event.is_set():
        try:
            # Run input in a thread pool to avoid blocking
            text = await asyncio.get_event_loop().run_in_executor(None, input_thread)
            
            if shutdown_event.is_set():  # Check again after blocking input
                break

            if text is None:  # EOF or error occurred
                logger.info(f"[{robot_id}] Input thread returned None. Initiating shutdown.")
                shutdown_event.set()
                break

            if text.lower() in ["quit", "exit"]:
                logger.info(f"[{robot_id}] Shutdown initiated from interactive shell.")
                shutdown_event.set()
                break

            # Package text as a special RobotStatusUpdate with CommandAcknowledgement
            ack_payload = shimmy_interface_pb2.CommandAcknowledgement(
                command_id="interactive_shell_command",  # Special ID for server to recognize
                status=shimmy_interface_pb2.CommandAcknowledgement.Status.SUCCESS,  # Status field is mandatory
                message=text  # User's command text
            )
            status_payload = shimmy_interface_pb2.RobotStatusUpdate(command_ack=ack_payload)
            robot_to_cloud_msg = shimmy_interface_pb2.RobotToCloudMessage(
                session_id=session_id,
                status_update=status_payload
            )
            await outgoing_message_queue.put(robot_to_cloud_msg)
            logger.info(f"[{robot_id}] Queued interactive command: '{text}'")

        except Exception as e:
            if not shutdown_event.is_set():  # Log error only if not part of a shutdown
                logger.error(f"[{robot_id}] Error in interactive_input_loop: {e}")
            # In case of unexpected errors, also trigger shutdown to be safe
            shutdown_event.set()
            break

    logger.info(f"[{robot_id}] Interactive input loop ended.")


async def generate_messages(robot_id: str, session_id: str, outgoing_message_queue: asyncio.Queue):
    """
    Async generator for messages to send to the server.
    Sends an initial status and then sends responses/commands from the queue.
    """
    initial_msg = await send_initial_status(robot_id, session_id)
    yield initial_msg
    logger.info(f"[{robot_id}] generate_messages: Successfully yielded initial status message.")

    while not shutdown_event.is_set():
        try:
            # Wait for a message to be put on the queue (either an ACK or an interactive command)
            # Add a timeout to allow checking shutdown_event periodically
            response_message = await asyncio.wait_for(outgoing_message_queue.get(), timeout=0.5)
            if response_message is None: # Signal to stop
                logger.info(f"[{robot_id}] generate_messages: Received None, stopping message generation.")
                break
            yield response_message
            outgoing_message_queue.task_done()
            logger.debug(f"[{robot_id}] generate_messages: Yielded message from queue: {type(response_message)}")
        except asyncio.TimeoutError:
            continue # Just to check shutdown_event again
        except Exception as e:
            if not shutdown_event.is_set():
                 logger.error(f"[{robot_id}] generate_messages: Error getting message from queue: {e}")
            break # Exit loop on other errors
    logger.info(f"[{robot_id}] generate_messages: Exiting.")


async def run_robot_client(robot_id: str, shared_shutdown_event: asyncio.Event):
    """Main function to run the mock robot client."""
    if not shimmy_interface_pb2 or not shimmy_interface_pb2_grpc:
        logger.error("gRPC modules not loaded. Exiting.")
        return

    server_address = f"{GRPC_SERVER_HOST}:{GRPC_SERVER_PORT}"
    logger.info(f"[{robot_id}] Attempting to connect to gRPC server at {server_address} with session {MOCK_CLIENT_SESSION_ID}...")

    # This queue is used for messages client wants to send to server:
    # 1. ACKs for commands received from server.
    # 2. Text commands from the interactive shell.
    outgoing_message_queue = asyncio.Queue()
    
    interactive_task = None
    max_retries = 5  # Maximum number of reconnection attempts
    base_delay = 1.0  # Base delay in seconds
    max_delay = 30.0  # Maximum delay in seconds

    while not shared_shutdown_event.is_set():
        retry_count = 0
        try:
            # Start the interactive shell first
            interactive_task = asyncio.create_task(
                interactive_input_loop(robot_id, outgoing_message_queue, MOCK_CLIENT_SESSION_ID)
            )

            # Wait a moment for the interactive shell to initialize
            await asyncio.sleep(0.1)

            async with grpc.aio.insecure_channel(server_address) as channel:
                stub = shimmy_interface_pb2_grpc.ShimmyCloudServiceStub(channel)
                logger.info(f"[{robot_id}] Connected. Starting 'Communicate' stream.")

                message_generator = generate_messages(robot_id, MOCK_CLIENT_SESSION_ID, outgoing_message_queue)
                
                logger.info(f"[{robot_id}] run_robot_client: About to call stub.Communicate with message_generator.")
                
                async for server_message in stub.Communicate(message_generator):
                    if shared_shutdown_event.is_set():
                        logger.info(f"[{robot_id}] Shutdown event detected in main gRPC loop. Breaking.")
                        break
                    
                    # Reset retry count on successful message
                    retry_count = 0
                    
                    logger.info(f"[{robot_id}] Received message from server (Session: {server_message.session_id}):")
                    payload_type = server_message.WhichOneof("cloud_payload")

                    if payload_type == "robot_command":
                        command = server_message.robot_command
                        command_type = command.WhichOneof("command_type")
                        logger.info(f"  -> RobotCommand ID: {command.command_id}, Type: {command_type}")

                        response_text = f"Mock success for {command_type} (ID: {command.command_id})"
                        ack_status = shimmy_interface_pb2.CommandAcknowledgement.Status.SUCCESS

                        # Special handling for get_power_status command to return actual data
                        if command_type == "system_info_command" and \
                           command.system_info_command.info_request == shimmy_interface_pb2.SystemInfoCommand.InfoRequest.GET_POWER_STATUS:
                            # Simulate a battery voltage, e.g., from a constant or a slight random variation
                            simulated_voltage = 4.15 + (uuid.uuid4().int % 10) / 100.0 # e.g., 4.15 to 4.24
                            response_text = f"Battery voltage: {simulated_voltage:.2f}V"
                            logger.info(f"[{robot_id}] Responding to GET_POWER_STATUS with simulated data: '{response_text}'")

                        status_payload = shimmy_interface_pb2.RobotStatusUpdate(
                            command_ack=shimmy_interface_pb2.CommandAcknowledgement(
                                command_id=command.command_id,
                                status=ack_status,
                                message=response_text
                            )
                        )
                        response_msg = shimmy_interface_pb2.RobotToCloudMessage(
                            session_id=server_message.session_id or MOCK_CLIENT_SESSION_ID,
                            status_update=status_payload
                        )
                        await outgoing_message_queue.put(response_msg)
                        logger.info(f"[{robot_id}] Queued acknowledgement for {command.command_id}")

                    elif payload_type == "text_response":
                        logger.info(f"  -> TextResponse: '{server_message.text_response.text_to_speak}'")
                    elif payload_type == "error_message":
                        logger.error(f"  -> ErrorMessage: '{server_message.error_message.message}'")
                    else:
                        logger.warning(f"  -> Unknown payload type: {payload_type}")

        except grpc.aio.AioRpcError as e:
            logger.error(f"[{robot_id}] gRPC Error: {e.code()} - {e.details()}")
            
            if retry_count < max_retries and not shared_shutdown_event.is_set():
                # Calculate delay with exponential backoff and jitter
                delay = min(max_delay, base_delay * (2 ** retry_count))
                jitter = random.uniform(0, 0.1 * delay)  # Add 10% jitter
                total_delay = delay + jitter
                
                retry_count += 1
                logger.info(f"[{robot_id}] Attempting to reconnect in {total_delay:.2f} seconds (attempt {retry_count}/{max_retries})")
                await asyncio.sleep(total_delay)
                continue
            else:
                logger.error(f"[{robot_id}] Max retries reached or shutdown requested. Exiting.")
                shared_shutdown_event.set()
                break
                
        except Exception as e:
            logger.exception(f"[{robot_id}] An unexpected error occurred in run_robot_client:")
            if not shared_shutdown_event.is_set():
                # For unexpected errors, wait a bit before retrying
                await asyncio.sleep(base_delay)
                continue
            break
            
        finally:
            logger.info(f"[{robot_id}] Communication stream ended or error occurred. Initiating shutdown sequence.")
            
            if interactive_task and not interactive_task.done():
                logger.info(f"[{robot_id}] Cancelling interactive input task.")
                interactive_task.cancel()
                try:
                    await interactive_task
                except asyncio.CancelledError:
                    logger.info(f"[{robot_id}] Interactive input task cancelled successfully.")
                except Exception as e_cancel:
                    logger.error(f"[{robot_id}] Error during interactive task cancellation: {e_cancel}")
            
            # Signal the message generator to stop by putting None on its queue.
            logger.info(f"[{robot_id}] Putting None on outgoing_message_queue to stop generator.")
            await outgoing_message_queue.put(None)
            
            if not shared_shutdown_event.is_set() and retry_count < max_retries:
                logger.info(f"[{robot_id}] Preparing for reconnection attempt {retry_count + 1}/{max_retries}")
                continue
            
            logger.info(f"[{robot_id}] Mock robot client run_robot_client finished.")


async def main_async_runner():
    # This function will run the client and handle graceful shutdown.
    # shutdown_event is global in this file.
    client_task = asyncio.create_task(run_robot_client(ROBOT_ID, shutdown_event))
    
    try:
        await shutdown_event.wait() # Wait until shutdown is signaled
        logger.info("Main runner: Shutdown signaled.")
    finally:
        logger.info("Main runner: Cleaning up client task...")
        if not client_task.done():
            client_task.cancel()
            try:
                await client_task
            except asyncio.CancelledError:
                logger.info("Main runner: Client task successfully cancelled.")
            except Exception as e:
                logger.error(f"Main runner: Error awaiting cancelled client task: {e}")
        logger.info("Main runner: Cleanup complete.")


if __name__ == "__main__":
    logger.info(f"Starting mock robot client: {ROBOT_ID} with session: {MOCK_CLIENT_SESSION_ID}")
    try:
        asyncio.run(main_async_runner())
    except KeyboardInterrupt:
        logger.info("KeyboardInterrupt received by __main__. Setting shutdown event.")
        shutdown_event.set()
        # asyncio.run() will exit, and main_async_runner's finally block should have handled task cancellation
        # if the event was set and awaited correctly.
        # To be absolutely sure, we can add a brief moment for tasks to wind down if necessary,
        # but the event-based coordination should be sufficient.
    finally:
        logger.info(f"Mock robot client {ROBOT_ID} application exiting.") 