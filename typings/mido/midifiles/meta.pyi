"""
This type stub file was generated by pyright.
"""

from contextlib import contextmanager
from ..messages import BaseMessage

"""
Meta messages for MIDI files.

TODO:
     - what if an unknown meta message is implemented and someone depends on
       the 'data' attribute?
     - is 'type_byte' a good name?
     - 'values' is not a good name for a dictionary.
     - type and value safety?
     - copy().
     - expose _key_signature_encode/decode?
"""
_charset = ...
class KeySignatureError(Exception):
    """ Raised when key cannot be converted from key/mode to key letter """
    ...


_key_signature_decode = ...
_key_signature_encode = ...
_smpte_framerate_decode = ...
_smpte_framerate_encode = ...
def signed(to_type, n): # -> Any:
    ...

def unsigned(to_type, n): # -> Any:
    ...

def encode_variable_int(value): # -> list[Any] | list[int]:
    """Encode variable length integer.

    Returns the integer as a list of bytes,
    where the last byte is < 128.

    This is used for delta times and meta message payload
    length.
    """
    ...

def decode_variable_int(value): # -> Literal[0]:
    """Decode a list to a variable length integer.

    Does the opposite of encode_variable_int(value)
    """
    ...

def encode_string(string): # -> list[int]:
    ...

def decode_string(data): # -> str:
    ...

@contextmanager
def meta_charset(tmp_charset): # -> Generator[None, Any, None]:
    ...

def check_int(value, low, high): # -> None:
    ...

def check_str(value): # -> None:
    ...

class MetaSpec:
    def check(self, name, value): # -> None:
        ...
    


class MetaSpec_sequence_number(MetaSpec):
    type_byte = ...
    attributes = ...
    defaults = ...
    def decode(self, message, data): # -> None:
        ...
    
    def encode(self, message): # -> list[Any]:
        ...
    
    def check(self, name, value): # -> None:
        ...
    


class MetaSpec_text(MetaSpec):
    type_byte = ...
    attributes = ...
    defaults = ...
    def decode(self, message, data): # -> None:
        ...
    
    def encode(self, message): # -> list[int]:
        ...
    
    def check(self, name, value): # -> None:
        ...
    


class MetaSpec_copyright(MetaSpec_text):
    type_byte = ...


class MetaSpec_track_name(MetaSpec_text):
    type_byte = ...
    attributes = ...
    defaults = ...
    def decode(self, message, data): # -> None:
        ...
    
    def encode(self, message): # -> list[int]:
        ...
    


class MetaSpec_instrument_name(MetaSpec_track_name):
    type_byte = ...


class MetaSpec_lyrics(MetaSpec_text):
    type_byte = ...


class MetaSpec_marker(MetaSpec_text):
    type_byte = ...


class MetaSpec_cue_marker(MetaSpec_text):
    type_byte = ...


class MetaSpec_device_name(MetaSpec_track_name):
    type_byte = ...


class MetaSpec_channel_prefix(MetaSpec):
    type_byte = ...
    attributes = ...
    defaults = ...
    def decode(self, message, data): # -> None:
        ...
    
    def encode(self, message): # -> list[Any]:
        ...
    
    def check(self, name, value): # -> None:
        ...
    


class MetaSpec_midi_port(MetaSpec):
    type_byte = ...
    attributes = ...
    defaults = ...
    def decode(self, message, data): # -> None:
        ...
    
    def encode(self, message): # -> list[Any]:
        ...
    
    def check(self, name, value): # -> None:
        ...
    


class MetaSpec_end_of_track(MetaSpec):
    type_byte = ...
    attributes = ...
    defaults = ...
    def decode(self, message, data): # -> None:
        ...
    
    def encode(self, message): # -> list[Any]:
        ...
    


class MetaSpec_set_tempo(MetaSpec):
    type_byte = ...
    attributes = ...
    defaults = ...
    def decode(self, message, data): # -> None:
        ...
    
    def encode(self, message): # -> list[Any]:
        ...
    
    def check(self, name, value): # -> None:
        ...
    


class MetaSpec_smpte_offset(MetaSpec):
    type_byte = ...
    attributes = ...
    defaults = ...
    def decode(self, message, data): # -> None:
        ...
    
    def encode(self, message): # -> list[Any]:
        ...
    
    def check(self, name, value): # -> None:
        ...
    


class MetaSpec_time_signature(MetaSpec):
    type_byte = ...
    attributes = ...
    defaults = ...
    def decode(self, message, data): # -> None:
        ...
    
    def encode(self, message): # -> list[Any | int]:
        ...
    
    def check(self, name, value): # -> None:
        ...
    


class MetaSpec_key_signature(MetaSpec):
    type_byte = ...
    attributes = ...
    defaults = ...
    def decode(self, message, data): # -> None:
        ...
    
    def encode(self, message): # -> list[Any | int]:
        ...
    
    def check(self, name, value): # -> None:
        ...
    


class MetaSpec_sequencer_specific(MetaSpec):
    type_byte = ...
    attributes = ...
    defaults = ...
    def decode(self, message, data): # -> None:
        ...
    
    def encode(self, message): # -> list[Any]:
        ...
    


def add_meta_spec(klass): # -> None:
    ...

_META_SPECS = ...
_META_SPEC_BY_TYPE = ...
def build_meta_message(meta_type, data, delta=...): # -> MetaMessage | UnknownMetaMessage:
    ...

class MetaMessage(BaseMessage):
    is_meta = ...
    def __init__(self, type, skip_checks=..., **kwargs) -> None:
        ...
    
    def copy(self, **overrides): # -> Self:
        """Return a copy of the message

        Attributes will be overridden by the passed keyword arguments.
        Only message specific attributes can be overridden. The message
        type can not be changed.
        """
        ...
    
    __setattr__ = ...
    def bytes(self):
        ...
    
    @classmethod
    def from_bytes(cls, msg_bytes): # -> MetaMessage | UnknownMetaMessage:
        ...
    


class UnknownMetaMessage(MetaMessage):
    def __init__(self, type_byte, data=..., time=..., type=..., **kwargs) -> None:
        ...
    
    def __repr__(self): # -> str:
        ...
    
    def __setattr__(self, name, value): # -> None:
        ...
    
    def bytes(self): # -> list[int | Any]:
        ...
    


