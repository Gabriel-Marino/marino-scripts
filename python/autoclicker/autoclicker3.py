import argparse
import ctypes
import logging
import os
import re
import sys
import threading
import time
import traceback

import ctypes.wintypes as w

from collections import Counter

class MOUSEINPUT(ctypes.Structure):

    _fields_ = [
        ("dx", w.LONG),
        ("dy", w.LONG),
        ("mouseData", w.DWORD),
        ("dwFlags", w.DWORD),
        ("time", w.DWORD),
        ("dwExtraInfo", ctypes.c_ulonglong)
    ]

class INPUTUNION(ctypes.Union):

    _fields_ = [
        ("mi", MOUSEINPUT)
    ]

class INPUT(ctypes.Structure):

    _fields_ = [
        ("type", w.DWORD),
        ("union", INPUTUNION)
    ]

class WindowsKeysHandler:

    u32 = ctypes.windll.user32
    GetAsyncKeyState = u32.GetAsyncKeyState
    VkKeyScanW = u32.VkKeyScanW
    GetKeyNameTextW = u32.GetKeyNameTextW
    MapVirtualKeyW = u32.MapVirtualKeyW
    send_input = u32.SendInput

    KEY_PRESS_MASK = 0x8000
    SHIFT_KEY_MASK = 0xFF

    MOUSE_INPUT = 0
    MOUSEEVENTF_LEFTDOWN = 0x0002
    MOUSEEVENTF_LEFTUP = 0x0004

    def is_key_pressed(self, virtual_key: int) -> bool:

        try:
            return self.GetAsyncKeyState(virtual_key) & self.KEY_PRESS_MASK != 0

        except ValueError:
            raise ValueError(f"Invalid virtual key code: {virtual_key}. Please provide a valid hexadecimal key code.")

    def get_virtual_key(self, key: str) -> int:

        if len(key) != 1:
            raise ValueError(f"Key '{key}' must be a single character.")
    
        return self.VkKeyScanW(ord(key)) & self.SHIFT_KEY_MASK

    def get_key_name(self, virtual_key: int) -> str:

        l_param = self.MapVirtualKeyW(virtual_key, 0) << 16
        buf = ctypes.create_unicode_buffer(64)

        if not self.GetKeyNameTextW(l_param, buf, 64):
            raise ValueError(f"Could not retrieve name for virtual key {virtual_key}.")
        
        return buf.value

    def mouse_send_input(self, dx: w.LONG, dy: w.LONG, data: w.DWORD, flags: w.DWORD, time: w.DWORD, extra_info: ctypes.c_ulonglong) -> int:

        input = INPUT()
        input.type = self.MOUSE_INPUT
        input.union.mi = MOUSEINPUT(
            dx=dx,
            dy=dy,
            mouseData=data,
            dwFlags=flags,
            time=time,
            dwExtraInfo=extra_info
        )

        return self.send_input(1, ctypes.byref(input), ctypes.sizeof(input))

    @staticmethod
    def rising_detection(curr: bool, prev: bool, safemode: bool, safekeyispressed: bool) -> list[bool]:

        if not safemode:
            return curr and not prev, curr

        elif safekeyispressed:
            return curr and not prev, curr

        return False, prev

