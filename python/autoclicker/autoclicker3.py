import argparse
import ctypes as ct
import ctypes.wintypes as wt
import logging
import os
import re
import sys
import threading
import time
import traceback

from collections import Counter
from msvcrt import kbhit, getch
from shutil import get_terminal_size
from typing import Callable

class KEYBDHOOK(ct.Structure):
    """
    Represents a keyboard hook structure for simulating keyboard input events.

    Attributes:
        wVk (wt.WORD): Virtual-key code of the key.
        wScan (wt.WORD): Hardware scan code of the key.
        dwFlags (wt.DWORD): Flags specifying various aspects of keyboard event (e.g., key up/down).
        time (wt.DWORD): Timestamp for the event, in milliseconds.
        dwExtraInfo (ct.c_ulonglong): Additional information associated with the keystroke.
    """
    _fields_ = [
        ("wVk", wt.WORD),
        ("wScan", wt.WORD),
        ("dwFlags", wt.DWORD),
        ("time", wt.DWORD),
        ("dwExtraInfo", ct.c_ulonglong)
    ]

class MOUSEHOOK(ct.Structure):
    """
    MOUSEHOOK is a ctypes Structure representing mouse event data.
    Attributes:
        dx (wt.LONG): The x-coordinate delta of the mouse event.
        dy (wt.LONG): The y-coordinate delta of the mouse event.
        mouseData (wt.DWORD): Additional mouse event data (e.g., wheel movement).
        dwFlags (wt.DWORD): Flags specifying various aspects of the mouse event.
        time (wt.DWORD): Timestamp for the event, in milliseconds.
        dwExtraInfo (ct.c_ulonglong): Extra information associated with the event.
    """

    _fields_ = [
        ("dx", wt.LONG),
        ("dy", wt.LONG),
        ("mouseData", wt.DWORD),
        ("dwFlags", wt.DWORD),
        ("time", wt.DWORD),
        ("dwExtraInfo", ct.c_ulonglong)
    ]

class INPUT(ct.Structure):
    """
    Represents a Windows INPUT structure for synthesizing input events.
    Attributes:
        type (wt.DWORD): Specifies the type of input (mouse, keyboard, or hardware).
        u (_INPUT_UNION): Anonymous union containing the input data for mouse (mi), keyboard (ki), or hardware.
    Inner Classes:
        _INPUT_UNION (ct.Union): Union holding the specific input structure:
            mi (MOUSEHOOK): Mouse input data.
            ki (KEYBDHOOK): Keyboard input data.
    Note:
        This structure is typically used with Windows API functions to simulate input events.
    """

    class _INPUT_UNION(ct.Union):

        _fields_ = [
            ("mi", MOUSEHOOK),
            ("ki", KEYBDHOOK),
        ]

    _anonymous_ = ("u",)
    _fields_ = [
        ("type", wt.DWORD),
        ("u", _INPUT_UNION)
    ]

