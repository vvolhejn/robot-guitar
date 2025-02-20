import mido

with mido.open_input("New Port", virtual=True) as inport:
    for message in inport:
        print(message)
