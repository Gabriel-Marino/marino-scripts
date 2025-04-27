import ctypes
import threading
import time
import msvcrt  # For reading keypresses on Windows

class POINT(ctypes.Structure):
    _fields_ = [("x", ctypes.c_long), ("y", ctypes.c_long)]

class AutoClicker:
    def __init__(self, delay=50):
        """Initialize an AutoClicker object with a specified delay."""
        self._running = False
        self._delay = delay / 1000  # Convert ms to seconds using division
        self._thread = None

    def click(self):
        """Perform a single mouse click.

        This function performs a single mouse click by first pressing (0x0002) and
        then releasing (0x0004) the left mouse button.  The other parameters are
        all ignored.

        This function does not move the mouse cursor, so it will perform a click
        at the current mouse position.
        """
        ctypes.windll.user32.mouse_event(0x0002 | 0x0004, 0, 0, 0, 0)

 
    def _click_loop(self):
        """
        The main loop of the auto-clicker thread.
        This loop continues running while `self._running` is True.
        """
        while self._running:
            if msvcrt.kbhit() and msvcrt.getch().decode('utf-8').lower() == 'b':
                print("Clicking stopped.")
                self.stop()
                break
            
            self.click()
            time.sleep(self._delay)

    def start(self):
        """Start the auto-clicker.

        This function starts the auto-clicker by creating a new thread
        running the `_click_loop` method.  The auto-clicker will continue
        running until the `stop` method is called.

        This function does nothing if the auto-clicker is already running.
        """
        if not self._running:
            self._running = True
            self._thread = threading.Thread(target=self._click_loop, daemon=True)
            self._thread.start()
            print("Clicking started.")

    def stop(self):
        """Stop the auto-clicker.

        This function stops the auto-clicker by setting the
        ``_running`` attribute to False.  This causes the
        `_click_loop` method to exit.

        This function does nothing if the auto-clicker is already
        stopped.
        """
        if self._running:
            self._running = False
            if self._thread and self._thread.is_alive():
                self._thread.join()  # Wait for the thread to finish

def main():
    """The main function of the script."""
    autoclicker = AutoClicker(delay=1)
    print("Press 'S' to start clicking and 'B' to stop and exit.")

    while True:
        if msvcrt.kbhit():
            key = msvcrt.getch().decode('utf-8').lower()
            if key == 's' and not autoclicker._running:
                print("Clicking started.")
                autoclicker.start()
            elif key == 'b' and autoclicker._running:
                print("Clicking stopped.")
                autoclicker.stop()
                break

if __name__ == "__main__":
    main()
