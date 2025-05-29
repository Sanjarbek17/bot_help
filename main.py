import tkinter as tk
import pyperclip
from pynput import mouse, keyboard
import time
import sys
import os
import subprocess
import logging
import ctypes


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
        return True

    try:
        # Try to create a mouse listener to test permissions
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


def search_in_file(keyword, context_lines=10):  # Reduced context lines tcp
    results = []

    try:
        if not os.path.exists(TEXT_FILE_PATH):
            logging.error(f"File not found: {TEXT_FILE_PATH}")
            return [f"Error: File {TEXT_FILE_PATH} not found"]

        with open(TEXT_FILE_PATH, "r", encoding="utf-8") as file:
            line_num = 0

            for line in file:
                if keyword.lower() in line.lower():
                    snippet = line.strip()
                    # Add additional lines after the match
                    for _ in range(context_lines):
                        next_line = next(file, None)
                        if next_line:
                            snippet += f"\n{next_line.strip()}"
                    results.append(snippet)
                    if len(results) >= MAX_RESULTS:  # Limit number of results
                        break
                line_num += 1

                if line_num % 1000 == 0:  # Periodic garbage collection
                    import gc

                    gc.collect()

    except Exception as e:
        logging.error(f"Error reading file: {str(e)}")
        results.append(f"[Error reading file: {e}]")

    return results if results else [f"No match found for: '{keyword}'"]


def create_popup(text_list):
    global popup_window, current_index, root

    if not root:
        return

    if not root.winfo_exists():
        return

    current_index = 0

    try:
        if popup_window and popup_window.winfo_exists():
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
            for widget in popup_window.winfo_children():
                if isinstance(widget, tk.Label):
                    widget.config(
                        text=f"Match {current_index + 1}/{len(text_list)}:\n{text_list[current_index]}"
                    )

        def on_key(event):
            global current_index
            if event.keysym in ("Right", "x") and current_index < len(text_list) - 1:
                current_index += 1
                update_display()
            elif event.keysym in ("Left", "z") and current_index > 0:
                current_index -= 1
                update_display()
            elif event.keysym == "Escape":
                popup_window.destroy()

        def on_move(x, y):
            try:
                if popup_window and popup_window.winfo_exists():
                    if not hasattr(on_move, "last_position"):
                        on_move.last_position = (x, y)

                    last_x, last_y = on_move.last_position
                    if abs(x - last_x) > 10 or abs(y - last_y) > 10:
                        popup_window.destroy()
                        setattr(sys.modules[__name__], "popup_window", None)

                    on_move.last_position = (x, y)
                return True
            except Exception as e:
                return False

        popup_window.bind("<Key>", on_key)
        popup_window.focus_force()
        popup_window.config(bg="white")
        popup_window.attributes("-transparentcolor", "white")

        label = tk.Label(
            popup_window,
            text=f"Match 1/{len(text_list)}:\n{text_list[0]}",
            font=("Courier", 9),
            bg="white",
            fg="black",
            justify="left",
            anchor="nw",
            padx=3,
            pady=3,
            wraplength=300,
        )
        label.pack(fill=tk.BOTH, expand=True)

        popup_window.update_idletasks()
        sw = popup_window.winfo_screenwidth()
        sh = popup_window.winfo_screenheight()
        w = 300
        h = 200
        x = (sw // 2) - (w // 2)
        y = sh - h - 100
        popup_window.geometry(f"{w}x{h}+{x}+{y}")

        mouse_listener = mouse.Listener(on_move=on_move)
        mouse_listener.daemon = True
        mouse_listener.start()

    except Exception as e:
        pass


def show_popup(text_list):
    if root:
        root.after(0, lambda: create_popup(text_list))
    else:
        logging.error("Root window not available")


def on_mouse_release(x, y, button, pressed):
    if not pressed and is_running:
        try:
            kb = keyboard.Controller()
            with kb.pressed(keyboard.Key.ctrl):
                kb.press("c")
                kb.release("c")

            time.sleep(0.1)
            selected = pyperclip.paste().strip()

            if not selected:
                return

            global last_text
            if selected and selected != last_text:
                last_text = selected
                matches = search_in_file(selected)
                show_popup(matches)
        except Exception as e:
            pass


# Add a keyboard listener to stop the program when Ctrl+Q is pressed
def on_key_press(key):
    print("Key pressed:", key.name)
    print(type(key.name))
    global is_running
    try:
        if "\x11" == key:
            print("Ctrl+Q pressed, stopping the program...")
            is_running = False
            print("Stopping the program...")
            root.quit()
            sys.exit(0)
    except Exception as e:
        pass


keyboard_listener = keyboard.Listener(on_press=on_key_press)
keyboard_listener.daemon = True
keyboard_listener.start()


if __name__ == "__main__":
    try:
        if not check_accessibility_permissions():
            sys.exit(1)

        root = tk.Tk()
        root.protocol(
            "WM_DELETE_WINDOW",
            lambda: (
                setattr(sys.modules[__name__], "is_running", False),
                root.destroy(),
            ),
        )
        root.withdraw()

        mouse_listener = mouse.Listener(on_click=on_mouse_release)
        mouse_listener.daemon = True
        mouse_listener.start()

        def check_running():
            if is_running and root.winfo_exists():
                root.after(1000, check_running)
            else:
                root.quit()

        root.after(1000, check_running)
        root.mainloop()

    except Exception as e:
        sys.exit(1)
    finally:
        pass
