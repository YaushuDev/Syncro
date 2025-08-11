# main_window.py
# Ubicación: /syncro_bot/gui/main_window.py
"""
Ventana principal de la interfaz gráfica de Syncro Bot.
Gestiona la configuración de la ventana, la creación del sistema de pestañas
y el manejo correcto del cierre de la aplicación.
"""

from tkinter import ttk
import time
from .tabs.automation_tab import AutomationTab
from .tabs.email_tab import EmailTab
from .tabs.registro_tab import RegistroTab


class MainWindow:
    def __init__(self, root):
        self.root = root
        self.is_closing = False
        self.setup_window()
        self.create_tabs()
        self.setup_close_handler()

    def setup_window(self):
        """Configurar las propiedades básicas de la ventana"""
        self.root.title("Syncro Bot")
        self.root.geometry("1100x600")
        self.root.resizable(True, True)

        # Configurar el icono de la ventana si existe
        try:
            # Opcional: agregar icono si tienes uno
            # self.root.iconbitmap("icon.ico")
            pass
        except:
            pass

    def create_tabs(self):
        """Crear el sistema de pestañas"""
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill='both', expand=True, padx=10, pady=10)

        # Inicializar las pestañas
        self.automation_tab = AutomationTab(self.notebook)
        self.email_tab = EmailTab(self.notebook)
        self.registro_tab = RegistroTab(self.notebook)

    def setup_close_handler(self):
        """Configura el manejo correcto del cierre de la aplicación"""
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

        # Manejar Ctrl+C en la consola
        try:
            import signal
            signal.signal(signal.SIGINT, self.signal_handler)
        except:
            pass

    def signal_handler(self, signum, frame):
        """Maneja señales del sistema (como Ctrl+C)"""
        self.on_closing()

    def on_closing(self):
        """Maneja el cierre de la aplicación de forma segura"""
        if self.is_closing:
            return

        self.is_closing = True

        try:
            # Limpiar pestaña de automatización
            if hasattr(self, 'automation_tab') and self.automation_tab:
                if self.automation_tab.get_automation_status():
                    self.automation_tab.automation_service.pause_automation()
                self.automation_tab.cleanup()

            # Limpiar otras pestañas si tienen métodos de limpieza
            if hasattr(self, 'email_tab') and self.email_tab:
                if hasattr(self.email_tab, 'cleanup'):
                    self.email_tab.cleanup()

            # Pequeña pausa para permitir que los hilos daemon se terminen
            time.sleep(0.1)

        except Exception as e:
            print(f"Error durante el cierre: {e}")
        finally:
            # Forzar la destrucción de la ventana
            try:
                self.root.quit()
                self.root.destroy()
            except:
                pass

    def get_automation_tab(self):
        """Retorna la instancia de la pestaña de automatización"""
        return self.automation_tab if hasattr(self, 'automation_tab') else None

    def get_email_tab(self):
        """Retorna la instancia de la pestaña de email"""
        return self.email_tab if hasattr(self, 'email_tab') else None

    def get_registro_tab(self):
        """Retorna la instancia de la pestaña de registro"""
        return self.registro_tab if hasattr(self, 'registro_tab') else None