class WindowsKeysHandler:
    """
    WindowsKeysHandler provides a set of utilities for handling keyboard and mouse input events on Windows systems using ctypes.
    Attributes:
        u32: Reference to the user32 DLL.
        GetAsyncKeyState: Function to get the state of a key.
        VkKeyScanW: Function to get the virtual key code for a character.
        GetKeyNameTextW: Function to get the name of a key from its virtual key code.
        MapVirtualKeyW: Function to map virtual key codes to scan codes.
        SendInput: Function to simulate input events.
        KEY_PRESS_MASK: Mask to check if a key is pressed.
        SHIFT_KEY_MASK: Mask for shift key operations.
        ESC_KEY: Virtual key code for the Escape key.
        MOUSE_INPUT: Input type for mouse events.
        KEYBD_INPUT: Input type for keyboard events.
        KEYBDEVENTF_KEYDOWN: Flag for key down event.
        KEYBDEVENTF_KEYUP: Flag for key up event.
        MOUSEEVENTF_LEFTDOWN: Flag for left mouse button down event.
        MOUSEEVENTF_LEFTUP: Flag for left mouse button up event.
        KEYEVENTF_SCANCODE: Flag for scan code event.
    Classes:
        IsKeyPressedWrapper:
            Wrapper for key press state, supporting double-click detection.
    Methods:
        is_key_pressed(virtual_key: int) -> IsKeyPressedWrapper:
            Returns a wrapper indicating whether the specified virtual key is currently pressed.
        get_virtual_key(key: str) -> int:
            Returns the virtual key code for a given single alphanumeric character.
        get_key_name(virtual_key: int) -> str:
            Returns the human-readable name of a key given its virtual key code.
        mouse_SendInput(flags, dx=0, dy=0, data=0, time=0, extra_info=0) -> int:
            Simulates a mouse input event with the specified parameters.
        keyboard_SendInput(flags, vk=0, scan=None, time=0, extra_info=0) -> int:
            Simulates a keyboard input event with the specified parameters.
        rising_detection(curr: bool, prev: bool, safemode: bool, safekeyispressed: bool) -> tuple[bool, bool]:
            Detects a rising edge (key press event) with optional safemode logic.
    """

    u32 = ct.windll.user32
    GetAsyncKeyState = u32.GetAsyncKeyState
    VkKeyScanW = u32.VkKeyScanW
    GetKeyNameTextW = u32.GetKeyNameTextW
    MapVirtualKeyW = u32.MapVirtualKeyW
    SendInput = u32.SendInput

    KEY_PRESS_MASK = 0x8000
    SHIFT_KEY_MASK = 0xFF
    ESC_KEY = 0x1B

    MOUSE_INPUT = 0
    KEYBD_INPUT = 1
    KEYBDEVENTF_KEYDOWN = 0x0000
    KEYBDEVENTF_KEYUP = 0x0002
    MOUSEEVENTF_LEFTDOWN = 0x0002
    MOUSEEVENTF_LEFTUP = 0x0004
    KEYEVENTF_SCANCODE = 0x0008

    class IsKeyPressedWrapper:
        _last_time_pressed = {}
        _last_state = {}
        _double_click_interval = 0.5

        def __init__(self, vk: int, is_pressed: bool):
            self.virtual_key = vk
            self.is_pressed = is_pressed

        def __bool__(self):
            """
            Return True if the button is pressed, otherwise False.

            This method allows instances of the class to be evaluated in boolean contexts,
            such as in conditional statements. It returns the value of the 'is_pressed' attribute.
            """
            return self.is_pressed
        
        def is_double_click(self) -> bool:
            """
            Determines whether the current key press event qualifies as a double-click.
            A double-click is detected if the key is pressed twice within a specified interval (`_double_click_interval`).
            The method checks the previous state of the key and the time elapsed since the last press.
            Returns:
                bool: True if the key press is considered a double-click, False otherwise.
            """
            now = time.time()

            prev_state = self._last_state.get(self.virtual_key, False)
            self._last_state[self.virtual_key] = self.is_pressed
            if self.is_pressed and not prev_state:
                last_time = self._last_time_pressed.get(self.virtual_key, 0)
                self._last_time_pressed[self.virtual_key] = now

                return (now - last_time) <= self._double_click_interval
            
            return False

    def is_key_pressed(self, virtual_key: int) -> 'IsKeyPressedWrapper':
        """
        Checks if a specific virtual key is currently pressed.
        Args:
            virtual_key (int): The virtual key code to check (usually in hexadecimal).
        Returns:
            IsKeyPressedWrapper: An instance containing the key code and its pressed state (True if pressed, False otherwise).
        Raises:
            ValueError: If the provided virtual key code is invalid.
        Example:
            is_pressed = self.is_key_pressed(0x41)  # Checks if 'A' key is pressed
        """

        try:
            return self.IsKeyPressedWrapper(virtual_key, self.GetAsyncKeyState(virtual_key) & self.KEY_PRESS_MASK != 0)

        except ValueError:
            raise ValueError(f"Invalid virtual key code: {virtual_key}. Please provide a valid hexadecimal key code")

    def get_virtual_key(self, key: str) -> int:
        """
        Returns the virtual key code for a given single alphanumeric character.
        Args:
            key (str): A single printable alphanumeric character.
        Returns:
            int: The virtual key code corresponding to the given character.
        Raises:
            ValueError: If the input is not a single character, not printable, not alphanumeric,
                        or if the virtual key code cannot be found.
        """

        if len(key) != 1:
            raise ValueError(f"Key '{key}' must be a single character")

        if not key.isalnum() or not key.isprintable():
            raise ValueError(f"'{key}' is not a valid printable alphanumeric character")

        vk = self.VkKeyScanW(ord(key)) & self.SHIFT_KEY_MASK

        if vk == self.SHIFT_KEY_MASK:
            raise ValueError(f"Unable to find virtual key for '{key}'")

        return vk

    def get_key_name(self, virtual_key: int) -> str:
        """
        Retrieves the human-readable name of a virtual key code.
        Args:
            virtual_key (int): The virtual key code to look up.
        Returns:
            str: The name of the key corresponding to the given virtual key code.
        Raises:
            ValueError: If the key name cannot be retrieved for the specified virtual key code.
        """

        l_param = self.MapVirtualKeyW(virtual_key, 0) << 16
        buf = ct.create_unicode_buffer(64)

        if not self.GetKeyNameTextW(l_param, buf, 64):
            raise ValueError(f"Could not retrieve name for virtual key {virtual_key}.")
        
        return buf.value

    def mouse_SendInput(self, flags: wt.DWORD, dx: wt.LONG=0, dy: wt.LONG=0, data: wt.DWORD=0, time: wt.DWORD=0, extra_info: ct.c_ulonglong=0) -> int:
        """
        Sends a mouse input event using the Windows SendInput API.
        Parameters:
            flags (wt.DWORD): Specifies various aspects of mouse motion and button clicks.
            dx (wt.LONG, optional): The absolute position or relative motion in the X direction. Defaults to 0.
            dy (wt.LONG, optional): The absolute position or relative motion in the Y direction. Defaults to 0.
            data (wt.DWORD, optional): Additional data associated with the mouse event (e.g., mouse wheel movement). Defaults to 0.
            time (wt.DWORD, optional): Timestamp for the event, in milliseconds. Defaults to 0.
            extra_info (ct.c_ulonglong, optional): Additional information associated with the event. Defaults to 0.
        Returns:
            int: The number of input events successfully inserted into the input stream.
        """

        input = INPUT()
        input.type = self.MOUSE_INPUT
        input.mi = MOUSEHOOK(
            dx=dx,
            dy=dy,
            mouseData=data,
            dwFlags=flags,
            time=time,
            dwExtraInfo=extra_info
        )

        return self.SendInput(1, ct.byref(input), ct.sizeof(input))

    def keyboard_SendInput(self, flags: wt.DWORD, vk: wt.WORD=0, scan: wt.WORD=None, time: wt.DWORD=0, extra_info: ct.c_ulonglong=0) -> int:
        """
        Sends a keyboard input event using the Windows SendInput API.
        Args:
            flags (wt.DWORD): Flags specifying various aspects of the keyboard event (e.g., key up/down).
            vk (wt.WORD, optional): Virtual-key code of the key to simulate. Defaults to 0.
            scan (wt.WORD, optional): Hardware scan code of the key. If None and vk is provided, it will be mapped automatically. Defaults to None.
            time (wt.DWORD, optional): Timestamp for the event, in milliseconds. Defaults to 0.
            extra_info (ct.c_ulonglong, optional): Additional data associated with the event. Defaults to 0.
        Returns:
            int: The number of input events successfully inserted into the input stream.
        """

        if scan is None and vk != 0:
            scan = self.MapVirtualKeyW(vk, 0)

        input = INPUT()
        input.type = self.KEYBD_INPUT
        input.ki = KEYBDHOOK(
            wVk=vk,
            wScan=scan,
            dwFlags=flags,
            time=time,
            dwExtraInfo=extra_info
        )

        return self.SendInput(1, ct.byref(input), ct.sizeof(input))

    @staticmethod
    def rising_detection(curr: bool, prev: bool, safemode: bool, safekeyispressed: bool) -> tuple[bool, bool]:
        """
        Detects a rising edge in a boolean signal, with optional safemode and safekey logic.
        Args:
            curr (bool): The current state of the signal.
            prev (bool): The previous state of the signal.
            safemode (bool): If True, enables safemode logic.
            safekeyispressed (bool): If True, allows detection even in safemode.
        Returns:
            tuple[bool, bool]: 
                - The first element is True if a rising edge is detected (curr is True and prev is False), otherwise False.
                - The second element is the updated previous state (usually curr or prev depending on safemode).
        """

        if not safemode:
            return curr and not prev, curr

        elif safekeyispressed:
            return curr and not prev, curr

        return False, prev

