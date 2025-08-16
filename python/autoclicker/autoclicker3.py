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
from msvcrt import kbhit, getch

class MOUSEINPUT(ctypes.Structure):

    _fields_ = [
        ("dx", w.LONG),
        ("dy", w.LONG),
        ("mouseData", w.DWORD),
        ("dwFlags", w.DWORD),
        ("time", w.DWORD),
        ("dwExtraInfo", ctypes.c_ulonglong)
    ]

class INPUT(ctypes.Structure):
    class _INPUT_UNION(ctypes.Union):
        _fields_ = [("mi", MOUSEINPUT)]

    _anonymous_ = ("u",)
    _fields_ = [("type", w.DWORD), ("u", _INPUT_UNION)]


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

        vk = self.VkKeyScanW(ord(key)) & self.SHIFT_KEY_MASK

        if vk == self.SHIFT_KEY_MASK:
            raise ValueError(f"Unable to find virtual key for '{key}'")

        return vk

    def get_key_name(self, virtual_key: int) -> str:

        l_param = self.MapVirtualKeyW(virtual_key, 0) << 16
        buf = ctypes.create_unicode_buffer(64)

        if not self.GetKeyNameTextW(l_param, buf, 64):
            raise ValueError(f"Could not retrieve name for virtual key {virtual_key}.")
        
        return buf.value

    def mouse_send_input(self, dx: w.LONG, dy: w.LONG, data: w.DWORD, flags: w.DWORD, time: w.DWORD, extra_info: ctypes.c_ulonglong) -> int:

        input = INPUT()
        input.type = self.MOUSE_INPUT
        input.mi = MOUSEINPUT(
            dx=dx,
            dy=dy,
            mouseData=data,
            dwFlags=flags,
            time=time,
            dwExtraInfo=extra_info
        )

        return self.send_input(1, ctypes.byref(input), ctypes.sizeof(input))

    @staticmethod
    def rising_detection(curr: bool, prev: bool, safemode: bool, safekeyispressed: bool) -> tuple[bool, bool]:

        if not safemode:
            return curr and not prev, curr

        elif safekeyispressed:
            return curr and not prev, curr

        return False, prev

class ParserHandler(WindowsKeysHandler):

    DEFAULT_CPS = 24.0
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

        dev_group = self.parser.add_argument_group('Developer settings')
        autoclicker_group = self.parser.add_argument_group('Autoclicker parameters')

        ARGS=(
            {"short": 'sk', "name": 'startkey', "type": str, "d_val": self.DEFAULT_START_KEY, "hint": f"Virtual key to start/resume clicking. Default: '{self.DEFAULT_START_KEY}'"},
            {"short": 'pk', "name": 'pausekey', "type": str, "d_val": self.DEFAULT_PAUSE_KEY, "hint": f"Virtual key to pause clicking. Default: '{self.DEFAULT_PAUSE_KEY}'"},
            {"short": 'qk', "name": 'quitkey' , "type": str, "d_val": self.DEFAULT_QUIT_KEY, "hint": f"Virtual key to quit the autoclicker. Default: '{self.DEFAULT_QUIT_KEY}'"},
            {"short": 'sf', "name": 'safekey' , "type": self._hexToInt, "d_val": self.DEFAULT_SAFE_KEY, "hint": f"Virtual key to use in safe mode. Default: 0x12 ({self.get_key_name(self.DEFAULT_SAFE_KEY)})"}
        )

        dev_group.add_argument('--debug', action='store_true')
        dev_group.add_argument('--no-safemode', dest='safemode', action='store_false', help=f"Disable safe mode. When enabled, the safe key must be held to start or quit the script to prevent unintended behavior")
        dev_group.add_argument('--no-cautions', dest='cautions', action='store_false', help="Disable cautions which can lead to unintended behaviour")

        autoclicker_group.add_argument('-cps', '--clicks-per-second', dest='clickspersec', type=float, default=self.DEFAULT_CPS, help=f"Target clicks per second (CPS). Default: '{self.DEFAULT_CPS}cps'")
        for arg in ARGS:
            autoclicker_group.add_argument(f"-{arg['short']}", f"--{arg['name']}", type=arg['type'], default=arg['d_val'], help=arg['hint'])

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

    def debug(self):
        console = logging.StreamHandler(sys.stderr)
        console.setLevel(logging.DEBUG)
        console.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        self.logger.addHandler(console)

