# main.py
# Ubicación: /syncro_bot/main.py
"""
Punto de entrada principal de Syncro Bot.
Inicializa la aplicación GUI y ejecuta el bucle principal de la interfaz.
"""

from gui.main_window import MainWindow
import tkinter as tk

def main():
    """Función principal para inicializar Syncro Bot"""
    root = tk.Tk()
    app = MainWindow(root)
    root.mainloop()

if __name__ == "__main__":
    main()