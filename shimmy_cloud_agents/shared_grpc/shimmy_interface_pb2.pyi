from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class AudioChunk(_message.Message):
    __slots__ = ("audio_data", "sequence_number")
    AUDIO_DATA_FIELD_NUMBER: _ClassVar[int]
    SEQUENCE_NUMBER_FIELD_NUMBER: _ClassVar[int]
    audio_data: bytes
    sequence_number: int
    def __init__(self, audio_data: _Optional[bytes] = ..., sequence_number: _Optional[int] = ...) -> None: ...

class RobotStatusUpdate(_message.Message):
    __slots__ = ("power_status", "movement_status", "image_data", "depth_data", "object_detection_result", "generic_state", "error_report")
    POWER_STATUS_FIELD_NUMBER: _ClassVar[int]
    MOVEMENT_STATUS_FIELD_NUMBER: _ClassVar[int]
    IMAGE_DATA_FIELD_NUMBER: _ClassVar[int]
    DEPTH_DATA_FIELD_NUMBER: _ClassVar[int]
    OBJECT_DETECTION_RESULT_FIELD_NUMBER: _ClassVar[int]
    GENERIC_STATE_FIELD_NUMBER: _ClassVar[int]
    ERROR_REPORT_FIELD_NUMBER: _ClassVar[int]
    power_status: PowerStatus
    movement_status: MovementStatus
    image_data: ImageData
    depth_data: DepthData
    object_detection_result: ObjectDetectionResult
    generic_state: GenericRobotState
    error_report: RobotError
    def __init__(self, power_status: _Optional[_Union[PowerStatus, _Mapping]] = ..., movement_status: _Optional[_Union[MovementStatus, _Mapping]] = ..., image_data: _Optional[_Union[ImageData, _Mapping]] = ..., depth_data: _Optional[_Union[DepthData, _Mapping]] = ..., object_detection_result: _Optional[_Union[ObjectDetectionResult, _Mapping]] = ..., generic_state: _Optional[_Union[GenericRobotState, _Mapping]] = ..., error_report: _Optional[_Union[RobotError, _Mapping]] = ...) -> None: ...

class PowerStatus(_message.Message):
    __slots__ = ("battery_voltage", "current_draw_amps", "power_consumption_watts")
    BATTERY_VOLTAGE_FIELD_NUMBER: _ClassVar[int]
    CURRENT_DRAW_AMPS_FIELD_NUMBER: _ClassVar[int]
    POWER_CONSUMPTION_WATTS_FIELD_NUMBER: _ClassVar[int]
    battery_voltage: float
    current_draw_amps: float
    power_consumption_watts: float
    def __init__(self, battery_voltage: _Optional[float] = ..., current_draw_amps: _Optional[float] = ..., power_consumption_watts: _Optional[float] = ...) -> None: ...

class MovementStatus(_message.Message):
    __slots__ = ("is_moving", "goal_reached", "message")
    IS_MOVING_FIELD_NUMBER: _ClassVar[int]
    GOAL_REACHED_FIELD_NUMBER: _ClassVar[int]
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    is_moving: bool
    goal_reached: bool
    message: str
    def __init__(self, is_moving: bool = ..., goal_reached: bool = ..., message: _Optional[str] = ...) -> None: ...

class ImageData(_message.Message):
    __slots__ = ("image_bytes", "format", "width", "height")
    IMAGE_BYTES_FIELD_NUMBER: _ClassVar[int]
    FORMAT_FIELD_NUMBER: _ClassVar[int]
    WIDTH_FIELD_NUMBER: _ClassVar[int]
    HEIGHT_FIELD_NUMBER: _ClassVar[int]
    image_bytes: bytes
    format: str
    width: int
    height: int
    def __init__(self, image_bytes: _Optional[bytes] = ..., format: _Optional[str] = ..., width: _Optional[int] = ..., height: _Optional[int] = ...) -> None: ...

class DepthData(_message.Message):
    __slots__ = ("depth_map_bytes", "format", "width", "height", "min_depth", "max_depth")
    DEPTH_MAP_BYTES_FIELD_NUMBER: _ClassVar[int]
    FORMAT_FIELD_NUMBER: _ClassVar[int]
    WIDTH_FIELD_NUMBER: _ClassVar[int]
    HEIGHT_FIELD_NUMBER: _ClassVar[int]
    MIN_DEPTH_FIELD_NUMBER: _ClassVar[int]
    MAX_DEPTH_FIELD_NUMBER: _ClassVar[int]
    depth_map_bytes: bytes
    format: str
    width: int
    height: int
    min_depth: float
    max_depth: float
    def __init__(self, depth_map_bytes: _Optional[bytes] = ..., format: _Optional[str] = ..., width: _Optional[int] = ..., height: _Optional[int] = ..., min_depth: _Optional[float] = ..., max_depth: _Optional[float] = ...) -> None: ...

