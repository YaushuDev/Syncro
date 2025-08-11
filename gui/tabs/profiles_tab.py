# profiles_tab.py
# Ubicación: /syncro_bot/gui/tabs/profiles_tab.py
"""
Pestaña de perfiles de automatización para Syncro Bot.
Permite programar horarios específicos para ejecutar automáticamente el bot.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import threading
import json
import os
from datetime import datetime, time


class ProfilesManager:
    """Gestor de perfiles de automatización programados"""

    def __init__(self):
        self.config_file = "automation_profiles.json"
        self.profiles = []
        self.load_profiles()

    def add_profile(self, name, hour, minute, days, enabled=True):
        """Añade un nuevo perfil de automatización"""
        profile = {
            "id": self._generate_id(),
            "name": name,
            "hour": hour,
            "minute": minute,
            "days": days,  # Lista de días: ['Lunes', 'Martes', etc.]
            "enabled": enabled,
            "created": datetime.now().isoformat()
        }
        self.profiles.append(profile)
        self.save_profiles()
        return profile

    def remove_profile(self, profile_id):
        """Elimina un perfil por ID"""
        self.profiles = [p for p in self.profiles if p["id"] != profile_id]
        self.save_profiles()

    def update_profile(self, profile_id, **kwargs):
        """Actualiza un perfil existente"""
        for profile in self.profiles:
            if profile["id"] == profile_id:
                profile.update(kwargs)
                self.save_profiles()
                return profile
        return None

    def get_profiles(self):
        """Obtiene todos los perfiles"""
        return self.profiles.copy()

    def save_profiles(self):
        """Guarda los perfiles en archivo"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.profiles, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"Error guardando perfiles: {e}")
            return False

    def load_profiles(self):
        """Carga los perfiles desde archivo"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    self.profiles = json.load(f)
            else:
                self.profiles = []
        except Exception as e:
            print(f"Error cargando perfiles: {e}")
            self.profiles = []

    def _generate_id(self):
        """Genera un ID único para el perfil"""
        return str(len(self.profiles) + 1) + str(int(datetime.now().timestamp()))


class ProfilesTab:
    """Pestaña de perfiles de automatización para Syncro Bot"""

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

        self.profiles_manager = ProfilesManager()
        self.widgets = {}
        self.selected_profile = None

        # Control de secciones colapsables
        self.expanded_section = None
        self.section_frames = {}

        self.create_tab()
        self.refresh_profiles_list()

    def create_tab(self):
        """Crear la pestaña de perfiles"""
        self.frame = ttk.Frame(self.parent)
        self.parent.add(self.frame, text="Perfiles Automatización")
        self.create_interface()

    def create_interface(self):
        """Crea la interfaz con diseño de 2 columnas"""
        # Container principal
        main_container = tk.Frame(self.frame, bg=self.colors['bg_primary'])
        main_container.pack(fill='both', expand=True, padx=15, pady=10)

        # Configurar grid para 2 columnas con separador
        main_container.grid_columnconfigure(0, weight=0, minsize=500)  # Columna izquierda
        main_container.grid_columnconfigure(1, weight=0, minsize=1)  # Separador
        main_container.grid_columnconfigure(2, weight=1, minsize=350)  # Columna derecha
        main_container.grid_rowconfigure(0, weight=1)

        # Columna izquierda - Configuración
        left_column = tk.Frame(main_container, bg=self.colors['bg_primary'], width=500)
        left_column.grid(row=0, column=0, sticky='ns', padx=(0, 5))
        left_column.grid_propagate(False)

        # Separador visual
        separator = tk.Frame(main_container, bg=self.colors['border'], width=1)
        separator.grid(row=0, column=1, sticky='ns', padx=5)

        # Columna derecha - Estado y Lista
        right_column = tk.Frame(main_container, bg=self.colors['bg_primary'])
        right_column.grid(row=0, column=2, sticky='nsew', padx=(5, 0))

        # Crear contenido
        self._create_left_column_collapsible(left_column)
        self._create_right_column(right_column)

    def _create_left_column_collapsible(self, parent):
        """Crea la columna izquierda con secciones colapsables"""
        parent.grid_rowconfigure(0, weight=0)  # Sección de configuración
        parent.grid_rowconfigure(1, weight=0)  # Sección de horarios
        parent.grid_rowconfigure(2, weight=0)  # Sección de acciones
        parent.grid_rowconfigure(3, weight=1)  # Espaciador
        parent.grid_columnconfigure(0, weight=1)

        # Sección de configuración básica
        self._create_collapsible_section(
            parent, "basic_config", "⚙️ Configuración Básica",
            self._create_basic_config_content, row=0, default_expanded=True,
            min_height=180
        )

        # Sección de horarios y días
        self._create_collapsible_section(
            parent, "schedule", "⏰ Programación de Horarios",
            self._create_schedule_content, row=1, default_expanded=False,
            min_height=220
        )

        # Sección de acciones
        self._create_collapsible_section(
            parent, "actions", "🎮 Acciones",
            self._create_actions_content, row=2, default_expanded=False,
            min_height=160
        )

        # Espaciador
        spacer = tk.Frame(parent, bg=self.colors['bg_primary'])
        spacer.grid(row=3, column=0, sticky='nsew')

    def _create_right_column(self, parent):
        """Crea el contenido de la columna derecha"""
        parent.grid_rowconfigure(0, weight=0)  # Estado
        parent.grid_rowconfigure(1, weight=1)  # Lista de perfiles
        parent.grid_columnconfigure(0, weight=1)

        # Sección de estado
        status_container = tk.Frame(parent, bg=self.colors['bg_primary'])
        status_container.grid(row=0, column=0, sticky='ew', pady=(0, 15))
        self._create_status_section(status_container)

        # Sección de lista de perfiles
        profiles_container = tk.Frame(parent, bg=self.colors['bg_primary'])
        profiles_container.grid(row=1, column=0, sticky='nsew')
        self._create_profiles_list_section(profiles_container)

    def _create_collapsible_section(self, parent, section_id, title, content_creator,
                                    row, default_expanded=False, min_height=150):
        """Crea una sección colapsable tipo acordeón"""
        # Container principal
        section_container = tk.Frame(parent, bg=self.colors['bg_primary'])
        section_container.configure(height=55)  # Solo header cuando está colapsada
        section_container.grid(row=row, column=0, sticky='ew', pady=(0, 10))
        section_container.grid_columnconfigure(0, weight=1)
        section_container.grid_propagate(False)

        # Frame de la tarjeta
        card = tk.Frame(section_container, bg=self.colors['bg_primary'],
                        relief='solid', bd=1)
        card.configure(highlightbackground=self.colors['border'],
                       highlightcolor=self.colors['border'],
                       highlightthickness=1)
        card.grid(row=0, column=0, sticky='ew')
        card.grid_columnconfigure(0, weight=1)

        # Header clickeable
        header = tk.Frame(card, bg=self.colors['bg_secondary'], height=45, cursor='hand2')
        header.grid(row=0, column=0, sticky='ew')
        header.grid_propagate(False)
        header.grid_columnconfigure(0, weight=1)

        # Contenido del header
        header_content = tk.Frame(header, bg=self.colors['bg_secondary'])
        header_content.grid(row=0, column=0, sticky='ew', padx=15, pady=12)
        header_content.grid_columnconfigure(0, weight=1)

        # Título
        title_label = tk.Label(header_content, text=title, bg=self.colors['bg_secondary'],
                               fg=self.colors['text_primary'], font=('Arial', 12, 'bold'),
                               cursor='hand2')
        title_label.grid(row=0, column=0, sticky='w')

        # Flecha indicadora
        arrow_label = tk.Label(header_content, text="▶",
                               bg=self.colors['bg_secondary'], fg=self.colors['accent'],
                               font=('Arial', 10, 'bold'), cursor='hand2')
        arrow_label.grid(row=0, column=1, sticky='e')

        # Content area
        content_frame = tk.Frame(card, bg=self.colors['bg_primary'])
        content_frame.grid_columnconfigure(0, weight=1)

        # Crear contenido específico
        content_creator(content_frame)

        # Guardar referencias
        self.section_frames[section_id] = {
            'container': section_container,
            'header': header,
            'content': content_frame,
            'arrow': arrow_label,
            'expanded': False,
            'min_height': min_height
        }

        # Bind eventos
        def toggle_section(event=None):
            self._toggle_section(section_id)

        header.bind("<Button-1>", toggle_section)
        title_label.bind("<Button-1>", toggle_section)
        arrow_label.bind("<Button-1>", toggle_section)

        # Expandir por defecto si se especifica
        if default_expanded:
            self._toggle_section(section_id)

    def _toggle_section(self, section_id):
        """Alterna la visibilidad de una sección"""
        current_section = self.section_frames[section_id]

        if current_section['expanded']:
            # Colapsar sección actual
            current_section['content'].grid_remove()
            current_section['arrow'].configure(text="▶")
            current_section['expanded'] = False
            current_section['container'].configure(height=55)
            current_section['container'].grid_propagate(False)
            self.expanded_section = None
        else:
            # Colapsar otra sección si está expandida
            if self.expanded_section and self.expanded_section in self.section_frames:
                expanded_section = self.section_frames[self.expanded_section]
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
            self.expanded_section = section_id

        self.frame.update_idletasks()

    def _create_basic_config_content(self, parent):
        """Crea el contenido de configuración básica"""
        content = tk.Frame(parent, bg=self.colors['bg_primary'])
        content.pack(fill='x', padx=18, pady=15)

        # Nombre del perfil
        tk.Label(content, text="📝 Nombre del Perfil:", bg=self.colors['bg_primary'],
                 fg=self.colors['text_primary'], font=('Arial', 10, 'bold')).pack(anchor='w', pady=(0, 5))

        self.widgets['profile_name'] = self._create_styled_entry(content)
        self.widgets['profile_name'].pack(fill='x', pady=(0, 15))

        # Estado del perfil
        status_frame = tk.Frame(content, bg=self.colors['bg_tertiary'])
        status_frame.pack(fill='x')

        self.widgets['enabled_var'] = tk.BooleanVar(value=True)
        enabled_cb = tk.Checkbutton(status_frame, text="✅ Perfil Activo al Guardar",
                                    variable=self.widgets['enabled_var'],
                                    bg=self.colors['bg_tertiary'], fg=self.colors['text_primary'],
                                    font=('Arial', 10, 'bold'),
                                    activebackground=self.colors['bg_tertiary'],
                                    selectcolor=self.colors['bg_tertiary'])
        enabled_cb.pack(padx=15, pady=12)

        # Información
        info_text = "💡 Los perfiles activos se ejecutarán automáticamente en los horarios programados"
        tk.Label(content, text=info_text, bg=self.colors['bg_primary'],
                 fg=self.colors['text_secondary'], font=('Arial', 9, 'italic')).pack(
            anchor='w', pady=(10, 0))

    def _create_schedule_content(self, parent):
        """Crea el contenido de programación de horarios"""
        content = tk.Frame(parent, bg=self.colors['bg_primary'])
        content.pack(fill='x', padx=18, pady=15)

        # Configuración de hora
        time_frame = tk.Frame(content, bg=self.colors['bg_primary'])
        time_frame.pack(fill='x', pady=(0, 20))

        tk.Label(time_frame, text="⏰ Hora de Ejecución:", bg=self.colors['bg_primary'],
                 fg=self.colors['text_primary'], font=('Arial', 10, 'bold')).pack(anchor='w', pady=(0, 8))

        time_inputs = tk.Frame(time_frame, bg=self.colors['bg_tertiary'])
        time_inputs.pack(fill='x', pady=5)

        time_inner = tk.Frame(time_inputs, bg=self.colors['bg_tertiary'])
        time_inner.pack(padx=15, pady=12)

        # Hora
        tk.Label(time_inner, text="Hora:", bg=self.colors['bg_tertiary'],
                 fg=self.colors['text_primary'], font=('Arial', 10)).grid(row=0, column=0, sticky='w', padx=(0, 10))

        self.widgets['hour_var'] = tk.StringVar(value="08")
        hour_spinbox = tk.Spinbox(time_inner, from_=0, to=23, format="%02.0f",
                                  textvariable=self.widgets['hour_var'], width=5,
                                  bg=self.colors['bg_tertiary'], fg=self.colors['text_primary'],
                                  font=('Arial', 10, 'bold'), relief='flat', bd=5)
        hour_spinbox.grid(row=0, column=1, sticky='w', padx=(0, 30))

        # Minutos
        tk.Label(time_inner, text="Minutos:", bg=self.colors['bg_tertiary'],
                 fg=self.colors['text_primary'], font=('Arial', 10)).grid(row=0, column=2, sticky='w', padx=(0, 10))

        self.widgets['minute_var'] = tk.StringVar(value="00")
        minute_spinbox = tk.Spinbox(time_inner, from_=0, to=59, format="%02.0f",
                                    textvariable=self.widgets['minute_var'], width=5,
                                    bg=self.colors['bg_tertiary'], fg=self.colors['text_primary'],
                                    font=('Arial', 10, 'bold'), relief='flat', bd=5)
        minute_spinbox.grid(row=0, column=3, sticky='w')

        # Días de la semana
        days_frame = tk.Frame(content, bg=self.colors['bg_primary'])
        days_frame.pack(fill='x')

        tk.Label(days_frame, text="📅 Días de Ejecución:", bg=self.colors['bg_primary'],
                 fg=self.colors['text_primary'], font=('Arial', 10, 'bold')).pack(anchor='w', pady=(0, 8))

        days_container = tk.Frame(days_frame, bg=self.colors['bg_tertiary'])
        days_container.pack(fill='x', pady=5)

        days_grid = tk.Frame(days_container, bg=self.colors['bg_tertiary'])
        days_grid.pack(padx=15, pady=12)

        self.widgets['days_vars'] = {}
        days = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo']

        for i, day in enumerate(days):
            var = tk.BooleanVar()
            self.widgets['days_vars'][day] = var

            cb = tk.Checkbutton(days_grid, text=day, variable=var,
                                bg=self.colors['bg_tertiary'], fg=self.colors['text_primary'],
                                font=('Arial', 9), activebackground=self.colors['bg_tertiary'],
                                selectcolor=self.colors['bg_tertiary'])

            row = i // 2
            col = i % 2
            cb.grid(row=row, column=col, sticky='w', padx=(0, 25), pady=3)

        days_grid.grid_columnconfigure(0, weight=1)
        days_grid.grid_columnconfigure(1, weight=1)

    def _create_actions_content(self, parent):
        """Crea el contenido de acciones"""
        content = tk.Frame(parent, bg=self.colors['bg_primary'])
        content.pack(fill='x', padx=18, pady=15)

        # Botón guardar perfil
        self.widgets['save_button'] = self._create_styled_button(
            content, "💾 Guardar Nuevo Perfil",
            self._save_profile, self.colors['success']
        )
        self.widgets['save_button'].pack(fill='x', pady=(0, 10))

        # Botón actualizar perfil
        self.widgets['update_button'] = self._create_styled_button(
            content, "📝 Actualizar Perfil Seleccionado",
            self._update_profile, self.colors['info']
        )
        self.widgets['update_button'].pack(fill='x', pady=(0, 10))
        self.widgets['update_button'].configure(state='disabled')

        # Botón limpiar formulario
        self.widgets['clear_button'] = self._create_styled_button(
            content, "🗑️ Limpiar Formulario",
            self._clear_form, self.colors['text_secondary']
        )
        self.widgets['clear_button'].pack(fill='x')

    def _create_card_frame(self, parent, title):
        """Crea un frame tipo tarjeta"""
        container = tk.Frame(parent, bg=self.colors['bg_primary'])
        container.pack(fill='both', expand=True)

        # Card frame
        card = tk.Frame(container, bg=self.colors['bg_primary'], relief='solid', bd=1)
        card.configure(highlightbackground=self.colors['border'],
                       highlightcolor=self.colors['border'],
                       highlightthickness=1)
        card.pack(fill='both', expand=True)

        # Header
        header = tk.Frame(card, bg=self.colors['bg_secondary'], height=45)
        header.pack(fill='x')
        header.pack_propagate(False)

        # Título
        tk.Label(header, text=title, bg=self.colors['bg_secondary'],
                 fg=self.colors['text_primary'], font=('Arial', 12, 'bold')).pack(
            side='left', padx=15, pady=12)

        # Content area
        content = tk.Frame(card, bg=self.colors['bg_primary'])
        content.pack(fill='both', expand=True, padx=18, pady=15)

        return content

    def _create_status_section(self, parent):
        """Crea sección de estado"""
        card = self._create_card_frame(parent, "📊 Estado del Sistema")

        # Estado de perfiles activos
        active_frame = tk.Frame(card, bg=self.colors['bg_tertiary'])
        active_frame.pack(fill='x', pady=(0, 10))

        tk.Label(active_frame, text="🟢 Perfiles Activos:", bg=self.colors['bg_tertiary'],
                 fg=self.colors['text_primary'], font=('Arial', 10)).pack(
            side='left', padx=10, pady=8)

        self.widgets['active_count'] = tk.Label(
            active_frame, text="0", bg=self.colors['bg_tertiary'],
            fg=self.colors['success'], font=('Arial', 10, 'bold')
        )
        self.widgets['active_count'].pack(side='right', padx=10, pady=8)

        # Total de perfiles
        total_frame = tk.Frame(card, bg=self.colors['bg_tertiary'])
        total_frame.pack(fill='x')

        tk.Label(total_frame, text="📋 Total Perfiles:", bg=self.colors['bg_tertiary'],
                 fg=self.colors['text_primary'], font=('Arial', 10)).pack(
            side='left', padx=10, pady=8)

        self.widgets['total_count'] = tk.Label(
            total_frame, text="0", bg=self.colors['bg_tertiary'],
            fg=self.colors['info'], font=('Arial', 10, 'bold')
        )
        self.widgets['total_count'].pack(side='right', padx=10, pady=8)

    def _create_profiles_list_section(self, parent):
        """Crea sección de lista de perfiles"""
        card = self._create_card_frame(parent, "📋 Perfiles Programados")

        # Frame para la lista
        list_frame = tk.Frame(card, bg=self.colors['bg_primary'])
        list_frame.pack(fill='both', expand=True, pady=(0, 15))

        # Treeview para mostrar perfiles
        columns = ('nombre', 'horario', 'dias', 'estado')
        self.widgets['profiles_tree'] = ttk.Treeview(list_frame, columns=columns, show='headings', height=12)

        # Configurar columnas
        self.widgets['profiles_tree'].heading('nombre', text='Nombre')
        self.widgets['profiles_tree'].heading('horario', text='Horario')
        self.widgets['profiles_tree'].heading('dias', text='Días')
        self.widgets['profiles_tree'].heading('estado', text='Estado')

        self.widgets['profiles_tree'].column('nombre', width=100)
        self.widgets['profiles_tree'].column('horario', width=70)
        self.widgets['profiles_tree'].column('dias', width=90)
        self.widgets['profiles_tree'].column('estado', width=70)

        # Scrollbar para la lista
        scrollbar = ttk.Scrollbar(list_frame, orient='vertical', command=self.widgets['profiles_tree'].yview)
        self.widgets['profiles_tree'].configure(yscrollcommand=scrollbar.set)

        # Pack treeview y scrollbar
        self.widgets['profiles_tree'].pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')

        # Bind evento de selección
        self.widgets['profiles_tree'].bind('<<TreeviewSelect>>', self._on_profile_select)

        # Botones de gestión de lista
        list_buttons = tk.Frame(card, bg=self.colors['bg_primary'])
        list_buttons.pack(fill='x')

        list_buttons.grid_columnconfigure(0, weight=1)
        list_buttons.grid_columnconfigure(1, weight=1)

        # Botón eliminar
        self.widgets['delete_button'] = self._create_styled_button(
            list_buttons, "🗑️ Eliminar",
            self._delete_profile, self.colors['error']
        )
        self.widgets['delete_button'].grid(row=0, column=0, sticky='ew', padx=(0, 5))
        self.widgets['delete_button'].configure(state='disabled')

        # Botón refrescar
        refresh_button = self._create_styled_button(
            list_buttons, "🔄 Refrescar",
            self.refresh_profiles_list, self.colors['info']
        )
        refresh_button.grid(row=0, column=1, sticky='ew', padx=(5, 0))

    def _create_styled_entry(self, parent, **kwargs):
        """Crea un Entry con estilo"""
        entry = tk.Entry(
            parent,
            bg=self.colors['bg_tertiary'],
            fg=self.colors['text_primary'],
            font=('Arial', 10),
            relief='flat',
            bd=10,
            **kwargs
        )
        return entry

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
            pady=10,
            cursor='hand2'
        )
        return btn

    def _save_profile(self):
        """Guarda un nuevo perfil"""
        if not self._validate_form():
            return

        try:
            name = self.widgets['profile_name'].get().strip()
            hour = int(self.widgets['hour_var'].get())
            minute = int(self.widgets['minute_var'].get())
            enabled = self.widgets['enabled_var'].get()

            # Obtener días seleccionados
            selected_days = []
            for day, var in self.widgets['days_vars'].items():
                if var.get():
                    selected_days.append(day)

            if not selected_days:
                messagebox.showerror("Error", "Debe seleccionar al menos un día")
                if self.expanded_section != "schedule":
                    self._toggle_section("schedule")
                return

            # Crear perfil
            profile = self.profiles_manager.add_profile(name, hour, minute, selected_days, enabled)

            messagebox.showinfo("Éxito", f"Perfil '{name}' guardado correctamente")
            self._clear_form()
            self.refresh_profiles_list()

        except Exception as e:
            messagebox.showerror("Error", f"Error al guardar perfil:\n{str(e)}")

    def _update_profile(self):
        """Actualiza el perfil seleccionado"""
        if not self.selected_profile or not self._validate_form():
            return

        try:
            name = self.widgets['profile_name'].get().strip()
            hour = int(self.widgets['hour_var'].get())
            minute = int(self.widgets['minute_var'].get())
            enabled = self.widgets['enabled_var'].get()

            # Obtener días seleccionados
            selected_days = []
            for day, var in self.widgets['days_vars'].items():
                if var.get():
                    selected_days.append(day)

            if not selected_days:
                messagebox.showerror("Error", "Debe seleccionar al menos un día")
                if self.expanded_section != "schedule":
                    self._toggle_section("schedule")
                return

            # Actualizar perfil
            updated_profile = self.profiles_manager.update_profile(
                self.selected_profile["id"],
                name=name, hour=hour, minute=minute, days=selected_days, enabled=enabled
            )

            if updated_profile:
                messagebox.showinfo("Éxito", f"Perfil '{name}' actualizado correctamente")
                self._clear_form()
                self.refresh_profiles_list()
            else:
                messagebox.showerror("Error", "No se pudo actualizar el perfil")

        except Exception as e:
            messagebox.showerror("Error", f"Error al actualizar perfil:\n{str(e)}")

    def _delete_profile(self):
        """Elimina el perfil seleccionado"""
        if not self.selected_profile:
            return

        if messagebox.askyesno("Confirmar",
                               f"¿Está seguro de eliminar el perfil '{self.selected_profile['name']}'?"):
            try:
                self.profiles_manager.remove_profile(self.selected_profile["id"])
                messagebox.showinfo("Éxito", "Perfil eliminado correctamente")
                self._clear_form()
                self.refresh_profiles_list()
            except Exception as e:
                messagebox.showerror("Error", f"Error al eliminar perfil:\n{str(e)}")

    def _clear_form(self):
        """Limpia el formulario"""
        self.widgets['profile_name'].delete(0, 'end')
        self.widgets['hour_var'].set("08")
        self.widgets['minute_var'].set("00")
        self.widgets['enabled_var'].set(True)

        # Limpiar días
        for var in self.widgets['days_vars'].values():
            var.set(False)

        # Resetear estado de botones
        self.selected_profile = None
        self.widgets['update_button'].configure(state='disabled')
        self.widgets['delete_button'].configure(state='disabled')
        self.widgets['save_button'].configure(state='normal')
        self.widgets['save_button'].configure(text="💾 Guardar Nuevo Perfil")

    def _validate_form(self):
        """Valida el formulario"""
        name = self.widgets['profile_name'].get().strip()

        if not name:
            messagebox.showerror("Error", "El nombre del perfil es obligatorio")
            if self.expanded_section != "basic_config":
                self._toggle_section("basic_config")
            self.widgets['profile_name'].focus()
            return False

        if len(name) < 3:
            messagebox.showerror("Error", "El nombre debe tener al menos 3 caracteres")
            if self.expanded_section != "basic_config":
                self._toggle_section("basic_config")
            self.widgets['profile_name'].focus()
            return False

        return True

    def _on_profile_select(self, event):
        """Maneja la selección de un perfil en la lista"""
        selection = self.widgets['profiles_tree'].selection()
        if not selection:
            self.selected_profile = None
            self.widgets['update_button'].configure(state='disabled')
            self.widgets['delete_button'].configure(state='disabled')
            self.widgets['save_button'].configure(text="💾 Guardar Nuevo Perfil")
            return

        # Obtener el perfil seleccionado
        item = self.widgets['profiles_tree'].item(selection[0])
        profile_name = item['values'][0]

        # Buscar el perfil completo
        profiles = self.profiles_manager.get_profiles()
        for profile in profiles:
            if profile['name'] == profile_name:
                self.selected_profile = profile
                self._load_profile_to_form(profile)
                break

        # Habilitar botones
        self.widgets['update_button'].configure(state='normal')
        self.widgets['delete_button'].configure(state='normal')
        self.widgets['save_button'].configure(state='disabled')
        self.widgets['save_button'].configure(text="⚠️ Seleccione 'Actualizar' para modificar")

    def _load_profile_to_form(self, profile):
        """Carga un perfil en el formulario"""
        # Limpiar formulario primero
        self._clear_form()

        # Cargar datos
        self.widgets['profile_name'].insert(0, profile['name'])
        self.widgets['hour_var'].set(f"{profile['hour']:02d}")
        self.widgets['minute_var'].set(f"{profile['minute']:02d}")
        self.widgets['enabled_var'].set(profile['enabled'])

        # Cargar días
        for day in profile['days']:
            if day in self.widgets['days_vars']:
                self.widgets['days_vars'][day].set(True)

    def refresh_profiles_list(self):
        """Refresca la lista de perfiles"""
        # Limpiar lista actual
        for item in self.widgets['profiles_tree'].get_children():
            self.widgets['profiles_tree'].delete(item)

        # Cargar perfiles
        profiles = self.profiles_manager.get_profiles()
        active_count = 0

        for profile in profiles:
            # Formatear horario
            horario = f"{profile['hour']:02d}:{profile['minute']:02d}"

            # Formatear días (mostrar solo primeros 2)
            dias = ", ".join(profile['days'][:2])
            if len(profile['days']) > 2:
                dias += f" (+{len(profile['days']) - 2})"

            # Estado
            estado = "✅ Activo" if profile['enabled'] else "❌ Inactivo"
            if profile['enabled']:
                active_count += 1

            # Insertar en la lista
            self.widgets['profiles_tree'].insert('', 'end', values=(
                profile['name'], horario, dias, estado
            ))

        # Actualizar contadores
        self.widgets['active_count'].configure(text=str(active_count))
        self.widgets['total_count'].configure(text=str(len(profiles)))

    def get_active_profiles(self):
        """Obtiene los perfiles activos"""
        profiles = self.profiles_manager.get_profiles()
        return [p for p in profiles if p['enabled']]