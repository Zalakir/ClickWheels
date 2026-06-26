import os
import subprocess
import sys
import time
import threading
import tkinter as tk
from pynput.mouse import Controller, Button
from pynput.keyboard import Listener, KeyCode
from tkinter import ttk


def relaunch_with_pythonw():
    #On Windows, relaunch the app with pythonw.exe so only the GUI opens.
    if os.name != "nt":
        return

    executable = os.path.abspath(sys.executable)
    if not executable.lower().endswith("python.exe"):
        return

    pythonw_path = executable.replace("python.exe", "pythonw.exe")
    if not os.path.exists(pythonw_path):
        return

    subprocess.Popen(
        [pythonw_path, os.path.abspath(__file__)],
        creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
    )
    raise SystemExit(0)


relaunch_with_pythonw()

# Define the key to toggle on/off.
TOGGLE_KEY = KeyCode(char="t")

# Global state used by the clicker thread and GUI.
clicking = False
mouse = Controller()
stop_event = threading.Event()

# Create the main application window and configure its basic properties.
root = tk.Tk()
root.geometry("400x200")
root.title("ClickWheels")

# Keep the application window on top.
root.attributes('-topmost', True)


# Load the icon from the assets folder, 
# If the icon file is missing or invalid, ignore and continue.
icon_path = os.path.join(os.path.dirname(__file__), "assets", "clickwheels.ico")
if os.path.exists(icon_path):
    try:
        root.iconbitmap(icon_path)
    except Exception:
        pass

# Create StringVar and DoubleVar instances for the GUI controls.
# status_var is shown in the status label, interval_var is bound to the slider.
status_var = tk.StringVar(value="Stopped")
interval_var = tk.DoubleVar(value=0.50)

# Define the clicker function that will run in a separate thread.
def clicker():
    #Continuously click while the clicker is enabled.
    while not stop_event.is_set():
        if clicking:
            mouse.click(Button.left, 1)
        # Use the current slider value as the delay between clicks.
        time.sleep(max(0.01, interval_var.get()))

# Update the status label based on the clicking state.
def update_status():
    #Refresh the status text and color in the GUI.
    status_var.set("Clicking" if clicking else "Stopped")
    if clicking:
        status_value.config(foreground="green")
    else:
        status_value.config(foreground="red")

# Define the function to toggle clicking state.
def toggle_clicking():
    #Switch the clicker on or off and update the GUI.
    global clicking
    clicking = not clicking
    update_status()

# Define the function to handle key presses.
def on_press(key):
    #Respond to the toggle hotkey from the keyboard listener.
    if key == TOGGLE_KEY:
        root.after(0, toggle_clicking)

# Define the function to handle window closing.
def on_closing():
    #Stop background threads and close the application cleanly.
    stop_event.set()
    if listener is not None:
        listener.stop()
    root.destroy()

## GUI Setup
# Create the GUI layout using ttk widgets.
frame = ttk.Frame(root, padding=16)
frame.grid(sticky="NSEW")
root.columnconfigure(0, weight=1)
root.rowconfigure(0, weight=1)

# Create and place the status label and value.
status_label = ttk.Label(frame, text="Status:")
status_label.grid(row=0, column=0, sticky="W", pady=(0, 6))
status_value = ttk.Label(frame, textvariable=status_var, foreground="red")
status_value.grid(row=0, column=1, sticky="W", pady=(0, 6))

# Create and place the interval label, current value, and slider.
interval_label = ttk.Label(frame, text="Interval (seconds)")
interval_label.grid(row=1, column=0, sticky="W")

# Display the current interval value to the right of the label.
interval_value = ttk.Label(frame, text=f"{interval_var.get():.2f}")
interval_value.grid(row=1, column=1, sticky="W", padx=(8, 0))

# Slider control to adjust the delay between mouse clicks.
interval_slider = ttk.Scale(
    frame,
    from_=0.01,
    to=2.0,
    variable=interval_var,
    orient="horizontal",
)
interval_slider.grid(row=1, column=1, sticky="EW", padx=(40, 0))


def refresh_interval_label(*args):
    #Update the displayed interval text whenever the slider value changes.
    interval_value.config(text=f"{interval_var.get():.2f}")

interval_var.trace_add("write", refresh_interval_label)

# Button to toggle the clicker state manually.
toggle_button = ttk.Button(frame, text="Toggle Clicker (T)", command=toggle_clicking)
toggle_button.grid(row=2, column=0, columnspan=3, pady=(12, 0), sticky="EW")

# Inform the user about the keyboard hotkey.
hotkey_label = ttk.Label(frame, text="Press 'T' to start/stop clicking")
hotkey_label.grid(row=3, column=0, columnspan=3, pady=(8, 0), sticky="W")

# Allow the middle column to expand so the slider can grow.
frame.columnconfigure(1, weight=1)

# Start the background clicker thread.
click_thread = threading.Thread(target=clicker, daemon=True)
click_thread.start()

# Start the keyboard listener thread.
listener = Listener(on_press=on_press, daemon=True)
listener.start()

# Register the close callback and start the GUI event loop.
root.protocol("WM_DELETE_WINDOW", on_closing)
root.mainloop()