# profiles_tab.py
# Ubicación: /syncro_bot/gui/tabs/profiles_tab.py
"""
Pestaña de perfiles de reportes automáticos para Syncro Bot.
Coordina componentes de datos, UI y servicios para la gestión
de perfiles simplificados que programan envío automático de reportes Excel por correo.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from ..components.profile_data_manager import ProfilesManager, ProfileValidator
from ..components.profile_execution_service import ProfileExecutionService, ProfileReportService
from ..components.profile_ui_components import ProfileUICoordinator
from ..components.registry_ui_components import UITheme, CardFrame


class ProfilesTab:
    """Coordinador principal de la pestaña de perfiles de reportes automáticos"""

    def __init__(self, parent_notebook):
        # Configuración básica
        self.parent = parent_notebook
        self.theme = UITheme()

        # Componentes principales
        self.profiles_manager = ProfilesManager()
        self.validator = ProfileValidator()
        self.execution_service = ProfileExecutionService()
        self.report_service = ProfileReportService()
        self.ui_coordinator = None

        # Estado
        self.selected_profile = None
        self.registry_tab = None
        self.current_execution_record = None

        # Inicializar
        self._initialize_components()

    def _initialize_components(self):
        """Inicializa todos los componentes"""
        self.create_tab()
        self._setup_services()
        self.refresh_data()

    def create_tab(self):
        """Crear la pestaña de perfiles de reportes"""
        self.frame = ttk.Frame(self.parent)
        self.parent.add(self.frame, text="Perfiles de Reportes")
        self._create_interface()

    def _create_interface(self):
        """Crea la interfaz principal con diseño de 2 columnas"""
        main_container = tk.Frame(self.frame, bg=self.theme.colors['bg_primary'])
        main_container.pack(fill='both', expand=True, padx=15, pady=10)

        # Configurar grid para 2 columnas
        main_container.grid_columnconfigure(0, weight=0, minsize=500)
        main_container.grid_columnconfigure(1, weight=0, minsize=1)
        main_container.grid_columnconfigure(2, weight=1, minsize=350)
        main_container.grid_rowconfigure(0, weight=1)

        # Crear columnas
        left_column = self._create_column(main_container, 0, (0, 5))
        self._create_separator(main_container)
        right_column = self._create_column(main_container, 2, (5, 0))

        # Inicializar UI coordinator
        self._setup_ui_coordinator(main_container, left_column, right_column)

    def _create_column(self, parent, col, padx):
        """Crea una columna con configuración estándar"""
        column = tk.Frame(parent, bg=self.theme.colors['bg_primary'])
        if col == 0:
            column.configure(width=500)
            column.grid_propagate(False)

        column.grid(row=0, column=col, sticky='nsew' if col == 2 else 'ns', padx=padx)
        return column

    def _create_separator(self, parent):
        """Crea separador visual"""
        separator = tk.Frame(parent, bg=self.theme.colors['border'], width=1)
        separator.grid(row=0, column=1, sticky='ns', padx=5)

    def _setup_ui_coordinator(self, main_container, left_column, right_column):
        """Configura el coordinador de UI"""
        self.ui_coordinator = ProfileUICoordinator(main_container, self.theme)
        self.ui_coordinator.initialize_components(left_column, right_column)
        self.ui_coordinator.set_callback('profile_selected', self._on_profile_selected)

        # Crear secciones simplificadas (sin reportes)
        self._create_form_sections(left_column)
        self._create_list_sections(right_column)

    def _create_form_sections(self, parent):
        """Crea las secciones del formulario simplificadas con mejor espaciado"""
        # Configurar filas
        for i in range(3):
            parent.grid_rowconfigure(i, weight=0 if i < 2 else 1)
        parent.grid_columnconfigure(0, weight=1)

        # Secciones optimizadas con alturas reducidas
        sections_config = [
            ("basic_config", "⚙️ Configuración Básica",
             lambda c: self.ui_coordinator.form_handler.create_basic_config_form(c),
             True, 160),  # Reducido de 180 a 160
            ("schedule", "⏰ Programación de Envío",
             lambda c: self.ui_coordinator.form_handler.create_schedule_form(c),
             False, 240),  # Reducido de 280 a 240
            ("actions", "🎮 Acciones",
             self._create_actions_content,
             False, 200)  # Reducido de 220 a 200
        ]

        for i, (section_id, title, content_creator, expanded, height) in enumerate(sections_config):
            self.ui_coordinator.section_manager.create_collapsible_section(
                section_id, title, content_creator, row=i,
                default_expanded=expanded, min_height=height
            )

    def _create_actions_content(self, container):
        """Crea contenido de acciones"""
        self.ui_coordinator.action_buttons.create_action_buttons(container)
        self.ui_coordinator.action_buttons.set_button_commands(
            save_command=lambda: self._handle_profile_operation('save'),
            update_command=lambda: self._handle_profile_operation('update'),
            test_command=self._test_send_report,
            clear_command=self._clear_form
        )
        return container

    def _create_list_sections(self, parent):
        """Crea las secciones de la lista"""
        # Configurar filas
        parent.grid_rowconfigure(0, weight=0)
        parent.grid_rowconfigure(1, weight=1)
        parent.grid_columnconfigure(0, weight=1)

        # Status section (actualizado)
        self._create_status_section(parent)

        # List section
        self._create_profile_list_section(parent)

    def _create_status_section(self, parent):
        """Crea sección de estado del sistema"""
        status_container = tk.Frame(parent, bg=self.theme.colors['bg_primary'])
        status_container.grid(row=0, column=0, sticky='ew', pady=(0, 15))

        status_card = CardFrame(status_container, "📊 Estado del Sistema de Reportes", self.theme)
        status_content = status_card.create()
        self.ui_coordinator.status_display.create_status_display(status_content)

    def _create_profile_list_section(self, parent):
        """Crea sección de lista de perfiles"""
        list_container = tk.Frame(parent, bg=self.theme.colors['bg_primary'])
        list_container.grid(row=1, column=0, sticky='nsew')

        list_card = CardFrame(list_container, "📋 Perfiles de Reportes Automáticos", self.theme)
        list_content = list_card.create()

        self.ui_coordinator.list_handler.create_profile_list(list_content)
        self.ui_coordinator.list_handler.create_list_buttons(list_content)
        self.ui_coordinator.list_handler.set_button_commands(
            delete_command=self._delete_profile,
            refresh_command=self.refresh_data
        )

    def _setup_services(self):
        """Configura los servicios"""
        self.execution_service.add_execution_callback(self._on_execution_event)
        if self.registry_tab:
            self.report_service.set_registry_tab(self.registry_tab)
            self.execution_service.set_registry_tab(self.registry_tab)

    def _on_profile_selected(self, profile_name):
        """Maneja selección de perfil"""
        self.selected_profile = None
        if profile_name:
            profiles = self.profiles_manager.get_profiles()
            self.selected_profile = next(
                (p for p in profiles if p['name'] == profile_name), None
            )
            if self.selected_profile:
                self.ui_coordinator.load_profile_to_form(self.selected_profile)

    def _handle_profile_operation(self, operation):
        """Maneja operaciones de perfil (guardar/actualizar) simplificadas"""
        try:
            form_data = self.ui_coordinator.get_form_data()
            errors = self._validate_profile_data(form_data)

            if errors:
                messagebox.showerror("Errores de Validación", "\n".join(errors))
                return

            if operation == 'save':
                self._save_new_profile(form_data)
            elif operation == 'update' and self.selected_profile:
                self._update_existing_profile(form_data)
            else:
                messagebox.showwarning("Sin Selección", "No hay perfil seleccionado para actualizar")

        except Exception as e:
            messagebox.showerror("Error", f"Error al {operation} perfil:\n{str(e)}")

    def _validate_profile_data(self, form_data):
        """Valida datos del formulario simplificado"""
        return self.validator.validate_profile_data(
            name=form_data['name'],
            hour=form_data['hour'],
            minute=form_data['minute'],
            days=form_data['days']
        )

    def _save_new_profile(self, form_data):
        """Guarda un nuevo perfil"""
        self.profiles_manager.add_profile(**form_data)
        messagebox.showinfo("Éxito", f"Perfil '{form_data['name']}' guardado correctamente\n\n" +
                            "Se enviará automáticamente un reporte Excel por correo según la programación.")
        self._post_operation_cleanup()

    def _update_existing_profile(self, form_data):
        """Actualiza perfil existente"""
        updated_profile = self.profiles_manager.update_profile(self.selected_profile["id"], **form_data)
        if updated_profile:
            messagebox.showinfo("Éxito", f"Perfil '{form_data['name']}' actualizado correctamente")
            self._post_operation_cleanup()
        else:
            messagebox.showerror("Error", "No se pudo actualizar el perfil")

    def _post_operation_cleanup(self):
        """Limpieza después de operaciones"""
        self._clear_form()
        self.refresh_data()

    def _delete_profile(self):
        """Elimina el perfil seleccionado"""
        selected_name = self.ui_coordinator.get_selected_profile_name()
        if not selected_name:
            messagebox.showwarning("Sin Selección", "No hay perfil seleccionado para eliminar")
            return

        if not messagebox.askyesno("Confirmar",
                                   f"¿Está seguro de eliminar el perfil '{selected_name}'?\n\n" +
                                   "Se detendrán los reportes automáticos programados."):
            return

        try:
            profile = next(
                (p for p in self.profiles_manager.get_profiles() if p['name'] == selected_name),
                None
            )
            if profile:
                self.profiles_manager.remove_profile(profile["id"])
                messagebox.showinfo("Éxito", "Perfil eliminado correctamente")
                self._post_operation_cleanup()
            else:
                messagebox.showerror("Error", "No se encontró el perfil para eliminar")

        except Exception as e:
            messagebox.showerror("Error", f"Error al eliminar perfil:\n{str(e)}")

    def _test_send_report(self):
        """Prueba el envío de reporte para un perfil seleccionado"""
        if not self.selected_profile:
            messagebox.showwarning("Sin Selección", "Debe seleccionar un perfil para probar el envío")
            return

        # Verificar que el sistema esté listo
        ready, message = self.execution_service.validate_execution_environment()
        if not ready:
            messagebox.showerror("Sistema No Listo", f"No se puede enviar reporte:\n\n{message}\n\n" +
                                 "Configure el email en la pestaña 'Email' primero.")
            return

        if self.execution_service.is_busy():
            messagebox.showwarning("Ocupado", "Ya hay un envío de reporte en curso")
            return

        # Confirmar envío de prueba
        if not messagebox.askyesno("Confirmar Envío",
                                   f"¿Enviar reporte de prueba para '{self.selected_profile['name']}'?\n\n" +
                                   "Se enviará un Excel con los registros de los últimos 7 días."):
            return

        self.execution_service.execute_profile_async(
            profile=self.selected_profile,
            success_callback=self._on_test_success,
            error_callback=self._on_test_error
        )

        messagebox.showinfo("Enviando Reporte",
                            f"Se está enviando el reporte de prueba para '{self.selected_profile['name']}'.\n\n" +
                            "Revise su correo en unos momentos.")

    def _clear_form(self):
        """Limpia el formulario"""
        self.ui_coordinator.clear_form()
        self.selected_profile = None

    def _on_execution_event(self, event_type, profile, data):
        """Maneja eventos de ejecución de reportes"""
        handlers = {
            'start': lambda: self._handle_execution_start(profile),
            'end': lambda: self._handle_execution_end(profile, data)
        }
        handler = handlers.get(event_type)
        if handler:
            handler()

    def _handle_execution_start(self, profile):
        """Maneja inicio de envío de reporte"""
        if self.registry_tab:
            try:
                from datetime import datetime
                self.current_execution_record = self.registry_tab.add_execution_record(
                    start_time=datetime.now(),
                    profile_name=profile['name'],
                    user_type="Sistema"
                )
            except Exception as e:
                print(f"Error creando registro de ejecución: {e}")

    def _handle_execution_end(self, profile, data):
        """Maneja finalización de envío de reporte"""
        success = data.get('success', False)
        message = data.get('message', '')

        # Actualizar registro
        if self.registry_tab and hasattr(self, 'current_execution_record'):
            try:
                from datetime import datetime
                self.registry_tab.update_execution_record(
                    record_id=self.current_execution_record['id'],
                    end_time=datetime.now(),
                    status="Exitoso" if success else "Fallido",
                    error_message="" if success else message
                )
            except Exception as e:
                print(f"Error actualizando registro: {e}")

    def _on_test_success(self, profile, message):
        """Callback para envío exitoso de reporte de prueba"""
        self.frame.after(0, lambda: messagebox.showinfo(
            "Reporte Enviado",
            f"✅ Reporte de prueba para '{profile['name']}' enviado exitosamente.\n\n{message}\n\n" +
            "Revise su bandeja de entrada."
        ))

    def _on_test_error(self, profile, message):
        """Callback para error en envío de reporte"""
        self.frame.after(0, lambda: messagebox.showerror(
            "Error de Envío",
            f"❌ Error enviando reporte para '{profile['name']}':\n\n{message}\n\n" +
            "Verifique la configuración de email."
        ))

    def refresh_data(self):
        """Refresca todos los datos mostrados"""
        try:
            profiles = self.profiles_manager.get_profiles()
            stats = self.profiles_manager.get_statistics()

            self.ui_coordinator.update_profile_list(profiles)
            self.ui_coordinator.update_statistics(stats)

            # Actualizar estado del email
            if hasattr(self, 'registry_tab') and self.registry_tab:
                email_tab = getattr(self.registry_tab, 'email_tab', None)
                self.ui_coordinator.update_email_status(email_tab)

        except Exception as e:
            messagebox.showerror("Error", f"Error refrescando datos:\n{str(e)}")

    # ===== MÉTODOS DE INTEGRACIÓN =====

    def set_registry_tab(self, registry_tab):
        """Establece la referencia al RegistroTab para logging y envío de reportes"""
        self.registry_tab = registry_tab
        self.report_service.set_registry_tab(registry_tab)
        self.execution_service.set_registry_tab(registry_tab)

        # Actualizar estado del email después de conectar
        self.refresh_data()

    def get_active_profiles(self):
        """Obtiene los perfiles activos"""
        return self.profiles_manager.get_active_profiles()

    def execute_profile_automatically(self, profile):
        """Método público para ejecutar un perfil automáticamente (envío de reporte)"""
        if self.execution_service.is_busy():
            return False, "Servicio de ejecución ocupado"

        validation_error = self.validator.validate_profile_for_execution(profile)
        if validation_error:
            return False, validation_error

        return self.execution_service.execute_profile(profile)

    def get_execution_status(self):
        """Obtiene estado actual de ejecución"""
        return self.execution_service.get_current_execution()

    def cleanup(self):
        """Limpia recursos al cerrar la pestaña"""
        try:
            if self.execution_service and self.execution_service.is_busy():
                self.execution_service.force_stop_execution()

            if self.execution_service:
                self.execution_service._execution_callbacks.clear()

            print("ProfilesTab (Reportes) cleanup completado")
        except Exception as e:
            print(f"Error durante cleanup de ProfilesTab: {e}")

    def get_system_info(self):
        """Obtiene información del sistema de reportes"""
        try:
            profiles = self.profiles_manager.get_profiles()
            active_profiles = self.profiles_manager.get_active_profiles()

            email_ready = False
            if hasattr(self, 'registry_tab') and self.registry_tab:
                email_tab = getattr(self.registry_tab, 'email_tab', None)
                email_ready = email_tab and email_tab.is_email_configured()

            return {
                'total_profiles': len(profiles),
                'active_profiles': len(active_profiles),
                'email_configured': email_ready,
                'execution_busy': self.execution_service.is_busy(),
                'system_ready': email_ready and len(active_profiles) > 0
            }
        except Exception as e:
            print(f"Error obteniendo info del sistema: {e}")
            return {
                'total_profiles': 0,
                'active_profiles': 0,
                'email_configured': False,
                'execution_busy': False,
                'system_ready': False
            }