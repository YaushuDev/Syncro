# automation_tab.py
# Ubicación: /syncro_bot/gui/tabs/automation_tab.py
"""
Pestaña de automatización para Syncro Bot.
Proporciona la interfaz para configurar y gestionar tareas automatizadas
con manejo mejorado de hilos y cierre seguro.
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import webbrowser
import threading
import time
from datetime import datetime


class AutomationService:
    """Servicio de automatización para gestionar tareas automatizadas"""

    def __init__(self):
        self.is_running = False
        self.target_url = "https://fieldservice.cabletica.com/dispatchFS/"
        self._lock = threading.Lock()

    def start_automation(self):
        """Inicia el proceso de automatización"""
        try:
            with self._lock:
                if self.is_running:
                    return False, "La automatización ya está en ejecución"

                webbrowser.open(self.target_url)
                self.is_running = True
                return True, "Automatización iniciada correctamente"

        except Exception as e:
            return False, f"Error al iniciar automatización: {str(e)}"

    def pause_automation(self):
        """Pausa el proceso de automatización"""
        try:
            with self._lock:
                if not self.is_running:
                    return False, "La automatización no está en ejecución"

                self.is_running = False
                return True, "Automatización pausada correctamente"

        except Exception as e:
            return False, f"Error al pausar automatización: {str(e)}"

    def get_status(self):
        """Obtiene el estado actual de la automatización"""
        with self._lock:
            return self.is_running

    def stop_all(self):
        """Detiene todas las operaciones de automatización"""
        with self._lock:
            self.is_running = False


class AutomationTab:
    """Pestaña de automatización para Syncro Bot"""

    def __init__(self, parent_notebook):
        self.parent = parent_notebook
        self.colors = {
            'bg_primary': '#f0f0f0',
            'bg_secondary': '#e0e0e0',
            'bg_tertiary': '#ffffff',
            'text_primary': '#333333',
            'text_secondary': '#666666',
            'border': '#cccccc',
            'accent': '#0078d4',
            'success': '#107c10',
            'warning': '#ff8c00',
            'error': '#d13438',
            'info': '#0078d4'
        }

        self.automation_service = AutomationService()
        self.widgets = {}
        self._is_closing = False
        self.create_tab()

    def create_tab(self):
        """Crear la pestaña de automatización"""
        self.frame = ttk.Frame(self.parent)
        self.parent.add(self.frame, text="Automatización")
        self.create_interface()

    def create_interface(self):
        """Crea la interfaz con diseño de 2 columnas"""
        main_container = tk.Frame(self.frame, bg=self.colors['bg_primary'])
        main_container.pack(fill='both', expand=True, padx=15, pady=10)

        main_container.grid_columnconfigure(0, weight=0, minsize=500)
        main_container.grid_columnconfigure(1, weight=0, minsize=1)
        main_container.grid_columnconfigure(2, weight=1, minsize=350)
        main_container.grid_rowconfigure(0, weight=1)

        left_column = tk.Frame(main_container, bg=self.colors['bg_primary'], width=500)
        left_column.grid(row=0, column=0, sticky='ns', padx=(0, 5))
        left_column.grid_propagate(False)

        separator = tk.Frame(main_container, bg=self.colors['border'], width=1)
        separator.grid(row=0, column=1, sticky='ns', padx=5)

        right_column = tk.Frame(main_container, bg=self.colors['bg_primary'])
        right_column.grid(row=0, column=2, sticky='nsew', padx=(5, 0))

        self._create_left_column(left_column)
        self._create_right_column(right_column)

    def _create_left_column(self, parent):
        """Crea la columna izquierda con estado y controles"""
        parent.grid_rowconfigure(0, weight=0)
        parent.grid_rowconfigure(1, weight=0)
        parent.grid_rowconfigure(2, weight=1)
        parent.grid_columnconfigure(0, weight=1)

        # Estado del sistema arriba
        status_container = tk.Frame(parent, bg=self.colors['bg_primary'])
        status_container.grid(row=0, column=0, sticky='ew', pady=(0, 15))
        self._create_status_section(status_container)

        # Controles debajo
        controls_container = tk.Frame(parent, bg=self.colors['bg_primary'])
        controls_container.grid(row=1, column=0, sticky='ew', pady=(0, 15))
        self._create_controls_section(controls_container)

        # Espaciador
        spacer = tk.Frame(parent, bg=self.colors['bg_primary'])
        spacer.grid(row=2, column=0, sticky='nsew')

    def _create_right_column(self, parent):
        """Crea el contenido de la columna derecha con log"""
        parent.grid_rowconfigure(0, weight=1)
        parent.grid_columnconfigure(0, weight=1)

        # Log en la columna derecha
        log_container = tk.Frame(parent, bg=self.colors['bg_primary'])
        log_container.grid(row=0, column=0, sticky='nsew')
        self._create_log_section(log_container)

    def _create_card_frame(self, parent, title):
        """Crea un frame tipo tarjeta"""
        container = tk.Frame(parent, bg=self.colors['bg_primary'])
        container.pack(fill='both', expand=True)

        card = tk.Frame(container, bg=self.colors['bg_primary'], relief='solid', bd=1)
        card.configure(highlightbackground=self.colors['border'],
                       highlightcolor=self.colors['border'],
                       highlightthickness=1)
        card.pack(fill='both', expand=True)

        header = tk.Frame(card, bg=self.colors['bg_secondary'], height=45)
        header.pack(fill='x')
        header.pack_propagate(False)

        tk.Label(header, text=title, bg=self.colors['bg_secondary'],
                 fg=self.colors['text_primary'], font=('Arial', 12, 'bold')).pack(
            side='left', padx=15, pady=12)

        content = tk.Frame(card, bg=self.colors['bg_primary'])
        content.pack(fill='both', expand=True, padx=18, pady=15)

        return content

    def _create_status_section(self, parent):
        """Crea sección de estado del sistema"""
        card = self._create_card_frame(parent, "📊 Estado del Sistema")

        status_frame = tk.Frame(card, bg=self.colors['bg_tertiary'])
        status_frame.pack(fill='x', pady=(0, 10))

        tk.Label(status_frame, text="🤖 Automatización:", bg=self.colors['bg_tertiary'],
                 fg=self.colors['text_primary'], font=('Arial', 10)).pack(
            side='left', padx=10, pady=8)

        self.widgets['automation_status'] = tk.Label(
            status_frame, text="Detenida", bg=self.colors['bg_tertiary'],
            fg=self.colors['text_secondary'], font=('Arial', 10, 'bold')
        )
        self.widgets['automation_status'].pack(side='right', padx=10, pady=8)

        url_frame = tk.Frame(card, bg=self.colors['bg_tertiary'])
        url_frame.pack(fill='x')

        tk.Label(url_frame, text="🌐 URL Objetivo:", bg=self.colors['bg_tertiary'],
                 fg=self.colors['text_primary'], font=('Arial', 10)).pack(
            side='left', padx=10, pady=8)

        self.widgets['url_status'] = tk.Label(
            url_frame, text="Cabletica Dispatch", bg=self.colors['bg_tertiary'],
            fg=self.colors['info'], font=('Arial', 10, 'bold')
        )
        self.widgets['url_status'].pack(side='right', padx=10, pady=8)

    def _create_controls_section(self, parent):
        """Crea sección de controles"""
        card = self._create_card_frame(parent, "🎮 Controles de Automatización")

        self.widgets['start_button'] = self._create_styled_button(
            card, "▶️ Iniciar Automatización",
            self._start_automation, self.colors['success']
        )
        self.widgets['start_button'].pack(fill='x', pady=(0, 15))

        self.widgets['pause_button'] = self._create_styled_button(
            card, "⏸️ Pausar Automatización",
            self._pause_automation, self.colors['warning']
        )
        self.widgets['pause_button'].pack(fill='x')
        self.widgets['pause_button'].configure(state='disabled')

    def _create_log_section(self, parent):
        """Crea sección de log"""
        card = self._create_card_frame(parent, "📋 Log de Actividades")

        # Área de texto con scroll
        self.widgets['log_text'] = scrolledtext.ScrolledText(
            card,
            bg=self.colors['bg_tertiary'],
            fg=self.colors['text_primary'],
            font=('Consolas', 9),
            relief='flat',
            wrap=tk.WORD,
            state=tk.DISABLED
        )
        self.widgets['log_text'].pack(fill='both', expand=True, pady=(0, 10))

        # Botón para limpiar log
        clear_log_btn = self._create_styled_button(
            card, "🗑️ Limpiar Log",
            self._clear_log, self.colors['text_secondary']
        )
        clear_log_btn.pack(fill='x')

        # Agregar mensaje inicial al log
        self._add_log_entry("Sistema iniciado")

    def _create_styled_button(self, parent, text, command, color):
        """Crea un botón con estilo"""
        btn = tk.Button(
            parent,
            text=text,
            command=command,
            bg=color,
            fg='white',
            font=('Arial', 10, 'bold'),
            relief='flat',
            padx=20,
            pady=12,
            cursor='hand2'
        )
        return btn

    def _add_log_entry(self, message, level="INFO"):
        """Añade una entrada al log"""
        if self._is_closing or 'log_text' not in self.widgets:
            return

        try:
            timestamp = datetime.now().strftime("%H:%M:%S")
            log_entry = f"[{timestamp}] {level}: {message}\n"

            self.widgets['log_text'].configure(state=tk.NORMAL)
            self.widgets['log_text'].insert(tk.END, log_entry)
            self.widgets['log_text'].configure(state=tk.DISABLED)
            self.widgets['log_text'].see(tk.END)
        except:
            pass

    def _clear_log(self):
        """Limpia el contenido del log"""
        if self._is_closing or 'log_text' not in self.widgets:
            return

        try:
            self.widgets['log_text'].configure(state=tk.NORMAL)
            self.widgets['log_text'].delete(1.0, tk.END)
            self.widgets['log_text'].configure(state=tk.DISABLED)
            self._add_log_entry("Log limpiado")
        except:
            pass

    def _start_automation(self):
        """Inicia la automatización"""
        if self._is_closing:
            return

        def start_thread():
            try:
                if self._is_closing:
                    return

                self._add_log_entry("Iniciando automatización...")
                success, message = self.automation_service.start_automation()

                if not self._is_closing:
                    self.frame.after(0, lambda: self._handle_start_result(success, message))
            except Exception as e:
                if not self._is_closing:
                    self.frame.after(0, lambda: self._handle_start_result(False, str(e)))

        thread = threading.Thread(target=start_thread, daemon=True)
        thread.start()
        self.widgets['start_button'].configure(state='disabled', text='Iniciando...')

    def _pause_automation(self):
        """Pausa la automatización"""
        if self._is_closing:
            return

        try:
            self._add_log_entry("Pausando automatización...")
            success, message = self.automation_service.pause_automation()
            if success:
                self._update_automation_status("Pausada", self.colors['warning'])
                self.widgets['start_button'].configure(state='normal', text='▶️ Iniciar Automatización')
                self.widgets['pause_button'].configure(state='disabled')
                self._add_log_entry("Automatización pausada exitosamente")
                if not self._is_closing:
                    messagebox.showinfo("Éxito", message)
            else:
                self._add_log_entry(f"Error al pausar: {message}", "ERROR")
                if not self._is_closing:
                    messagebox.showerror("Error", message)
        except Exception as e:
            error_msg = str(e)
            self._add_log_entry(f"Excepción al pausar: {error_msg}", "ERROR")
            if not self._is_closing:
                messagebox.showerror("Error", f"Error al pausar automatización:\n{error_msg}")

    def _handle_start_result(self, success, message):
        """Maneja el resultado del inicio de automatización"""
        if self._is_closing:
            return

        if success:
            self._update_automation_status("En ejecución", self.colors['success'])
            self.widgets['start_button'].configure(state='disabled', text='▶️ Iniciando...')
            self.widgets['pause_button'].configure(state='normal')
            self._add_log_entry("Automatización iniciada exitosamente")
            self._add_log_entry("Página web abierta en el navegador")
            messagebox.showinfo("Éxito", f"{message}\n\nLa página web se ha abierto en su navegador.")
        else:
            self._update_automation_status("Error", self.colors['error'])
            self.widgets['start_button'].configure(state='normal', text='▶️ Iniciar Automatización')
            self.widgets['pause_button'].configure(state='disabled')
            self._add_log_entry(f"Error al iniciar: {message}", "ERROR")
            messagebox.showerror("Error", message)

    def _update_automation_status(self, text, color):
        """Actualiza el estado de la automatización"""
        if not self._is_closing and hasattr(self, 'widgets') and 'automation_status' in self.widgets:
            try:
                self.widgets['automation_status'].configure(text=text, fg=color)
            except:
                pass

    def get_automation_status(self):
        """Obtiene el estado actual de la automatización"""
        return self.automation_service.get_status()

    def cleanup(self):
        """Limpia recursos al cerrar la pestaña"""
        self._is_closing = True
        self._add_log_entry("Cerrando sistema...")
        self.automation_service.stop_all()
        time.sleep(0.05)  # Pequeña pausa para que los hilos terminen