class ParserHandler(WindowsKeysHandler):

    DEFAULT_TIMEOUT = 42.0
    DEFAULT_START_KEY = 'S'
    DEFAULT_PAUSE_KEY = 'P'
    DEFAULT_QUIT_KEY = 'Q'
    DEFAULT_SAFE_KEY = 0x12  # Virtual key code for generic Alt key,

    def __init__(self):

        super().__init__()

        self.parser = argparse.ArgumentParser(
            prog=os.path.relpath(__file__),
            usage="%(prog)s [options]",
            description="A simple auto-clicker script that allows you to automate mouse clicks.",
            epilog="Press 'StartKey' to start/resume clicking, 'PauseKey' to pause, and 'QuitKey' to quit.",
            formatter_class=argparse.RawTextHelpFormatter,
            allow_abbrev=False
        )
        self._setup_args()

    def _setup_args(self):

        ARGS=(
            {"short": 'to', "name": 'timeout' , "type": float, "d_val": self.DEFAULT_TIMEOUT, "hint": f"Sleep time in milliseconds between clicks. Default: '{self.DEFAULT_TIMEOUT}'"},
            {"short": 'sk', "name": 'startkey', "type": str, "d_val": self.DEFAULT_START_KEY, "hint": f"Virtual key to start/resume clicking. Default: '{self.DEFAULT_START_KEY}'"},
            {"short": 'pk', "name": 'pausekey', "type": str, "d_val": self.DEFAULT_PAUSE_KEY, "hint": f"Virtual key to pause clicking. Default: '{self.DEFAULT_PAUSE_KEY}'"},
            {"short": 'qk', "name": 'quitkey' , "type": str, "d_val": self.DEFAULT_QUIT_KEY, "hint": f"Virtual key to quit the autoclicker. Default: '{self.DEFAULT_QUIT_KEY}'"},
            {"short": 'sf', "name": 'safekey' , "type": self._hexToInt, "d_val": self.DEFAULT_SAFE_KEY, "hint": f"Virtual key to use in safe mode. Default: 0x12 ({self.get_key_name(self.DEFAULT_SAFE_KEY)})"}
        )

        self.parser.add_argument('--no-safemode', dest='safemode', action='store_false', help=f"Disable safe mode. Safe mode is used to prevent unintended behavior, requiring to the safe key to be held to start or quit the script")
        self.parser.add_argument('--allow-duplicates', dest='duplicates', action='store_true', help="Allow using the same key for multiple actions (not recommended)")

        for arg in ARGS:
            self.parser.add_argument(f"-{arg['short']}", f"--{arg['name']}", type=arg['type'], default=arg['d_val'], help=arg['hint'])

    def get_parser(self) -> argparse.ArgumentParser:

        return self.parser

    @staticmethod
    def _hexToInt(hex) -> int:

        if isinstance(hex, int):
            return hex

        try:
            return int(hex, 16)

        except ValueError:
            raise argparse.ArgumentTypeError(f"Invalid hexadecimal value: {hex}. Please provide a valid hexadecimal string or integer.")

class LoggingHandler(ParserHandler):

    def __init__(self):

        super().__init__()

        self.need_cleanup = True
        self.logger = logging.getLogger()
        self.logger.setLevel(logging.DEBUG)
        self.log_file = logging.FileHandler(re.sub(r'\.py$', '.log', os.path.relpath(__file__)), mode='a')
        self.log_file.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        self.logger.addHandler(self.log_file)

