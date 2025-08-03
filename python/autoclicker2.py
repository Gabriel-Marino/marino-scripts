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

class MOUSEINPUT(ctypes.Structure):
    """
    Represents the MOUSEINPUT structure used by the Windows API for synthesizing mouse input events.

    Attributes:
        dx (w.LONG): The absolute position of the mouse, or the amount of motion since the last event, depending on the value of dwFlags.
        dy (w.LONG): The absolute position of the mouse, or the amount of motion since the last event, depending on the value of dwFlags.
        mouseData (w.DWORD): If dwFlags contains MOUSEEVENTF_WHEEL, then mouseData specifies the amount of wheel movement. Otherwise, it may specify X button information.
        dwFlags (w.DWORD): A set of bit flags that specify various aspects of mouse motion and button clicks.
        time (w.DWORD): The time stamp for the event, in milliseconds. If this parameter is 0, the system will provide its own time stamp.
        dwExtraInfo (ctypes.c_ulonglong): An additional value associated with the mouse event.
    """

    _fields_ = [
        ("dx", w.LONG),
        ("dy", w.LONG),
        ("mouseData", w.DWORD),
        ("dwFlags", w.DWORD),
        ("time", w.DWORD),
        ("dwExtraInfo", ctypes.c_ulonglong)
    ]

class INPUTUNION(ctypes.Union):
    """
    A ctypes.Union subclass representing the INPUTUNION structure used in Windows API input simulation.

    Attributes:
        mi (MOUSEINPUT): Represents mouse input data for the union. This field is used when simulating mouse events.
    """

    _fields_ = [
        ("mi", MOUSEINPUT)
    ]

class INPUT(ctypes.Structure):
    """
    Represents a generic input event structure for use with Windows API functions.

    Attributes:
        type (w.DWORD): Specifies the type of the input event (e.g., mouse, keyboard, hardware).
        union (INPUTUNION): A union containing the information about the input event, 
            which varies depending on the type specified.
    """

    _fields_ = [
        ("type", w.DWORD),
        ("union", INPUTUNION)
    ]

