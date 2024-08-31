import mido


def find_midi_input() -> str:
    substring = "Launchkey Mini LK Mini MIDI"
    for name in mido.get_input_names():
        if substring in name:
            return name

    raise OSError(
        f"Could not open MIDI input port matching {repr(substring)}. "
        f"Available ports: {mido.get_input_names()}"
    )
