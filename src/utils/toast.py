import tkinter as tk
from tkinter import Toplevel, Label
import logging

class Toast:
    def __init__(self, root):
        self.root = root
        self.toast_window = None
        self.logger = logging.getLogger(__name__)

    def show_toast(self, message, color, duration_ms=3000):
        """Displays a temporary toast notification."""
        if self.toast_window and self.toast_window.winfo_exists():
            self.toast_window.destroy()

        self.toast_window = Toplevel(self.root)
        self.toast_window.overrideredirect(True) # Remove window decorations
        self.toast_window.attributes('-alpha', 0.0) # Start fully transparent
        
        # Calculate position (bottom-right of the main window)
        x = self.root.winfo_x() + self.root.winfo_width() - 320
        y = self.root.winfo_y() + self.root.winfo_height() - 70
        self.toast_window.geometry(f"300x50+{x}+{y}")
        
        label = Label(self.toast_window, text=message, bg=color, fg="white", font=("Helvetica", 10, "bold"), padx=10, pady=10)
        label.pack(fill=tk.BOTH, expand=True)

        self._fade_in()
        self.root.after(duration_ms, self._fade_out)
        self.logger.info(f"Toast displayed: '{message}' with color {color}")

    def _fade_in(self):
        alpha = self.toast_window.attributes('-alpha')
        if alpha < 1.0:
            alpha += 0.1
            self.toast_window.attributes('-alpha', alpha)
            self.root.after(50, self._fade_in)
        
    def _fade_out(self):
        if not self.toast_window or not self.toast_window.winfo_exists():
            return # Window might have been closed already

        alpha = self.toast_window.attributes('-alpha')
        if alpha > 0.1:
            alpha -= 0.1
            self.toast_window.attributes('-alpha', alpha)
            self.root.after(50, self._fade_out)
        else:
            self.toast_window.destroy()
            self.logger.debug("Toast faded out and destroyed.")

# Global instance of Toast for easy access
_global_toast_instance = None

def show_toast(root, message, color, duration_ms=3000):
    """Helper function to show a toast notification using a global instance."""
    global _global_toast_instance
    if _global_toast_instance is None or not _global_toast_instance.root.winfo_exists():
        _global_toast_instance = Toast(root)
    _global_toast_instance.show_toast(message, color, duration_ms)