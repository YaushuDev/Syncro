# automation_tab.py
# Ubicación: /syncro_bot/gui/tabs/automation_tab.py
"""
Pestaña de automatización refactorizada para Syncro Bot.
Coordina todos los componentes de automatización: credenciales, servicio,
UI y logging. Mantiene la interfaz limpia y maneja la comunicación
entre componentes y la integración con el sistema de registro.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import threading
from datetime import datetime

# Importar componentes de automatización
from ..components.automation.credentials_manager import CredentialsManager
from ..components.automation.automation_service import AutomationService
from ..components.automation.automation_ui_components import (
    AutomationTheme, AutomationUIFactory, CollapsibleSection
)
from ..components.automation.automation_logger import AutomationLoggerFactory, LogLevel


class AutomationTab:
    """Pestaña de automatización refactorizada con componentes modulares"""

    def __init__(self, parent_notebook):
        self.parent = parent_notebook
        self.theme = AutomationTheme()

        # Componentes principales
        self.credentials_manager = CredentialsManager()
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
        """Inicializa los componentes principales"""
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
        """Crea la columna izquierda con secciones colapsables"""
        left_column = tk.Frame(parent, bg=self.theme.colors['bg_primary'], width=500)
        left_column.grid(row=0, column=0, sticky='ns', padx=(0, 5))
        left_column.grid_propagate(False)

        # Configurar filas
        left_column.grid_rowconfigure(0, weight=0)  # Credenciales
        left_column.grid_rowconfigure(1, weight=0)  # Estado
        left_column.grid_rowconfigure(2, weight=0)  # Controles
        left_column.grid_rowconfigure(3, weight=1)  # Espaciador
        left_column.grid_columnconfigure(0, weight=1)

        # Crear secciones usando componentes modulares
        self._create_credentials_section(left_column)
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

    def _create_status_section(self, parent):
        """Crea sección de estado usando componentes modulares"""
        section = AutomationUIFactory.create_collapsible_section(
            parent, "status", "📊 Estado del Sistema", self.theme
        )
        content = section.create(row=1, min_height=150, default_expanded=False)
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
        content = section.create(row=2, min_height=180, default_expanded=False)
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

        # Agregar mensajes iniciales al log
        self.logger.info("🚀 Sistema de automatización con login automático iniciado")
        self.logger.info("🔧 Configuración: Esperas robustas y detección inteligente de carga")

        if self.automation_service.is_selenium_available():
            self.logger.info("✅ Selenium disponible - Login automático habilitado")
        else:
            self.logger.warning("⚠️ Selenium no disponible - Solo modo navegador básico")

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

                success, message = self.automation_service.test_credentials(username, password)
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
        """Inicia la automatización usando componentes"""
        if self._is_closing:
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

        def start_thread():
            try:
                if self._is_closing:
                    return

                self.logger.log_automation_start({'username': username})

                # Registrar inicio de ejecución
                if self.registry_tab:
                    try:
                        self.execution_start_time = datetime.now()
                        self.current_execution_record = self.registry_tab.add_execution_record(
                            start_time=self.execution_start_time,
                            profile_name="Manual (Con Login)",
                            user_type="Usuario"
                        )
                        self.logger.info(f"Registro de ejecución creado: ID {self.current_execution_record['id']}")
                    except Exception as e:
                        self.logger.warning(f"Error creando registro: {str(e)}")

                success, message = self.automation_service.start_automation(username, password)

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
        """Maneja el resultado del inicio de automatización"""
        if self._is_closing:
            return

        if success:
            self.status_panel.update_automation_status("En ejecución", self.theme.colors['success'])
            self.control_panel.set_button_state('start_button', 'disabled')
            self.control_panel.set_button_text('start_button', '▶️ Iniciando...')
            self.control_panel.set_button_state('pause_button', 'normal')

            self.logger.log_automation_end(True, {'message': message})

            display_message = f"{message}\n\n"
            if self.automation_service.is_selenium_available():
                display_message += "🎯 Características avanzadas activas:\n"
                display_message += "• Login automático completado\n"
                display_message += "• Esperas robustas implementadas\n"
                display_message += "• Detección inteligente de carga\n"
                display_message += "• Navegador controlado automáticamente\n\n"
                display_message += "💡 El navegador permanecerá abierto para continuar la automatización."
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

                self.logger.info("Automatización pausada exitosamente")

                # Actualizar registro como exitoso
                self._update_execution_record("Exitoso", "")

                if not self._is_closing:
                    messagebox.showinfo("Éxito", message)
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
        """Actualiza el registro de ejecución"""
        if self.registry_tab and self.current_execution_record:
            try:
                end_time = datetime.now()
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

    def cleanup(self):
        """Limpia recursos al cerrar la pestaña"""
        self._is_closing = True
        self.logger.info("Cerrando sistema...")

        # Si hay una ejecución en curso, marcarla como interrumpida
        if self.registry_tab and self.current_execution_record:
            try:
                end_time = datetime.now()
                self.registry_tab.update_execution_record(
                    record_id=self.current_execution_record['id'],
                    end_time=end_time,
                    status="Fallido",
                    error_message="Ejecución interrumpida por cierre de aplicación"
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