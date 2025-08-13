# schedule_ui_components.py
# Ubicación: /syncro_bot/gui/components/schedule_ui_components.py
"""
Componentes UI para programaciones de ejecución automática del bot.
Proporciona formularios y listas para gestionar programaciones que ejecutan
el bot automáticamente en horarios específicos sin intervención manual.
"""

import tkinter as tk
from tkinter import ttk
from ..components.registry_ui_components import UITheme, StyledWidgets, CollapsibleSection


class ScheduleFormHandler:
    """Maneja los formularios de programaciones de ejecución automática"""

    def __init__(self, parent, theme=None):
        self.parent = parent
        self.theme = theme or UITheme()
        self.styled_widgets = StyledWidgets(self.theme)
        self.widgets = {}
        self.validation_callbacks = []

    def create_basic_config_form(self, container):
        """Crea el formulario de configuración básica"""
        content = tk.Frame(container, bg=self.theme.colors['bg_primary'])
        content.pack(fill='x', padx=18, pady=15)

        # Nombre de la programación
        tk.Label(content, text="📝 Nombre de la Programación:", bg=self.theme.colors['bg_primary'],
                 fg=self.theme.colors['text_primary'], font=('Arial', 10, 'bold')).pack(anchor='w', pady=(0, 5))

        self.widgets['schedule_name'] = self._create_styled_entry(content)
        self.widgets['schedule_name'].pack(fill='x', pady=(0, 15))

        # Estado de la programación
        status_frame = tk.Frame(content, bg=self.theme.colors['bg_tertiary'])
        status_frame.pack(fill='x')

        self.widgets['enabled_var'] = tk.BooleanVar(value=True)
        enabled_cb = tk.Checkbutton(status_frame, text="✅ Programación Activa (Ejecución Automática)",
                                    variable=self.widgets['enabled_var'],
                                    bg=self.theme.colors['bg_tertiary'], fg=self.theme.colors['text_primary'],
                                    font=('Arial', 10, 'bold'),
                                    activebackground=self.theme.colors['bg_tertiary'],
                                    selectcolor=self.theme.colors['bg_tertiary'])
        enabled_cb.pack(padx=15, pady=12)

        # Información
        info_text = "💡 Las programaciones activas ejecutarán el bot automáticamente en los horarios configurados"
        tk.Label(content, text=info_text, bg=self.theme.colors['bg_primary'],
                 fg=self.theme.colors['text_secondary'], font=('Arial', 9, 'italic')).pack(
            anchor='w', pady=(10, 0))

        return content

    def create_schedule_form(self, container):
        """Crea el formulario de configuración de horarios"""
        content = tk.Frame(container, bg=self.theme.colors['bg_primary'])
        content.pack(fill='x', padx=18, pady=15)

        # Configuración de hora
        time_frame = tk.Frame(content, bg=self.theme.colors['bg_primary'])
        time_frame.pack(fill='x', pady=(0, 20))

        tk.Label(time_frame, text="⏰ Hora de Ejecución del Bot:", bg=self.theme.colors['bg_primary'],
                 fg=self.theme.colors['text_primary'], font=('Arial', 10, 'bold')).pack(anchor='w', pady=(0, 8))

        time_inputs = tk.Frame(time_frame, bg=self.theme.colors['bg_tertiary'])
        time_inputs.pack(fill='x', pady=5)

        time_inner = tk.Frame(time_inputs, bg=self.theme.colors['bg_tertiary'])
        time_inner.pack(padx=15, pady=12)

        # Hora
        tk.Label(time_inner, text="Hora:", bg=self.theme.colors['bg_tertiary'],
                 fg=self.theme.colors['text_primary'], font=('Arial', 10)).grid(row=0, column=0, sticky='w',
                                                                                padx=(0, 10))

        self.widgets['hour_var'] = tk.StringVar(value="08")
        hour_spinbox = tk.Spinbox(time_inner, from_=0, to=23, format="%02.0f",
                                  textvariable=self.widgets['hour_var'], width=5,
                                  bg=self.theme.colors['bg_tertiary'], fg=self.theme.colors['text_primary'],
                                  font=('Arial', 10, 'bold'), relief='flat', bd=5)
        hour_spinbox.grid(row=0, column=1, sticky='w', padx=(0, 30))

        # Minutos
        tk.Label(time_inner, text="Minutos:", bg=self.theme.colors['bg_tertiary'],
                 fg=self.theme.colors['text_primary'], font=('Arial', 10)).grid(row=0, column=2, sticky='w',
                                                                                padx=(0, 10))

        self.widgets['minute_var'] = tk.StringVar(value="00")
        minute_spinbox = tk.Spinbox(time_inner, from_=0, to=59, format="%02.0f",
                                    textvariable=self.widgets['minute_var'], width=5,
                                    bg=self.theme.colors['bg_tertiary'], fg=self.theme.colors['text_primary'],
                                    font=('Arial', 10, 'bold'), relief='flat', bd=5)
        minute_spinbox.grid(row=0, column=3, sticky='w')

        # Información sobre la ejecución
        info_frame = tk.Frame(content, bg=self.theme.colors['bg_secondary'])
        info_frame.pack(fill='x', pady=(15, 10))

        info_text = ("🤖 Se ejecutará automáticamente el bot de automatización\n"
                     "en la página de Cabletica en los horarios programados.")
        tk.Label(info_frame, text=info_text, bg=self.theme.colors['bg_secondary'],
                 fg=self.theme.colors['text_secondary'], font=('Arial', 9, 'italic'),
                 justify='left').pack(padx=10, pady=8)

        # Días de la semana
        self._create_days_selection(content)

        return content

    def _create_days_selection(self, parent):
        """Crea la selección de días de la semana"""
        days_frame = tk.Frame(parent, bg=self.theme.colors['bg_primary'])
        days_frame.pack(fill='x')

        tk.Label(days_frame, text="📅 Días para Ejecución Automática:", bg=self.theme.colors['bg_primary'],
                 fg=self.theme.colors['text_primary'], font=('Arial', 10, 'bold')).pack(anchor='w', pady=(0, 8))

        days_container = tk.Frame(days_frame, bg=self.theme.colors['bg_tertiary'])
        days_container.pack(fill='x', pady=5)

        days_grid = tk.Frame(days_container, bg=self.theme.colors['bg_tertiary'])
        days_grid.pack(padx=15, pady=12)

        self.widgets['days_vars'] = {}
        days = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo']

        for i, day in enumerate(days):
            var = tk.BooleanVar()
            self.widgets['days_vars'][day] = var

            cb = tk.Checkbutton(days_grid, text=day, variable=var,
                                bg=self.theme.colors['bg_tertiary'], fg=self.theme.colors['text_primary'],
                                font=('Arial', 9), activebackground=self.theme.colors['bg_tertiary'],
                                selectcolor=self.theme.colors['bg_tertiary'])

            row = i // 2
            col = i % 2
            cb.grid(row=row, column=col, sticky='w', padx=(0, 25), pady=3)

        days_grid.grid_columnconfigure(0, weight=1)
        days_grid.grid_columnconfigure(1, weight=1)

    def get_form_data(self):
        """Obtiene todos los datos del formulario"""
        form_data = {
            'name': self.widgets['schedule_name'].get().strip(),
            'hour': int(self.widgets['hour_var'].get()),
            'minute': int(self.widgets['minute_var'].get()),
            'enabled': self.widgets['enabled_var'].get(),
            'days': []
        }

        # Obtener días seleccionados
        for day, var in self.widgets['days_vars'].items():
            if var.get():
                form_data['days'].append(day)

        return form_data

    def load_schedule_data(self, schedule):
        """Carga datos de una programación en el formulario"""
        self.clear_form()

        self.widgets['schedule_name'].insert(0, schedule['name'])
        self.widgets['hour_var'].set(f"{schedule['hour']:02d}")
        self.widgets['minute_var'].set(f"{schedule['minute']:02d}")
        self.widgets['enabled_var'].set(schedule['enabled'])

        # Cargar días
        for day in schedule['days']:
            if day in self.widgets['days_vars']:
                self.widgets['days_vars'][day].set(True)

    def clear_form(self):
        """Limpia todos los campos del formulario"""
        self.widgets['schedule_name'].delete(0, 'end')
        self.widgets['hour_var'].set("08")
        self.widgets['minute_var'].set("00")
        self.widgets['enabled_var'].set(True)

        # Limpiar días
        for var in self.widgets['days_vars'].values():
            var.set(False)

    def _create_styled_entry(self, parent, **kwargs):
        """Crea un Entry con estilo"""
        return self.styled_widgets.create_styled_entry(parent, **kwargs)

    def add_validation_callback(self, callback):
        """Añade callback de validación"""
        self.validation_callbacks.append(callback)

    def trigger_validation(self):
        """Ejecuta todas las validaciones"""
        for callback in self.validation_callbacks:
            try:
                callback(self.get_form_data())
            except Exception as e:
                print(f"Error en callback de validación: {e}")


