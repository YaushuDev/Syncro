# schedule_tab.py
# Ubicación: /syncro_bot/gui/tabs/schedule_tab.py
"""
Pestaña de programación de ejecución automática para Syncro Bot.
Coordina componentes de datos, UI y servicios para la gestión
de programaciones que ejecutan el bot automáticamente en horarios específicos.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from ..components.schedule_data_manager import ScheduleManager, ScheduleValidator
from ..components.schedule_execution_service import ScheduleExecutionService, BotScheduler
from ..components.schedule_ui_components import ScheduleUICoordinator
from ..components.registry_ui_components import UITheme, CardFrame


class ScheduleTab:
    """Coordinador principal de la pestaña de programación de ejecución automática"""

    def __init__(self, parent_notebook):
        # Configuración básica
        self.parent = parent_notebook
        self.theme = UITheme()

        # Componentes principales
        self.schedule_manager = ScheduleManager()
        self.validator = ScheduleValidator()
        self.execution_service = ScheduleExecutionService()
        self.bot_scheduler = None
        self.ui_coordinator = None

        # Estado
        self.selected_schedule = None
        self.registry_tab = None
        self.automation_tab = None
        self.current_execution_record = None
        self.integrations_ready = False
        self.pending_status_update = False

        # Inicializar
        self._initialize_components()

    def _initialize_components(self):
        """Inicializa todos los componentes"""
        self.create_tab()
        self._setup_services()
        self._load_initial_data()

    def create_tab(self):
        """Crear la pestaña de programación"""
        self.frame = ttk.Frame(self.parent)
        self.parent.add(self.frame, text="Programar Ejecución")
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
        self.ui_coordinator = ScheduleUICoordinator(main_container, self.theme)
        self.ui_coordinator.initialize_components(left_column, right_column)
        self.ui_coordinator.set_callback('schedule_selected', self._on_schedule_selected)

        # Crear secciones
        self._create_form_sections(left_column)
        self._create_list_sections(right_column)

    def _create_form_sections(self, parent):
        """Crea las secciones del formulario"""
        # Configurar filas
        parent.grid_rowconfigure(0, weight=0)
        parent.grid_rowconfigure(1, weight=0)
        parent.grid_rowconfigure(2, weight=0)
        parent.grid_rowconfigure(3, weight=1)
        parent.grid_columnconfigure(0, weight=1)

        # Sección 1: Configuración Básica
        self._create_custom_section(parent, "basic_config", "⚙️ Configuración Básica",
                                    lambda c: self.ui_coordinator.form_handler.create_basic_config_form(c),
                                    row=0, expanded=True, height=160, pady_bottom=10)

        # Sección 2: Programación de Horarios
        self._create_custom_section(parent, "schedule", "⏰ Programación de Horarios",
                                    lambda c: self.ui_coordinator.form_handler.create_schedule_form(c),
                                    row=1, expanded=False, height=240, pady_bottom=10)

        # Sección 3: Acciones
        self._create_custom_section(parent, "actions", "🎮 Acciones",
                                    self._create_actions_content,
                                    row=2, expanded=False, height=200, pady_bottom=0)

    def _create_custom_section(self, parent, section_id, title, content_creator,
                               row, expanded, height, pady_bottom):
        """Crea una sección colapsable con control personalizado de espaciado"""
        section_container = tk.Frame(parent, bg=self.theme.colors['bg_primary'])
        section_container.configure(height=55)
        section_container.grid(row=row, column=0, sticky='ew', pady=(0, pady_bottom))
        section_container.grid_columnconfigure(0, weight=1)
        section_container.grid_propagate(False)

        # Frame de la tarjeta
        card = tk.Frame(section_container, bg=self.theme.colors['bg_primary'],
                        relief='solid', bd=1)
        card.configure(highlightbackground=self.theme.colors['border'],
                       highlightcolor=self.theme.colors['border'],
                       highlightthickness=1)
        card.grid(row=0, column=0, sticky='ew')
        card.grid_columnconfigure(0, weight=1)

        # Header clickeable
        header = tk.Frame(card, bg=self.theme.colors['bg_secondary'], height=45, cursor='hand2')
        header.grid(row=0, column=0, sticky='ew')
        header.grid_propagate(False)
        header.grid_columnconfigure(0, weight=1)

        # Contenido del header
        header_content = tk.Frame(header, bg=self.theme.colors['bg_secondary'])
        header_content.grid(row=0, column=0, sticky='ew', padx=15, pady=12)
        header_content.grid_columnconfigure(0, weight=1)

        # Título
        title_label = tk.Label(header_content, text=title, bg=self.theme.colors['bg_secondary'],
                               fg=self.theme.colors['text_primary'], font=('Arial', 12, 'bold'),
                               cursor='hand2')
        title_label.grid(row=0, column=0, sticky='w')

        # Flecha indicadora
        arrow_label = tk.Label(header_content, text="▶" if not expanded else "▼",
                               bg=self.theme.colors['bg_secondary'], fg=self.theme.colors['accent'],
                               font=('Arial', 10, 'bold'), cursor='hand2')
        arrow_label.grid(row=0, column=1, sticky='e')

        # Content area
        content_frame = tk.Frame(card, bg=self.theme.colors['bg_primary'])
        content_frame.grid_columnconfigure(0, weight=1)

        # Crear contenido específico
        content_creator(content_frame)

        # Guardar referencias para el UI coordinator
        if not hasattr(self.ui_coordinator, 'section_frames'):
            self.ui_coordinator.section_frames = {}

        self.ui_coordinator.section_frames[section_id] = {
            'container': section_container,
            'header': header,
            'content': content_frame,
            'arrow': arrow_label,
            'expanded': expanded,
            'min_height': height
        }

        # Estado inicial
        if expanded:
            content_frame.grid(row=1, column=0, sticky='ew')
            section_container.configure(height=height)
            section_container.grid_propagate(True)
            if not hasattr(self.ui_coordinator, 'expanded_section'):
                self.ui_coordinator.expanded_section = section_id

        # Bind eventos
        def toggle_section(event=None):
            self._toggle_section(section_id)

        header.bind("<Button-1>", toggle_section)
        title_label.bind("<Button-1>", toggle_section)
        arrow_label.bind("<Button-1>", toggle_section)

    def _toggle_section(self, section_id):
        """Alterna la visibilidad de una sección"""
        if not hasattr(self.ui_coordinator, 'section_frames'):
            return

        current_section = self.ui_coordinator.section_frames[section_id]

        if current_section['expanded']:
            # Colapsar sección actual
            current_section['content'].grid_remove()
            current_section['arrow'].configure(text="▶")
            current_section['expanded'] = False
            current_section['container'].configure(height=55)
            current_section['container'].grid_propagate(False)
            if hasattr(self.ui_coordinator, 'expanded_section'):
                self.ui_coordinator.expanded_section = None
        else:
            # Colapsar otra sección si está expandida
            if hasattr(self.ui_coordinator, 'expanded_section') and self.ui_coordinator.expanded_section:
                if self.ui_coordinator.expanded_section in self.ui_coordinator.section_frames:
                    expanded_section = self.ui_coordinator.section_frames[self.ui_coordinator.expanded_section]
                    expanded_section['content'].grid_remove()
                    expanded_section['arrow'].configure(text="▶")
                    expanded_section['expanded'] = False
                    expanded_section['container'].configure(height=55)
                    expanded_section['container'].grid_propagate(False)

            # Expandir nueva sección
            current_section['content'].grid(row=1, column=0, sticky='ew')
            current_section['arrow'].configure(text="▼")
            current_section['expanded'] = True
            current_section['container'].configure(height=current_section['min_height'])
            current_section['container'].grid_propagate(True)
            self.ui_coordinator.expanded_section = section_id

        self.frame.update_idletasks()

    def _create_actions_content(self, container):
        """Crea contenido de acciones"""
        self.ui_coordinator.action_buttons.create_action_buttons(container)
        self.ui_coordinator.action_buttons.set_button_commands(
            save_command=lambda: self._handle_schedule_operation('save'),
            update_command=lambda: self._handle_schedule_operation('update'),
            test_command=self._test_execute_bot,
            clear_command=self._clear_form
        )
        return container

    def _create_list_sections(self, parent):
        """Crea las secciones de la lista"""
        # Configurar filas
        parent.grid_rowconfigure(0, weight=0)
        parent.grid_rowconfigure(1, weight=1)
        parent.grid_columnconfigure(0, weight=1)

        # Status section
        self._create_status_section(parent)

        # List section
        self._create_schedule_list_section(parent)

    def _create_status_section(self, parent):
        """Crea sección de estado del sistema"""
        status_container = tk.Frame(parent, bg=self.theme.colors['bg_primary'])
        status_container.grid(row=0, column=0, sticky='ew', pady=(0, 15))

        status_card = CardFrame(status_container, "📊 Estado del Sistema de Programación", self.theme)
        status_content = status_card.create()
        self.ui_coordinator.status_display.create_status_display(status_content)

    def _create_schedule_list_section(self, parent):
        """Crea sección de lista de programaciones"""
        list_container = tk.Frame(parent, bg=self.theme.colors['bg_primary'])
        list_container.grid(row=1, column=0, sticky='nsew')

        list_card = CardFrame(list_container, "📋 Programaciones de Ejecución Automática", self.theme)
        list_content = list_card.create()

        self.ui_coordinator.list_handler.create_schedule_list(list_content)
        self.ui_coordinator.list_handler.create_list_buttons(list_content)
        self.ui_coordinator.list_handler.set_button_commands(
            delete_command=self._delete_schedule,
            refresh_command=self.refresh_data
        )

    def _setup_services(self):
        """Configura los servicios"""
        self.execution_service.add_execution_callback(self._on_execution_event)

    def _load_initial_data(self):
        """Carga datos iniciales"""
        try:
            schedules = self.schedule_manager.get_schedules()
            stats = self.schedule_manager.get_statistics()

            self.ui_coordinator.update_schedule_list(schedules)
            self.ui_coordinator.update_statistics(stats)

        except Exception as e:
            print(f"Error cargando datos iniciales: {e}")
            if self.ui_coordinator:
                self.ui_coordinator.update_schedule_list([])
                self.ui_coordinator.update_statistics({'total': 0, 'active': 0})

    def _deferred_status_update(self):
        """Actualiza el estado del sistema de forma diferida"""
        if not self.integrations_ready:
            return

        try:
            # Actualizar estado de automatización
            self.ui_coordinator.update_automation_status(self.automation_tab)

            # Actualizar estado del scheduler
            scheduler_running = self.bot_scheduler and self.bot_scheduler.is_running
            self.ui_coordinator.update_scheduler_status(scheduler_running)

            self.pending_status_update = False
            print("✅ Estado del sistema de programación actualizado")
        except Exception as e:
            print(f"Error en actualización diferida: {e}")

    def _on_schedule_selected(self, schedule_name):
        """Maneja selección de programación"""
        self.selected_schedule = None
        if schedule_name:
            schedules = self.schedule_manager.get_schedules()
            self.selected_schedule = next(
                (s for s in schedules if s['name'] == schedule_name), None
            )
            if self.selected_schedule:
                self.ui_coordinator.load_schedule_to_form(self.selected_schedule)

    def _handle_schedule_operation(self, operation):
        """Maneja operaciones de programación (guardar/actualizar)"""
        try:
            form_data = self.ui_coordinator.get_form_data()
            errors = self._validate_schedule_data(form_data)

            if errors:
                messagebox.showerror("Errores de Validación", "\n".join(errors))
                return

            if operation == 'save':
                self._save_new_schedule(form_data)
            elif operation == 'update' and self.selected_schedule:
                self._update_existing_schedule(form_data)
            else:
                messagebox.showwarning("Sin Selección", "No hay programación seleccionada para actualizar")

        except Exception as e:
            messagebox.showerror("Error", f"Error al {operation} programación:\n{str(e)}")

    def _validate_schedule_data(self, form_data):
        """Valida datos del formulario"""
        return self.validator.validate_schedule_data(
            name=form_data['name'],
            hour=form_data['hour'],
            minute=form_data['minute'],
            days=form_data['days']
        )

    def _save_new_schedule(self, form_data):
        """Guarda una nueva programación"""
        self.schedule_manager.add_schedule(**form_data)
        messagebox.showinfo("Éxito", f"Programación '{form_data['name']}' guardada correctamente\n\n" +
                            "Se ejecutará automáticamente el bot según la programación.")
        self._post_operation_cleanup()

    def _update_existing_schedule(self, form_data):
        """Actualiza programación existente"""
        updated_schedule = self.schedule_manager.update_schedule(self.selected_schedule["id"], **form_data)
        if updated_schedule:
            messagebox.showinfo("Éxito", f"Programación '{form_data['name']}' actualizada correctamente")
            self._post_operation_cleanup()
        else:
            messagebox.showerror("Error", "No se pudo actualizar la programación")

    def _post_operation_cleanup(self):
        """Limpieza después de operaciones"""
        self._clear_form()
        self.refresh_data()

    def _delete_schedule(self):
        """Elimina la programación seleccionada"""
        selected_name = self.ui_coordinator.get_selected_schedule_name()
        if not selected_name:
            messagebox.showwarning("Sin Selección", "No hay programación seleccionada para eliminar")
            return

        if not messagebox.askyesno("Confirmar",
                                   f"¿Está seguro de eliminar la programación '{selected_name}'?\n\n" +
                                   "Se detendrá la ejecución automática programada."):
            return

        try:
            schedule = next(
                (s for s in self.schedule_manager.get_schedules() if s['name'] == selected_name),
                None
            )
            if schedule:
                self.schedule_manager.remove_schedule(schedule["id"])
                messagebox.showinfo("Éxito", "Programación eliminada correctamente")
                self._post_operation_cleanup()
            else:
                messagebox.showerror("Error", "No se encontró la programación para eliminar")

        except Exception as e:
            messagebox.showerror("Error", f"Error al eliminar programación:\n{str(e)}")

    def _test_execute_bot(self):
        """Prueba la ejecución del bot para una programación seleccionada"""
        if not self.selected_schedule:
            messagebox.showwarning("Sin Selección", "Debe seleccionar una programación para probar")
            return

        # Verificar que el sistema esté listo
        ready, message = self.execution_service.validate_execution_environment()
        if not ready:
            messagebox.showerror("Sistema No Listo", f"No se puede ejecutar:\n\n{message}")
            return

        if self.execution_service.is_busy():
            messagebox.showwarning("Ocupado", "Ya hay una ejecución en curso")
            return

        # Confirmar ejecución de prueba
        if not messagebox.askyesno("Confirmar Ejecución",
                                   f"¿Ejecutar el bot de prueba para '{self.selected_schedule['name']}'?\n\n" +
                                   "Se abrirá el bot de automatización en el navegador."):
            return

        self.execution_service.execute_schedule_async(
            schedule=self.selected_schedule,
            success_callback=self._on_test_success,
            error_callback=self._on_test_error
        )

        messagebox.showinfo("Ejecutando Bot",
                            f"Se está ejecutando el bot de prueba para '{self.selected_schedule['name']}'.\n\n" +
                            "El bot se abrirá en su navegador.")

    def _clear_form(self):
        """Limpia el formulario"""
        self.ui_coordinator.clear_form()
        self.selected_schedule = None

    def _on_execution_event(self, event_type, schedule, data):
        """Maneja eventos de ejecución"""
        handlers = {
            'start': lambda: self._handle_execution_start(schedule),
            'end': lambda: self._handle_execution_end(schedule, data)
        }
        handler = handlers.get(event_type)
        if handler:
            handler()

    def _handle_execution_start(self, schedule):
        """Maneja inicio de ejecución"""
        if self.registry_tab:
            try:
                from datetime import datetime
                self.current_execution_record = self.registry_tab.add_execution_record(
                    start_time=datetime.now(),
                    profile_name=f"Programación: {schedule['name']}",
                    user_type="Sistema"
                )
            except Exception as e:
                print(f"Error creando registro de ejecución: {e}")

    def _handle_execution_end(self, schedule, data):
        """Maneja finalización de ejecución"""
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

    def _on_test_success(self, schedule, message):
        """Callback para ejecución exitosa de prueba"""
        self.frame.after(0, lambda: messagebox.showinfo(
            "Bot Ejecutado",
            f"✅ Bot ejecutado exitosamente para '{schedule['name']}'.\n\n{message}"
        ))

    def _on_test_error(self, schedule, message):
        """Callback para error en ejecución"""
        self.frame.after(0, lambda: messagebox.showerror(
            "Error de Ejecución",
            f"❌ Error ejecutando bot para '{schedule['name']}':\n\n{message}"
        ))

    def refresh_data(self):
        """Refresca todos los datos mostrados"""
        try:
            schedules = self.schedule_manager.get_schedules()
            stats = self.schedule_manager.get_statistics()

            self.ui_coordinator.update_schedule_list(schedules)
            self.ui_coordinator.update_statistics(stats)

            # Actualizar estado del sistema si las integraciones están listas
            if self.integrations_ready:
                if not self.pending_status_update:
                    self.pending_status_update = True
                    self.frame.after(10, self._deferred_status_update)

        except Exception as e:
            messagebox.showerror("Error", f"Error refrescando datos:\n{str(e)}")

    # ===== MÉTODOS DE INTEGRACIÓN =====

    def set_automation_tab(self, automation_tab):
        """Establece la referencia al AutomationTab para ejecutar el bot"""
        self.automation_tab = automation_tab
        self.execution_service.set_automation_tab(automation_tab)

        # Inicializar scheduler automático
        self._initialize_bot_scheduler()

        # Marcar integraciones como listas
        self.integrations_ready = True

        # Actualizar estado con delay
        if not self.pending_status_update:
            self.pending_status_update = True
            self.frame.after(50, self._deferred_status_update)

    def set_registry_tab(self, registry_tab):
        """Establece la referencia al RegistroTab para logging"""
        self.registry_tab = registry_tab

    def _initialize_bot_scheduler(self):
        """Inicializa el scheduler automático del bot"""
        if not self.automation_tab:
            print("❌ AutomationTab no disponible - scheduler no iniciado")
            return

        try:
            # Crear instancia del scheduler
            self.bot_scheduler = BotScheduler(
                schedule_manager=self.schedule_manager,
                execution_service=self.execution_service
            )
            print("✅ BotScheduler creado exitosamente")

            # Iniciar scheduler automáticamente
            success, message = self.bot_scheduler.start_scheduler()
            if success:
                print(f"🚀 BotScheduler iniciado: {message}")
            else:
                print(f"❌ Error iniciando BotScheduler: {message}")
                self.bot_scheduler = None

        except Exception as e:
            print(f"❌ Error configurando BotScheduler: {e}")
            self.bot_scheduler = None

    def get_active_schedules(self):
        """Obtiene las programaciones activas"""
        return self.schedule_manager.get_active_schedules()

    def execute_schedule_manually(self, schedule):
        """Método público para ejecutar una programación manualmente"""
        if self.execution_service.is_busy():
            return False, "Servicio de ejecución ocupado"

        validation_error = self.validator.validate_schedule_for_execution(schedule)
        if validation_error:
            return False, validation_error

        return self.execution_service.execute_schedule(schedule)

    def get_execution_status(self):
        """Obtiene estado actual de ejecución"""
        return self.execution_service.get_current_execution()

    def get_scheduler_status(self):
        """Obtiene estado del scheduler"""
        if not self.bot_scheduler:
            return {'available': False, 'running': False}
        return self.bot_scheduler.get_scheduler_status()

    def cleanup(self):
        """Limpia recursos al cerrar la pestaña"""
        try:
            # Detener scheduler
            if self.bot_scheduler and self.bot_scheduler.is_running:
                success, message = self.bot_scheduler.stop_scheduler()
                print(f"BotScheduler detenido: {message}")

            # Detener ejecución si está activa
            if self.execution_service and self.execution_service.is_busy():
                self.execution_service.force_stop_execution()

            # Limpiar callbacks
            if self.execution_service:
                self.execution_service._execution_callbacks.clear()

            print("ScheduleTab cleanup completado")
        except Exception as e:
            print(f"Error durante cleanup de ScheduleTab: {e}")

    def get_system_info(self):
        """Obtiene información del sistema de programación"""
        try:
            schedules = self.schedule_manager.get_schedules()
            active_schedules = self.schedule_manager.get_active_schedules()

            automation_ready = bool(self.automation_tab)
            scheduler_running = self.bot_scheduler and self.bot_scheduler.is_running

            return {
                'total_schedules': len(schedules),
                'active_schedules': len(active_schedules),
                'automation_available': automation_ready,
                'scheduler_running': scheduler_running,
                'execution_busy': self.execution_service.is_busy(),
                'system_ready': automation_ready and scheduler_running
            }
        except Exception as e:
            print(f"Error obteniendo info del sistema: {e}")
            return {
                'total_schedules': 0,
                'active_schedules': 0,
                'automation_available': False,
                'scheduler_running': False,
                'execution_busy': False,
                'system_ready': False
            }