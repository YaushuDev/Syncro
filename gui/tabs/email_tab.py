# email_tab.py
# Ubicación: /syncro_bot/gui/tabs/email_tab.py
# Syncro Bot - Pestaña de Email

import tkinter as tk
from tkinter import ttk


class EmailTab:
    def __init__(self, parent_notebook):
        self.parent = parent_notebook
        self.create_tab()

    def create_tab(self):
        """Crear la pestaña de email"""
        self.frame = ttk.Frame(self.parent)
        self.parent.add(self.frame, text="Email")

        # Placeholder del título
        title_label = tk.Label(self.frame, text="Email",
                               font=("Arial", 16, "bold"))
        title_label.pack(pady=20)