class ScheduleListHandler:
    """Maneja la lista de programaciones en TreeView"""

    def __init__(self, parent, theme=None):
        self.parent = parent
        self.theme = theme or UITheme()
        self.styled_widgets = StyledWidgets(self.theme)
        self.widgets = {}
        self.selection_callbacks = []
        self.current_selection = None

    def create_schedule_list(self, container):
        """Crea la lista de programaciones con TreeView"""
        # Frame para la lista
        list_frame = tk.Frame(container, bg=self.theme.colors['bg_primary'])
        list_frame.pack(fill='both', expand=True, pady=(0, 15))

        # Treeview para mostrar programaciones
        columns = ('nombre', 'horario', 'dias', 'estado', 'proxima', 'ejecuciones')
        self.widgets['schedules_tree'] = ttk.Treeview(list_frame, columns=columns, show='headings', height=12)

        # Configurar columnas
        self.widgets['schedules_tree'].heading('nombre', text='Nombre')
        self.widgets['schedules_tree'].heading('horario', text='Horario')
        self.widgets['schedules_tree'].heading('dias', text='Días')
        self.widgets['schedules_tree'].heading('estado', text='Estado')
        self.widgets['schedules_tree'].heading('proxima', text='Próxima Ejecución')
        self.widgets['schedules_tree'].heading('ejecuciones', text='Ejecutado')

        self.widgets['schedules_tree'].column('nombre', width=100)
        self.widgets['schedules_tree'].column('horario', width=70)
        self.widgets['schedules_tree'].column('dias', width=80)
        self.widgets['schedules_tree'].column('estado', width=70)
        self.widgets['schedules_tree'].column('proxima', width=110)
        self.widgets['schedules_tree'].column('ejecuciones', width=70)

        # Scrollbar para la lista
        scrollbar = ttk.Scrollbar(list_frame, orient='vertical', command=self.widgets['schedules_tree'].yview)
        self.widgets['schedules_tree'].configure(yscrollcommand=scrollbar.set)

        # Pack treeview y scrollbar
        self.widgets['schedules_tree'].pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')

        # Bind evento de selección
        self.widgets['schedules_tree'].bind('<<TreeviewSelect>>', self._on_selection_change)

        return list_frame

    def create_list_buttons(self, container):
        """Crea botones de gestión de lista"""
        list_buttons = tk.Frame(container, bg=self.theme.colors['bg_primary'])
        list_buttons.pack(fill='x')

        list_buttons.grid_columnconfigure(0, weight=1)
        list_buttons.grid_columnconfigure(1, weight=1)

        # Botón eliminar
        self.widgets['delete_button'] = self.styled_widgets.create_styled_button(
            list_buttons, "🗑️ Eliminar", None, self.theme.colors['error']
        )
        self.widgets['delete_button'].grid(row=0, column=0, sticky='ew', padx=(0, 5))
        self.widgets['delete_button'].configure(state='disabled')

        # Botón refrescar
        self.widgets['refresh_button'] = self.styled_widgets.create_styled_button(
            list_buttons, "🔄 Refrescar", None, self.theme.colors['info']
        )
        self.widgets['refresh_button'].grid(row=0, column=1, sticky='ew', padx=(5, 0))

        return list_buttons

    def populate_schedules(self, schedules):
        """Puebla la lista con programaciones"""
        # Limpiar lista actual
        for item in self.widgets['schedules_tree'].get_children():
            self.widgets['schedules_tree'].delete(item)

        # Cargar programaciones
        for schedule in schedules:
            # Formatear horario
            horario = f"{schedule['hour']:02d}:{schedule['minute']:02d}"

            # Formatear días (mostrar solo primeros 2)
            dias = ", ".join(schedule['days'][:2])
            if len(schedule['days']) > 2:
                dias += f" (+{len(schedule['days']) - 2})"

            # Estado
            estado = "✅ Activa" if schedule['enabled'] else "❌ Inactiva"

            # Próxima ejecución
            proxima = self._calculate_next_execution_short(schedule)

            # Ejecuciones
            ejecuciones = f"{schedule.get('execution_count', 0)}x"

            # Insertar en la lista
            self.widgets['schedules_tree'].insert('', 'end', values=(
                schedule['name'], horario, dias, estado, proxima, ejecuciones
            ))

    def _calculate_next_execution_short(self, schedule):
        """Calcula próxima ejecución en formato corto"""
        from ..components.schedule_data_manager import ScheduleDataHelper

        if not schedule.get('enabled', False):
            return "Deshabilitada"

        try:
            next_info = ScheduleDataHelper.get_next_execution_info(schedule)
            # Acortar el texto para que quepa en la columna
            if "Hoy a las" in next_info:
                return next_info.replace("Hoy a las ", "Hoy ")
            elif "Mañana a las" in next_info:
                return next_info.replace("Mañana a las ", "Mañ. ")
            elif " a las " in next_info:
                parts = next_info.split(" a las ")
                if len(parts) == 2:
                    return f"{parts[0][:6]}... {parts[1]}"
            return next_info[:15] + "..." if len(next_info) > 15 else next_info
        except:
            return "Error"

    def get_selected_schedule_name(self):
        """Obtiene el nombre de la programación seleccionada"""
        selection = self.widgets['schedules_tree'].selection()
        if not selection:
            return None

        item = self.widgets['schedules_tree'].item(selection[0])
        return item['values'][0] if item['values'] else None

    def clear_selection(self):
        """Limpia la selección actual"""
        self.widgets['schedules_tree'].selection_remove(self.widgets['schedules_tree'].selection())
        self.current_selection = None
        self._update_button_states()

    def set_button_commands(self, delete_command, refresh_command):
        """Establece los comandos de los botones"""
        self.widgets['delete_button'].configure(command=delete_command)
        self.widgets['refresh_button'].configure(command=refresh_command)

    def add_selection_callback(self, callback):
        """Añade callback para cambios de selección"""
        self.selection_callbacks.append(callback)

    def _on_selection_change(self, event):
        """Maneja cambios en la selección"""
        selected_name = self.get_selected_schedule_name()
        self.current_selection = selected_name
        self._update_button_states()

        # Notificar callbacks
        for callback in self.selection_callbacks:
            try:
                callback(selected_name)
            except Exception as e:
                print(f"Error en callback de selección: {e}")

    def _update_button_states(self):
        """Actualiza estado de botones según selección"""
        has_selection = self.current_selection is not None
        state = 'normal' if has_selection else 'disabled'
        self.widgets['delete_button'].configure(state=state)


