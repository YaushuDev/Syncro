# automation_tab.py
# Ubicación: /syncro_bot/gui/tabs/automation_tab.py
"""
Pestaña de automatización para Syncro Bot.
Proporciona la interfaz para configurar y gestionar tareas automatizadas.
"""

import tkinter as tk
from tkinter import ttk


class AutomationTab:
    def __init__(self, parent_notebook):
        self.parent = parent_notebook
        self.create_tab()

    def create_tab(self):
        """Crear la pestaña de automatización"""
        self.frame = ttk.Frame(self.parent)
        self.parent.add(self.frame, text="Automatización")

        # Placeholder del título
        title_label = tk.Label(self.frame, text="Automatización",
                               font=("Arial", 16, "bold"))
        title_label.pack(pady=20)