class Autoclicker(LoggingHandler):

    DEBOUNCE_SLEEP_TIME = 0.069

    def __init__(self) -> None:

        super().__init__()

        self.click_thread = None
        self.clicking_event = threading.Event()
        self.quit_event = threading.Event()

        self.timeout = 42.0
        self.start_key = 0x41
        self.pause_key = 0x42
        self.quit_key = 0x43
        self.safe_mode = True
        self.safe_key = 0x12 # Virtual key code for generic Alt key, used for safe mode checks.
        self.start_state = self.pause_state = self.quit_state = False

    def setup(self, timeout: float, start_key: int, pause_key: int, quit_key: int, safe_key: int, safemode: bool, allow_duplicate: bool = False) -> None:

        self.timeout = timeout
        self.start_key = start_key
        self.pause_key = pause_key
        self.quit_key = quit_key
        self.safe_key = safe_key
        self.safe_mode = safemode

        if not timeout > 0:
            raise ValueError(f'{self.timeout} is not a valid value. Timeout must be a positive real number (unsigned float). And it is advised to be greater than 10ms')

        if any([x for _, x in Counter([value for key, value in self.__dict__.items() if key.endswith('_key')]).items() if x != 1]) and not allow_duplicate:
            raise ValueError('It is not advised to use the same key for two different actions')

    def run(self) -> None:

        self.click_thread = threading.Thread(target=self._click_loop)
        self.click_thread.start()

        print(f"Safemode is enabled. Press the safe key '{self.get_key_name(self.safe_key)}' to use the start and quit keys.") if self.safe_mode else None
        print(f"Press '{self.get_key_name(self.start_key)}' to start/resume clicking, '{self.get_key_name(self.pause_key)}' to pause, and '{self.get_key_name(self.quit_key)}' to quit.")

        while not self.quit_event.is_set():
            start_edge, self.start_state = self.rising_detection(self.is_key_pressed(self.start_key), self.start_state, self.safe_mode, self.is_key_pressed(self.safe_key))
            if not self.clicking_event.is_set() and start_edge:
                self._start()

            # I meant the safemode to only prevent unintended starting and quitting, not pausing, so the pause key gets True in the safekeyispressed argument regardless of the safemode state.
            pause_edge, self.pause_state = self.rising_detection(self.is_key_pressed(self.pause_key), self.pause_state, self.safe_mode, True)
            if self.clicking_event.is_set() and pause_edge:
                self._pause()

            quit_edge, self.quit_state = self.rising_detection(self.is_key_pressed(self.quit_key), self.quit_state, self.safe_mode, self.is_key_pressed(self.safe_key))
            if quit_edge:
                self._quit()
                break

        time.sleep(self.DEBOUNCE_SLEEP_TIME)
        if self.click_thread.is_alive():
            self.click_thread.join()

    def _click_loop(self) -> None:

        while not self.quit_event.is_set():
            if self.clicking_event.is_set():
                self.mouse_send_input(0, 0, 0, self.MOUSEEVENTF_LEFTDOWN | self.MOUSEEVENTF_LEFTUP, 0, 0)
                time.sleep(0.001 * self.timeout)
            else:
                time.sleep(0.2)

    def _start(self) -> None:

        print("Clicking started.", end="\r")
        self.clicking_event.set()
        time.sleep(self.DEBOUNCE_SLEEP_TIME)

    def _pause(self) -> None:

        print("Clicking paused.", end="\r")
        self.clicking_event.clear()
        time.sleep(self.DEBOUNCE_SLEEP_TIME)

    def _quit(self) -> None:

        self.clicking_event.clear()
        self.quit_event.set()
        print("\nQuitting...")
        time.sleep(self.DEBOUNCE_SLEEP_TIME)
        self.cleanup()

    def cleanup(self) -> None:

        if not self.need_cleanup:
            return
        
        if self.click_thread and self.click_thread.is_alive():
            self.click_thread.join()

        self.mouse_send_input(0, 0, 0, self.MOUSEEVENTF_LEFTUP, 0, 0)

        self.parser.exit()

        TEXT = "Resources are cleaned up."

        self.logger.info(TEXT)
        logging.shutdown()

        print(TEXT)

        self.need_cleanup = False

def main() -> None:

    autoclicker = None

    try:
        autoclicker = Autoclicker()

        parser = autoclicker.get_parser()
        args = parser.parse_args()
        autoclicker.logger.info(f"Parsed arguments: {vars(args)}")
        autoclicker.setup(
            timeout=args.timeout,
            start_key=autoclicker.get_virtual_key(args.startkey),
            pause_key=autoclicker.get_virtual_key(args.pausekey),
            quit_key=autoclicker.get_virtual_key(args.quitkey),
            safe_key=args.safekey,
            safemode=args.safemode,
            allow_duplicate=args.duplicates
        )
        autoclicker.run()

    except KeyboardInterrupt:
        print("\nInterrupted by keyboard!")
        autoclicker.logger.info("Interrupted by keyboard!")
        autoclicker.cleanup()

    except Exception as e:
        print(f"\n An exception occurred: {e}.")
        tb = traceback.extract_tb(e.__traceback__)
        if autoclicker is not None:
            if tb:
                filename, line, func, text = tb[-1]
                log_path = getattr(autoclicker.log_file, 'baseFilename', "something very unexpected happened at the point I can't even explain why there's not a log file.")
                print(f"File: {filename}, line no.: {line}.\nCheck the complete traceback at: {log_path}.\n")

            autoclicker.logger.error("An exception occurred!", exc_info=True)
            logging.shutdown()

        else:
            print("Autoclicker was not instantiated.")

        raise

    finally:
        if autoclicker is not None:
            autoclicker.cleanup()

if __name__ == "__main__":
    if sys.platform != "win32":
        raise RuntimeError("This script is designed to run on Windows only!")

    os.system('cls')
    main()