class ScheduleStatusDisplay:
    """Display de estado y estadísticas de programaciones"""

    def __init__(self, parent, theme=None):
        self.parent = parent
        self.theme = theme or UITheme()
        self.styled_widgets = StyledWidgets(self.theme)
        self.widgets = {}

    def create_status_display(self, container):
        """Crea el display de estado"""
        # Estado de programaciones activas
        active_frame = tk.Frame(container, bg=self.theme.colors['bg_tertiary'])
        active_frame.pack(fill='x', pady=(0, 10))

        tk.Label(active_frame, text="🟢 Programaciones Activas:", bg=self.theme.colors['bg_tertiary'],
                 fg=self.theme.colors['text_primary'], font=('Arial', 10)).pack(
            side='left', padx=10, pady=8)

        self.widgets['active_count'] = tk.Label(
            active_frame, text="0", bg=self.theme.colors['bg_tertiary'],
            fg=self.theme.colors['success'], font=('Arial', 10, 'bold')
        )
        self.widgets['active_count'].pack(side='right', padx=10, pady=8)

        # Total de programaciones
        total_frame = tk.Frame(container, bg=self.theme.colors['bg_tertiary'])
        total_frame.pack(fill='x', pady=(0, 10))

        tk.Label(total_frame, text="📋 Total Programaciones:", bg=self.theme.colors['bg_tertiary'],
                 fg=self.theme.colors['text_primary'], font=('Arial', 10)).pack(
            side='left', padx=10, pady=8)

        self.widgets['total_count'] = tk.Label(
            total_frame, text="0", bg=self.theme.colors['bg_tertiary'],
            fg=self.theme.colors['text_secondary'], font=('Arial', 10, 'bold')
        )
        self.widgets['total_count'].pack(side='right', padx=10, pady=8)

        # Sistema de automatización
        automation_frame = tk.Frame(container, bg=self.theme.colors['bg_tertiary'])
        automation_frame.pack(fill='x', pady=(0, 10))

        tk.Label(automation_frame, text="🤖 Sistema Bot:", bg=self.theme.colors['bg_tertiary'],
                 fg=self.theme.colors['text_primary'], font=('Arial', 10)).pack(
            side='left', padx=10, pady=8)

        self.widgets['automation_status'] = tk.Label(
            automation_frame, text="⏳ Inicializando...", bg=self.theme.colors['bg_tertiary'],
            fg=self.theme.colors['text_secondary'], font=('Arial', 10, 'bold')
        )
        self.widgets['automation_status'].pack(side='right', padx=10, pady=8)

        # Scheduler status
        scheduler_frame = tk.Frame(container, bg=self.theme.colors['bg_tertiary'])
        scheduler_frame.pack(fill='x')

        tk.Label(scheduler_frame, text="⏰ Scheduler:", bg=self.theme.colors['bg_tertiary'],
                 fg=self.theme.colors['text_primary'], font=('Arial', 10)).pack(
            side='left', padx=10, pady=8)

        self.widgets['scheduler_status'] = tk.Label(
            scheduler_frame, text="🔴 Detenido", bg=self.theme.colors['bg_tertiary'],
            fg=self.theme.colors['error'], font=('Arial', 10, 'bold')
        )
        self.widgets['scheduler_status'].pack(side='right', padx=10, pady=8)

        return container

    def update_statistics(self, stats):
        """Actualiza las estadísticas mostradas"""
        self.widgets['active_count'].configure(text=str(stats.get('active', 0)))
        self.widgets['total_count'].configure(text=str(stats.get('total', 0)))

    def update_automation_status(self, automation_tab):
        """Actualiza el estado del sistema de automatización"""
        if not automation_tab:
            self.widgets['automation_status'].configure(
                text="❌ No disponible", fg=self.theme.colors['error']
            )
        else:
            self.widgets['automation_status'].configure(
                text="✅ Disponible", fg=self.theme.colors['success']
            )

    def update_scheduler_status(self, is_running):
        """Actualiza el estado del scheduler"""
        if is_running:
            self.widgets['scheduler_status'].configure(
                text="🟢 Ejecutándose", fg=self.theme.colors['success']
            )
        else:
            self.widgets['scheduler_status'].configure(
                text="🔴 Detenido", fg=self.theme.colors['error']
            )