class WindowsKeysHandler:
    """
    WindowsKeysHandler
    A utility class for handling keyboard and mouse input events on Windows using the ctypes library.
    Provides static methods to check key states, convert characters to virtual key codes, retrieve key names,
    detect rising edges in boolean signals, and simulate mouse left-click events using the Windows API.
    Attributes:
        u32: Reference to the user32 DLL loaded via ctypes.
        GetAsyncKeyState: Function pointer to user32.GetAsyncKeyState for checking key states.
        VkKeyScanW: Function pointer to user32.VkKeyScanW for converting characters to virtual key codes.
        GetKeyNameTextW: Function pointer to user32.GetKeyNameTextW for retrieving key names.
        MapVirtualKeyW: Function pointer to user32.MapVirtualKeyW for mapping virtual key codes.
        send_input: Function pointer to user32.SendInput for simulating input events.
        KEY_PRESS_MASK (int): Bitmask for detecting key press state.
        SHIFT_KEY_MASK (int): Bitmask for extracting virtual key code from VkKeyScanW result.
        MOUSEEVENTF_LEFTDOWN (int): Flag for mouse left button down event.
        MOUSEEVENTF_LEFTUP (int): Flag for mouse left button up event.
    Methods:
        is_key_pressed(virtual_key: int) -> bool
        get_virtual_key(key: str) -> int
        get_key_name(virtual_key: int) -> str
        rising_detection(curr: bool, prev: bool) -> list[bool, bool]
        mouse_left_down()
            Simulates a mouse left button down event.
        mouse_left_up()
            Simulates a mouse left button up event.
        mouse_click()
            Simulates a mouse left-click event (down and up).
    """

    u32 = ctypes.windll.user32
    GetAsyncKeyState = u32.GetAsyncKeyState
    VkKeyScanW = u32.VkKeyScanW
    GetKeyNameTextW = u32.GetKeyNameTextW
    MapVirtualKeyW = u32.MapVirtualKeyW
    # mouse_event = u32.mouse_event
    send_input = u32.SendInput

    KEY_PRESS_MASK = 0x8000
    SHIFT_KEY_MASK = 0xFF

    MOUSE_INPUT = 0
    MOUSEEVENTF_LEFTDOWN = 0x0002
    MOUSEEVENTF_LEFTUP = 0x0004

    @staticmethod
    def is_key_pressed(virtual_key: int) -> bool:
        """
        Checks if a specific virtual key is currently pressed.

        Args:
            virtual_key (int): The virtual key code to check.

        Returns:
            bool: True if the specified key is pressed, False otherwise.
        """
        try:
            return WindowsKeysHandler.GetAsyncKeyState(virtual_key) & WindowsKeysHandler.KEY_PRESS_MASK != 0

        except ValueError:
            raise ValueError(f"Invalid virtual key code: {virtual_key}. Please provide a valid hexadecimal key code.")

    @staticmethod
    def get_virtual_key(key: str) -> int:
        """
        Converts a single character key to its corresponding virtual key code.
        Args:
            key (str): A single character string representing the key to convert.
        Returns:
            int: The virtual key code corresponding to the given character.
        Raises:
            ValueError: If the input key is not a single character.
        """

        if len(key) != 1:
            raise ValueError(f"Key '{key}' must be a single character.")
    
        return WindowsKeysHandler.VkKeyScanW(ord(key)) & WindowsKeysHandler.SHIFT_KEY_MASK

    @staticmethod
    def get_key_name(virtual_key: int) -> str:
        """
        Retrieves the human-readable name of a virtual key code.
        Args:
            virtual_key (int): The virtual key code for which to retrieve the name.
        Returns:
            str: The name of the virtual key.
        Raises:
            ValueError: If the name for the given virtual key cannot be retrieved.
        """

        l_param = WindowsKeysHandler.MapVirtualKeyW(virtual_key, 0) << 16
        buf = ctypes.create_unicode_buffer(64)

        if not WindowsKeysHandler.GetKeyNameTextW(l_param, buf, 64):
            raise ValueError(f"Could not retrieve name for virtual key {virtual_key}.")
        
        return buf.value

    @staticmethod
    def rising_detection(curr: bool, prev: bool, safemode: bool, safekeyispressed: bool) -> list[bool]:
        """
        Detects a rising edge in a boolean signal, with optional safemode and safekey logic.
        Args:
            curr (bool): The current boolean state.
            prev (bool): The previous boolean state.
            safemode (bool): If True, rising edge detection is only enabled when the safekey is pressed.
            safekeyispressed (bool): Indicates whether the safekey is currently pressed.
        Returns:
            list[bool]: A list containing two boolean values:
                - The first value is True if a rising edge is detected (curr is True and prev is False), otherwise False.
                - The second value is the current state (curr) if detection is enabled, or the previous state (prev) if not.
        """

        if not safemode:
            return curr and not prev, curr

        elif safekeyispressed:
            return curr and not prev, curr

        return False, prev

    @staticmethod
    def mouse_left_down():
        """
        Simulates a left mouse button press (mouse down event) using the Windows API.
        Returns:
            int: The result of the SendInput function call, indicating the number of events successfully inserted into the input stream.
        """

        input = INPUT()
        input.type = WindowsKeysHandler.MOUSE_INPUT
        input.union.mi = MOUSEINPUT(
            dx=0,
            dy=0,
            mouseData=0,
            dwFlags=WindowsKeysHandler.MOUSEEVENTF_LEFTDOWN,
            time=0,
            dwExtraInfo=0
        )

        return WindowsKeysHandler.send_input(1, ctypes.byref(input), ctypes.sizeof(input))

    @staticmethod
    def mouse_left_up():
        """
        Simulates a mouse left button release event.
        This function creates and sends a low-level input event to the operating system,
        emulating the release (up) of the left mouse button. It constructs the appropriate
        INPUT structure with the necessary flags and parameters, then dispatches it using
        the Windows API.
        Returns:
            int: The number of events successfully inserted into the input stream.
        """

        input = INPUT()
        input.type = WindowsKeysHandler.MOUSE_INPUT
        input.union.mi = MOUSEINPUT(
            dx=0,
            dy=0,
            mouseData=0,
            dwFlags=WindowsKeysHandler.MOUSEEVENTF_LEFTUP,
            time=0,
            dwExtraInfo=0
        )

        return WindowsKeysHandler.send_input(1, ctypes.byref(input), ctypes.sizeof(input))

    # A snippet of the original mouse_click function, here the clicking action is send in a single input event using the pipe operator
    # @staticmethod
    # def mouse_click():
    #     """
    #     Simulates a mouse left-click event by triggering both mouse button down and up actions.

    #     Returns:
    #         int: The result of the mouse_event function, typically indicating success or failure.
    #     """

    #     # By stated in the documentation, this function is suspended: https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-mouse_event
    #     # return WindowsKeysHandler.mouse_event(WindowsKeysHandler.MOUSEEVENTF_LEFTDOWN | WindowsKeysHandler.MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
    #     # Documentation says to use SendInput instead, this implementation was made using the help of chatgpt and copilot
    #     input = INPUT()
    #     input.type = WindowsKeysHandler.MOUSE_INPUT
    #     input.union.mi = MOUSEINPUT(
    #         dx=0,
    #         dy=0,
    #         mouseData=0,
    #         dwFlags=WindowsKeysHandler.MOUSEEVENTF_LEFTDOWN | WindowsKeysHandler.MOUSEEVENTF_LEFTUP,
    #         time=0,
    #         dwExtraInfo=0
    #     )

    #     # Send one input event, which is a mouse click
    #     return WindowsKeysHandler.send_input(1, ctypes.byref(input), ctypes.sizeof(input))

