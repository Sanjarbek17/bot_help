import tkinter as tk
from pynput import mouse
from pynput.mouse import Controller
import subprocess
import time

TEXT_FILE_PATH = "test.txt"  # ⬅️ Set your file path here


def get_clipboard_text():
    try:
        return subprocess.check_output("pbpaste", universal_newlines=True)
    except Exception:
        return ""


def search_in_file(keyword, context=4):
    matches = []
    try:
        with open(TEXT_FILE_PATH, "r", encoding="utf-8") as f:
            lines = f.readlines()
        for i, line in enumerate(lines):
            if keyword.lower() in line.lower():
                start = max(0, i - context)
                end = min(len(lines), i + context + 1)
                snippet = "".join(lines[start:end]).strip()
                matches.append(snippet)
    except Exception as e:
        matches.append(f"Error reading file: {e}")
    if not matches:
        matches.append(f"No results for: '{keyword}'")
    return matches


def show_popup(text_snippets):
    if not text_snippets:
        return

    popup = tk.Toplevel()
    popup.attributes("-topmost", True)
    popup.overrideredirect(True)
    popup.attributes("-alpha", 0.85)  # Set transparency
    popup.configure(bg="#000000")

    # Create a temporary label to calculate required height
    temp_label = tk.Label(
        popup,
        text=text_snippets[0],
        font=("Courier", 12),
        wraplength=680,
        justify="left",
    )
    temp_label.pack()
    temp_label.update()

    # Calculate required height (add small padding)
    required_height = temp_label.winfo_height() + 20
    temp_label.destroy()

    width = 700
    screen_width = popup.winfo_screenwidth()
    screen_height = popup.winfo_screenheight()
    x = (screen_width - width) // 2
    y = screen_height - required_height - 60
    popup.geometry(f"{width}x{required_height}+{x}+{y}")

    index = {"current": 0}

    label = tk.Label(
        popup,
        text=text_snippets[0],
        font=("Courier", 12),
        bg="#000000",
        fg="#FFFFFF",
        wraplength=680,
        justify="left",
    )
    label.pack(padx=10, pady=10)

    def update_label():
        label.config(text=text_snippets[index["current"]])

    def key_handler(event):
        if event.keysym in ["Right", "n"]:
            if index["current"] < len(text_snippets) - 1:
                index["current"] += 1
                update_label()
        elif event.keysym in ["Left", "p"]:
            if index["current"] > 0:
                index["current"] -= 1
                update_label()
        elif event.keysym == "Escape":
            popup.destroy()

    def on_mouse_move(event):
        popup.destroy()

    popup.bind("<Key>", key_handler)
    popup.bind("<Motion>", on_mouse_move)
    popup.focus_force()


def on_mouse_release(x, y, button, pressed):
    if not pressed:
        subprocess.run("pbcopy < /dev/null", shell=True)
        subprocess.run(
            'osascript -e \'tell application "System Events" to keystroke "c" using command down\'',
            shell=True,
        )

        time.sleep(0.2)
        selected_text = get_clipboard_text().strip()

        if selected_text:
            snippets = search_in_file(selected_text)
            # Show popup in GUI thread
            root.after(0, lambda: show_popup(snippets))
            # Click again at the same position to deselect
            mouse_controller = Controller()
            mouse_controller.position = (x, y)
            mouse_controller.click(button)


# Create a root Tk instance (used only for scheduling)
root = tk.Tk()
root.withdraw()

# Start mouse listener
mouse.Listener(on_click=on_mouse_release).start()

# Run the main loop to process GUI events
root.mainloop()