class ScheduleActionButtons:
    """Botones de acción para programaciones"""

    def __init__(self, parent, theme=None):
        self.parent = parent
        self.theme = theme or UITheme()
        self.styled_widgets = StyledWidgets(self.theme)
        self.widgets = {}

    def create_action_buttons(self, container):
        """Crea botones de acción"""
        content = tk.Frame(container, bg=self.theme.colors['bg_primary'])
        content.pack(fill='x', padx=18, pady=15)

        # Botón guardar programación
        self.widgets['save_button'] = self.styled_widgets.create_styled_button(
            content, "💾 Guardar Nueva Programación", None, self.theme.colors['success']
        )
        self.widgets['save_button'].pack(fill='x', pady=(0, 10))

        # Botón actualizar programación
        self.widgets['update_button'] = self.styled_widgets.create_styled_button(
            content, "📝 Actualizar Programación Seleccionada", None, self.theme.colors['info']
        )
        self.widgets['update_button'].pack(fill='x', pady=(0, 10))
        self.widgets['update_button'].configure(state='disabled')

        # Botón para probar ejecución
        self.widgets['test_execute_button'] = self.styled_widgets.create_styled_button(
            content, "🤖 Probar Ejecución del Bot", None, self.theme.colors['warning']
        )
        self.widgets['test_execute_button'].pack(fill='x', pady=(0, 10))
        self.widgets['test_execute_button'].configure(state='disabled')

        # Botón limpiar formulario
        self.widgets['clear_button'] = self.styled_widgets.create_styled_button(
            content, "🗑️ Limpiar Formulario", None, self.theme.colors['text_secondary']
        )
        self.widgets['clear_button'].pack(fill='x')

        return content

    def set_button_commands(self, save_command, update_command, test_command, clear_command):
        """Establece comandos para todos los botones"""
        self.widgets['save_button'].configure(command=save_command)
        self.widgets['update_button'].configure(command=update_command)
        self.widgets['test_execute_button'].configure(command=test_command)
        self.widgets['clear_button'].configure(command=clear_command)

    def update_button_states(self, has_selection=False, is_editing=False):
        """Actualiza estados de botones según contexto"""
        if has_selection:
            self.widgets['update_button'].configure(state='normal')
            self.widgets['test_execute_button'].configure(state='normal')
            self.widgets['save_button'].configure(state='disabled',
                                                  text="⚠️ Seleccione 'Actualizar' para modificar")
        else:
            self.widgets['update_button'].configure(state='disabled')
            self.widgets['test_execute_button'].configure(state='disabled')
            self.widgets['save_button'].configure(state='normal',
                                                  text="💾 Guardar Nueva Programación")