class ObjectDetectionResult(_message.Message):
    __slots__ = ("object_name", "found", "relative_x", "relative_y", "relative_z", "confidence")
    OBJECT_NAME_FIELD_NUMBER: _ClassVar[int]
    FOUND_FIELD_NUMBER: _ClassVar[int]
    RELATIVE_X_FIELD_NUMBER: _ClassVar[int]
    RELATIVE_Y_FIELD_NUMBER: _ClassVar[int]
    RELATIVE_Z_FIELD_NUMBER: _ClassVar[int]
    CONFIDENCE_FIELD_NUMBER: _ClassVar[int]
    object_name: str
    found: bool
    relative_x: float
    relative_y: float
    relative_z: float
    confidence: float
    def __init__(self, object_name: _Optional[str] = ..., found: bool = ..., relative_x: _Optional[float] = ..., relative_y: _Optional[float] = ..., relative_z: _Optional[float] = ..., confidence: _Optional[float] = ...) -> None: ...

class GenericRobotState(_message.Message):
    __slots__ = ("state_description",)
    STATE_DESCRIPTION_FIELD_NUMBER: _ClassVar[int]
    state_description: str
    def __init__(self, state_description: _Optional[str] = ...) -> None: ...

class RobotError(_message.Message):
    __slots__ = ("error_code", "error_message")
    ERROR_CODE_FIELD_NUMBER: _ClassVar[int]
    ERROR_MESSAGE_FIELD_NUMBER: _ClassVar[int]
    error_code: str
    error_message: str
    def __init__(self, error_code: _Optional[str] = ..., error_message: _Optional[str] = ...) -> None: ...

class Transcription(_message.Message):
    __slots__ = ("text", "is_final", "confidence")
    TEXT_FIELD_NUMBER: _ClassVar[int]
    IS_FINAL_FIELD_NUMBER: _ClassVar[int]
    CONFIDENCE_FIELD_NUMBER: _ClassVar[int]
    text: str
    is_final: bool
    confidence: float
    def __init__(self, text: _Optional[str] = ..., is_final: bool = ..., confidence: _Optional[float] = ...) -> None: ...

class SpeechAnalysis(_message.Message):
    __slots__ = ("speaker_id", "emotion", "is_directed_at_robot", "original_text")
    SPEAKER_ID_FIELD_NUMBER: _ClassVar[int]
    EMOTION_FIELD_NUMBER: _ClassVar[int]
    IS_DIRECTED_AT_ROBOT_FIELD_NUMBER: _ClassVar[int]
    ORIGINAL_TEXT_FIELD_NUMBER: _ClassVar[int]
    speaker_id: str
    emotion: str
    is_directed_at_robot: bool
    original_text: str
    def __init__(self, speaker_id: _Optional[str] = ..., emotion: _Optional[str] = ..., is_directed_at_robot: bool = ..., original_text: _Optional[str] = ...) -> None: ...

class TextResponse(_message.Message):
    __slots__ = ("text_to_speak",)
    TEXT_TO_SPEAK_FIELD_NUMBER: _ClassVar[int]
    text_to_speak: str
    def __init__(self, text_to_speak: _Optional[str] = ...) -> None: ...