class ParserHandler:

    DEFAULT_TIMEOUT = 42.0
    DEFAULT_START_KEY = 'S'
    DEFAULT_PAUSE_KEY = 'P'
    DEFAULT_QUIT_KEY = 'Q'
    DEFAULT_SAFE_KEY = 0x12  # Virtual key code for generic Alt key,

    @staticmethod
    def _stringToBool(arg: str) -> bool:
        """
        Converts a string representation of a boolean value to a boolean.
        Args:
            arg (str): The string to convert. Accepts 'true', '1', 'yes' for True,
                and 'false', '0', 'no' for False (case-insensitive). If a boolean is passed,
                it is returned as is.
        Returns:
            bool: The boolean value corresponding to the input string or boolean.
        Raises:
            AttributeError: If the input is not a string or boolean.
        """

        if isinstance(arg, bool):
            return arg

        if arg.lower() in ('true', '1', 'yes'):
            return True

        if arg.lower() in ('false', '0', 'no'):
            return False

        raise ValueError(f"Argument '{arg}' is not interpreted as a boolean value.")

    @staticmethod
    def _hexToInt(hex) -> int:

        try:
            if isinstance(hex, str):
                return int(hex, 16)

        except ValueError:
            raise argparse.ArgumentTypeError(f"Invalid hexadecimal value: {hex}. Please provide a valid hexadecimal string or integer.")

    @staticmethod
    def get_parser() -> argparse.ArgumentParser:

        parser = argparse.ArgumentParser(
            prog=os.path.basename(__file__),
            usage="%(prog)s [options]",
            description="A simple auto-clicker script that allows you to automate mouse clicks.",
            epilog="Press 'StartKey' to start/resume clicking, 'PauseKey' to pause, and 'QuitKey' to quit."
        )

        parser.add_argument("--timeout" , type=float, default=ParserHandler.DEFAULT_TIMEOUT, help=f"Sleep time in milliseconds between clicks. Default: '{ParserHandler.DEFAULT_TIMEOUT}'.")
        parser.add_argument("--startkey", type=str, default=ParserHandler.DEFAULT_START_KEY, help=f"Virtual key to start/resume clicking. Default: '{ParserHandler.DEFAULT_START_KEY}'.")
        parser.add_argument("--pausekey", type=str, default=ParserHandler.DEFAULT_PAUSE_KEY, help=f"Virtual key to pause clicking. Default: '{ParserHandler.DEFAULT_PAUSE_KEY}'.")
        parser.add_argument("--quitkey" , type=str, default=ParserHandler.DEFAULT_QUIT_KEY, help=f"Virtual key to quit the autoclicker. Default: '{ParserHandler.DEFAULT_QUIT_KEY}'.")
        parser.add_argument("--safekey" , type=ParserHandler._hexToInt, default=ParserHandler.DEFAULT_SAFE_KEY, help=f"Virtual key to use in safe mode. Default: 0x12 ({WindowsKeysHandler.get_key_name(ParserHandler.DEFAULT_SAFE_KEY)}).")
        parser.add_argument("--safemode", type=ParserHandler._stringToBool, default=True, help=f"Safe mode is used to prevent unintended behavior, requiring to the safe key to be held to start or quit the script. Default: True.")

        return parser

