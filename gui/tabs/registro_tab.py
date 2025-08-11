# registro_tab.py
# Ubicación: /syncro_bot/gui/tabs/registro_tab.py
# Syncro Bot - Pestaña de Registro

import tkinter as tk
from tkinter import ttk


class RegistroTab:
    def __init__(self, parent_notebook):
        self.parent = parent_notebook
        self.create_tab()

    def create_tab(self):
        """Crear la pestaña de registro"""
        self.frame = ttk.Frame(self.parent)
        self.parent.add(self.frame, text="Registro")

        # Placeholder del título
        title_label = tk.Label(self.frame, text="Registro",
                               font=("Arial", 16, "bold"))
        title_label.pack(pady=20)