class RobotCommand(_message.Message):
    __slots__ = ("command_id", "move_command", "led_command", "camera_command", "system_info_command", "voice_settings_command", "find_object_command", "cancel_command")
    COMMAND_ID_FIELD_NUMBER: _ClassVar[int]
    MOVE_COMMAND_FIELD_NUMBER: _ClassVar[int]
    LED_COMMAND_FIELD_NUMBER: _ClassVar[int]
    CAMERA_COMMAND_FIELD_NUMBER: _ClassVar[int]
    SYSTEM_INFO_COMMAND_FIELD_NUMBER: _ClassVar[int]
    VOICE_SETTINGS_COMMAND_FIELD_NUMBER: _ClassVar[int]
    FIND_OBJECT_COMMAND_FIELD_NUMBER: _ClassVar[int]
    CANCEL_COMMAND_FIELD_NUMBER: _ClassVar[int]
    command_id: str
    move_command: MoveCommand
    led_command: LEDCommand
    camera_command: CameraCommand
    system_info_command: SystemInfoCommand
    voice_settings_command: VoiceSettingsCommand
    find_object_command: FindObjectCommand
    cancel_command: CancelCommand
    def __init__(self, command_id: _Optional[str] = ..., move_command: _Optional[_Union[MoveCommand, _Mapping]] = ..., led_command: _Optional[_Union[LEDCommand, _Mapping]] = ..., camera_command: _Optional[_Union[CameraCommand, _Mapping]] = ..., system_info_command: _Optional[_Union[SystemInfoCommand, _Mapping]] = ..., voice_settings_command: _Optional[_Union[VoiceSettingsCommand, _Mapping]] = ..., find_object_command: _Optional[_Union[FindObjectCommand, _Mapping]] = ..., cancel_command: _Optional[_Union[CancelCommand, _Mapping]] = ...) -> None: ...

class MoveCommand(_message.Message):
    __slots__ = ("target_linear_distance_meters", "target_angular_degrees", "target_object_name", "target_x", "target_y", "target_z", "reference_frame")
    TARGET_LINEAR_DISTANCE_METERS_FIELD_NUMBER: _ClassVar[int]
    TARGET_ANGULAR_DEGREES_FIELD_NUMBER: _ClassVar[int]
    TARGET_OBJECT_NAME_FIELD_NUMBER: _ClassVar[int]
    TARGET_X_FIELD_NUMBER: _ClassVar[int]
    TARGET_Y_FIELD_NUMBER: _ClassVar[int]
    TARGET_Z_FIELD_NUMBER: _ClassVar[int]
    REFERENCE_FRAME_FIELD_NUMBER: _ClassVar[int]
    target_linear_distance_meters: float
    target_angular_degrees: float
    target_object_name: str
    target_x: float
    target_y: float
    target_z: float
    reference_frame: str
    def __init__(self, target_linear_distance_meters: _Optional[float] = ..., target_angular_degrees: _Optional[float] = ..., target_object_name: _Optional[str] = ..., target_x: _Optional[float] = ..., target_y: _Optional[float] = ..., target_z: _Optional[float] = ..., reference_frame: _Optional[str] = ...) -> None: ...

class LEDCommand(_message.Message):
    __slots__ = ("color_hex", "brightness", "pattern", "turn_off")
    COLOR_HEX_FIELD_NUMBER: _ClassVar[int]
    BRIGHTNESS_FIELD_NUMBER: _ClassVar[int]
    PATTERN_FIELD_NUMBER: _ClassVar[int]
    TURN_OFF_FIELD_NUMBER: _ClassVar[int]
    color_hex: str
    brightness: float
    pattern: str
    turn_off: bool
    def __init__(self, color_hex: _Optional[str] = ..., brightness: _Optional[float] = ..., pattern: _Optional[str] = ..., turn_off: bool = ...) -> None: ...

