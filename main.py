# main.py
# Ubicación: /syncro_bot/main.py
"""
Punto de entrada principal de Syncro Bot.
Inicializa la aplicación GUI y ejecuta el bucle principal de la interfaz
con manejo robusto de excepciones y cierre seguro.
"""

import tkinter as tk
import sys
import signal
from gui.main_window import MainWindow

def signal_handler(signum, frame):
    """Maneja señales del sistema para cierre limpio"""
    print("\nCerrando Syncro Bot...")
    sys.exit(0)


def main():
    """Función principal para inicializar Syncro Bot"""
    try:
        # Configurar manejo de señales
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

        # Crear ventana principal
        root = tk.Tk()
        app = MainWindow(root)

        # Ejecutar bucle principal con manejo de excepciones
        try:
            root.mainloop()
        except KeyboardInterrupt:
            print("\nCerrando Syncro Bot...")
        except Exception as e:
            print(f"Error en la aplicación: {e}")
        finally:
            # Asegurar cierre limpio
            try:
                if root and root.winfo_exists():
                    root.quit()
                    root.destroy()
            except:
                pass

    except Exception as e:
        print(f"Error fatal al inicializar Syncro Bot: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()