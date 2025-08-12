# profiles_tab.py
# Ubicación: /syncro_bot/gui/tabs/profiles_tab.py
"""
Pestaña de perfiles de automatización para Syncro Bot.
Permite programar horarios específicos para ejecutar automáticamente el bot
con integración al sistema de registro de ejecuciones y envío programado de reportes.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import threading
import json
import os
import webbrowser
from datetime import datetime, time


class ProfilesManager:
    """Gestor de perfiles de automatización programados"""

    def __init__(self):
        self.config_file = "automation_profiles.json"
        self.profiles = []
        self.load_profiles()

    def add_profile(self, name, hour, minute, days, enabled=True,
                    send_report=False, report_frequency="Después de cada ejecución",
                    report_type="Últimos 7 días"):
        """Añade un nuevo perfil de automatización con configuración de reportes"""
        profile = {
            "id": self._generate_id(),
            "name": name,
            "hour": hour,
            "minute": minute,
            "days": days,  # Lista de días: ['Lunes', 'Martes', etc.]
            "enabled": enabled,
            # ===== NUEVOS CAMPOS DE REPORTES =====
            "send_report": send_report,
            "report_frequency": report_frequency,
            "report_type": report_type,
            # ===== FIN NUEVOS CAMPOS =====
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
                    loaded_profiles = json.load(f)

                # Migrar perfiles antiguos que no tienen campos de reportes
                for profile in loaded_profiles:
                    if "send_report" not in profile:
                        profile["send_report"] = False
                        profile["report_frequency"] = "Después de cada ejecución"
                        profile["report_type"] = "Últimos 7 días"

                self.profiles = loaded_profiles
                # Guardar cambios de migración
                if any("send_report" not in p for p in loaded_profiles):
                    self.save_profiles()
            else:
                self.profiles = []
        except Exception as e:
            print(f"Error cargando perfiles: {e}")
            self.profiles = []

    def _generate_id(self):
        """Genera un ID único para el perfil"""
        return str(len(self.profiles) + 1) + str(int(datetime.now().timestamp()))


class ProfileExecutionService:
    """Servicio de ejecución de perfiles automáticos"""

    def __init__(self):
        self.target_url = "https://fieldservice.cabletica.com/dispatchFS/"
        self.is_executing = False
        self._lock = threading.Lock()

    def execute_profile(self, profile):
        """Ejecuta un perfil específico"""
        try:
            with self._lock:
                if self.is_executing:
                    return False, "Ya hay una ejecución de perfil en curso"

                self.is_executing = True

                # Simular ejecución - abrir navegador
                webbrowser.open(self.target_url)

                # Simular tiempo de procesamiento (en una implementación real aquí iría la lógica del bot)
                # Por ahora solo simulamos que tarda un poco
                time_to_simulate = 2  # segundos
                threading.Timer(time_to_simulate, self._finish_execution).start()

                return True, f"Perfil '{profile['name']}' ejecutado correctamente"

        except Exception as e:
            with self._lock:
                self.is_executing = False
            return False, f"Error ejecutando perfil: {str(e)}"

    def _finish_execution(self):
        """Finaliza la ejecución simulada"""
        with self._lock:
            self.is_executing = False

    def is_busy(self):
        """Verifica si está ejecutando un perfil"""
        with self._lock:
            return self.is_executing


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
        self.execution_service = ProfileExecutionService()
        self.widgets = {}
        self.selected_profile = None

        # ===== INTEGRACIÓN CON REGISTRO Y EMAIL =====
        self.registry_tab = None
        self.current_execution_record = None
        # ===== FIN INTEGRACIÓN =====

        # Control de secciones colapsables
        self.expanded_section = None
        self.section_frames = {}

        self.create_tab()
        self.refresh_profiles_list()

    def set_registry_tab(self, registry_tab):
        """Establece la referencia al RegistroTab para logging"""
        self.registry_tab = registry_tab

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
        parent.grid_rowconfigure(2, weight=0)  # Sección de reportes ===== NUEVA =====
        parent.grid_rowconfigure(3, weight=0)  # Sección de acciones
        parent.grid_rowconfigure(4, weight=1)  # Espaciador
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

        # ===== NUEVA SECCIÓN DE REPORTES =====
        self._create_collapsible_section(
            parent, "reports", "📧 Configuración de Reportes",
            self._create_reports_content, row=2, default_expanded=False,
            min_height=260
        )
        # ===== FIN NUEVA SECCIÓN =====

        # Sección de acciones
        self._create_collapsible_section(
            parent, "actions", "🎮 Acciones",
            self._create_actions_content, row=3, default_expanded=False,
            min_height=200
        )

        # Espaciador
        spacer = tk.Frame(parent, bg=self.colors['bg_primary'])
        spacer.grid(row=4, column=0, sticky='nsew')

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

    # ===== NUEVA SECCIÓN DE REPORTES =====
    def _create_reports_content(self, parent):
        """Crea el contenido de configuración de reportes"""
        content = tk.Frame(parent, bg=self.colors['bg_primary'])
        content.pack(fill='x', padx=18, pady=15)

        # Activar reportes
        report_enable_frame = tk.Frame(content, bg=self.colors['bg_tertiary'])
        report_enable_frame.pack(fill='x', pady=(0, 15))

        self.widgets['send_report_var'] = tk.BooleanVar(value=False)
        send_report_cb = tk.Checkbutton(report_enable_frame,
                                        text="📧 Enviar Reportes Automáticamente",
                                        variable=self.widgets['send_report_var'],
                                        command=self._toggle_report_options,
                                        bg=self.colors['bg_tertiary'],
                                        fg=self.colors['text_primary'],
                                        font=('Arial', 10, 'bold'),
                                        activebackground=self.colors['bg_tertiary'],
                                        selectcolor=self.colors['bg_tertiary'])
        send_report_cb.pack(padx=15, pady=12)

        # Opciones de reportes (inicialmente deshabilitadas)
        self.widgets['report_options_frame'] = tk.Frame(content, bg=self.colors['bg_primary'])

        # Frecuencia de reportes
        freq_frame = tk.Frame(self.widgets['report_options_frame'], bg=self.colors['bg_primary'])
        freq_frame.pack(fill='x', pady=(0, 10))

        tk.Label(freq_frame, text="📅 Frecuencia de Envío:", bg=self.colors['bg_primary'],
                 fg=self.colors['text_primary'], font=('Arial', 10, 'bold')).pack(anchor='w', pady=(0, 5))

        self.widgets['report_frequency'] = ttk.Combobox(freq_frame, values=[
            "Después de cada ejecución",
            "Diario",
            "Semanal",
            "Mensual"
        ], state="readonly", width=25)
        self.widgets['report_frequency'].set("Después de cada ejecución")
        self.widgets['report_frequency'].pack(anchor='w')

        # Tipo de reporte
        type_frame = tk.Frame(self.widgets['report_options_frame'], bg=self.colors['bg_primary'])
        type_frame.pack(fill='x')

        tk.Label(type_frame, text="📝 Tipo de Reporte:", bg=self.colors['bg_primary'],
                 fg=self.colors['text_primary'], font=('Arial', 10, 'bold')).pack(anchor='w', pady=(0, 5))

        self.widgets['report_type'] = ttk.Combobox(type_frame, values=[
            "Últimos 7 días",
            "Últimos 30 días",
            "Solo Exitosos",
            "Solo Fallidos",
            "Solo Ejecuciones del Perfil",
            "Todos los Registros"
        ], state="readonly", width=25)
        self.widgets['report_type'].set("Últimos 7 días")
        self.widgets['report_type'].pack(anchor='w')

        # Información
        info_frame = tk.Frame(self.widgets['report_options_frame'], bg=self.colors['bg_secondary'])
        info_frame.pack(fill='x', pady=(15, 0))

        info_text = ("💡 Los reportes se enviarán automáticamente según la frecuencia configurada.\n"
                     "📧 Asegúrese de tener configurado el email en la pestaña 'Email'.")
        tk.Label(info_frame, text=info_text, bg=self.colors['bg_secondary'],
                 fg=self.colors['text_secondary'], font=('Arial', 9, 'italic'),
                 justify='left').pack(padx=10, pady=8)

        # Inicialmente ocultar opciones
        self._toggle_report_options()

    # ===== FIN NUEVA SECCIÓN =====

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

        # Botón para probar ejecución de perfil (simulando ejecución automática)
        self.widgets['test_execute_button'] = self._create_styled_button(
            content, "🧪 Probar Ejecución de Perfil",
            self._test_execute_profile, self.colors['warning']
        )
        self.widgets['test_execute_button'].pack(fill='x', pady=(0, 10))
        self.widgets['test_execute_button'].configure(state='disabled')

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

        # ===== NUEVO: Estado de reportes =====
        reports_frame = tk.Frame(card, bg=self.colors['bg_tertiary'])
        reports_frame.pack(fill='x', pady=(0, 10))

        tk.Label(reports_frame, text="📧 Con Reportes:", bg=self.colors['bg_tertiary'],
                 fg=self.colors['text_primary'], font=('Arial', 10)).pack(
            side='left', padx=10, pady=8)

        self.widgets['reports_count'] = tk.Label(
            reports_frame, text="0", bg=self.colors['bg_tertiary'],
            fg=self.colors['info'], font=('Arial', 10, 'bold')
        )
        self.widgets['reports_count'].pack(side='right', padx=10, pady=8)
        # ===== FIN NUEVO =====

        # Total de perfiles
        total_frame = tk.Frame(card, bg=self.colors['bg_tertiary'])
        total_frame.pack(fill='x')

        tk.Label(total_frame, text="📋 Total Perfiles:", bg=self.colors['bg_tertiary'],
                 fg=self.colors['text_primary'], font=('Arial', 10)).pack(
            side='left', padx=10, pady=8)

        self.widgets['total_count'] = tk.Label(
            total_frame, text="0", bg=self.colors['bg_tertiary'],
            fg=self.colors['text_secondary'], font=('Arial', 10, 'bold')
        )
        self.widgets['total_count'].pack(side='right', padx=10, pady=8)

    def _create_profiles_list_section(self, parent):
        """Crea sección de lista de perfiles"""
        card = self._create_card_frame(parent, "📋 Perfiles Programados")

        # Frame para la lista
        list_frame = tk.Frame(card, bg=self.colors['bg_primary'])
        list_frame.pack(fill='both', expand=True, pady=(0, 15))

        # Treeview para mostrar perfiles (añadida columna de reportes)
        columns = ('nombre', 'horario', 'dias', 'estado', 'reportes')
        self.widgets['profiles_tree'] = ttk.Treeview(list_frame, columns=columns, show='headings', height=12)

        # Configurar columnas
        self.widgets['profiles_tree'].heading('nombre', text='Nombre')
        self.widgets['profiles_tree'].heading('horario', text='Horario')
        self.widgets['profiles_tree'].heading('dias', text='Días')
        self.widgets['profiles_tree'].heading('estado', text='Estado')
        self.widgets['profiles_tree'].heading('reportes', text='Reportes')

        self.widgets['profiles_tree'].column('nombre', width=80)
        self.widgets['profiles_tree'].column('horario', width=60)
        self.widgets['profiles_tree'].column('dias', width=70)
        self.widgets['profiles_tree'].column('estado', width=60)
        self.widgets['profiles_tree'].column('reportes', width=60)

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

    # ===== NUEVO MÉTODO PARA ALTERNAR OPCIONES DE REPORTES =====
    def _toggle_report_options(self):
        """Alterna la visibilidad de las opciones de reportes"""
        if self.widgets['send_report_var'].get():
            self.widgets['report_options_frame'].pack(fill='x', pady=(0, 15))
        else:
            self.widgets['report_options_frame'].pack_forget()

    # ===== FIN NUEVO MÉTODO =====

    def _save_profile(self):
        """Guarda un nuevo perfil"""
        if not self._validate_form():
            return

        try:
            name = self.widgets['profile_name'].get().strip()
            hour = int(self.widgets['hour_var'].get())
            minute = int(self.widgets['minute_var'].get())
            enabled = self.widgets['enabled_var'].get()

            # ===== NUEVOS CAMPOS DE REPORTES =====
            send_report = self.widgets['send_report_var'].get()
            report_frequency = self.widgets['report_frequency'].get()
            report_type = self.widgets['report_type'].get()
            # ===== FIN NUEVOS CAMPOS =====

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

            # Crear perfil con campos de reportes
            profile = self.profiles_manager.add_profile(
                name, hour, minute, selected_days, enabled,
                send_report, report_frequency, report_type
            )

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

            # ===== NUEVOS CAMPOS DE REPORTES =====
            send_report = self.widgets['send_report_var'].get()
            report_frequency = self.widgets['report_frequency'].get()
            report_type = self.widgets['report_type'].get()
            # ===== FIN NUEVOS CAMPOS =====

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

            # Actualizar perfil con campos de reportes
            updated_profile = self.profiles_manager.update_profile(
                self.selected_profile["id"],
                name=name, hour=hour, minute=minute, days=selected_days, enabled=enabled,
                send_report=send_report, report_frequency=report_frequency, report_type=report_type
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

    def _test_execute_profile(self):
        """Ejecuta un perfil seleccionado para pruebas (simula ejecución automática)"""
        if not self.selected_profile:
            messagebox.showwarning("Sin Selección", "Debe seleccionar un perfil para ejecutar")
            return

        if self.execution_service.is_busy():
            messagebox.showwarning("Ocupado", "Ya hay una ejecución de perfil en curso")
            return

        def execute_thread():
            try:
                profile = self.selected_profile
                profile_name = profile['name']

                # Registrar inicio de ejecución automática
                start_time = datetime.now()
                execution_record = None

                if self.registry_tab:
                    try:
                        execution_record = self.registry_tab.add_execution_record(
                            start_time=start_time,
                            profile_name=profile_name,
                            user_type="Sistema"  # Ejecuciones de perfiles son automáticas
                        )
                        print(f"Registro creado para perfil '{profile_name}': ID {execution_record['id']}")
                    except Exception as e:
                        print(f"Error creando registro: {str(e)}")

                # Ejecutar el perfil
                success, message = self.execution_service.execute_profile(profile)

                # Esperar a que termine la ejecución simulada
                import time
                time.sleep(2.5)

                # Actualizar registro con resultado final
                end_time = datetime.now()
                final_status = "Exitoso" if success else "Fallido"
                error_message = "" if success else message

                if self.registry_tab and execution_record:
                    try:
                        self.registry_tab.update_execution_record(
                            record_id=execution_record['id'],
                            end_time=end_time,
                            status=final_status,
                            error_message=error_message
                        )
                        print(f"Registro actualizado: {final_status}")
                    except Exception as e:
                        print(f"Error actualizando registro: {str(e)}")

                # ===== NUEVO: ENVÍO DE REPORTES AUTOMÁTICOS =====
                if success and profile.get('send_report', False):
                    try:
                        self._send_profile_report(profile, execution_record)
                    except Exception as e:
                        print(f"Error enviando reporte automático: {str(e)}")
                # ===== FIN NUEVO =====

                # Mostrar resultado en UI
                self.frame.after(0, lambda: self._show_execution_result(success, message, profile_name))

            except Exception as e:
                error_msg = str(e)
                print(f"Excepción en ejecución de perfil: {error_msg}")

                # Actualizar registro con excepción
                if self.registry_tab and execution_record:
                    try:
                        end_time = datetime.now()
                        self.registry_tab.update_execution_record(
                            record_id=execution_record['id'],
                            end_time=end_time,
                            status="Fallido",
                            error_message=f"Excepción: {error_msg}"
                        )
                    except Exception as reg_error:
                        print(f"Error actualizando registro con excepción: {str(reg_error)}")

                self.frame.after(0, lambda: self._show_execution_result(False, error_msg, profile['name']))

        # Ejecutar en hilo separado
        threading.Thread(target=execute_thread, daemon=True).start()

        # Feedback inmediato
        messagebox.showinfo("Ejecución Iniciada",
                            f"Se ha iniciado la ejecución del perfil '{self.selected_profile['name']}'.\n\n" +
                            "Revise la pestaña 'Registro' para ver el progreso.")

    def _show_execution_result(self, success, message, profile_name):
        """Muestra el resultado de la ejecución en la UI"""
        if success:
            messagebox.showinfo("Ejecución Completada",
                                f"✅ Perfil '{profile_name}' ejecutado exitosamente.\n\n{message}")
        else:
            messagebox.showerror("Error de Ejecución",
                                 f"❌ Error ejecutando perfil '{profile_name}':\n\n{message}")

    # ===== NUEVO MÉTODO PARA ENVÍO DE REPORTES =====
    def _send_profile_report(self, profile, execution_record=None):
        """Envía reporte según configuración del perfil"""
        if not self.registry_tab:
            print("Warning: No hay referencia a registry_tab para enviar reporte")
            return

        try:
            report_frequency = profile.get('report_frequency', 'Después de cada ejecución')
            report_type = profile.get('report_type', 'Últimos 7 días')

            # Por ahora solo implementamos "Después de cada ejecución"
            # Las otras frecuencias requerirían un sistema de scheduling más complejo
            if report_frequency == "Después de cada ejecución":

                # Ajustar tipo de reporte si es específico del perfil
                if report_type == "Solo Ejecuciones del Perfil":
                    # Esto requeriría filtrar por nombre de perfil, pero por simplicidad
                    # usaremos "Últimos 7 días" como fallback
                    report_type_to_send = "Últimos 7 días"
                else:
                    report_type_to_send = report_type

                # Generar título personalizado
                custom_title = f"Reporte Automático - Perfil '{profile['name']}'"

                # Enviar reporte
                success, message = self.registry_tab.generate_and_send_report(
                    report_type=report_type_to_send,
                    custom_title=custom_title
                )

                if success:
                    print(f"Reporte enviado exitosamente para perfil '{profile['name']}'")
                else:
                    print(f"Error enviando reporte para perfil '{profile['name']}': {message}")

            else:
                print(f"Frecuencia '{report_frequency}' no implementada aún")

        except Exception as e:
            print(f"Excepción enviando reporte automático: {str(e)}")

    # ===== FIN NUEVO MÉTODO =====

    def _clear_form(self):
        """Limpia el formulario"""
        self.widgets['profile_name'].delete(0, 'end')
        self.widgets['hour_var'].set("08")
        self.widgets['minute_var'].set("00")
        self.widgets['enabled_var'].set(True)

        # ===== LIMPIAR CAMPOS DE REPORTES =====
        self.widgets['send_report_var'].set(False)
        self.widgets['report_frequency'].set("Después de cada ejecución")
        self.widgets['report_type'].set("Últimos 7 días")
        self._toggle_report_options()  # Ocultar opciones
        # ===== FIN LIMPIAR CAMPOS =====

        # Limpiar días
        for var in self.widgets['days_vars'].values():
            var.set(False)

        # Resetear estado de botones
        self.selected_profile = None
        self.widgets['update_button'].configure(state='disabled')
        self.widgets['delete_button'].configure(state='disabled')
        self.widgets['test_execute_button'].configure(state='disabled')
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
            self.widgets['test_execute_button'].configure(state='disabled')
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
        self.widgets['test_execute_button'].configure(state='normal')
        self.widgets['save_button'].configure(state='disabled')
        self.widgets['save_button'].configure(text="⚠️ Seleccione 'Actualizar' para modificar")

    def _load_profile_to_form(self, profile):
        """Carga un perfil en el formulario"""
        # Limpiar formulario primero
        self._clear_form()

        # Cargar datos básicos
        self.widgets['profile_name'].insert(0, profile['name'])
        self.widgets['hour_var'].set(f"{profile['hour']:02d}")
        self.widgets['minute_var'].set(f"{profile['minute']:02d}")
        self.widgets['enabled_var'].set(profile['enabled'])

        # ===== CARGAR CAMPOS DE REPORTES =====
        self.widgets['send_report_var'].set(profile.get('send_report', False))
        self.widgets['report_frequency'].set(profile.get('report_frequency', 'Después de cada ejecución'))
        self.widgets['report_type'].set(profile.get('report_type', 'Últimos 7 días'))
        self._toggle_report_options()  # Mostrar/ocultar según configuración
        # ===== FIN CARGAR CAMPOS =====

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
        reports_count = 0  # ===== NUEVO CONTADOR =====

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

            # ===== COLUMNA DE REPORTES =====
            reportes = "📧 Sí" if profile.get('send_report', False) else "❌ No"
            if profile.get('send_report', False):
                reports_count += 1
            # ===== FIN COLUMNA DE REPORTES =====

            # Insertar en la lista (con nueva columna)
            self.widgets['profiles_tree'].insert('', 'end', values=(
                profile['name'], horario, dias, estado, reportes
            ))

        # Actualizar contadores
        self.widgets['active_count'].configure(text=str(active_count))
        self.widgets['reports_count'].configure(text=str(reports_count))  # ===== NUEVO =====
        self.widgets['total_count'].configure(text=str(len(profiles)))

    def get_active_profiles(self):
        """Obtiene los perfiles activos"""
        profiles = self.profiles_manager.get_profiles()
        return [p for p in profiles if p['enabled']]

    def execute_profile_automatically(self, profile):
        """
        Método público para ejecutar un perfil automáticamente (llamado por scheduler).
        Este sería usado por un sistema de scheduling futuro.
        """

        def execute_async():
            try:
                profile_name = profile['name']

                # Registrar inicio
                start_time = datetime.now()
                execution_record = None

                if self.registry_tab:
                    execution_record = self.registry_tab.add_execution_record(
                        start_time=start_time,
                        profile_name=profile_name,
                        user_type="Sistema"
                    )

                # Ejecutar
                success, message = self.execution_service.execute_profile(profile)

                # Esperar finalización
                import time
                time.sleep(2.5)

                # Actualizar registro
                if self.registry_tab and execution_record:
                    end_time = datetime.now()
                    final_status = "Exitoso" if success else "Fallido"
                    error_message = "" if success else message

                    self.registry_tab.update_execution_record(
                        record_id=execution_record['id'],
                        end_time=end_time,
                        status=final_status,
                        error_message=error_message
                    )

                # ===== ENVÍO AUTOMÁTICO DE REPORTES =====
                if success and profile.get('send_report', False):
                    try:
                        self._send_profile_report(profile, execution_record)
                    except Exception as e:
                        print(f"Error enviando reporte automático: {str(e)}")
                # ===== FIN ENVÍO AUTOMÁTICO =====

                return success, message

            except Exception as e:
                # Manejar excepción
                if self.registry_tab and execution_record:
                    end_time = datetime.now()
                    self.registry_tab.update_execution_record(
                        record_id=execution_record['id'],
                        end_time=end_time,
                        status="Fallido",
                        error_message=f"Excepción: {str(e)}"
                    )
                return False, str(e)

        # Ejecutar de forma asíncrona
        thread = threading.Thread(target=execute_async, daemon=True)
        thread.start()