class LoggingHandler:
    """
    LoggingHandler is a utility class responsible for configuring and managing application-wide logging.
    Class Attributes:
        logger (logging.Logger): The root logger configured to log DEBUG and higher level messages to a file.
            The log file is named after the current script, with a '.log' extension.
    Methods:
        cleanup() -> None:
    """

    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    log_file = logging.FileHandler(re.sub(r'\.py$', '.log', os.path.basename(__file__)), mode='a')
    log_file.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
    logger.addHandler(log_file)

    @staticmethod
    def cleanup() -> None:
        """
        Performs cleanup operations by releasing the left mouse button, logging the cleanup event,
        shutting down the logging system, and printing a confirmation message.
        """

        TEXT = "Resources are cleaned up."
        WindowsKeysHandler.mouse_left_up()
        LoggingHandler.logger.info(TEXT)
        logging.shutdown()
        print(TEXT)

class Autoclicker:
    """
    Autoclicker is a configurable class for automating mouse click actions on Windows systems.
    This class provides methods to start, pause, and stop an autoclicking process, with support for customizable hotkeys and an optional safe mode that requires a modifier key for activation. The autoclicking runs in a background thread and can be controlled via user-defined keyboard shortcuts. The class is designed to be thread-safe and includes debounce logic to prevent accidental rapid toggling of states.
        DEBOUNCE_SLEEP_TIME (float): Time in seconds to wait after key events to prevent rapid toggling.
        clicking_event (threading.Event): Event flag to control the clicking loop.
        quit_event (threading.Event): Event flag to signal quitting the application.
        timeout (float): Time interval between clicks in milliseconds.
        start_key (int): Virtual key code to start clicking.
        pause_key (int): Virtual key code to pause clicking.
        quit_key (int): Virtual key code to quit the application.
        safe_key (int): Virtual key code for the safe mode key (e.g., Alt key).
        start_state (bool): State flag for the start key (for edge detection).
        pause_state (bool): State flag for the pause key (for edge detection).
        quit_state (bool): State flag for the quit key (for edge detection).
    Methods:
        __init__():
        setup(timeout: float, start_key: int, pause_key: int, quit_key: int, safe_key: int, safemode: bool) -> None:
        run():
            Starts the autoclicker's main event loop, handling user input for controlling the clicking process.
            Blocks until the quit event is triggered.
        _click_loop():
        _start():
            Starts the autoclicking process by setting the clicking flag and printing a status message.
        _pause():
            Pauses the autoclicking process and prints a status message.
        _quit():
            Stops the autoclicker, prints a quitting message, and performs cleanup operations.
    """

    DEBOUNCE_SLEEP_TIME = 0.069

    def __init__(self) -> None:
        """
        Initializes the autoclicker instance with default configuration.
        Attributes:
            clicking_event (threading.Event): Event to control the clicking loop.
            quit_event (threading.Event): Event to signal quitting the application.
            timeout (float): Time interval between clicks in seconds.
            start_key (int): Virtual key code to start clicking (default: 0x41).
            pause_key (int): Virtual key code to pause clicking (default: 0x42).
            quit_key (int): Virtual key code to quit the application (default: 0x43).
            safe_mode (bool): Enables or disables safe mode for extra safety.
            safe_key (int): Virtual key code for the safe mode key (default: 0x12, Alt key).
            start_state (bool): State flag for the start key.
            pause_state (bool): State flag for the pause key.
            quit_state (bool): State flag for the quit key.
        """

        self.clicking_event = threading.Event()
        self.quit_event = threading.Event()

        self.timeout = 42.0
        self.start_key = 0x41
        self.pause_key = 0x42
        self.quit_key = 0x43
        self.safe_mode = True
        self.safe_key = 0x12 # Virtual key code for generic Alt key, used for safe mode checks.
        self.start_state = self.pause_state = self.quit_state = False

    def setup(self, timeout: float, start_key: int, pause_key: int, quit_key: int, safe_key: int, safemode: bool) -> None:
        """
        Configures the autoclicker with the specified settings.
        Args:
            timeout (float): The delay between clicks in seconds.
            start_key (int): The key code to start the autoclicker.
            pause_key (int): The key code to pause the autoclicker.
            quit_key (int): The key code to quit the autoclicker.
            safe_key (int): The key code to activate the safety mechanism.
            safemode (bool): Enables or disables safe mode.
        Returns:
            None
        """

        self.timeout = timeout
        self.start_key = start_key
        self.pause_key = pause_key
        self.quit_key = quit_key
        self.safe_key = safe_key
        self.safe_mode = safemode

    def run(self) -> None:
        """
        Starts the autoclicker's main event loop and manages user input for controlling the clicking process.
        This method launches a separate thread to handle the clicking loop, then enters a loop to listen for
        key events to start, pause, or quit the autoclicker. Key detection supports an optional safe mode,
        requiring a safety key to be held for other controls to activate.
        - Starts the click loop in a background thread.
        - Prints instructions for user controls, including safe mode if enabled.
        - Monitors for rising edge key events to:
            - Start/resume clicking (`start_key`)
            - Pause clicking (`pause_key`)
            - Quit the autoclicker (`quit_key`)
        - Exits the loop and joins the click thread upon quitting.
        The method blocks until the quit event is triggered.
        Raises:
            None
        """

        click_thread = threading.Thread(target=self._click_loop, daemon=True)
        click_thread.start()

        print(f"Safemode is enabled. Press the safe key '{WindowsKeysHandler.get_key_name(self.safe_key)}' to use the start and quit keys.") if self.safe_mode else None
        print(f"Press '{WindowsKeysHandler.get_key_name(self.start_key)}' to start/resume clicking, '{WindowsKeysHandler.get_key_name(self.pause_key)}' to pause, and '{WindowsKeysHandler.get_key_name(self.quit_key)}' to quit.")

        while not self.quit_event.is_set():
            start_edge, self.start_state = WindowsKeysHandler.rising_detection(WindowsKeysHandler.is_key_pressed(self.start_key), self.start_state, self.safe_mode, WindowsKeysHandler.is_key_pressed(self.safe_key))
            if not self.clicking_event.is_set() and start_edge:
                self._start()

            # I meant the safemode to only prevent unintended starting and quitting, not pausing, so the pause key gets True in the safekeyispressed argument regardless of the safemode state.
            pause_edge, self.pause_state = WindowsKeysHandler.rising_detection(WindowsKeysHandler.is_key_pressed(self.pause_key), self.pause_state, self.safe_mode, True)
            if self.clicking_event.is_set() and pause_edge:
                self._pause()

            quit_edge, self.quit_state = WindowsKeysHandler.rising_detection(WindowsKeysHandler.is_key_pressed(self.quit_key), self.quit_state, self.safe_mode, WindowsKeysHandler.is_key_pressed(self.safe_key))
            if quit_edge:
                self._quit()
                break

        time.sleep(Autoclicker.DEBOUNCE_SLEEP_TIME)
        click_thread.join() if click_thread.is_alive() else None

    def _click_loop(self) -> None:
        """
        Continuously performs mouse left-click actions while the clicking event is set.
        This loop checks for the `clicking_event` flag. If set, it simulates a mouse left button click
        by calling `WindowsKeysHandler.mouse_left_down()` and `WindowsKeysHandler.mouse_left_up()`,
        then waits for a duration determined by `self.timeout` (in milliseconds). If the clicking event
        is not set, the loop sleeps for 0.2 seconds before checking again. The loop exits when
        `self.quit_event` is set.
        """

        while not self.quit_event.is_set():
            if self.clicking_event.is_set():
                WindowsKeysHandler.mouse_left_down()
                WindowsKeysHandler.mouse_left_up()
                time.sleep(0.001 * self.timeout)
            else:
                time.sleep(0.2)

    def _start(self) -> None:
        """
        Starts the autoclicking process by setting the clicking flag to True and printing a status message.
        Waits for a debounce period defined by DEBOUNCE_SLEEP_TIME before proceeding.

        Side Effects:
            - Sets self.clicking to True.
            - Prints "Clicking started." to the console.
            - Pauses execution for a short debounce period.
        """

        print("Clicking started.", end="\r")
        self.clicking_event.set()
        time.sleep(Autoclicker.DEBOUNCE_SLEEP_TIME)

    def _pause(self) -> None:
        """
        Pauses the autoclicking process.
        This method sets the clicking flag to False, prints a message indicating that clicking is paused,
        and waits for a debounce period defined by DEBOUNCE_SLEEP_TIME to prevent rapid toggling.
        """

        print("Clicking paused.", end="\r")
        self.clicking_event.clear()
        time.sleep(Autoclicker.DEBOUNCE_SLEEP_TIME)

    def _quit(self) -> None:
        """
        Stops the autoclicker, prints a quitting message, waits for a debounce period, and performs cleanup operations.
        This method sets the clicking flag to False to halt the autoclicker, displays a message to the user, waits for a predefined debounce time, and calls the cleanup method of the LoggingHandler to release any resources or perform necessary shutdown procedures.
        """

        self.clicking_event.clear()
        self.quit_event.set()
        print("\nQuitting...")
        time.sleep(Autoclicker.DEBOUNCE_SLEEP_TIME)
        LoggingHandler.cleanup()

