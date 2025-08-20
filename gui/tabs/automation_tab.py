# automation_tab.py
# Ubicación: /syncro_bot/gui/tabs/automation_tab.py
"""
Pestaña de automatización refactorizada para Syncro Bot con configuración de fechas
obligatoria y estado. Coordina todos los componentes de automatización: credenciales,
configuración de fechas (ahora obligatoria), configuración de estado, servicio, UI y logging.
Incluye extracción de números de serie de equipos mediante lectura de tablas HTML.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import threading
from datetime import datetime

# Importar componentes de automatización
from ..components.automation.credentials_manager import CredentialsManager
from ..components.automation.date_config_manager import DateConfigManager
from ..components.automation.state_config_manager import StateConfigManager
from ..components.automation.automation_service import AutomationService
from ..components.automation.automation_ui_components import (
    AutomationTheme, AutomationUIFactory, CollapsibleSection
)
from ..components.automation.automation_logger import AutomationLoggerFactory, LogLevel


class AutomationTab:
    """Pestaña de automatización refactorizada con componentes modulares, configuración de fechas obligatoria y estado expandido, y extracción de números de serie"""

    def __init__(self, parent_notebook):
        self.parent = parent_notebook
        self.theme = AutomationTheme()

        # Componentes principales
        self.credentials_manager = CredentialsManager()
        self.date_config_manager = DateConfigManager()
        self.state_config_manager = StateConfigManager()
        self.automation_service = None
        self.logger = None

        # Componentes UI
        self.ui_components = {}
        self.section_frames = {}

        # Estado de secciones
        self.expanded_section = None

        # Variables para registro de ejecuciones
        self.current_execution_record = None
        self.execution_start_time = None
        self.registry_tab = None

        # Flag de cierre
        self._is_closing = False

        # Inicializar
        self._initialize_components()
        self.create_tab()
        self._setup_initial_state()

    def _initialize_components(self):
        """Inicializa los componentes principales con soporte para extracción de números de serie"""
        # Crear logger con callback para UI
        self.logger = AutomationLoggerFactory.create_ui_logger(
            ui_callback=self._log_to_ui
        )

        # Crear servicio de automatización con logger
        self.automation_service = AutomationService(logger=self._log_message)

    def set_registry_tab(self, registry_tab):
        """Establece la referencia al RegistroTab para logging"""
        self.registry_tab = registry_tab

    def create_tab(self):
        """Crear la pestaña de automatización"""
        self.frame = ttk.Frame(self.parent)
        self.parent.add(self.frame, text="Automatización")
        self._create_interface()

    def _create_interface(self):
        """Crea la interfaz con diseño de 2 columnas usando componentes modulares"""
        main_container = tk.Frame(self.frame, bg=self.theme.colors['bg_primary'])
        main_container.pack(fill='both', expand=True, padx=15, pady=10)

        # Configurar grid
        main_container.grid_columnconfigure(0, weight=0, minsize=500)
        main_container.grid_columnconfigure(1, weight=0, minsize=1)
        main_container.grid_columnconfigure(2, weight=1, minsize=350)
        main_container.grid_rowconfigure(0, weight=1)

        # Crear columnas
        self._create_left_column(main_container)
        self._create_separator(main_container)
        self._create_right_column(main_container)

    def _create_left_column(self, parent):
        """Crea la columna izquierda con secciones colapsables incluyendo configuración de estado expandida"""
        left_column = tk.Frame(parent, bg=self.theme.colors['bg_primary'], width=500)
        left_column.grid(row=0, column=0, sticky='ns', padx=(0, 5))
        left_column.grid_propagate(False)

        # Configurar filas
        left_column.grid_rowconfigure(0, weight=0)  # Credenciales
        left_column.grid_rowconfigure(1, weight=0)  # Configuración de fechas
        left_column.grid_rowconfigure(2, weight=0)  # Configuración de estado
        left_column.grid_rowconfigure(3, weight=0)  # Estado
        left_column.grid_rowconfigure(4, weight=0)  # Controles
        left_column.grid_rowconfigure(5, weight=1)  # Espaciador
        left_column.grid_columnconfigure(0, weight=1)

        # Crear secciones usando componentes modulares
        self._create_credentials_section(left_column)
        self._create_date_config_section(left_column)
        self._create_state_config_section(left_column)
        self._create_status_section(left_column)
        self._create_controls_section(left_column)

    def _create_separator(self, parent):
        """Crea separador visual"""
        separator = tk.Frame(parent, bg=self.theme.colors['border'], width=1)
        separator.grid(row=0, column=1, sticky='ns', padx=5)

    def _create_right_column(self, parent):
        """Crea la columna derecha con log usando componentes modulares"""
        right_column = tk.Frame(parent, bg=self.theme.colors['bg_primary'])
        right_column.grid(row=0, column=2, sticky='nsew', padx=(5, 0))
        right_column.grid_rowconfigure(0, weight=1)
        right_column.grid_columnconfigure(0, weight=1)

        # Crear panel de log
        log_component = AutomationUIFactory.create_log_panel(right_column, self.theme)
        self.ui_components.update(log_component.create())

        # Configurar comando de limpiar log
        log_component.set_clear_command(self._clear_log)

    def _create_credentials_section(self, parent):
        """Crea sección de credenciales usando componentes modulares"""
        section = AutomationUIFactory.create_collapsible_section(
            parent, "credentials", "🔐 Credenciales de Login", self.theme
        )
        content = section.create(row=0, min_height=200, default_expanded=True)
        section.set_toggle_callback(self._on_section_toggle)
        self.section_frames["credentials"] = section

        # Crear formulario de credenciales
        credentials_form = AutomationUIFactory.create_credentials_form(content, self.theme)
        credentials_widgets = credentials_form.create()
        self.ui_components.update(credentials_widgets)

        # Configurar comandos de botones
        credentials_form.set_button_command('test_credentials_button', self._test_credentials)
        credentials_form.set_button_command('save_credentials_button', self._save_credentials)
        credentials_form.set_button_command('clear_credentials_button', self._clear_credentials)

    def _create_date_config_section(self, parent):
        """Crea sección de configuración de fechas usando componentes modulares"""
        section = AutomationUIFactory.create_collapsible_section(
            parent, "date_config", "📅 Configuración de Fechas", self.theme
        )
        content = section.create(row=1, min_height=220, default_expanded=False)  # Cerrada por defecto
        section.set_toggle_callback(self._on_section_toggle)
        self.section_frames["date_config"] = section

        # Crear formulario de configuración de fechas
        date_config_form = AutomationUIFactory.create_date_config_form(content, self.theme)
        date_config_widgets = date_config_form.create()
        self.ui_components.update(date_config_widgets)

        # Configurar comandos de botones
        date_config_form.set_button_command('set_today_button', self._set_today_dates)
        date_config_form.set_button_command('clear_dates_button', self._clear_dates)

        # Guardar referencia al formulario para métodos específicos
        self.date_config_form = date_config_form

    def _create_state_config_section(self, parent):
        """🆕 Crea sección de configuración de estado expandida usando componentes modulares"""
        section = AutomationUIFactory.create_collapsible_section(
            parent, "state_config", "📋 Configuración de Estado", self.theme
        )
        content = section.create(row=2, min_height=220, default_expanded=False)
        section.set_toggle_callback(self._on_section_toggle)
        self.section_frames["state_config"] = section

        # Crear formulario de configuración de estado
        self._create_state_config_form(content)

    def _create_state_config_form(self, parent):
        """🆕 Crea el formulario de configuración de estado personalizado con 3 opciones"""
        # Contenedor principal
        form_frame = tk.Frame(parent, bg=self.theme.colors['bg_primary'])
        form_frame.pack(fill='both', expand=True, padx=15, pady=10)

        # Título y descripción
        title_label = tk.Label(
            form_frame,
            text="Seleccionar Estado del Dropdown",
            font=('Segoe UI', 10, 'bold'),
            fg=self.theme.colors['text_primary'],
            bg=self.theme.colors['bg_primary']
        )
        title_label.pack(anchor='w', pady=(0, 5))

        desc_label = tk.Label(
            form_frame,
            text="Configura el estado y tipo de despacho para la automatización",
            font=('Segoe UI', 8),
            fg=self.theme.colors['text_secondary'],
            bg=self.theme.colors['bg_primary']
        )
        desc_label.pack(anchor='w', pady=(0, 15))

        # Variable para radio buttons
        self.state_var = tk.StringVar(value="PENDIENTE")

        # Frame para radio buttons
        radio_frame = tk.Frame(form_frame, bg=self.theme.colors['bg_primary'])
        radio_frame.pack(fill='x', pady=(0, 15))

        # Radio button para PENDIENTE
        pendiente_radio = tk.Radiobutton(
            radio_frame,
            text="⏳ PENDIENTE (102_UDR_FS)",
            variable=self.state_var,
            value="PENDIENTE",
            font=('Segoe UI', 9),
            fg=self.theme.colors['text_primary'],
            bg=self.theme.colors['bg_primary'],
            selectcolor='#e6f3ff',
            activebackground=self.theme.colors['bg_primary'],
            activeforeground=self.theme.colors['text_primary'],
            command=self._on_state_change
        )
        pendiente_radio.pack(anchor='w', pady=2)

        # Radio button para FINALIZADO
        finalizado_radio = tk.Radiobutton(
            radio_frame,
            text="✅ FINALIZADO (102_UDR_FS)",
            variable=self.state_var,
            value="FINALIZADO",
            font=('Segoe UI', 9),
            fg=self.theme.colors['text_primary'],
            bg=self.theme.colors['bg_primary'],
            selectcolor='#e6f3ff',
            activebackground=self.theme.colors['bg_primary'],
            activeforeground=self.theme.colors['text_primary'],
            command=self._on_state_change
        )
        finalizado_radio.pack(anchor='w', pady=2)

        # 🆕 Radio button para FINALIZADO_67_PLUS
        finalizado_67_plus_radio = tk.Radiobutton(
            radio_frame,
            text="📺 FINALIZADO 67 PLUS (67_PLUS TV)",
            variable=self.state_var,
            value="FINALIZADO_67_PLUS",
            font=('Segoe UI', 9),
            fg=self.theme.colors['text_primary'],
            bg=self.theme.colors['bg_primary'],
            selectcolor='#e6f3ff',
            activebackground=self.theme.colors['bg_primary'],
            activeforeground=self.theme.colors['text_primary'],
            command=self._on_state_change
        )
        finalizado_67_plus_radio.pack(anchor='w', pady=2)

        # Frame para botones
        buttons_frame = tk.Frame(form_frame, bg=self.theme.colors['bg_primary'])
        buttons_frame.pack(fill='x', pady=(10, 0))

        # Botón para aplicar preset Pendiente
        pendiente_button = tk.Button(
            buttons_frame,
            text="📋 Pendiente",
            font=('Segoe UI', 8),
            fg='white',
            bg='#4a90e2',
            activebackground='#357abd',
            relief='flat',
            padx=8,
            pady=4,
            command=self._set_pendiente_preset
        )
        pendiente_button.pack(side='left', padx=(0, 5))

        # Botón para aplicar preset Finalizado
        finalizado_button = tk.Button(
            buttons_frame,
            text="✅ Finalizado",
            font=('Segoe UI', 8),
            fg='white',
            bg='#4a90e2',
            activebackground='#357abd',
            relief='flat',
            padx=8,
            pady=4,
            command=self._set_finalizado_preset
        )
        finalizado_button.pack(side='left', padx=5)

        # 🆕 Botón para aplicar preset Finalizado 67 Plus
        finalizado_67_plus_button = tk.Button(
            buttons_frame,
            text="📺 67 Plus",
            font=('Segoe UI', 8),
            fg='white',
            bg='#4a90e2',
            activebackground='#357abd',
            relief='flat',
            padx=8,
            pady=4,
            command=self._set_finalizado_67_plus_preset
        )
        finalizado_67_plus_button.pack(side='left', padx=5)

        # Botón para limpiar configuración
        clear_state_button = tk.Button(
            buttons_frame,
            text="🗑️ Por Defecto",
            font=('Segoe UI', 8),
            fg='white',
            bg='#6c757d',
            activebackground='#545b62',
            relief='flat',
            padx=8,
            pady=4,
            command=self._clear_state_config
        )
        clear_state_button.pack(side='right')

        # Guardar referencias
        self.ui_components.update({
            'state_var': self.state_var,
            'pendiente_radio': pendiente_radio,
            'finalizado_radio': finalizado_radio,
            'finalizado_67_plus_radio': finalizado_67_plus_radio,
            'pendiente_button': pendiente_button,
            'finalizado_button': finalizado_button,
            'finalizado_67_plus_button': finalizado_67_plus_button,
            'clear_state_button': clear_state_button
        })

    def _create_status_section(self, parent):
        """Crea sección de estado usando componentes modulares"""
        section = AutomationUIFactory.create_collapsible_section(
            parent, "status", "📊 Estado del Sistema", self.theme
        )
        content = section.create(row=3, min_height=150, default_expanded=False)
        section.set_toggle_callback(self._on_section_toggle)
        self.section_frames["status"] = section

        # Crear panel de estado
        status_panel = AutomationUIFactory.create_status_panel(content, self.theme)
        status_widgets = status_panel.create()
        self.ui_components.update(status_widgets)

        # Guardar referencia al panel para actualizaciones
        self.status_panel = status_panel

    def _create_controls_section(self, parent):
        """Crea sección de controles usando componentes modulares"""
        section = AutomationUIFactory.create_collapsible_section(
            parent, "controls", "🎮 Controles de Automatización", self.theme
        )
        content = section.create(row=4, min_height=180, default_expanded=False)
        section.set_toggle_callback(self._on_section_toggle)
        self.section_frames["controls"] = section

        # Crear panel de controles
        control_panel = AutomationUIFactory.create_control_panel(content, self.theme)
        control_widgets = control_panel.create()
        self.ui_components.update(control_widgets)

        # Configurar comandos de botones
        control_panel.set_button_command('start_button', self._start_automation)
        control_panel.set_button_command('pause_button', self._pause_automation)

        # Guardar referencia al panel para actualizaciones
        self.control_panel = control_panel

    def _setup_initial_state(self):
        """Configura el estado inicial de la interfaz"""
        # Cargar credenciales guardadas
        self._load_saved_credentials()

        # Cargar configuración de fechas guardada
        self._load_saved_date_config()

        # Cargar configuración de estado guardada
        self._load_saved_state_config()

        # Agregar mensajes iniciales al log
        self.logger.info(
            "🚀 Sistema de automatización con login automático, configuración de fechas obligatoria y estado iniciado")
        self.logger.info(
            "🔧 Configuración: Esperas robustas, detección inteligente, fechas obligatorias y estado configurables")
        self.logger.info("🔢 Extracción avanzada de números de serie mediante lectura de tablas HTML")

        if self.automation_service.is_selenium_available():
            self.logger.info("✅ Selenium disponible - Login automático, configuración de fechas y estado habilitados")
        else:
            self.logger.warning("⚠️ Selenium no disponible - Solo modo navegador básico")

        # Verificar disponibilidad de extracción de números de serie
        if self.automation_service.is_serie_extraction_available():
            self.logger.info("🔢 Extracción de números de serie disponible - Lectura directa de tablas HTML")
        else:
            self.logger.warning("⚠️ Extracción de números de serie no disponible")

        # Mostrar estado inicial de fechas y estado
        self._log_date_config_status()
        self._log_state_config_status()

        # Mostrar advertencia sobre fechas obligatorias
        self.logger.warning("📅 IMPORTANTE: Ahora es obligatorio configurar fechas antes de iniciar la automatización")

    def _on_section_toggle(self, section_id, is_expanded):
        """Maneja toggle de secciones - solo una expandida a la vez"""
        if is_expanded:
            # Colapsar otras secciones
            for sid, section in self.section_frames.items():
                if sid != section_id and section.is_expanded():
                    section.collapse()
            self.expanded_section = section_id
        else:
            self.expanded_section = None

    def _log_message(self, message, level="INFO"):
        """Método de logging para el automation_service"""
        level_map = {
            "DEBUG": LogLevel.DEBUG,
            "INFO": LogLevel.INFO,
            "WARNING": LogLevel.WARNING,
            "ERROR": LogLevel.ERROR,
            "CRITICAL": LogLevel.CRITICAL
        }

        log_level = level_map.get(level, LogLevel.INFO)
        if log_level == LogLevel.DEBUG:
            self.logger.debug(message)
        elif log_level == LogLevel.INFO:
            self.logger.info(message)
        elif log_level == LogLevel.WARNING:
            self.logger.warning(message)
        elif log_level == LogLevel.ERROR:
            self.logger.error(message)
        elif log_level == LogLevel.CRITICAL:
            self.logger.critical(message)

    def _log_to_ui(self, formatted_message, level):
        """Callback para mostrar logs en la UI"""
        if self._is_closing or 'log_text' not in self.ui_components:
            return

        try:
            log_text = self.ui_components['log_text']
            log_text.configure(state=tk.NORMAL)
            log_text.insert(tk.END, formatted_message + "\n")
            log_text.configure(state=tk.DISABLED)
            log_text.see(tk.END)
        except Exception:
            pass  # Ignorar errores de UI durante cierre

    def _clear_log(self):
        """Limpia el contenido del log"""
        if self._is_closing or 'log_text' not in self.ui_components:
            return

        try:
            self.logger.clear()
            log_text = self.ui_components['log_text']
            log_text.configure(state=tk.NORMAL)
            log_text.delete(1.0, tk.END)
            log_text.configure(state=tk.DISABLED)
            self.logger.info("Log limpiado")
        except Exception:
            pass

    def _get_credentials_from_form(self):
        """Obtiene credenciales del formulario usando componentes"""
        username = self.ui_components['username_entry'].get().strip()
        password = self.ui_components['password_entry'].get().strip()
        return username, password

    def _set_credentials_in_form(self, username, password):
        """Establece credenciales en el formulario"""
        self.ui_components['username_entry'].delete(0, 'end')
        self.ui_components['username_entry'].insert(0, username)
        self.ui_components['password_entry'].delete(0, 'end')
        self.ui_components['password_entry'].insert(0, password)

    def _load_saved_credentials(self):
        """Carga credenciales guardadas al iniciar"""
        try:
            credentials = self.credentials_manager.load_credentials()
            if credentials:
                username = credentials.get('username', '')
                password = credentials.get('password', '')
                self._set_credentials_in_form(username, password)
                self.logger.info("Credenciales cargadas desde archivo seguro")
        except Exception as e:
            self.logger.warning(f"Error cargando credenciales: {e}")

    # MÉTODOS PARA CONFIGURACIÓN DE FECHAS

    def _load_saved_date_config(self):
        """Carga configuración de fechas guardada al iniciar"""
        try:
            config = self.date_config_manager.load_config()
            if config:
                self.date_config_form.set_date_config(config)
                self.logger.info("📅 Configuración de fechas cargada desde archivo seguro")
            else:
                self.logger.info("📅 Usando configuración de fechas por defecto (sin fechas)")
        except Exception as e:
            self.logger.warning(f"Error cargando configuración de fechas: {e}")

    def _save_current_date_config(self):
        """Guarda la configuración actual de fechas"""
        try:
            config = self.date_config_form.get_date_config()
            success, message = self.date_config_manager.save_config(config)

            if success:
                self.logger.info(f"💾 {message}")
                return True
            else:
                self.logger.error(f"❌ Error guardando fechas: {message}")
                return False
        except Exception as e:
            self.logger.error(f"❌ Excepción guardando configuración de fechas: {e}")
            return False

    def _check_dates_configured(self):
        """🆕 Verifica si las fechas están configuradas (no vacías y no omitidas)"""
        try:
            config = self.date_config_form.get_date_config()

            # Si skip_dates es True, las fechas no están configuradas
            if config.get('skip_dates', True):
                return False

            # Verificar que al menos una fecha esté configurada
            date_from = config.get('date_from', '').strip()
            date_to = config.get('date_to', '').strip()

            # Si ambas fechas están vacías, no están configuradas
            if not date_from and not date_to:
                return False

            return True
        except Exception as e:
            self.logger.error(f"Error verificando configuración de fechas: {e}")
            return False

    def _show_date_configuration_dialog(self):
        """🆕 Muestra diálogo para configurar fechas obligatorias"""
        dialog = tk.Toplevel(self.frame)
        dialog.title("Configuración de Fechas Requerida")
        dialog.geometry("500x400")
        dialog.resizable(False, False)
        dialog.grab_set()  # Modal

        # Centrar el diálogo
        dialog.transient(self.frame.winfo_toplevel())

        # Variable para resultado
        result = {'configured': False}

        # Frame principal
        main_frame = tk.Frame(dialog, bg='white', padx=20, pady=20)
        main_frame.pack(fill='both', expand=True)

        # Título
        title_label = tk.Label(
            main_frame,
            text="📅 Configuración de Fechas Obligatoria",
            font=('Segoe UI', 14, 'bold'),
            fg='#2c3e50',
            bg='white'
        )
        title_label.pack(pady=(0, 10))

        # Mensaje explicativo
        message_label = tk.Label(
            main_frame,
            text="Debe configurar un rango de fechas antes de iniciar la automatización.\n"
                 "Seleccione una opción rápida o configure fechas personalizadas:",
            font=('Segoe UI', 10),
            fg='#34495e',
            bg='white',
            justify='left'
        )
        message_label.pack(pady=(0, 20))

        # Frame para opciones rápidas
        quick_frame = tk.LabelFrame(main_frame, text="Opciones Rápidas", font=('Segoe UI', 10, 'bold'),
                                    bg='white', fg='#2c3e50')
        quick_frame.pack(fill='x', pady=(0, 15))

        # Botones de opciones rápidas
        quick_buttons = [
            ("📅 Solo Hoy", lambda: self._apply_quick_date_option(dialog, result, 'today')),
            ("📆 Última Semana", lambda: self._apply_quick_date_option(dialog, result, 'last_week')),
            ("🗓️ Último Mes", lambda: self._apply_quick_date_option(dialog, result, 'last_month'))
        ]

        for i, (text, command) in enumerate(quick_buttons):
            btn = tk.Button(
                quick_frame,
                text=text,
                font=('Segoe UI', 9),
                fg='white',
                bg='#3498db',
                activebackground='#2980b9',
                relief='flat',
                padx=15,
                pady=8,
                command=command
            )
            btn.pack(side='left', padx=5, pady=10)

        # Frame para configuración manual
        manual_frame = tk.LabelFrame(main_frame, text="Configuración Manual", font=('Segoe UI', 10, 'bold'),
                                     bg='white', fg='#2c3e50')
        manual_frame.pack(fill='x', pady=(0, 15))

        # Campos de fecha
        fields_frame = tk.Frame(manual_frame, bg='white')
        fields_frame.pack(fill='x', padx=10, pady=10)

        # Fecha desde
        tk.Label(fields_frame, text="Fecha Desde (DD/MM/YYYY):", font=('Segoe UI', 9),
                 bg='white', fg='#2c3e50').grid(row=0, column=0, sticky='w', pady=2)
        date_from_entry = tk.Entry(fields_frame, font=('Segoe UI', 9), width=15)
        date_from_entry.grid(row=0, column=1, padx=10, pady=2)

        # Fecha hasta
        tk.Label(fields_frame, text="Fecha Hasta (DD/MM/YYYY):", font=('Segoe UI', 9),
                 bg='white', fg='#2c3e50').grid(row=1, column=0, sticky='w', pady=2)
        date_to_entry = tk.Entry(fields_frame, font=('Segoe UI', 9), width=15)
        date_to_entry.grid(row=1, column=1, padx=10, pady=2)

        # Botón para aplicar configuración manual
        apply_manual_btn = tk.Button(
            manual_frame,
            text="✅ Aplicar Fechas Manuales",
            font=('Segoe UI', 9),
            fg='white',
            bg='#27ae60',
            activebackground='#229954',
            relief='flat',
            padx=15,
            pady=8,
            command=lambda: self._apply_manual_dates(dialog, result, date_from_entry.get(), date_to_entry.get())
        )
        apply_manual_btn.pack(pady=10)

        # Frame para botones de acción
        action_frame = tk.Frame(main_frame, bg='white')
        action_frame.pack(fill='x', pady=(15, 0))

        # Botón cancelar
        cancel_btn = tk.Button(
            action_frame,
            text="❌ Cancelar",
            font=('Segoe UI', 9),
            fg='white',
            bg='#e74c3c',
            activebackground='#c0392b',
            relief='flat',
            padx=15,
            pady=8,
            command=lambda: dialog.destroy()
        )
        cancel_btn.pack(side='right', padx=5)

        # Esperar a que se cierre el diálogo
        dialog.wait_window()

        return result['configured']

    def _apply_quick_date_option(self, dialog, result, option):
        """🆕 Aplica una opción rápida de fechas"""
        try:
            success = False

            if option == 'today':
                success = self.apply_date_preset('today')
            elif option == 'last_week':
                success = self.apply_date_preset('last_week')
            elif option == 'last_month':
                success = self.apply_date_preset('last_month')

            if success:
                result['configured'] = True
                self.logger.info(f"📅 Configuración rápida aplicada: {option}")
                dialog.destroy()
            else:
                messagebox.showerror("Error", f"No se pudo aplicar la configuración {option}")

        except Exception as e:
            self.logger.error(f"Error aplicando opción rápida {option}: {e}")
            messagebox.showerror("Error", f"Error aplicando configuración: {str(e)}")

    def _apply_manual_dates(self, dialog, result, date_from, date_to):
        """🆕 Aplica fechas configuradas manualmente"""
        try:
            # Validar fechas
            if not date_from and not date_to:
                messagebox.showerror("Error", "Debe ingresar al menos una fecha")
                return

            # Crear configuración
            config = {
                'skip_dates': False,
                'date_from': date_from.strip(),
                'date_to': date_to.strip()
            }

            # Validar configuración
            is_valid, message = self.date_config_manager.validate_config(config)
            if not is_valid:
                messagebox.showerror("Fechas Inválidas", message)
                return

            # Aplicar configuración
            success = self.set_date_config(config)
            if success:
                result['configured'] = True
                self.logger.info(f"📅 Fechas manuales aplicadas: {date_from} - {date_to}")
                dialog.destroy()
            else:
                messagebox.showerror("Error", "No se pudo guardar la configuración")

        except Exception as e:
            self.logger.error(f"Error aplicando fechas manuales: {e}")
            messagebox.showerror("Error", f"Error configurando fechas: {str(e)}")

    def _validate_current_date_config(self):
        """Valida la configuración actual de fechas"""
        try:
            config = self.date_config_form.get_date_config()
            is_valid, message = self.date_config_manager.validate_config(config)

            if not is_valid:
                self.logger.warning(f"⚠️ Configuración de fechas inválida: {message}")
                messagebox.showerror("Configuración de Fechas Inválida", message)
                return False

            return True
        except Exception as e:
            self.logger.error(f"❌ Error validando fechas: {e}")
            messagebox.showerror("Error", f"Error validando fechas: {str(e)}")
            return False

    def _get_date_config_for_automation(self):
        """Obtiene configuración de fechas para enviar al automation_service"""
        try:
            config = self.date_config_form.get_date_config()

            # Guardar configuración automáticamente antes de usarla
            self._save_current_date_config()

            return config
        except Exception as e:
            self.logger.error(f"❌ Error obteniendo configuración de fechas: {e}")
            return {'skip_dates': True}  # Fallback seguro

    def _log_date_config_status(self):
        """Muestra el estado actual de configuración de fechas en el log"""
        try:
            config = self.date_config_form.get_date_config()

            if config['skip_dates']:
                self.logger.warning("📅 Configuración de fechas: NO CONFIGURADA (se requerirá antes de iniciar)")
            else:
                date_from = config.get('date_from', 'No especificada')
                date_to = config.get('date_to', 'No especificada')
                self.logger.info(f"📅 Configuración de fechas: Desde={date_from}, Hasta={date_to}")
        except Exception as e:
            self.logger.warning(f"Error mostrando estado de fechas: {e}")

    def _set_today_dates(self):
        """Establece fechas de hoy en ambos campos"""
        try:
            self.date_config_form.set_today_dates()
            self.logger.info("📅 Fechas establecidas a HOY")
            self._log_date_config_status()
        except Exception as e:
            self.logger.error(f"❌ Error estableciendo fecha de hoy: {e}")

    def _clear_dates(self):
        """Limpia los campos de fecha"""
        try:
            self.date_config_form.clear_dates()
            self.logger.warning("🗑️ Campos de fecha limpiados - Se requerirá configuración antes de iniciar")
            self._log_date_config_status()
        except Exception as e:
            self.logger.error(f"❌ Error limpiando fechas: {e}")

    # 🆕 MÉTODOS PARA CONFIGURACIÓN DE ESTADO EXPANDIDA

    def _load_saved_state_config(self):
        """Carga configuración de estado guardada al iniciar"""
        try:
            config = self.state_config_manager.load_config()
            if config:
                selected_state = config.get('selected_state', 'PENDIENTE')
                self.state_var.set(selected_state)
                self.logger.info("📋 Configuración de estado cargada desde archivo seguro")
            else:
                self.state_var.set('PENDIENTE')
                self.logger.info("📋 Usando configuración de estado por defecto (PENDIENTE)")
        except Exception as e:
            self.logger.warning(f"Error cargando configuración de estado: {e}")
            self.state_var.set('PENDIENTE')

    def _save_current_state_config(self):
        """Guarda la configuración actual de estado"""
        try:
            config = self._get_state_config_from_form()
            success, message = self.state_config_manager.save_config(config)

            if success:
                self.logger.info(f"💾 {message}")
                return True
            else:
                self.logger.error(f"❌ Error guardando estado: {message}")
                return False
        except Exception as e:
            self.logger.error(f"❌ Excepción guardando configuración de estado: {e}")
            return False

    def _validate_current_state_config(self):
        """Valida la configuración actual de estado"""
        try:
            config = self._get_state_config_from_form()
            is_valid, message = self.state_config_manager.validate_config(config)

            if not is_valid:
                self.logger.warning(f"⚠️ Configuración de estado inválida: {message}")
                messagebox.showerror("Configuración de Estado Inválida", message)
                return False

            return True
        except Exception as e:
            self.logger.error(f"❌ Error validando estado: {e}")
            messagebox.showerror("Error", f"Error validando estado: {str(e)}")
            return False

    def _get_state_config_from_form(self):
        """Obtiene configuración de estado desde el formulario"""
        return {
            'selected_state': self.state_var.get(),
            'auto_save': True
        }

    def _get_state_config_for_automation(self):
        """Obtiene configuración de estado para enviar al automation_service"""
        try:
            config = self._get_state_config_from_form()

            # Guardar configuración automáticamente antes de usarla
            self._save_current_state_config()

            return config
        except Exception as e:
            self.logger.error(f"❌ Error obteniendo configuración de estado: {e}")
            return {'selected_state': 'PENDIENTE', 'auto_save': True}  # Fallback seguro

    def _log_state_config_status(self):
        """Muestra el estado actual de configuración de estado en el log"""
        try:
            config = self._get_state_config_from_form()
            selected_state = config.get('selected_state', 'PENDIENTE')
            display_name = self.state_config_manager.get_state_display_name(selected_state)
            self.logger.info(f"📋 Configuración de estado: {display_name}")
        except Exception as e:
            self.logger.warning(f"Error mostrando estado de configuración: {e}")

    def _on_state_change(self):
        """Callback cuando cambia la selección de estado"""
        try:
            self._save_current_state_config()
            self._log_state_config_status()
        except Exception as e:
            self.logger.error(f"❌ Error al cambiar estado: {e}")

    def _set_pendiente_preset(self):
        """Aplica preset PENDIENTE"""
        try:
            success, message = self.state_config_manager.apply_preset('pendiente')
            if success:
                self.state_var.set('PENDIENTE')
                self.logger.info(f"📋 {message}")
                self._log_state_config_status()
            else:
                self.logger.error(f"❌ Error aplicando preset PENDIENTE: {message}")
        except Exception as e:
            self.logger.error(f"❌ Error aplicando preset PENDIENTE: {e}")

    def _set_finalizado_preset(self):
        """Aplica preset FINALIZADO"""
        try:
            success, message = self.state_config_manager.apply_preset('finalizado')
            if success:
                self.state_var.set('FINALIZADO')
                self.logger.info(f"✅ {message}")
                self._log_state_config_status()
            else:
                self.logger.error(f"❌ Error aplicando preset FINALIZADO: {message}")
        except Exception as e:
            self.logger.error(f"❌ Error aplicando preset FINALIZADO: {e}")

    def _set_finalizado_67_plus_preset(self):
        """🆕 Aplica preset FINALIZADO_67_PLUS"""
        try:
            success, message = self.state_config_manager.apply_preset('finalizado_67_plus')
            if success:
                self.state_var.set('FINALIZADO_67_PLUS')
                self.logger.info(f"📺 {message}")
                self._log_state_config_status()
            else:
                self.logger.error(f"❌ Error aplicando preset FINALIZADO_67_PLUS: {message}")
        except Exception as e:
            self.logger.error(f"❌ Error aplicando preset FINALIZADO_67_PLUS: {e}")

    def _clear_state_config(self):
        """Limpia configuración de estado (vuelve a por defecto)"""
        try:
            if messagebox.askyesno("Confirmar",
                                   "¿Restablecer configuración de estado a valores por defecto (PENDIENTE)?"):
                success, message = self.state_config_manager.clear_config()
                if success:
                    self.state_var.set('PENDIENTE')
                    self.logger.info(f"🗑️ {message}")
                    self._log_state_config_status()
                else:
                    self.logger.error(f"❌ Error restableciendo estado: {message}")
        except Exception as e:
            self.logger.error(f"❌ Error restableciendo configuración de estado: {e}")

    # MÉTODOS EXISTENTES DE CREDENCIALES

    def _test_credentials(self):
        """Prueba las credenciales usando componentes"""
        if not self.automation_service.is_selenium_available():
            messagebox.showwarning("Selenium No Disponible",
                                   "No se pueden probar las credenciales sin Selenium.\n\n" +
                                   "Instale Selenium para usar esta funcionalidad:\n" +
                                   "pip install selenium")
            return

        username, password = self._get_credentials_from_form()
        if not username or not password:
            messagebox.showerror("Credenciales Incompletas", "Debe ingresar usuario y contraseña")
            return

        self.logger.info("🔍 Iniciando prueba de credenciales...")

        # Deshabilitar botón durante prueba
        test_button = self.ui_components['test_credentials_button']
        test_button.configure(state='disabled', text='Probando...')

        def test_thread():
            try:
                self.logger.info("🔧 Configurando navegador para prueba...")
                self.logger.info("🌐 Navegando a página de login...")
                self.logger.info("⏳ Esperando carga completa de página...")
                self.logger.info("👤 Ingresando credenciales...")
                self.logger.info("🔐 Verificando login...")

                # Incluir configuraciones de fecha y estado en la prueba
                date_config = self._get_date_config_for_automation()
                state_config = self._get_state_config_for_automation()

                success, message = self.automation_service.test_credentials(username, password, date_config,
                                                                            state_config)
                self.frame.after(0, lambda: self._handle_test_credentials_result(success, message))
            except Exception as e:
                self.frame.after(0, lambda: self._handle_test_credentials_result(False, str(e)))

        threading.Thread(target=test_thread, daemon=True).start()

    def _handle_test_credentials_result(self, success, message):
        """Maneja resultado de prueba de credenciales"""
        # Restaurar botón
        test_button = self.ui_components['test_credentials_button']
        test_button.configure(state='normal', text='🔍 Probar')

        if success:
            self.logger.info("✅ Credenciales verificadas correctamente")
            messagebox.showinfo("Credenciales Válidas", f"¡Credenciales correctas!\n\n{message}")
        else:
            self.logger.error(f"❌ Error en credenciales: {message}")
            messagebox.showerror("Credenciales Inválidas", f"Error verificando credenciales:\n\n{message}")

    def _save_credentials(self):
        """Guarda las credenciales usando componentes"""
        username, password = self._get_credentials_from_form()

        # Validar usando el manager
        valid, message = self.credentials_manager.validate_credentials(username, password)
        if not valid:
            messagebox.showerror("Credenciales Inválidas", message)
            return

        success, save_message = self.credentials_manager.save_credentials(username, password)

        if success:
            self.logger.info("💾 Credenciales guardadas de forma segura")
            messagebox.showinfo("Éxito", "Credenciales guardadas correctamente de forma encriptada")
        else:
            self.logger.error("❌ Error guardando credenciales")
            messagebox.showerror("Error", f"No se pudieron guardar las credenciales: {save_message}")

    def _clear_credentials(self):
        """Limpia las credenciales usando componentes"""
        if messagebox.askyesno("Confirmar", "¿Eliminar todas las credenciales guardadas?"):
            # Limpiar formulario
            self.ui_components['username_entry'].delete(0, 'end')
            self.ui_components['password_entry'].delete(0, 'end')

            # Limpiar archivos
            success, clear_message = self.credentials_manager.clear_credentials()

            if success:
                self.logger.info("🗑️ Credenciales eliminadas")
                messagebox.showinfo("Éxito", f"Credenciales eliminadas correctamente: {clear_message}")
            else:
                self.logger.error(f"❌ Error eliminando credenciales: {clear_message}")
                messagebox.showerror("Error", f"Error eliminando credenciales: {clear_message}")

    def _start_automation(self):
        """🔄 Inicia la automatización con verificación obligatoria de fechas"""
        if self._is_closing:
            return

        # 🆕 VERIFICAR FECHAS OBLIGATORIAS ANTES DE CONTINUAR
        if not self._check_dates_configured():
            self.logger.warning("📅 No hay fechas configuradas - Solicitando configuración al usuario")

            # Expandir sección de fechas para mostrar que es importante
            if "date_config" in self.section_frames:
                self.section_frames["date_config"].expand()

            # Mostrar diálogo de configuración de fechas
            configured = self._show_date_configuration_dialog()

            if not configured:
                self.logger.warning("📅 Usuario canceló la configuración de fechas - Automatización no iniciada")
                messagebox.showwarning("Configuración Cancelada",
                                       "La automatización requiere configurar fechas para continuar.")
                return

            # Verificar nuevamente que las fechas estén configuradas
            if not self._check_dates_configured():
                self.logger.error("📅 Error: Las fechas siguen sin estar configuradas después del diálogo")
                messagebox.showerror("Error de Configuración",
                                     "No se pudo configurar las fechas correctamente. Intente de nuevo.")
                return

        # Validar configuración de fechas antes de iniciar
        if not self._validate_current_date_config():
            return

        # Validar configuración de estado antes de iniciar
        if not self._validate_current_state_config():
            return

        username, password = self._get_credentials_from_form()
        if not username or not password:
            # Intentar cargar credenciales guardadas
            credentials = self.credentials_manager.load_credentials()
            if not credentials:
                messagebox.showerror("Credenciales Requeridas",
                                     "Debe configurar credenciales antes de iniciar la automatización")
                return
            username = credentials.get('username')
            password = credentials.get('password')

        # Obtener configuración de fechas (ya verificada que existe)
        date_config = self._get_date_config_for_automation()

        # Obtener configuración de estado
        state_config = self._get_state_config_for_automation()

        def start_thread():
            try:
                if self._is_closing:
                    return

                self.logger.log_automation_start({
                    'username': username,
                    'date_config': date_config,
                    'state_config': state_config
                })

                # Registrar inicio de ejecución
                if self.registry_tab:
                    try:
                        self.execution_start_time = datetime.now()
                        profile_name = "Manual (Con Login"
                        if not date_config.get('skip_dates', True):
                            profile_name += " + Fechas"
                        # Incluir estado en el nombre del perfil
                        selected_state = state_config.get('selected_state', 'PENDIENTE')
                        if selected_state == "FINALIZADO_67_PLUS":
                            profile_name += " + Estado: 📺 67 Plus"
                        else:
                            profile_name += f" + Estado: {selected_state}"
                        profile_name += " + Números de Serie)"

                        self.current_execution_record = self.registry_tab.add_execution_record(
                            start_time=self.execution_start_time,
                            profile_name=profile_name,
                            user_type="Usuario"
                        )
                        self.logger.info(f"Registro de ejecución creado: ID {self.current_execution_record['id']}")
                    except Exception as e:
                        self.logger.warning(f"Error creando registro: {str(e)}")

                # Iniciar automatización con configuración de fechas y estado
                success, message = self.automation_service.start_automation(
                    username, password, date_config, state_config
                )

                if not self._is_closing:
                    self.frame.after(0, lambda: self._handle_start_result(success, message))
            except Exception as e:
                if not self._is_closing:
                    self.frame.after(0, lambda: self._handle_start_result(False, str(e)))

        # Actualizar UI
        self.control_panel.set_button_state('start_button', 'disabled')
        self.control_panel.set_button_text('start_button', 'Iniciando...')

        threading.Thread(target=start_thread, daemon=True).start()

    def _handle_start_result(self, success, message):
        """🆕 Maneja el resultado del inicio de automatización incluyendo estado expandido y números de serie"""
        if self._is_closing:
            return

        if success:
            self.status_panel.update_automation_status("En ejecución", self.theme.colors['success'])
            self.control_panel.set_button_state('start_button', 'disabled')
            self.control_panel.set_button_text('start_button', '▶️ Iniciando...')
            self.control_panel.set_button_state('pause_button', 'normal')

            self.logger.log_automation_end(True, {'message': message})

            # Obtener información de números de serie si está disponible
            serie_count = self.automation_service.get_last_serie_count()
            last_file = self.automation_service.get_last_extraction_file()

            display_message = f"{message}\n\n"
            if self.automation_service.is_selenium_available():
                display_message += "🎯 Características avanzadas activas:\n"
                display_message += "• Login automático completado\n"
                display_message += "• Configuración de fechas obligatoria aplicada\n"
                display_message += "• Configuración de estado aplicada\n"
                display_message += "• Extracción de números de serie mediante lectura de tablas HTML\n"
                display_message += "• Esperas robustas implementadas\n"
                display_message += "• Detección inteligente de carga\n"
                display_message += "• Navegador controlado automáticamente\n"

                if serie_count > 0:
                    display_message += f"• {serie_count} números de serie extraídos exitosamente\n"

                if last_file:
                    display_message += f"• Archivo Excel generado: {last_file}\n"

                display_message += "\n💡 El navegador permanecerá abierto para continuar la automatización."
            else:
                display_message += "La página web se ha abierto en su navegador (modo básico)."

            messagebox.showinfo("Éxito", display_message)
        else:
            self.status_panel.update_automation_status("Error", self.theme.colors['error'])
            self.control_panel.set_button_state('start_button', 'normal')
            self.control_panel.set_button_text('start_button', '▶️ Iniciar Automatización con Login')
            self.control_panel.set_button_state('pause_button', 'disabled')

            self.logger.log_automation_end(False, {'error': message})

            # Actualizar registro como fallido
            self._update_execution_record("Fallido", message)

            messagebox.showerror("Error", message)

    def _pause_automation(self):
        """Pausa la automatización usando componentes"""
        if self._is_closing:
            return

        try:
            self.logger.info("Pausando automatización...")
            success, message = self.automation_service.pause_automation()

            if success:
                self.status_panel.update_automation_status("Pausada", self.theme.colors['warning'])
                self.control_panel.set_button_state('start_button', 'normal')
                self.control_panel.set_button_text('start_button', '▶️ Iniciar Automatización con Login')
                self.control_panel.set_button_state('pause_button', 'disabled')

                # Obtener estadísticas finales de números de serie
                serie_count = self.automation_service.get_last_serie_count()
                last_file = self.automation_service.get_last_extraction_file()

                final_message = "Automatización pausada exitosamente"
                if serie_count > 0:
                    final_message += f"\n\n🔢 Números de serie extraídos: {serie_count}"
                if last_file:
                    final_message += f"\n📄 Archivo Excel: {last_file}"

                self.logger.info(final_message)

                # Actualizar registro como exitoso
                self._update_execution_record("Exitoso", "")

                if not self._is_closing:
                    messagebox.showinfo("Éxito", final_message)
            else:
                self.status_panel.update_automation_status("Error", self.theme.colors['error'])
                self.logger.error(f"Error al pausar: {message}")

                # Actualizar registro como fallido
                self._update_execution_record("Fallido", message)

                if not self._is_closing:
                    messagebox.showerror("Error", message)

        except Exception as e:
            error_msg = str(e)
            self.logger.error(f"Excepción al pausar: {error_msg}")

            # Actualizar registro con la excepción
            self._update_execution_record("Fallido", f"Excepción: {error_msg}")

            if not self._is_closing:
                messagebox.showerror("Error", f"Error al pausar automatización:\n{error_msg}")

    def _update_execution_record(self, status, error_message):
        """Actualiza el registro de ejecución con información de números de serie"""
        if self.registry_tab and self.current_execution_record:
            try:
                end_time = datetime.now()

                # Agregar información de números de serie al mensaje
                serie_count = self.automation_service.get_last_serie_count()
                if status == "Exitoso" and serie_count > 0:
                    if error_message:
                        error_message += f" | {serie_count} números de serie extraídos"
                    else:
                        error_message = f"{serie_count} números de serie extraídos"

                self.registry_tab.update_execution_record(
                    record_id=self.current_execution_record['id'],
                    end_time=end_time,
                    status=status,
                    error_message=error_message
                )
                self.logger.info(f"Registro actualizado: {status}")
                self.current_execution_record = None
                self.execution_start_time = None
            except Exception as e:
                self.logger.warning(f"Error actualizando registro: {str(e)}")

    def get_automation_status(self):
        """Obtiene el estado actual de la automatización"""
        return self.automation_service.get_status()

    # MÉTODOS PÚBLICOS PARA CONFIGURACIÓN DE FECHAS Y ESTADO

    def get_current_date_config(self):
        """Obtiene la configuración actual de fechas"""
        try:
            return self.date_config_form.get_date_config()
        except Exception as e:
            self.logger.warning(f"Error obteniendo configuración de fechas: {e}")
            return {'skip_dates': True}

    def set_date_config(self, config):
        """Establece configuración de fechas específica"""
        try:
            self.date_config_form.set_date_config(config)
            self._save_current_date_config()
            self._log_date_config_status()
            return True
        except Exception as e:
            self.logger.error(f"Error estableciendo configuración de fechas: {e}")
            return False

    def get_current_state_config(self):
        """Obtiene la configuración actual de estado"""
        try:
            return self._get_state_config_from_form()
        except Exception as e:
            self.logger.warning(f"Error obteniendo configuración de estado: {e}")
            return {'selected_state': 'PENDIENTE', 'auto_save': True}

    def set_state_config(self, config):
        """Establece configuración de estado específica"""
        try:
            selected_state = config.get('selected_state', 'PENDIENTE')
            self.state_var.set(selected_state)
            self._save_current_state_config()
            self._log_state_config_status()
            return True
        except Exception as e:
            self.logger.error(f"Error estableciendo configuración de estado: {e}")
            return False

    def apply_date_preset(self, preset_name):
        """Aplica un preset de fechas predefinido"""
        try:
            success, message = self.date_config_manager.apply_preset(preset_name)
            if success:
                # Recargar configuración en el formulario
                self._load_saved_date_config()
                self.logger.info(f"📅 {message}")
                return True
            else:
                self.logger.error(f"❌ Error aplicando preset: {message}")
                return False
        except Exception as e:
            self.logger.error(f"❌ Excepción aplicando preset: {e}")
            return False

    def apply_state_preset(self, preset_name):
        """Aplica un preset de estado predefinido"""
        try:
            success, message = self.state_config_manager.apply_preset(preset_name)
            if success:
                # Recargar configuración en la UI
                self._load_saved_state_config()
                self.logger.info(f"📋 {message}")
                return True
            else:
                self.logger.error(f"❌ Error aplicando preset: {message}")
                return False
        except Exception as e:
            self.logger.error(f"❌ Excepción aplicando preset: {e}")
            return False

    # MÉTODOS PÚBLICOS PARA EXTRACCIÓN DE NÚMEROS DE SERIE

    def get_serie_extraction_status(self):
        """Obtiene el estado actual de extracción de números de serie"""
        try:
            return {
                'available': self.automation_service.is_serie_extraction_available(),
                'last_count': self.automation_service.get_last_serie_count(),
                'last_file': self.automation_service.get_last_extraction_file(),
                'extraction_method': 'HTML Table Reading'
            }
        except Exception as e:
            self.logger.warning(f"Error obteniendo estado de números de serie: {e}")
            return {
                'available': False,
                'error': str(e)
            }

    def test_serie_extraction(self):
        """Prueba la funcionalidad de extracción de números de serie"""
        try:
            if not self.automation_service.get_status():
                messagebox.showwarning("Automatización No Activa",
                                       "Debe iniciar la automatización primero para probar la extracción de números de serie")
                return False

            success, message = self.automation_service.test_data_extraction()

            if success:
                self.logger.info(f"✅ Prueba de extracción de números de serie exitosa: {message}")
                messagebox.showinfo("Prueba Exitosa", f"Funcionalidad de números de serie disponible:\n\n{message}")
            else:
                self.logger.error(f"❌ Prueba de extracción falló: {message}")
                messagebox.showerror("Prueba Fallida", f"Error en funcionalidad de números de serie:\n\n{message}")

            return success
        except Exception as e:
            error_msg = f"Error probando extracción de números de serie: {str(e)}"
            self.logger.error(error_msg)
            messagebox.showerror("Error", error_msg)
            return False

    def extract_serie_data_manual(self):
        """Ejecuta extracción manual de números de serie"""
        try:
            if not self.automation_service.get_status():
                messagebox.showwarning("Automatización No Activa",
                                       "Debe iniciar la automatización primero para extraer números de serie")
                return False

            self.logger.info("🔢 Iniciando extracción manual de números de serie...")

            success, message, excel_file = self.automation_service.extract_data_with_series()

            if success:
                serie_count = self.automation_service.get_last_serie_count()
                final_message = f"Extracción completada exitosamente\n\n"
                final_message += f"📊 {message}\n"
                final_message += f"🔢 Números de serie extraídos: {serie_count}\n"
                if excel_file:
                    final_message += f"📄 Archivo Excel: {excel_file}"

                self.logger.info(f"✅ Extracción manual exitosa: {serie_count} números de serie")
                messagebox.showinfo("Extracción Exitosa", final_message)
            else:
                self.logger.error(f"❌ Extracción manual falló: {message}")
                messagebox.showerror("Error en Extracción", f"Error extrayendo números de serie:\n\n{message}")

            return success
        except Exception as e:
            error_msg = f"Error en extracción manual: {str(e)}"
            self.logger.error(error_msg)
            messagebox.showerror("Error", error_msg)
            return False

    def cleanup(self):
        """Limpia recursos al cerrar la pestaña"""
        self._is_closing = True
        self.logger.info("Cerrando sistema...")

        # Guardar configuraciones actuales antes de cerrar
        try:
            self._save_current_date_config()
            self._save_current_state_config()
        except Exception as e:
            self.logger.warning(f"Error guardando configuraciones al cerrar: {e}")

        # Si hay una ejecución en curso, marcarla como interrumpida
        if self.registry_tab and self.current_execution_record:
            try:
                end_time = datetime.now()

                # Incluir información de números de serie en el mensaje de interrupción
                serie_count = self.automation_service.get_last_serie_count()
                interruption_message = "Ejecución interrumpida por cierre de aplicación"
                if serie_count > 0:
                    interruption_message += f" | {serie_count} números de serie extraídos antes de la interrupción"

                self.registry_tab.update_execution_record(
                    record_id=self.current_execution_record['id'],
                    end_time=end_time,
                    status="Fallido",
                    error_message=interruption_message
                )
                self.logger.info("Registro actualizado: Ejecución interrumpida")
            except Exception as e:
                self.logger.warning(f"Error finalizando registro: {str(e)}")

        # Detener automatización
        if self.automation_service:
            self.automation_service.stop_all()

        # Limpiar logger
        if self.logger:
            self.logger.info("Sistema cerrado correctamente")