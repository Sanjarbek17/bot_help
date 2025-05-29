import tkinter as tk
import pyperclip
from pynput import mouse, keyboard
import threading
import time
import sys
import os
import subprocess
import logging
import traceback
from collections import deque
from threading import Thread

# Set up logging with more detailed formatting
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - [%(threadName)s] - %(message)s",
    handlers=[logging.FileHandler("debug.log"), logging.StreamHandler()],
)

# Global variables
TEXT_FILE_PATH = "kte.txt"
popup_window = None
last_text = ""
current_index = 0
root = None
is_running = True
MAX_RESULTS = 10  # Limit maximum number of results


# Add exception hook to catch unhandled exceptions
def handle_exception(exc_type, exc_value, exc_traceback):
    logging.error("Unhandled exception", exc_info=(exc_type, exc_value, exc_traceback))


sys.excepthook = handle_exception


def check_accessibility_permissions():
    logging.info("Checking accessibility permissions...")
    if sys.platform != "darwin":  # Only check on macOS
        logging.debug("Not on macOS, skipping permission check")
        return True

    try:
        # Try to create a mouse listener to test permissions
        logging.debug("Testing mouse listener...")
        with mouse.Listener(on_click=lambda *args: None) as listener:
            logging.info("Accessibility permissions granted")
            return True
    except Exception as e:
        logging.error(f"Permission error: {str(e)}")
        if "Accessibility" in str(e):
            root = tk.Tk()
            root.withdraw()  # Hide the main window

            msg = tk.Toplevel(root)
            msg.title("Accessibility Permissions Required")

            label = tk.Label(
                msg,
                text="This app requires accessibility permissions to work.\n\n"
                "1. Open System Preferences > Security & Privacy > Privacy > Accessibility\n"
                "2. Click the lock icon to make changes\n"
                "3. Add and enable Terminal or Python in the list\n"
                "4. Restart the application",
                padx=20,
                pady=20,
                wraplength=400,
            )
            label.pack()

            def open_preferences():
                subprocess.run(
                    [
                        "open",
                        "x-apple.systempreferences:com.apple.preference.security?Privacy_Accessibility",
                    ]
                )

            def quit_app():
                root.quit()
                sys.exit(0)

            tk.Button(
                msg, text="Open System Preferences", command=open_preferences
            ).pack(pady=5)
            tk.Button(msg, text="Quit", command=quit_app).pack(pady=5)

            # Center the window
            msg.update_idletasks()
            width = msg.winfo_width()
            height = msg.winfo_height()
            x = (msg.winfo_screenwidth() // 2) - (width // 2)
            y = (msg.winfo_screenheight() // 2) - (height // 2)
            msg.geometry(f"{width}x{height}+{x}+{y}")

            msg.mainloop()
            return False

        return False


def search_in_file(keyword, context_lines=3):  # Reduced context lines
    logging.debug(f"Searching for keyword: {keyword}")
    results = []

    try:
        if not os.path.exists(TEXT_FILE_PATH):
            logging.error(f"File not found: {TEXT_FILE_PATH}")
            return [f"Error: File {TEXT_FILE_PATH} not found"]

        with open(TEXT_FILE_PATH, "r", encoding="utf-8") as file:
            # Use deque with maxlen for efficient ring buffer
            context_buffer = deque(maxlen=context_lines * 2 + 1)
            line_num = 0

            for line in file:
                context_buffer.append(line.strip())

                if len(context_buffer) == context_lines * 2 + 1:
                    if keyword.lower() in context_buffer[context_lines].lower():
                        snippet = "\n".join(list(context_buffer))
                        results.append(snippet)
                        if len(results) >= MAX_RESULTS:  # Limit number of results
                            logging.info(
                                f"Reached maximum results limit ({MAX_RESULTS})"
                            )
                            break
                line_num += 1

                if line_num % 1000 == 0:  # Periodic garbage collection
                    import gc

                    gc.collect()

    except Exception as e:
        logging.error(f"Error reading file: {str(e)}")
        results.append(f"[Error reading file: {e}]")

    logging.info(f"Found {len(results)} matches")
    return results if results else [f"No match found for: '{keyword}'"]


def create_popup(text_list):
    global popup_window, current_index, root
    logging.debug("Creating popup window")

    if not root:
        logging.error("Root window is None, cannot create popup")
        return

    if not root.winfo_exists():
        logging.error("Root window has been destroyed")
        return

    current_index = 0

    try:
        if popup_window and popup_window.winfo_exists():
            logging.debug("Destroying existing popup")
            popup_window.destroy()
            del popup_window  # Explicitly delete old window

        popup_window = tk.Toplevel(root)
        popup_window.protocol(
            "WM_DELETE_WINDOW",
            lambda: (
                popup_window.destroy(),
                setattr(sys.modules[__name__], "popup_window", None),
            ),
        )
        popup_window.overrideredirect(True)
        popup_window.attributes("-topmost", True)
        popup_window.attributes("-alpha", 0.9)  # Slight transparency

        def update_display():
            logging.debug(f"Updating display to index {current_index}")
            for widget in popup_window.winfo_children():
                if isinstance(widget, tk.Label):
                    widget.config(text=text_list[current_index])

        def on_key(event):
            global current_index
            logging.debug(f"Key pressed: {event.keysym}")
            if event.keysym in ("Right", "x") and current_index < len(text_list) - 1:
                current_index += 1
                update_display()
            elif event.keysym in ("Left", "z") and current_index > 0:
                current_index -= 1
                update_display()
            elif event.keysym == "Escape":
                logging.debug("Closing popup (Escape pressed)")
                popup_window.destroy()

        def on_move(x, y):
            try:
                if popup_window and popup_window.winfo_exists():
                    logging.debug(f"Mouse moved to ({x}, {y})")
                    popup_window.destroy()
                return False
            except Exception as e:
                logging.error(f"Error in on_move: {str(e)}")
                return False

        popup_window.bind("<Key>", on_key)
        popup_window.focus_force()

        label = tk.Label(
            popup_window,
            text=text_list[0],
            font=("Courier", 9),
            bg="black",
            fg="white",
            justify="left",
            anchor="nw",
            padx=3,
            pady=3,
            wraplength=300,  # Smaller text wrap width
        )
        label.pack(fill=tk.BOTH, expand=True)

        # Position window at the bottom center of the screen
        popup_window.update_idletasks()
        sw = popup_window.winfo_screenwidth()
        sh = popup_window.winfo_screenheight()
        w = 300  # Width of the popup
        h = 100  # Height of the popup
        x = (sw // 2) - (w // 2)  # Center horizontally
        y = sh - h - 40  # Position near the bottom
        popup_window.geometry(f"{w}x{h}+{x}+{y}")

        # Listen for mouse movement to close popup
        mouse_listener = mouse.Listener(on_move=on_move)
        mouse_listener.daemon = True  # Make sure thread doesn't prevent program exit
        mouse_listener.start()

        logging.info("Popup window created successfully")
    except Exception as e:
        logging.error(f"Error creating popup: {str(e)}\n{traceback.format_exc()}")


def show_popup(text_list):
    if root:
        logging.debug("Scheduling popup creation")
        root.after(0, lambda: create_popup(text_list))
    else:
        logging.error("Root window not available")


def on_mouse_release(x, y, button, pressed):
    if not pressed and is_running:
        logging.debug(f"Mouse released at ({x}, {y})")
        try:
            kb = keyboard.Controller()
            with kb.pressed(keyboard.Key.ctrl):
                kb.press("c")
                kb.release("c")

            time.sleep(0.1)
            selected = pyperclip.paste().strip()

            if not selected:
                logging.debug("No text selected")
                return

            logging.debug(f"Selected text: {selected[:50]}...")

            global last_text
            if selected and selected != last_text:
                last_text = selected
                matches = search_in_file(selected)
                show_popup(matches)
        except Exception as e:
            logging.error(
                f"Error handling mouse release: {str(e)}\n{traceback.format_exc()}"
            )


if __name__ == "__main__":
    logging.info("Starting application...")
    try:
        if not check_accessibility_permissions():
            logging.error("Permission check failed")
            sys.exit(1)

        root = tk.Tk()
        root.protocol(
            "WM_DELETE_WINDOW",
            lambda: (
                setattr(sys.modules[__name__], "is_running", False),
                root.destroy(),
            ),
        )
        root.withdraw()  # Hide the main window
        logging.debug("Root window created and hidden")

        # Start mouse listener
        mouse_listener = mouse.Listener(on_click=on_mouse_release)
        mouse_listener.daemon = True  # Make sure thread doesn't prevent program exit
        mouse_listener.start()
        logging.info("Mouse listener started")

        # Keep checking if we should continue running
        def check_running():
            if is_running and root.winfo_exists():
                root.after(1000, check_running)
            else:
                logging.info("Application stopping...")
                root.quit()

        root.after(1000, check_running)

        logging.info("Entering main loop")
        root.mainloop()

    except Exception as e:
        logging.critical(f"Critical error: {str(e)}\n{traceback.format_exc()}")
        sys.exit(1)
    finally:
        logging.info("Application terminated")