class ParserHandler(WindowsKeysHandler):
    """
    Handles command-line argument parsing for the autoclicker script, extending WindowsKeysHandler.
    This class sets up an argparse.ArgumentParser with options for developer settings and autoclicker parameters,
    including keys for starting, pausing, quitting, and safe mode operation. It provides default values and
    descriptions for each argument, and includes utility methods for argument parsing and hexadecimal conversion.
    Attributes:
        DEFAULT_CPS (float): Default clicks per second.
        DEFAULT_START_KEY (str): Default key to start/resume clicking.
        DEFAULT_PAUSE_KEY (str): Default key to pause clicking.
        DEFAULT_QUIT_KEY (str): Default key to quit the autoclicker.
        DEFAULT_SAFE_KEY (int): Default virtual key code for safe mode (Alt key).
    Methods:
        __init__():
            Initializes the parser and sets up command-line arguments.
        _setup_args():
            Adds developer and autoclicker argument groups to the parser.
        get_parser() -> argparse.ArgumentParser:
            Returns the configured argument parser.
        _hexToInt(hex) -> int:
            Converts a hexadecimal string or integer to an integer, raising an error for invalid input.
    """

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
            description="A simple auto-clicker script that automates clicks.",
            epilog="Press the 'StartKey' to start or resume clicking, 'PauseKey' to pause, and 'QuitKey' to quit.\nAs fallback options, you can use Ctrl+C or double-press the ESC key to stop the script.",
            formatter_class=argparse.RawTextHelpFormatter,
            allow_abbrev=False
        )
        self._setup_args()

    def _setup_args(self):
        """
        Configures command-line argument parsing for the autoclicker application.
        This method sets up two argument groups:
        - Developer settings: Includes options for debugging, disabling safe mode, and disabling cautions.
        - Autoclicker parameters: Includes options for setting the start, pause, quit, and safe keys, as well as the target clicks per second (CPS).
        Arguments added:
            --debug: Enables debug mode.
            --no-safemode: Disables safe mode, allowing the script to start/quit without holding the safe key.
            --no-cautions: Disables caution prompts, which may lead to unintended behavior.
            -cps / --clicks-per-second: Sets the target CPS (float).
            -sk / --startkey: Sets the virtual key to start/resume clicking (string).
            -pk / --pausekey: Sets the virtual key to pause clicking (string).
            -qk / --quitkey: Sets the virtual key to quit the autoclicker (string).
            -sf / --safekey: Sets the virtual key for safe mode (hexadecimal integer).
        Default values and help messages are provided for each argument.
        """

        dev_group = self.parser.add_argument_group('Developer settings')
        autoclicker_group = self.parser.add_argument_group('Autoclicker parameters')

        dev_group.add_argument('--debug', action='store_true')
        dev_group.add_argument('--no-safemode', dest='safemode', action='store_false', help=f"Disable safe mode. When enabled, the safe key must be held to start or quit the script to prevent unintended behavior")
        dev_group.add_argument('--no-cautions', dest='cautions', action='store_false', help="Disable cautions which can lead to unintended behaviour")

        ARGS=(
            {"short": 'sk', "name": 'startkey', "type": str, "d_val": self.DEFAULT_START_KEY, "hint": f"Virtual key to start/resume clicking. Default: '{self.DEFAULT_START_KEY}'"},
            {"short": 'pk', "name": 'pausekey', "type": str, "d_val": self.DEFAULT_PAUSE_KEY, "hint": f"Virtual key to pause clicking. Default: '{self.DEFAULT_PAUSE_KEY}'"},
            {"short": 'qk', "name": 'quitkey' , "type": str, "d_val": self.DEFAULT_QUIT_KEY, "hint": f"Virtual key to quit the autoclicker. Default: '{self.DEFAULT_QUIT_KEY}'"},
            {"short": 'sf', "name": 'safekey' , "type": self._hexToInt, "d_val": self.DEFAULT_SAFE_KEY, "hint": f"Virtual key to use in safe mode. Default: 0x12 ({self.get_key_name(self.DEFAULT_SAFE_KEY)})"}
        )

        autoclicker_group.add_argument('-cps', '--clicks-per-second', dest='clickspersec', type=float, default=self.DEFAULT_CPS, help=f"Target clicks per second (CPS). Default: '{self.DEFAULT_CPS}cps'")
        for arg in ARGS:
            autoclicker_group.add_argument(f"-{arg['short']}", f"--{arg['name']}", type=arg['type'], default=arg['d_val'], help=arg['hint'])

    def get_parser(self) -> argparse.ArgumentParser:
        """
        Returns the argument parser instance.
        Returns:
            argparse.ArgumentParser: The parser used for command-line argument parsing.
        """

        return self.parser

    @staticmethod
    def _hexToInt(hex) -> int:
        """
        Converts a hexadecimal string or integer to an integer.
        Args:
            hex (str or int): The value to convert. Can be a hexadecimal string (e.g., '0x1A', '1A') or an integer.
        Returns:
            int: The integer representation of the input value.
        Raises:
            argparse.ArgumentTypeError: If the input is a string that cannot be converted to an integer.
        """

        if isinstance(hex, int):
            return hex

        try:
            return int(hex, 16)

        except ValueError:
            raise argparse.ArgumentTypeError(f"Invalid hexadecimal value: {hex}. Please provide a valid hexadecimal string or integer.")