class CameraCommand(_message.Message):
    __slots__ = ("capture_type",)
    class CaptureType(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = ()
        CAPTURE_TYPE_UNSPECIFIED: _ClassVar[CameraCommand.CaptureType]
        RGB_IMAGE: _ClassVar[CameraCommand.CaptureType]
        DEPTH_IMAGE: _ClassVar[CameraCommand.CaptureType]
    CAPTURE_TYPE_UNSPECIFIED: CameraCommand.CaptureType
    RGB_IMAGE: CameraCommand.CaptureType
    DEPTH_IMAGE: CameraCommand.CaptureType
    CAPTURE_TYPE_FIELD_NUMBER: _ClassVar[int]
    capture_type: CameraCommand.CaptureType
    def __init__(self, capture_type: _Optional[_Union[CameraCommand.CaptureType, str]] = ...) -> None: ...

class SystemInfoCommand(_message.Message):
    __slots__ = ("info_request", "time_zone")
    class InfoRequest(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = ()
        INFO_REQUEST_UNSPECIFIED: _ClassVar[SystemInfoCommand.InfoRequest]
        GET_POWER_STATUS: _ClassVar[SystemInfoCommand.InfoRequest]
        GET_CURRENT_TIME: _ClassVar[SystemInfoCommand.InfoRequest]
    INFO_REQUEST_UNSPECIFIED: SystemInfoCommand.InfoRequest
    GET_POWER_STATUS: SystemInfoCommand.InfoRequest
    GET_CURRENT_TIME: SystemInfoCommand.InfoRequest
    INFO_REQUEST_FIELD_NUMBER: _ClassVar[int]
    TIME_ZONE_FIELD_NUMBER: _ClassVar[int]
    info_request: SystemInfoCommand.InfoRequest
    time_zone: str
    def __init__(self, info_request: _Optional[_Union[SystemInfoCommand.InfoRequest, str]] = ..., time_zone: _Optional[str] = ...) -> None: ...

class VoiceSettingsCommand(_message.Message):
    __slots__ = ("volume_level",)
    VOLUME_LEVEL_FIELD_NUMBER: _ClassVar[int]
    volume_level: float
    def __init__(self, volume_level: _Optional[float] = ...) -> None: ...

class FindObjectCommand(_message.Message):
    __slots__ = ("object_name",)
    OBJECT_NAME_FIELD_NUMBER: _ClassVar[int]
    object_name: str
    def __init__(self, object_name: _Optional[str] = ...) -> None: ...

class CancelCommand(_message.Message):
    __slots__ = ("command_id_to_cancel",)
    COMMAND_ID_TO_CANCEL_FIELD_NUMBER: _ClassVar[int]
    command_id_to_cancel: str
    def __init__(self, command_id_to_cancel: _Optional[str] = ...) -> None: ...

class SystemDirective(_message.Message):
    __slots__ = ("directive",)
    class DirectiveType(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = ()
        DIRECTIVE_TYPE_UNSPECIFIED: _ClassVar[SystemDirective.DirectiveType]
        HALT_PROCESSING: _ClassVar[SystemDirective.DirectiveType]
    DIRECTIVE_TYPE_UNSPECIFIED: SystemDirective.DirectiveType
    HALT_PROCESSING: SystemDirective.DirectiveType
    DIRECTIVE_FIELD_NUMBER: _ClassVar[int]
    directive: SystemDirective.DirectiveType
    def __init__(self, directive: _Optional[_Union[SystemDirective.DirectiveType, str]] = ...) -> None: ...

class RobotToCloudMessage(_message.Message):
    __slots__ = ("session_id", "robot_id", "audio_chunk", "status_update")
    SESSION_ID_FIELD_NUMBER: _ClassVar[int]
    ROBOT_ID_FIELD_NUMBER: _ClassVar[int]
    AUDIO_CHUNK_FIELD_NUMBER: _ClassVar[int]
    STATUS_UPDATE_FIELD_NUMBER: _ClassVar[int]
    session_id: str
    robot_id: str
    audio_chunk: AudioChunk
    status_update: RobotStatusUpdate
    def __init__(self, session_id: _Optional[str] = ..., robot_id: _Optional[str] = ..., audio_chunk: _Optional[_Union[AudioChunk, _Mapping]] = ..., status_update: _Optional[_Union[RobotStatusUpdate, _Mapping]] = ...) -> None: ...

class CloudToRobotMessage(_message.Message):
    __slots__ = ("session_id", "transcription", "speech_analysis", "text_response", "robot_command", "system_directive")
    SESSION_ID_FIELD_NUMBER: _ClassVar[int]
    TRANSCRIPTION_FIELD_NUMBER: _ClassVar[int]
    SPEECH_ANALYSIS_FIELD_NUMBER: _ClassVar[int]
    TEXT_RESPONSE_FIELD_NUMBER: _ClassVar[int]
    ROBOT_COMMAND_FIELD_NUMBER: _ClassVar[int]
    SYSTEM_DIRECTIVE_FIELD_NUMBER: _ClassVar[int]
    session_id: str
    transcription: Transcription
    speech_analysis: SpeechAnalysis
    text_response: TextResponse
    robot_command: RobotCommand
    system_directive: SystemDirective
    def __init__(self, session_id: _Optional[str] = ..., transcription: _Optional[_Union[Transcription, _Mapping]] = ..., speech_analysis: _Optional[_Union[SpeechAnalysis, _Mapping]] = ..., text_response: _Optional[_Union[TextResponse, _Mapping]] = ..., robot_command: _Optional[_Union[RobotCommand, _Mapping]] = ..., system_directive: _Optional[_Union[SystemDirective, _Mapping]] = ...) -> None: ...
