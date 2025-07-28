import ctypes
import time
import logging
import traceback
import argparse
import sys

#! THIS IS AN AUTOCLICKER I DEVELOPED MAINLY WITH HELP OF CHATGPT, I MADE IT ESPECIALLY TO EXPAND MY PYTHON KNOWLEDGE BEYOND THE BASIC AND TO INTRODUCE MYSELF TO HANDLE ERRORS, LOGGING, TRACEBACK AND ARGPARSING

logger = logging.getLogger()
logger.setLevel(logging.ERROR)
log_file = logging.FileHandler('autoclicker.log', mode='a')
log_file.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
logger.addHandler(log_file)

u32 = ctypes.windll.user32
GetAsyncKeyState = u32.GetAsyncKeyState
VkKeyScanW = u32.VkKeyScanW
GetKeyNameTextW = u32.GetKeyNameTextW
MapVirtualKeyW = u32.MapVirtualKeyW

is_key_pressed= lambda virtual_key: GetAsyncKeyState(virtual_key) & 0x8000 != 0

get_virtual_key = lambda key: (
    VkKeyScanW(ord(key)) & 0xFF if len(key) == 1 else (_ for _ in ()).throw(ValueError(f"Key '{key}' must be a single character."))
)

get_key_name= lambda virtual_key: (
    lambda _, l_param: (
        lambda buf: GetKeyNameTextW(l_param, buf, 64) and buf.value
    )(
        ctypes.create_unicode_buffer(64)
    )
)(
    MapVirtualKeyW(virtual_key, 0), MapVirtualKeyW(virtual_key, 0) << 16
)

# Detects rising edge (key just pressed this frame)
rising_detection = lambda curr, prev: (curr and not prev, curr)

def autoclick(timeout: float=50.0, VK_START: int=0x41, VK_PAUSE: int=0x42, VK_QUIT: int=0x43) -> None:
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

    # To prevent the start and the quitting at unintended moments
    VK_CTRL = 0x11

    MOUSEEVENTF_LEFTDOWN = 0x0002
    MOUSEEVENTF_LEFTUP = 0x0004

    # To prevent immediate re-trigger, the sleep duration is arbitrary, thus I choose a funny number
    SLEEPTIME = 0.069

    print("Press '{} + {}' to start/resume clicking, '{}' to pause, and '{} + {}' to quit.".format(get_key_name(VK_CTRL), get_key_name(VK_START), get_key_name(VK_PAUSE), get_key_name(VK_CTRL), get_key_name(VK_QUIT)))

    clicking = False
    start_state = pause_state = quit_state = False

    while True:

        check_start, start_state = rising_detection(is_key_pressed(VK_CTRL) and is_key_pressed(VK_START), start_state)
        if not clicking and check_start:
            print("Clicking started.", end="\r")
            clicking = True
            time.sleep(SLEEPTIME)

        check_pause, pause_state = rising_detection(is_key_pressed(VK_PAUSE), pause_state)
        if clicking and check_pause:
            print("Clicking paused.", end="\r")
            clicking = False
            time.sleep(SLEEPTIME)

        check_quit, quit_state = rising_detection(is_key_pressed(VK_CTRL) and is_key_pressed(VK_QUIT), quit_state)
        if check_quit:
            print("\nQuitting...")
            time.sleep(SLEEPTIME)
            break

        if clicking:
            u32.mouse_event(MOUSEEVENTF_LEFTDOWN | MOUSEEVENTF_LEFTUP, 0, 0, 0, 0) # the pipe operator cause both events to be sent simultaneously
            time.sleep(0.001*timeout)

        else:
            time.sleep(.2)


def get_parser ():
    parser = argparse.ArgumentParser()
    parser.add_argument("--timeout" , type=float, default=42.0, help="Sleep time in milliseconds between clicks.")
    parser.add_argument("--startkey", type=str, default='S', help="Virtual key to start/resume clicking.")
    parser.add_argument("--pausekey", type=str, default='P', help="Virtual key to pause clicking.")
    parser.add_argument("--quitkey" , type=str, default='Q', help="Virtual key to quit the autoclicker.")

    return parser

def main():
    """
    Starts the auto-clicker.

    This function does nothing but call `autoclick`, which is where all the actual
    auto-clicking logic happens.
    """

    ... if sys.platform == "win32" else (_ for _ in ()).throw(RuntimeError("This script is intended to be Windows OS only!"))

    try:
        parser = get_parser()
        args = parser.parse_args()
        logger.info(f"Parsed arguments: {vars(args)}")
        autoclick(timeout=args.timeout, VK_START=get_virtual_key(args.startkey), VK_PAUSE=get_virtual_key(args.pausekey), VK_QUIT=get_virtual_key(args.quitkey))

    except KeyboardInterrupt:
        print("\nInterrupted by keyboard!")

    except Exception as e:
        print(f"\n An exception occurred: {e}.")
        tb = traceback.extract_tb(e.__traceback__)
        if tb:
            filename, line, func, text = tb[-1]
            log_path = getattr(log_file, 'baseFilename', "something very unexpected happened at the point I can't even explain why there's not a log file.")
            print(f"File: {filename}, line no.: {line}.\nCheck the complete traceback at: {log_path}.\n")

        logger.error("An exception occurred!", exc_info=True)
        raise


if __name__ == "__main__":
    main()