class LoggingHandler(ParserHandler):
    """
    A handler class that sets up logging for the application.
    This class initializes a logger that writes debug-level logs to a file
    (with the same name as the script, but with a .log extension) and optionally
    to the console. It extends the ParserHandler base class.
    Attributes:
        need_cleanup (bool): Indicates if cleanup is needed for the handler.
        logger (logging.Logger): The logger instance used for logging messages.
        log_file (logging.FileHandler): The file handler for logging to a file.
    Methods:
        debug():
            Adds a StreamHandler to the logger to output debug-level logs to the console (stderr).
    """

    def __init__(self):

        super().__init__()

        self.need_cleanup = True
        self.logger = logging.getLogger()
        self.logger.setLevel(logging.DEBUG)
        self.log_file = logging.FileHandler(re.sub(r'\.py$', '.log', os.path.relpath(__file__)), mode='a')
        self.log_file.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        self.logger.addHandler(self.log_file) if not self.logger.hasHandlers() else None

    def debug(self):
        """
        Configures the logger to output debug information to the console (stderr).

        This method adds a StreamHandler to the logger, sets its level to DEBUG,
        and applies a formatter to display the timestamp, log level, and message.

        Useful for debugging purposes to see detailed log output in the console.
        """
        console = logging.StreamHandler(sys.stderr)
        console.setLevel(logging.DEBUG)
        console.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        self.logger.addHandler(console)

