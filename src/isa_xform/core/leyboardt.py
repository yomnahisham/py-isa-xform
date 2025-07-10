from pynput import keyboard

def on_press(key):
    try:
        print(f"Key {key.char} pressed")
    except AttributeError:
        print(f"Special key {key} pressed")

if __name__ == "__main__":
    with keyboard.Listener(on_press=on_press) as listener:
        listener.join()
