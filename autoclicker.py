import ctypes
import time
import logging
import traceback
import argparse
import sys
import os
import re
from typing import Callable

#! THIS IS AN AUTOCLICKER I DEVELOPED MAINLY WITH HELP OF CHATGPT, I MADE IT ESPECIALLY TO EXPAND MY PYTHON KNOWLEDGE BEYOND THE BASIC AND TO INTRODUCE MYSELF TO HANDLE ERRORS, LOGGING, TRACEBACK AND ARGPARSING

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
log_file = logging.FileHandler('autoclicker.log', mode='a')
log_file.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
logger.addHandler(log_file)

u32 = ctypes.windll.user32
GetAsyncKeyState = u32.GetAsyncKeyState
VkKeyScanW = u32.VkKeyScanW
GetKeyNameTextW = u32.GetKeyNameTextW
MapVirtualKeyW = u32.MapVirtualKeyW
mouse_event = u32.mouse_event

MOUSEEVENTF_LEFTDOWN = 0x0002
MOUSEEVENTF_LEFTUP = 0x0004
KEY_PRESS_MASK = 0x8000

IS_KEY_PRESSED: Callable[[int], bool] = lambda virtual_key: GetAsyncKeyState(virtual_key) & KEY_PRESS_MASK != 0

GET_VIRTUAL_KEY: Callable[[str], int] = lambda key: (
    VkKeyScanW(ord(key)) & 0xFF if len(key) == 1 else (_ for _ in ()).throw(ValueError(f"Key '{key}' must be a single character."))
)

GET_KEY_NAME: Callable[[int], str] = lambda virtual_key: (
    lambda _, l_param: (
        lambda buf: GetKeyNameTextW(l_param, buf, 64) and buf.value
    )(
        ctypes.create_unicode_buffer(64)
    )
)(
    MapVirtualKeyW(virtual_key, 0), MapVirtualKeyW(virtual_key, 0) << 16
)

# Detects rising edge (key just pressed this frame)
RISING_DETECTION: Callable[[bool, bool], list] = lambda curr, prev: (curr and not prev, curr)

def cleanup() -> None:
    """
    Performs cleanup operations by releasing the left mouse button, logging the cleanup event,
    shutting down the logging system, and printing a confirmation message.

    This function is typically called at the end of the program to ensure that resources
    related to mouse events and logging are properly released.
    """
    TEXT = "Resources are cleaned up."
    mouse_event(MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
    logger.info(TEXT)
    logging.shutdown()
    print(TEXT)

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

    # To prevent immediate re-trigger, the sleep duration is arbitrary, thus I choose a funny number
    DEBOUNCE_SLEEP_TIME = 0.069

    print(f"Press '{GET_KEY_NAME(VK_CTRL)} + {GET_KEY_NAME(VK_START)}' to start/resume clicking, '{GET_KEY_NAME(VK_PAUSE)}' to pause, and '{GET_KEY_NAME(VK_CTRL)} + {GET_KEY_NAME(VK_QUIT)}' to quit.")

    clicking = False
    start_state = pause_state = quit_state = False

    while True:

        start, start_state = RISING_DETECTION(IS_KEY_PRESSED(VK_CTRL) and IS_KEY_PRESSED(VK_START), start_state)
        if not clicking and start:
            print("Clicking started.", end="\r")
            clicking = True
            time.sleep(DEBOUNCE_SLEEP_TIME)

        pause, pause_state = RISING_DETECTION(IS_KEY_PRESSED(VK_PAUSE), pause_state)
        if clicking and pause:
            print("Clicking paused.", end="\r")
            clicking = False
            time.sleep(DEBOUNCE_SLEEP_TIME)

        quit, quit_state = RISING_DETECTION(IS_KEY_PRESSED(VK_CTRL) and IS_KEY_PRESSED(VK_QUIT), quit_state)
        if quit:
            print("\nQuitting...")
            time.sleep(DEBOUNCE_SLEEP_TIME)
            cleanup()
            break

        if clicking:
            # the pipe operator cause both events to be sent simultaneously
            mouse_event(MOUSEEVENTF_LEFTDOWN | MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
            time.sleep(0.001*timeout)

        else:
            time.sleep(.2)


def get_parser() -> object:
    """
    Creates and returns an argument parser for the autoclicker script.
    The parser supports the following command-line arguments:
        --timeout:   Sleep time in milliseconds between clicks (float, default: 42.0).
        --startkey:  Virtual key to start/resume clicking (str, default: 'S').
        --pausekey:  Virtual key to pause clicking (str, default: 'P').
        --quitkey:   Virtual key to quit the autoclicker (str, default: 'Q').
    Returns:
        argparse.ArgumentParser: Configured argument parser for the autoclicker.
    """
    parser = argparse.ArgumentParser(
        prog=re.sub(r'\.py$', '', os.path.basename(__file__)),
        usage="%(prog)s [options]",
        description="A simple auto-clicker script that allows you to automate mouse clicks.",
        epilog="Press 'Ctrl + StartKey' to start/resume clicking, 'PauseKey' to pause, and 'Ctrl + QuitKey' to quit."
    )
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
        autoclick(
            timeout=args.timeout,
            VK_START=GET_VIRTUAL_KEY(args.startkey),
            VK_PAUSE=GET_VIRTUAL_KEY(args.pausekey),
            VK_QUIT=GET_VIRTUAL_KEY(args.quitkey)
        )

    except KeyboardInterrupt:
        print("\nInterrupted by keyboard!")
        logger.info("Interrupted by user.")
        cleanup()

    except Exception as e:
        print(f"\n An exception occurred: {e}.")
        tb = traceback.extract_tb(e.__traceback__)
        if tb:
            filename, line, func, text = tb[-1]
            log_path = getattr(log_file, 'baseFilename', "something very unexpected happened at the point I can't even explain why there's not a log file.")
            print(f"File: {filename}, line no.: {line}.\nCheck the complete traceback at: {log_path}.\n")

        logger.error("An exception occurred!", exc_info=True)
        logging.shutdown()
        raise


if __name__ == "__main__":
    main()