class ScheduleUICoordinator:
    """Coordinador de todos los componentes UI de programaciones"""

    def __init__(self, parent, theme=None):
        self.parent = parent
        self.theme = theme or UITheme()

        # Componentes UI
        self.form_handler = None
        self.list_handler = None
        self.status_display = None
        self.action_buttons = None

        # Estado
        self.current_schedule = None
        self.ui_callbacks = {}

    def initialize_components(self, left_column, right_column):
        """Inicializa todos los componentes UI"""
        # Form handler
        self.form_handler = ScheduleFormHandler(left_column, self.theme)

        # List handler
        self.list_handler = ScheduleListHandler(right_column, self.theme)

        # Status display
        self.status_display = ScheduleStatusDisplay(right_column, self.theme)

        # Action buttons
        self.action_buttons = ScheduleActionButtons(left_column, self.theme)

        # Configurar callbacks entre componentes
        self._setup_internal_callbacks()

    def _setup_internal_callbacks(self):
        """Configura callbacks internos entre componentes"""
        if self.list_handler:
            self.list_handler.add_selection_callback(self._on_schedule_selected)

    def _on_schedule_selected(self, schedule_name):
        """Maneja selección de programación en la lista"""
        has_selection = schedule_name is not None

        # Actualizar botones
        if self.action_buttons:
            self.action_buttons.update_button_states(has_selection=has_selection)

        # Notificar callback externo si existe
        if 'schedule_selected' in self.ui_callbacks:
            self.ui_callbacks['schedule_selected'](schedule_name)

    def set_callback(self, event_name, callback):
        """Establece callback para eventos UI"""
        self.ui_callbacks[event_name] = callback

    def get_form_data(self):
        """Obtiene datos del formulario"""
        return self.form_handler.get_form_data() if self.form_handler else None

    def load_schedule_to_form(self, schedule):
        """Carga programación en el formulario"""
        if self.form_handler:
            self.form_handler.load_schedule_data(schedule)
            self.current_schedule = schedule

    def clear_form(self):
        """Limpia el formulario"""
        if self.form_handler:
            self.form_handler.clear_form()
        if self.action_buttons:
            self.action_buttons.update_button_states(has_selection=False)
        self.current_schedule = None

    def update_schedule_list(self, schedules):
        """Actualiza la lista de programaciones"""
        if self.list_handler:
            self.list_handler.populate_schedules(schedules)

    def update_statistics(self, stats):
        """Actualiza estadísticas"""
        if self.status_display:
            self.status_display.update_statistics(stats)

    def update_automation_status(self, automation_tab):
        """Actualiza estado del sistema de automatización"""
        if self.status_display:
            self.status_display.update_automation_status(automation_tab)

    def update_scheduler_status(self, is_running):
        """Actualiza estado del scheduler"""
        if self.status_display:
            self.status_display.update_scheduler_status(is_running)

    def get_selected_schedule_name(self):
        """Obtiene nombre de la programación seleccionada"""
        return self.list_handler.get_selected_schedule_name() if self.list_handler else None