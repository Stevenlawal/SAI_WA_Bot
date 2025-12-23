from neonize.proto.waE2E.WAWebProtobufsE2E_pb2 import (
    Message,
    ExtendedTextMessage,
)
from .config import COLOR_BLACK_ARGB

def build_black_status_message(text_content):
    """
    Construct the Protobuf message for a black background status.
    """
    return Message(
        extendedTextMessage=ExtendedTextMessage(
            text=text_content,
            backgroundArgb=COLOR_BLACK_ARGB,
            # We use integers to avoid "Enum has no value" errors
            # 1 = SERIF font
            # 0 = SANS_SERIF font
            font=1, 
            
            # 0 = NONE (No link preview)
            previewType=0 
        )
    )