def main() -> None:
    """
    Main entry point for the autoclicker application.
    This function initializes the Autoclicker, parses command-line arguments,
    sets up the autoclicker with the provided options, and starts its execution.
    It handles keyboard interrupts gracefully and logs any exceptions that occur,
    providing traceback information and ensuring proper cleanup of logging resources.
    Raises:
        Exception: Re-raises any unexpected exceptions after logging and cleanup.
    """

    try:
        autoclicker = Autoclicker()
        parser = ParserHandler.get_parser()
        args = parser.parse_args()
        LoggingHandler.logger.info(f"Parsed arguments: {vars(args)}")
        autoclicker.setup(
            timeout=args.timeout,
            start_key=WindowsKeysHandler.get_virtual_key(args.startkey),
            pause_key=WindowsKeysHandler.get_virtual_key(args.pausekey),
            quit_key=WindowsKeysHandler.get_virtual_key(args.quitkey),
            safe_key=args.safekey,
            safemode=args.safemode
        )
        autoclicker.run()

    except KeyboardInterrupt:
        print("\nInterrupted by keyboard!")
        LoggingHandler.logger.info("Interrupted by keyboard!")
        LoggingHandler.cleanup()

    except Exception as e:
        print(f"\n An exception occurred: {e}.")
        tb = traceback.extract_tb(e.__traceback__)
        if tb:
            filename, line, func, text = tb[-1]
            log_path = getattr(LoggingHandler.log_file, 'baseFilename', "something very unexpected happened at the point I can't even explain why there's not a log file.")
            print(f"File: {filename}, line no.: {line}.\nCheck the complete traceback at: {log_path}.\n")

        LoggingHandler.logger.error("An exception occurred!", exc_info=True)
        logging.shutdown()
        raise

if __name__ == "__main__":
    if sys.platform != "win32":
        raise RuntimeError("This script is designed to run on Windows only!")

    main()

