# profile_ui_components.py
# Ubicación: /syncro_bot/gui/components/profile_ui_components.py
"""
Componentes UI simplificados para perfiles de reportes automáticos.
Proporciona formularios y listas para gestionar perfiles que programan
el envío automático de reportes por correo sin configuraciones complejas.
"""

import tkinter as tk
from tkinter import ttk
from ..components.registry_ui_components import UITheme, StyledWidgets, CollapsibleSection


class ProfileFormHandler:
    """Maneja los formularios simplificados de perfiles de reportes"""

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

        # Nombre del perfil
        tk.Label(content, text="📝 Nombre del Perfil de Reporte:", bg=self.theme.colors['bg_primary'],
                 fg=self.theme.colors['text_primary'], font=('Arial', 10, 'bold')).pack(anchor='w', pady=(0, 5))

        self.widgets['profile_name'] = self._create_styled_entry(content)
        self.widgets['profile_name'].pack(fill='x', pady=(0, 15))

        # Estado del perfil
        status_frame = tk.Frame(content, bg=self.theme.colors['bg_tertiary'])
        status_frame.pack(fill='x')

        self.widgets['enabled_var'] = tk.BooleanVar(value=True)
        enabled_cb = tk.Checkbutton(status_frame, text="✅ Perfil Activo (Envío Automático)",
                                    variable=self.widgets['enabled_var'],
                                    bg=self.theme.colors['bg_tertiary'], fg=self.theme.colors['text_primary'],
                                    font=('Arial', 10, 'bold'),
                                    activebackground=self.theme.colors['bg_tertiary'],
                                    selectcolor=self.theme.colors['bg_tertiary'])
        enabled_cb.pack(padx=15, pady=12)

        # Información
        info_text = "💡 Los perfiles activos enviarán reportes de actividad automáticamente por correo"
        tk.Label(content, text=info_text, bg=self.theme.colors['bg_primary'],
                 fg=self.theme.colors['text_secondary'], font=('Arial', 9, 'italic')).pack(
            anchor='w', pady=(10, 0))

        return content

    def create_schedule_form(self, container):
        """Crea el formulario de programación de horarios"""
        content = tk.Frame(container, bg=self.theme.colors['bg_primary'])
        content.pack(fill='x', padx=18, pady=15)

        # Configuración de hora
        time_frame = tk.Frame(content, bg=self.theme.colors['bg_primary'])
        time_frame.pack(fill='x', pady=(0, 20))

        tk.Label(time_frame, text="⏰ Hora de Envío del Reporte:", bg=self.theme.colors['bg_primary'],
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

        # Información sobre el reporte
        info_frame = tk.Frame(content, bg=self.theme.colors['bg_secondary'])
        info_frame.pack(fill='x', pady=(15, 10))

        info_text = ("📧 Se enviará automáticamente un reporte Excel con los registros\n"
                     "de actividad de los últimos 7 días a la hora programada.")
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

        tk.Label(days_frame, text="📅 Días para Envío de Reportes:", bg=self.theme.colors['bg_primary'],
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
        """Obtiene todos los datos del formulario simplificado"""
        form_data = {
            'name': self.widgets['profile_name'].get().strip(),
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

    def load_profile_data(self, profile):
        """Carga datos de un perfil en el formulario"""
        self.clear_form()

        self.widgets['profile_name'].insert(0, profile['name'])
        self.widgets['hour_var'].set(f"{profile['hour']:02d}")
        self.widgets['minute_var'].set(f"{profile['minute']:02d}")
        self.widgets['enabled_var'].set(profile['enabled'])

        # Cargar días
        for day in profile['days']:
            if day in self.widgets['days_vars']:
                self.widgets['days_vars'][day].set(True)

    def clear_form(self):
        """Limpia todos los campos del formulario"""
        self.widgets['profile_name'].delete(0, 'end')
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


class ProfileListHandler:
    """Maneja la lista de perfiles de reportes en TreeView"""

    def __init__(self, parent, theme=None):
        self.parent = parent
        self.theme = theme or UITheme()
        self.styled_widgets = StyledWidgets(self.theme)
        self.widgets = {}
        self.selection_callbacks = []
        self.current_selection = None

    def create_profile_list(self, container):
        """Crea la lista de perfiles con TreeView simplificado"""
        # Frame para la lista
        list_frame = tk.Frame(container, bg=self.theme.colors['bg_primary'])
        list_frame.pack(fill='both', expand=True, pady=(0, 15))

        # Treeview para mostrar perfiles (simplificado - sin columna de reportes)
        columns = ('nombre', 'horario', 'dias', 'estado', 'proxima')
        self.widgets['profiles_tree'] = ttk.Treeview(list_frame, columns=columns, show='headings', height=12)

        # Configurar columnas
        self.widgets['profiles_tree'].heading('nombre', text='Nombre')
        self.widgets['profiles_tree'].heading('horario', text='Horario')
        self.widgets['profiles_tree'].heading('dias', text='Días')
        self.widgets['profiles_tree'].heading('estado', text='Estado')
        self.widgets['profiles_tree'].heading('proxima', text='Próximo Envío')

        self.widgets['profiles_tree'].column('nombre', width=100)
        self.widgets['profiles_tree'].column('horario', width=70)
        self.widgets['profiles_tree'].column('dias', width=80)
        self.widgets['profiles_tree'].column('estado', width=70)
        self.widgets['profiles_tree'].column('proxima', width=110)

        # Scrollbar para la lista
        scrollbar = ttk.Scrollbar(list_frame, orient='vertical', command=self.widgets['profiles_tree'].yview)
        self.widgets['profiles_tree'].configure(yscrollcommand=scrollbar.set)

        # Pack treeview y scrollbar
        self.widgets['profiles_tree'].pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')

        # Bind evento de selección
        self.widgets['profiles_tree'].bind('<<TreeviewSelect>>', self._on_selection_change)

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

    def populate_profiles(self, profiles):
        """Puebla la lista con perfiles de reportes"""
        # Limpiar lista actual
        for item in self.widgets['profiles_tree'].get_children():
            self.widgets['profiles_tree'].delete(item)

        # Cargar perfiles
        for profile in profiles:
            # Formatear horario
            horario = f"{profile['hour']:02d}:{profile['minute']:02d}"

            # Formatear días (mostrar solo primeros 2)
            dias = ", ".join(profile['days'][:2])
            if len(profile['days']) > 2:
                dias += f" (+{len(profile['days']) - 2})"

            # Estado
            estado = "✅ Activo" if profile['enabled'] else "❌ Inactivo"

            # Próximo envío
            proxima = self._calculate_next_execution_short(profile)

            # Insertar en la lista
            self.widgets['profiles_tree'].insert('', 'end', values=(
                profile['name'], horario, dias, estado, proxima
            ))

    def _calculate_next_execution_short(self, profile):
        """Calcula próxima ejecución en formato corto"""
        from ..components.profile_data_manager import ProfileDataHelper

        if not profile.get('enabled', False):
            return "Deshabilitado"

        try:
            next_info = ProfileDataHelper.get_next_execution_info(profile)
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

    def get_selected_profile_name(self):
        """Obtiene el nombre del perfil seleccionado"""
        selection = self.widgets['profiles_tree'].selection()
        if not selection:
            return None

        item = self.widgets['profiles_tree'].item(selection[0])
        return item['values'][0] if item['values'] else None

    def clear_selection(self):
        """Limpia la selección actual"""
        self.widgets['profiles_tree'].selection_remove(self.widgets['profiles_tree'].selection())
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
        selected_name = self.get_selected_profile_name()
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


class ProfileStatusDisplay:
    """Display de estado y estadísticas simplificadas de perfiles"""

    def __init__(self, parent, theme=None):
        self.parent = parent
        self.theme = theme or UITheme()
        self.styled_widgets = StyledWidgets(self.theme)
        self.widgets = {}

    def create_status_display(self, container):
        """Crea el display de estado simplificado"""
        # Estado de perfiles activos
        active_frame = tk.Frame(container, bg=self.theme.colors['bg_tertiary'])
        active_frame.pack(fill='x', pady=(0, 10))

        tk.Label(active_frame, text="🟢 Perfiles Activos:", bg=self.theme.colors['bg_tertiary'],
                 fg=self.theme.colors['text_primary'], font=('Arial', 10)).pack(
            side='left', padx=10, pady=8)

        self.widgets['active_count'] = tk.Label(
            active_frame, text="0", bg=self.theme.colors['bg_tertiary'],
            fg=self.theme.colors['success'], font=('Arial', 10, 'bold')
        )
        self.widgets['active_count'].pack(side='right', padx=10, pady=8)

        # Total de perfiles
        total_frame = tk.Frame(container, bg=self.theme.colors['bg_tertiary'])
        total_frame.pack(fill='x', pady=(0, 10))

        tk.Label(total_frame, text="📋 Total Perfiles:", bg=self.theme.colors['bg_tertiary'],
                 fg=self.theme.colors['text_primary'], font=('Arial', 10)).pack(
            side='left', padx=10, pady=8)

        self.widgets['total_count'] = tk.Label(
            total_frame, text="0", bg=self.theme.colors['bg_tertiary'],
            fg=self.theme.colors['text_secondary'], font=('Arial', 10, 'bold')
        )
        self.widgets['total_count'].pack(side='right', padx=10, pady=8)

        # Sistema de email
        email_frame = tk.Frame(container, bg=self.theme.colors['bg_tertiary'])
        email_frame.pack(fill='x')

        tk.Label(email_frame, text="📧 Sistema Email:", bg=self.theme.colors['bg_tertiary'],
                 fg=self.theme.colors['text_primary'], font=('Arial', 10)).pack(
            side='left', padx=10, pady=8)

        self.widgets['email_status'] = tk.Label(
            email_frame, text="Sin configurar", bg=self.theme.colors['bg_tertiary'],
            fg=self.theme.colors['warning'], font=('Arial', 10, 'bold')
        )
        self.widgets['email_status'].pack(side='right', padx=10, pady=8)

        return container

    def update_statistics(self, stats):
        """Actualiza las estadísticas mostradas (simplificadas)"""
        self.widgets['active_count'].configure(text=str(stats.get('active', 0)))
        self.widgets['total_count'].configure(text=str(stats.get('total', 0)))

    def update_email_status(self, email_tab):
        """Actualiza el estado del sistema de email"""
        if not email_tab:
            self.widgets['email_status'].configure(
                text="No disponible", fg=self.theme.colors['error']
            )
        elif email_tab.is_email_configured():
            self.widgets['email_status'].configure(
                text="✅ Configurado", fg=self.theme.colors['success']
            )
        else:
            self.widgets['email_status'].configure(
                text="❌ Sin configurar", fg=self.theme.colors['error']
            )


class ProfileActionButtons:
    """Botones de acción para perfiles simplificados"""

    def __init__(self, parent, theme=None):
        self.parent = parent
        self.theme = theme or UITheme()
        self.styled_widgets = StyledWidgets(self.theme)
        self.widgets = {}

    def create_action_buttons(self, container):
        """Crea botones de acción simplificados"""
        content = tk.Frame(container, bg=self.theme.colors['bg_primary'])
        content.pack(fill='x', padx=18, pady=15)

        # Botón guardar perfil
        self.widgets['save_button'] = self.styled_widgets.create_styled_button(
            content, "💾 Guardar Nuevo Perfil", None, self.theme.colors['success']
        )
        self.widgets['save_button'].pack(fill='x', pady=(0, 10))

        # Botón actualizar perfil
        self.widgets['update_button'] = self.styled_widgets.create_styled_button(
            content, "📝 Actualizar Perfil Seleccionado", None, self.theme.colors['info']
        )
        self.widgets['update_button'].pack(fill='x', pady=(0, 10))
        self.widgets['update_button'].configure(state='disabled')

        # Botón para probar envío de reporte
        self.widgets['test_execute_button'] = self.styled_widgets.create_styled_button(
            content, "📧 Probar Envío de Reporte", None, self.theme.colors['warning']
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
                                                  text="💾 Guardar Nuevo Perfil")


class ProfileSectionManager:
    """Gestor de secciones colapsables para perfiles simplificado"""

    def __init__(self, parent, theme=None):
        self.parent = parent
        self.theme = theme or UITheme()
        self.sections = {}
        self.expanded_section = None

    def create_collapsible_section(self, section_id, title, content_creator, row,
                                   default_expanded=False, min_height=150):
        """Crea una sección colapsable"""
        section = CollapsibleSection(self.parent, section_id, title, self.theme)
        content_frame = section.create(row=row, min_height=min_height, default_expanded=default_expanded)

        # Crear contenido usando el creator proporcionado
        content_creator(content_frame)

        # Configurar callback
        section.set_toggle_callback(self._on_section_toggle)

        # Guardar referencia
        self.sections[section_id] = section

        if default_expanded:
            self.expanded_section = section_id

        return content_frame

    def _on_section_toggle(self, section_id, is_expanded):
        """Maneja toggle de secciones (solo una expandida a la vez)"""
        if is_expanded:
            # Colapsar otras secciones
            for sid, section in self.sections.items():
                if sid != section_id and section.is_expanded():
                    section.collapse()
            self.expanded_section = section_id
        else:
            self.expanded_section = None

    def expand_section(self, section_id):
        """Expande una sección específica"""
        if section_id in self.sections:
            if not self.sections[section_id].is_expanded():
                self.sections[section_id].expand()

    def get_expanded_section(self):
        """Obtiene la sección actualmente expandida"""
        return self.expanded_section


class ProfileUICoordinator:
    """Coordinador de todos los componentes UI de perfiles simplificado"""

    def __init__(self, parent, theme=None):
        self.parent = parent
        self.theme = theme or UITheme()

        # Componentes UI
        self.form_handler = None
        self.list_handler = None
        self.status_display = None
        self.action_buttons = None
        self.section_manager = None

        # Estado
        self.current_profile = None
        self.ui_callbacks = {}

    def initialize_components(self, left_column, right_column):
        """Inicializa todos los componentes UI"""
        # Form handler
        self.form_handler = ProfileFormHandler(left_column, self.theme)

        # List handler
        self.list_handler = ProfileListHandler(right_column, self.theme)

        # Status display
        self.status_display = ProfileStatusDisplay(right_column, self.theme)

        # Action buttons
        self.action_buttons = ProfileActionButtons(left_column, self.theme)

        # Section manager
        self.section_manager = ProfileSectionManager(left_column, self.theme)

        # Configurar callbacks entre componentes
        self._setup_internal_callbacks()

    def _setup_internal_callbacks(self):
        """Configura callbacks internos entre componentes"""
        if self.list_handler:
            self.list_handler.add_selection_callback(self._on_profile_selected)

    def _on_profile_selected(self, profile_name):
        """Maneja selección de perfil en la lista"""
        has_selection = profile_name is not None

        # Actualizar botones
        if self.action_buttons:
            self.action_buttons.update_button_states(has_selection=has_selection)

        # Notificar callback externo si existe
        if 'profile_selected' in self.ui_callbacks:
            self.ui_callbacks['profile_selected'](profile_name)

    def set_callback(self, event_name, callback):
        """Establece callback para eventos UI"""
        self.ui_callbacks[event_name] = callback

    def get_form_data(self):
        """Obtiene datos del formulario"""
        return self.form_handler.get_form_data() if self.form_handler else None

    def load_profile_to_form(self, profile):
        """Carga perfil en el formulario"""
        if self.form_handler:
            self.form_handler.load_profile_data(profile)
            self.current_profile = profile

    def clear_form(self):
        """Limpia el formulario"""
        if self.form_handler:
            self.form_handler.clear_form()
        if self.action_buttons:
            self.action_buttons.update_button_states(has_selection=False)
        self.current_profile = None

    def update_profile_list(self, profiles):
        """Actualiza la lista de perfiles"""
        if self.list_handler:
            self.list_handler.populate_profiles(profiles)

    def update_statistics(self, stats):
        """Actualiza estadísticas"""
        if self.status_display:
            self.status_display.update_statistics(stats)

    def update_email_status(self, email_tab):
        """Actualiza estado del email"""
        if self.status_display:
            self.status_display.update_email_status(email_tab)

    def get_selected_profile_name(self):
        """Obtiene nombre del perfil seleccionado"""
        return self.list_handler.get_selected_profile_name() if self.list_handler else None