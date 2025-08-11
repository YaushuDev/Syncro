# main.py
# Ubicación: /syncro_bot/main.py
# Syncro Bot - Punto de entrada principal

from gui.main_window import MainWindow
import tkinter as tk

def main():
    """Función principal para inicializar Syncro Bot"""
    root = tk.Tk()
    app = MainWindow(root)
    root.mainloop()

if __name__ == "__main__":
    main()