class Autoclicker(LoggingHandler):
    """
    Autoclicker is a configurable class for automating mouse clicks at a specified rate, 
    with support for start, pause, quit, and safe mode key bindings. It runs the clicking 
    action in a separate thread and provides safety checks to prevent unintended behaviors.
    Attributes:
        DEBOUNCE_SLEEP_TIME (float): Time to wait after key events to debounce input.
        click_thread (threading.Thread): Thread running the click loop.
        clicking_event (threading.Event): Event to control clicking state.
        quit_event (threading.Event): Event to signal quitting.
        clickspersec (float): Number of clicks per second.
        start_key (int): Virtual key code to start/resume clicking.
        pause_key (int): Virtual key code to pause clicking.
        quit_key (int): Virtual key code to quit the autoclicker.
        safe_mode (bool): If True, requires safe_key to be pressed for start/quit actions.
        safe_key (int): Virtual key code for safe mode checks.
        start_state (bool): State of the start key.
        pause_state (bool): State of the pause key.
        quit_state (bool): State of the quit key.
    Methods:
        setup(clickspersec, start_key, pause_key, quit_key, safe_key, safemode, caution_mode=True):
            Configures the autoclicker with the given parameters and performs safety checks.
        run(fun, **fun_args):
            Starts the autoclicker, listens for key events, and manages the click loop.
        _click_loop(fun, fun_args):
            Internal method that repeatedly executes the provided function at the configured rate.
        _start():
            Sets the autoclicker to the clicking state and prints status.
        _pause():
            Pauses the autoclicker and prints status.
        _quit():
            Signals the autoclicker to quit, prints status, and performs cleanup.
        cleanup():
            Cleans up resources, stops threads, and shuts down logging.
    Raises:
        ValueError: If clickspersec is not positive, exceeds safe limits, or duplicate keys are used.
        AttributeError: If a required key attribute is missing.
    """

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
        """
        Configures the autoclicker with the specified settings.
        Args:
            clickspersec (float): Number of clicks per second. Must be a positive real number.
            start_key (int): Key code to start clicking.
            pause_key (int): Key code to pause clicking.
            quit_key (int): Key code to quit the autoclicker.
            safe_key (int): Key code to toggle safe mode.
            safemode (bool): Enables or disables safe mode.
            caution_mode (bool, optional): If True, enables built-in safety checks to prevent unintended behaviors. Defaults to True.
        Raises:
            ValueError: If clickspersec is not a positive number.
            ValueError: If clickspersec exceeds 500 and caution_mode is enabled.
            ValueError: If duplicate key bindings are detected and caution_mode is enabled.
        Notes:
            - Disabling caution_mode allows potentially unsafe configurations, such as duplicate key bindings or high click rates.
            - User confirmation is required when disabling caution_mode.
        """

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

        self.clickspersec = clickspersec
        self.start_key = start_key
        self.pause_key = pause_key
        self.quit_key = quit_key
        self.safe_key = safe_key
        self.safe_mode = safemode

    def run(self, fun: Callable, **fun_args) -> None:
        """
        Starts the autoclicker main loop and manages key events for starting, pausing, and quitting.
        Args:
            fun (Callable): The function to be executed in the click loop.
            **fun_args: Additional keyword arguments to pass to the click loop function.
        Raises:
            AttributeError: If a required key attribute is missing.
        Behavior:
            - Initializes key states for start, pause, and quit actions.
            - Starts the click loop in a separate daemon thread.
            - Prints usage information and key bindings.
            - Monitors key events to start, pause, or quit the autoclicker.
            - Supports a safemode that requires a safe key to be pressed for starting and quitting.
            - Joins the click thread on exit to ensure proper cleanup.
        """

        for key, _ in self.__dict__.items():
            if key.endswith('_state'):
                key_key = key[:-5] + 'key'
                if not hasattr(self, key_key):
                    raise AttributeError('I have no clue why this happend.')
                setattr(self, key, self.is_key_pressed(getattr(self, key_key)))

        self.click_thread = threading.Thread(target=self._click_loop, args=(fun, fun_args), daemon=True)
        self.click_thread.start()

        print("Use --help (-h) for usage information")
        print(f"Safemode is enabled. Press the safe key '{self.get_key_name(self.safe_key)}' to use the start and quit keys") if self.safe_mode else None
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
            if quit_edge or self.rising_detection(self.is_key_pressed(self.ESC_KEY).is_double_click(), self.quit_state, self.safe_mode, True)[0]:
                self._quit()
                break

        time.sleep(self.DEBOUNCE_SLEEP_TIME)
        if self.click_thread.is_alive():
            self.click_thread.join(timeout=1)

    def _click_loop(self, fun: Callable, fun_args: dict[str, any]) -> None:
        """
        Continuously executes a given function at a specified rate while the clicking event is set.
        Args:
            fun (Callable): The function to be repeatedly executed.
            fun_args (dict[str, any]): A dictionary of keyword arguments to pass to the function.
        Behavior:
            - Runs in a loop until the quit event is set.
            - If the clicking event is set, calls the provided function with the given arguments.
            - Handles exceptions by logging the error and pausing execution.
            - Waits for a duration based on the clicks per second rate between function calls.
            - If the clicking event is not set, sleeps for a short interval before checking again.
        """

        while not self.quit_event.is_set():
            if self.clicking_event.is_set():
                try:
                    fun(**fun_args)
                except Exception as e:
                    self.logger.error(f"Exception when trying to execute the action to be repeated: {e}", exc_info=True)
                    self._pause()
                finally:
                    time.sleep(1/self.clickspersec)
            else:
                time.sleep(0.2)

    def _start(self) -> None:
        """
        Initiates the clicking process by setting the clicking event and printing a status message.
        Waits for a short debounce period before proceeding.
        Side Effects:
            - Prints a status message to the terminal.
            - Sets the `clicking_event` to signal the start of clicking.
            - Pauses execution for `DEBOUNCE_SLEEP_TIME` seconds.
        Returns:
            None
        """

        print("Clicking started.".ljust(get_terminal_size().columns), end="\r", flush=True)
        self.clicking_event.set()
        time.sleep(self.DEBOUNCE_SLEEP_TIME)

    def _pause(self) -> None:
        """
        Pauses the clicking process.
        This method prints a message indicating that clicking is paused,
        clears the clicking event to stop the clicking loop, and waits
        for a short debounce period to prevent rapid toggling.
        Returns:
            None
        """

        print("Clicking paused.".ljust(get_terminal_size().columns), end="\r", flush=True)
        self.clicking_event.clear()
        time.sleep(self.DEBOUNCE_SLEEP_TIME)

    def _quit(self) -> None:
        """
        Signals the application to quit by setting the quit event, prints a quitting message,
        waits for a debounce period, and performs cleanup operations.
        This method is typically called to gracefully terminate the autoclicker process.
        """

        self.quit_event.set()
        print("Quitting...".ljust(get_terminal_size().columns))
        time.sleep(self.DEBOUNCE_SLEEP_TIME)
        self.cleanup()

    def cleanup(self) -> None:
        """
        Cleans up resources and gracefully exits the application.
        This method performs the following actions:
            - Checks if cleanup is needed; if not, exits the program immediately.
            - Clears the clicking event and sets the quit event to signal threads to stop.
            - Waits for the click thread to finish if it is still running.
            - Logs and prints a message indicating resources have been cleaned up.
            - Shuts down the logging system.
            - Exits the argument parser.
        Returns:
            None
        """

        if not self.need_cleanup:
            sys.exit(0)

        self.need_cleanup = False

        self.clicking_event.clear()
        self.quit_event.set()
        if self.click_thread and self.click_thread.is_alive():
            self.click_thread.join(timeout=1)

        TEXT = "Resources are cleaned up."
        print(TEXT)
        self.logger.info(TEXT)
        logging.shutdown()

        self.parser.exit()

