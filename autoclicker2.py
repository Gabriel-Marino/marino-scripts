import argparse
import ctypes
import logging
import os
import re
import sys
import time
import traceback

class WindowsKeysHandler:
    """
    WindowsKeysHandler provides static methods for interacting with virtual keyboard and mouse events on Windows systems.
    This class leverages the Windows API via ctypes to:
    - Check if a virtual key is currently pressed.
    - Convert a character to its corresponding virtual key code.
    - Retrieve the human-readable name of a virtual key.
    - Detect rising edges in boolean signals (useful for key press detection).
    - Simulate mouse left-click events.
    Attributes:
        u32: Reference to the user32 DLL from the Windows API.
        GetAsyncKeyState: Function to get the state of a virtual key.
        VkKeyScanW: Function to translate a character to a virtual key code.
        GetKeyNameTextW: Function to retrieve the name of a key.
        MapVirtualKeyW: Function to map virtual key codes.
        mouse_event: Function to simulate mouse events.
        KEY_PRESS_MASK: Bitmask for detecting key press state.
        SHIFT_KEY_MASK: Bitmask for extracting virtual key code.
        MOUSEEVENTF_LEFTDOWN: Flag for mouse left button down event.
        MOUSEEVENTF_LEFTUP: Flag for mouse left button up event.
    Methods:
        is_key_pressed(virtual_key: int) -> bool:
        get_virtual_key(key: str) -> int:
        get_key_name(virtual_key: int) -> str:
        rising_detection(curr: bool, prev: bool) -> list[bool, bool]:
        mouse_click():
            Simulates a mouse left-click event.
    """

    u32 = ctypes.windll.user32
    GetAsyncKeyState = u32.GetAsyncKeyState
    VkKeyScanW = u32.VkKeyScanW
    GetKeyNameTextW = u32.GetKeyNameTextW
    MapVirtualKeyW = u32.MapVirtualKeyW
    mouse_event = u32.mouse_event

    KEY_PRESS_MASK = 0x8000
    SHIFT_KEY_MASK = 0xFF

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
        return WindowsKeysHandler.GetAsyncKeyState(virtual_key) & WindowsKeysHandler.KEY_PRESS_MASK != 0

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
    def rising_detection(curr: bool, prev: bool) -> list[bool, bool]:
        """
        Detects a rising edge in a boolean signal.

        Args:
            curr (bool): The current boolean value.
            prev (bool): The previous boolean value.

        Returns:
            list[bool, bool]: A list containing two elements:
                - The first element is True if a rising edge is detected (curr is True and prev is False), otherwise False.
                - The second element is the current boolean value (curr).
        """

        return curr and not prev, curr

    @staticmethod
    def mouse_click():
        """
        Simulates a mouse left-click event by triggering both mouse button down and up actions.

        Returns:
            int: The result of the mouse_event function, typically indicating success or failure.
        """

        return WindowsKeysHandler.mouse_event(WindowsKeysHandler.MOUSEEVENTF_LEFTDOWN | WindowsKeysHandler.MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
    
class ParserHandler:
    """
    ParserHandler provides a static method to create and configure an argument parser
    for the auto-clicker script. The parser supports command-line options to customize
    the click interval and control keys for starting, pausing, and quitting the auto-clicker.
    Methods:
        get_parser() -> object:
            Creates and returns an argparse.ArgumentParser configured with the following options:
    """

    @staticmethod
    def get_parser() -> object:
        """
        Creates and returns an argument parser for the auto-clicker script.
        The parser supports the following command-line options:
            --timeout   : Sleep time in milliseconds between clicks (default: 42.0).
            --startkey  : Virtual key to start/resume clicking (default: 'S').
            --pausekey  : Virtual key to pause clicking (default: 'Z').
            --quitkey   : Virtual key to quit the autoclicker (default: 'X').
        Returns:
            argparse.ArgumentParser: Configured argument parser for the script.
        """

        parser = argparse.ArgumentParser(
            prog=os.path.basename(__file__),
            usage="%(prog)s [options]",
            description="A simple auto-clicker script that allows you to automate mouse clicks.",
            epilog="Press 'Ctrl + StartKey' to start/resume clicking, 'PauseKey' to pause, and 'Ctrl + QuitKey' to quit."
        )

        parser.add_argument("--timeout" , type=float, default=42.0, help="Sleep time in milliseconds between clicks.")
        parser.add_argument("--startkey", type=str, default='S', help="Virtual key to start/resume clicking.")
        parser.add_argument("--pausekey", type=str, default='Z', help="Virtual key to pause clicking.")
        parser.add_argument("--quitkey" , type=str, default='X', help="Virtual key to quit the autoclicker.")

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
        WindowsKeysHandler.mouse_event(Autoclicker.MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
        LoggingHandler.logger.info(TEXT)
        logging.shutdown()
        print(TEXT)

class Autoclicker:

    DEBOUNCE_SLEEP_TIME = 0.069

    def __init__(self):
        """
        Initializes the autoclicker with default settings.

        Attributes:
            timeout (float): The delay between clicks in seconds.
            start_key (int): The virtual-key code to start clicking (default: 0x41).
            pause_key (int): The virtual-key code to pause clicking (default: 0x42).
            quit_key (int): The virtual-key code to quit the autoclicker (default: 0x43).
            clicking (bool): Indicates whether the autoclicker is currently clicking.
            start_state (bool): Tracks the state of the start key.
            pause_state (bool): Tracks the state of the pause key.
            quit_state (bool): Tracks the state of the quit key.
        """

        self.timeout = 42.0
        self.start_key = 0x41
        self.pause_key = 0x42
        self.quit_key = 0x43
        self.clicking = False
        self.start_state = self.pause_state = self.quit_state = False

    def setup(self, timeout: float, start_key: int, pause_key: int, quit_key: int) -> None:
        """
        Configures the autoclicker with the specified timeout and control keys.

        Args:
            timeout (float): The delay in seconds between each click.
            start_key (int): The key code to start the autoclicker.
            pause_key (int): The key code to pause the autoclicker.
            quit_key (int): The key code to quit the autoclicker.

        Returns:
            None
        """

        self.timeout = timeout
        self.start_key = start_key
        self.pause_key = pause_key
        self.quit_key = quit_key

    def run(self):
        """
        Runs the main loop for the autoclicker, handling start, pause, and quit commands via keyboard input.
        Prints instructions for the user, then continuously checks for key presses to control the autoclicker:
            - Starts or resumes clicking when the start key is pressed.
            - Pauses clicking when the pause key is pressed.
            - Quits the autoclicker when the quit key is pressed.
        While active, performs mouse clicks at intervals defined by `self.timeout`.
        Relies on the WindowsKeysHandler for key detection and mouse actions.
        """

        print(f"Press '{WindowsKeysHandler.get_key_name(self.start_key)}' to start/resume clicking, '{WindowsKeysHandler.get_key_name(self.pause_key)}' to pause, and '{WindowsKeysHandler.get_key_name(self.quit_key)}' to quit.")

        while True:
            start, self.rising_detection = WindowsKeysHandler.rising_detection(WindowsKeysHandler.is_key_pressed(self.start_key), self.start_state)
            if not self.clicking and start:
                Autoclicker._start(self)

            pause, self.pause_state = WindowsKeysHandler.rising_detection(WindowsKeysHandler.is_key_pressed(self.pause_key), self.pause_state)
            if self.clicking and pause:
                Autoclicker._pause(self)

            quit, self.quit_state = WindowsKeysHandler.rising_detection(WindowsKeysHandler.is_key_pressed(self.quit_key), self.quit_state)
            if self.clicking and quit:
                Autoclicker._quit(self)
                break

            if self.clicking:
                WindowsKeysHandler.mouse_click()
                time.sleep(0.001 * self.timeout)

    def _start(self):
        """
        Starts the autoclicking process by setting the clicking flag to True and printing a status message.
        Waits for a debounce period defined by DEBOUNCE_SLEEP_TIME before proceeding.

        Side Effects:
            - Sets self.clicking to True.
            - Prints "Clicking started." to the console.
            - Pauses execution for a short debounce period.
        """

        print("Clicking started.", end="\r")
        self.clicking = True
        time.sleep(Autoclicker.DEBOUNCE_SLEEP_TIME)

    def _pause(self):
        """
        Pauses the autoclicking process.
        This method sets the clicking flag to False, prints a message indicating that clicking is paused,
        and waits for a debounce period defined by DEBOUNCE_SLEEP_TIME to prevent rapid toggling.
        """

        print("Clicking paused.", end="\r")
        self.clicking = False
        time.sleep(Autoclicker.DEBOUNCE_SLEEP_TIME)

    def _quit(self):
        """
        Stops the autoclicker, prints a quitting message, waits for a debounce period, and performs cleanup operations.
        This method sets the clicking flag to False to halt the autoclicker, displays a message to the user, waits for a predefined debounce time, and calls the cleanup method of the LoggingHandler to release any resources or perform necessary shutdown procedures.
        """

        self.clicking = False
        print("\nQuitting...")
        time.sleep(Autoclicker.DEBOUNCE_SLEEP_TIME)
        LoggingHandler.cleanup()

def main() -> None:
    """
    Main entry point for the autoclicker script.
    This function performs the following steps:
    1. Ensures the script is running on a Windows platform.
    2. Initializes the Autoclicker and argument parser.
    3. Parses command-line arguments and sets up the autoclicker with the specified keys and timeout.
    4. Runs the autoclicker.
    Exception Handling:
    - Handles KeyboardInterrupt to allow graceful shutdown and logs the interruption.
    - Handles all other exceptions, prints a summary, logs the error with traceback, and re-raises the exception.
    Raises:
        RuntimeError: If the script is not run on Windows.
        Exception: Any exception that occurs during setup or execution is logged and re-raised.
    """

    if sys.platform != "win32":
        raise RuntimeError("This script is designed to run on Windows only!")

    try:
        autoclicker = Autoclicker()
        parser = ParserHandler.get_parser()
        args = parser.parse_args()
        autoclicker.setup(
            timeout=args.timeout,
            start_key=WindowsKeysHandler.get_virtual_key(args.startkey),
            pause_key=WindowsKeysHandler.get_virtual_key(args.pausekey),
            quit_key=WindowsKeysHandler.get_virtual_key(args.quitkey)
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
    main()