class Autoclicker(LoggingHandler):

    DEBOUNCE_SLEEP_TIME = 0.069

    def __init__(self) -> None:

        super().__init__()

        self.click_thread = None
        self.clicking_event = threading.Event()
        self.quit_event = threading.Event()

        self.clickspersec = 42.0
        self.start_key = 0x41
        self.pause_key = 0x42
        self.quit_key = 0x43
        self.safe_mode = True
        self.safe_key = 0x12 # Virtual key code for generic Alt key, used for safe mode checks.
        self.start_state = self.pause_state = self.quit_state = False

    def setup(self, clickspersec: float, start_key: int, pause_key: int, quit_key: int, safe_key: int, safemode: bool, caution_mode: bool = True) -> None:

        self.clickspersec = clickspersec
        self.start_key = start_key
        self.pause_key = pause_key
        self.quit_key = quit_key
        self.safe_key = safe_key
        self.safe_mode = safemode

        allow_duplicate = False
        allow_cps_over_500 = False
        if not caution_mode:

            print(f"You are disabling the pre-programed cautions. The cautions are intended to prevent unintended behaviors. Press Enter to continue or {self.get_key_name(self.quit_key)} to quit")
            while True:

                if kbhit():

                    try:
                        key = getch().decode(errors='ignore').lower()
                        if key == '\r':
                            allow_duplicate = True
                            allow_cps_over_500 = True
                            return

                        elif key == chr(self.quit_key).lower():
                            self._quit()

                    except Exception as e:
                        print(f'Error: {e}')

        if not clickspersec > 0:
            raise ValueError(f'{self.clickspersec} is not a valid value. clicks per second must be a positive real number (unsigned float)')

        if not allow_cps_over_500 and clickspersec > 500:
            raise ValueError(f"{self.clickspersec} is too big, Python don't hand well values under 2ms inside timeout")

        keys = [value for key, value in self.__dict__.items() if key.endswith('_key')]
        duplicates = any([value for _, value in Counter(keys).items() if value != 1])
        if not allow_duplicate and duplicates:
            raise ValueError('It is not advised to use the same key for two different actions')

    def run(self, fun: callable, **fun_args) -> None:

        self.click_thread = threading.Thread(target=self._click_loop, args=(fun, fun_args))
        self.click_thread.start()

        print(f"Safemode is enabled. Press the safe key '{self.get_key_name(self.safe_key)}' to use the start and quit keys.") if self.safe_mode else None
        print(f"Press '{self.get_key_name(self.start_key)}' to start/resume clicking, '{self.get_key_name(self.pause_key)}' to pause, and '{self.get_key_name(self.quit_key)}' to quit. CPS: {self.clickspersec}/sec")

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

    def _click_loop(self, fun: callable, fun_args: dict) -> None:

        while not self.quit_event.is_set():
            if self.clicking_event.is_set():
                fun(**fun_args)
                time.sleep(1/self.clickspersec)
            else:
                time.sleep(0.2)

    def _start(self) -> None:

        print("Clicking started.", end="\r", flush=True)
        self.clicking_event.set()
        time.sleep(self.DEBOUNCE_SLEEP_TIME)

    def _pause(self) -> None:

        print("Clicking paused.", end="\r", flush=True)
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

        if args.debug:
            autoclicker.debug()

        autoclicker.setup(
            clickspersec=args.clickspersec,
            start_key=autoclicker.get_virtual_key(args.startkey),
            pause_key=autoclicker.get_virtual_key(args.pausekey),
            quit_key=autoclicker.get_virtual_key(args.quitkey),
            safe_key=args.safekey,
            safemode=args.safemode,
            caution_mode=args.cautions
        )
        autoclicker.run(autoclicker.mouse_send_input, dx=0, dy=0, data=0, flags=autoclicker.MOUSEEVENTF_LEFTDOWN | autoclicker.MOUSEEVENTF_LEFTUP, time=0, extra_info=0)

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

    os.system('cls' if os.name == 'nt' else 'clear')
    main()
