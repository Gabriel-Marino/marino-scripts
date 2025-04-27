import ctypes
import time

# Virtual-Key codes
VK_START = 0x53  # 'S'
VK_PAUSE = 0x50  # 'P'
VK_QUIT  = 0x51  # 'Q'

GetAsyncKeyState = ctypes.windll.user32.GetAsyncKeyState

is_key_pressed = lambda key: GetAsyncKeyState(key) & 0x8000 != 0

def autoClick(timeout: float) -> None:
    """
    Clicks the mouse at a regular interval, given in milliseconds (timeout argument),
    until the user presses the 'Q' key.

    The user can pause/resume the clicking by pressing the 'P' key.

    The function prints messages to the console to indicate the state of the
    autoclicker.

    The timeout argument is a float representing the number of milliseconds to wait
    before the next click.  This function uses the system's high-resolution
    timer, so the actual time slept will be very close to this value.

    The function blocks the calling thread until the user presses the 'Q' key.
    """

    print("Press 'S' to start/resume clicking, 'P' to pause, and 'Q' to quit.")

    clicking = False

    while True:
        if not clicking and is_key_pressed(VK_START):
            print("Clicking started.")
            clicking = True
            time.sleep(2*timeout/1000)  # prevent immediate re-trigger

        elif clicking and is_key_pressed(VK_PAUSE):
            print("Clicking paused.")
            clicking = False
            time.sleep(2*timeout/1000)

        elif is_key_pressed(VK_QUIT):
            print("Quitting...")
            time.sleep(2*timeout/1000)
            break

        if clicking:
            ctypes.windll.user32.mouse_event(0x0002 | 0x0004, 0, 0, 0, 0)
            time.sleep(timeout/1000)

        else:
            time.sleep(2*timeout/1000)  # just idle waiting


def main():
    """
    Starts the auto-clicker.

    This function does nothing but call `autoClick`, which is where all the actual
    auto-clicking logic happens.
    """

    autoClick(50)


if __name__ == "__main__":
    main()
