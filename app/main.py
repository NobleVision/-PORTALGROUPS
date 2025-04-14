import sys
import os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

import tkinter as tk
from ui.main_window import DXNetOpsTroubleshooter

def main():
    root = tk.Tk()
    app = DXNetOpsTroubleshooter(root)
    root.mainloop()

if __name__ == "__main__":
    main()