def main() -> None:
    """
    Main entry point for the autoclicker application.
    This function initializes the Autoclicker instance, parses command-line arguments,
    sets up the autoclicker configuration, and starts the autoclicker loop. It handles
    debug mode, logging, and exception management, including keyboard interrupts and
    unexpected errors. Upon termination or exception, it ensures proper cleanup of resources.
    Raises:
        Exception: Propagates any exception that occurs during execution after logging.
    """

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
        autoclicker.run(autoclicker.mouse_SendInput, flags=autoclicker.MOUSEEVENTF_LEFTDOWN | autoclicker.MOUSEEVENTF_LEFTUP)
        # autoclicker.run(autoclicker.mouse_SendInput, dx=0, dy=0, data=0, flags=autoclicker.MOUSEEVENTF_LEFTDOWN | autoclicker.MOUSEEVENTF_LEFTUP, time=0, extra_info=0)
        # autoclicker.run(autoclicker.keyboard_SendInput, vk=autoclicker.quit_key, scan=None, flags=autoclicker.KEYBDEVENTF_KEYDOWN | autoclicker.KEYBDEVENTF_KEYUP, time=0, extra_info=0)

    except KeyboardInterrupt:
        print("\nInterrupted by keyboard!")
        if autoclicker is not None:
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
            del autoclicker

if __name__ == "__main__":
    if sys.platform != "win32":
        raise RuntimeError("This script is designed to run on Windows only!")

    os.system('cls' if os.name == 'nt' else 'clear') if sys.stdin.isatty() else None
    main()
