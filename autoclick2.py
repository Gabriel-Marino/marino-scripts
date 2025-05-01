import ctypes
import time

GetAsyncKeyState = ctypes.windll.user32.GetAsyncKeyState

is_key_pressed = lambda virtual_key: GetAsyncKeyState(virtual_key) & 0x8000 != 0

vk_to_key = lambda virtual_key: (
        lambda _, l_param: (
            lambda buf: ctypes.windll.user32.GetKeyNameTextW(l_param, buf, 64) and buf.value
        )(ctypes.create_unicode_buffer(64))
    )(ctypes.windll.user32.MapVirtualKeyW(virtual_key, 0), ctypes.windll.user32.MapVirtualKeyW(virtual_key, 0) << 16)

def autoClick(timeout: float=50.0, VK_START: int=0x41, VK_PAUSE: int=0x42, VK_QUIT: int=0x43) -> None:
    """
    Starts the auto-clicker loop.

    This function waits for a key-press event corresponding to the `VK_START` virtual key, and
    then starts auto-clicking. It will keep clicking until it receives a key-press event
    corresponding to the `VK_PAUSE` virtual key. It will then pause, and wait for the
    `VK_START` key to be pressed again to resume clicking. If the `VK_QUIT` key is pressed at
    any time, the auto-clicker will stop and return.

    The `timeout` parameter determines how many milliseconds to wait between each click.

    The `VK_START`, `VK_PAUSE`, and `VK_QUIT` parameters determine the virtual keys that
    correspond to the start, pause, and quit actions, respectively.

    :param timeout: milliseconds to wait between each click
    :param VK_START: virtual key to start/resume clicking
    :param VK_PAUSE: virtual key to pause clicking
    :param VK_QUIT: virtual key to quit auto-clicker
    """

    print("Press '{}' to start/resume clicking, '{}' to pause, and '{}' to quit.".format(vk_to_key(VK_START), vk_to_key(VK_PAUSE), vk_to_key(VK_QUIT)))

    clicking = False

    while True:
        if not clicking and is_key_pressed(VK_START):
            print("Clicking started.")
            clicking = True
            time.sleep(0.200)  # prevent immediate re-trigger

        elif clicking and is_key_pressed(VK_PAUSE):
            print("Clicking paused.")
            clicking = False
            time.sleep(0.200)

        elif is_key_pressed(VK_QUIT):
            print("Quitting...")
            time.sleep(0.200)
            break

        if clicking:
            ctypes.windll.user32.mouse_event(0x0002 | 0x0004, 0, 0, 0, 0)
            time.sleep(0.001*timeout)


def main():
    """
    Starts the auto-clicker.

    This function does nothing but call `autoClick`, which is where all the actual
    auto-clicking logic happens.
    """

    # Virtual-Key codes
    START = 0x67
    PAUSE = 0x68
    QUIT  = 0x69

    autoClick(VK_START=START, VK_PAUSE=PAUSE, VK_QUIT=QUIT)


if __name__ == "__main__":
    main()
