# main_window.py
# Ubicación: /syncro_bot/gui/main_window.py
# Syncro Bot - Ventana principal de la interfaz gráfica

import tkinter as tk
from tkinter import ttk
from .tabs.automation_tab import AutomationTab
from .tabs.email_tab import EmailTab
from .tabs.registro_tab import RegistroTab


class MainWindow:
    def __init__(self, root):
        self.root = root
        self.setup_window()
        self.create_tabs()

    def setup_window(self):
        """Configurar las propiedades básicas de la ventana"""
        self.root.title("Syncro Bot")
        self.root.geometry("800x600")
        self.root.resizable(True, True)

    def create_tabs(self):
        """Crear el sistema de pestañas"""
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill='both', expand=True, padx=10, pady=10)

        # Inicializar las pestañas
        self.automation_tab = AutomationTab(self.notebook)
        self.email_tab = EmailTab(self.notebook)
        self.registro_tab = RegistroTab(self.notebook)