import os
import sys
import time
import random
import threading
import tkinter as tk
import ctypes
import keyboard
import queue

# --- Admin Check ---
if not ctypes.windll.shell32.IsUserAnAdmin():
    params = " ".join([f'"{arg}"' for arg in sys.argv])
    ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, params, None, 0)
    sys.exit()

# --- Global State ---
running = True
active = True
injecting = False
injecting_lock = threading.Lock()
key_queue = queue.Queue()

# We do NOT suppress these. We let them pass through instantly 
# so Windows knows Shift/Ctrl is held BEFORE the delayed letter arrives.
PASS_THROUGH = {
    "shift", "left shift", "right shift",
    "ctrl", "left ctrl", "right ctrl",
    "alt", "left alt", "right alt",
    "windows", "left windows", "right windows",
    "caps lock",
}

def stop_program():
    global running
    running = False
    keyboard.unhook_all()
    try:
        root.after(0, root.destroy)
    except:
        pass

def toggle_active():
    global active
    active = not active
    label.config(
        text="● ANON ACTIVE" if active else "○ BYPASS MODE",
        fg="#00FF66" if active else "#FFCC00"
    )

def on_key(e):
    global injecting
    # If we are the ones typing, don't hook it!
    if injecting:
        return True

    # System Keys
    if e.event_type == "down":
        if e.name == "esc":
            threading.Thread(target=stop_program, daemon=True).start()
            return True
        if e.name == "f8":
            toggle_active()
            return True

    # 1. Let Modifiers through instantly (fixes Caps/Symbols/Shortcuts)
    if e.name in PASS_THROUGH:
        return True

    # 2. If bypass is on, let everything through
    if not active:
        return True

    # 3. Otherwise, queue the physical Scan Code and suppress the original
    key_queue.put((e.scan_code, e.event_type))
    return False 

# Initialize the hook
keyboard.hook(on_key, suppress=True)

def delay_worker():
    global injecting
    while running:
        try:
            # We get the scan_code (the physical button index)
            scan_code, event_type = key_queue.get(timeout=0.1)
        except queue.Empty:
            continue

        if not running: break

        # Human-like delay
        if event_type == "down":
            time.sleep(random.uniform(0.02, 0.06))

        with injecting_lock:
            injecting = True
            try:
                if event_type == "down":
                    keyboard.press(scan_code)
                else:
                    keyboard.release(scan_code)
            finally:
                injecting = False

# --- UI ---
root = tk.Tk()
root.title("AnonType")
root.geometry("240x40")
root.attributes("-topmost", True)
root.overrideredirect(True)
root.configure(bg="#111")

def start_move(event): root.x, root.y = event.x, event.y
def on_move(event): 
    x = root.winfo_x() + (event.x - root.x)
    y = root.winfo_y() + (event.y - root.y)
    root.geometry(f"+{x}+{y}")

f = tk.Frame(root, bg="#111", highlightbackground="#333", highlightthickness=1)
f.pack(fill="both", expand=True)

label = tk.Label(f, text="● ANON ACTIVE", fg="#00FF66", bg="#111", font=("Consolas", 9, "bold"))
label.pack(side="left", padx=10)

root.bind("<ButtonPress-1>", start_move)
root.bind("<B1-Motion>", on_move)

tk.Button(f, text="✕", command=stop_program, bg="#111", fg="white", bd=0, padx=10).pack(side="right", fill="y")

threading.Thread(target=delay_worker, daemon=True).start()
root.mainloop()