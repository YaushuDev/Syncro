# automation_ui_components.py
# Ubicación: /syncro_bot/gui/components/automation/automation_ui_components.py
"""
Componentes UI reutilizables para el sistema de automatización.
Proporciona widgets especializados, secciones colapsables, formularios
de credenciales, configuración de fechas y elementos estilizados para la interfaz de automatización.
"""

import tkinter as tk
from tkinter import ttk, scrolledtext
import re
from datetime import datetime


class AutomationTheme:
    """Tema de colores específico para automatización"""

    def __init__(self):
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


class CollapsibleSection:
    """Componente de sección colapsable tipo acordeón para automatización"""

    def __init__(self, parent, section_id, title, theme=None):
        self.parent = parent
        self.section_id = section_id
        self.title = title
        self.theme = theme or AutomationTheme()
        self.expanded = False
        self.min_height = 150

        # Referencias a elementos
        self.container = None
        self.header = None
        self.content_frame = None
        self.arrow_label = None
        self.on_toggle_callback = None

    def create(self, row, min_height=150, default_expanded=False):
        """Crea la sección colapsable"""
        self.min_height = min_height

        # Contenedor principal
        self.container = tk.Frame(self.parent, bg=self.theme.colors['bg_primary'])
        self.container.configure(height=55)
        self.container.grid(row=row, column=0, sticky='ew', pady=(0, 10))
        self.container.grid_columnconfigure(0, weight=1)
        self.container.grid_propagate(False)

        # Frame de la tarjeta
        card = tk.Frame(self.container, bg=self.theme.colors['bg_primary'],
                        relief='solid', bd=1)
        card.configure(highlightbackground=self.theme.colors['border'],
                       highlightcolor=self.theme.colors['border'],
                       highlightthickness=1)
        card.grid(row=0, column=0, sticky='ew')
        card.grid_columnconfigure(0, weight=1)

        # Header clickeable
        self.header = tk.Frame(card, bg=self.theme.colors['bg_secondary'],
                               height=45, cursor='hand2')
        self.header.grid(row=0, column=0, sticky='ew')
        self.header.grid_propagate(False)
        self.header.grid_columnconfigure(0, weight=1)

        # Contenido del header
        header_content = tk.Frame(self.header, bg=self.theme.colors['bg_secondary'])
        header_content.grid(row=0, column=0, sticky='ew', padx=15, pady=12)
        header_content.grid_columnconfigure(0, weight=1)

        # Título
        title_label = tk.Label(header_content, text=self.title,
                               bg=self.theme.colors['bg_secondary'],
                               fg=self.theme.colors['text_primary'],
                               font=('Arial', 12, 'bold'), cursor='hand2')
        title_label.grid(row=0, column=0, sticky='w')

        # Flecha indicadora
        self.arrow_label = tk.Label(header_content, text="▶",
                                    bg=self.theme.colors['bg_secondary'],
                                    fg=self.theme.colors['accent'],
                                    font=('Arial', 10, 'bold'), cursor='hand2')
        self.arrow_label.grid(row=0, column=1, sticky='e')

        # Content area
        self.content_frame = tk.Frame(card, bg=self.theme.colors['bg_primary'])
        self.content_frame.grid_columnconfigure(0, weight=1)

        # Estado inicial
        if default_expanded:
            self.content_frame.grid(row=1, column=0, sticky='ew')
            self.arrow_label.configure(text="▼")
            self.expanded = True
            self.container.configure(height=min_height)
            self.container.grid_propagate(True)

        # Bind eventos
        def toggle_section(event=None):
            self.toggle()

        self.header.bind("<Button-1>", toggle_section)
        title_label.bind("<Button-1>", toggle_section)
        self.arrow_label.bind("<Button-1>", toggle_section)

        return self.content_frame

    def toggle(self):
        """Alterna la visibilidad de la sección"""
        if self.expanded:
            self.content_frame.grid_remove()
            self.arrow_label.configure(text="▶")
            self.expanded = False
            self.container.configure(height=55)
            self.container.grid_propagate(False)
        else:
            self.content_frame.grid(row=1, column=0, sticky='ew')
            self.arrow_label.configure(text="▼")
            self.expanded = True
            self.container.configure(height=self.min_height)
            self.container.grid_propagate(True)

        if self.on_toggle_callback:
            self.on_toggle_callback(self.section_id, self.expanded)

    def set_toggle_callback(self, callback):
        """Establece callback para eventos de toggle"""
        self.on_toggle_callback = callback

    def is_expanded(self):
        """Verifica si la sección está expandida"""
        return self.expanded

    def expand(self):
        """Fuerza expansión de la sección"""
        if not self.expanded:
            self.toggle()

    def collapse(self):
        """Fuerza colapso de la sección"""
        if self.expanded:
            self.toggle()


class CredentialsForm:
    """Formulario de credenciales con funcionalidades avanzadas"""

    def __init__(self, parent, theme=None):
        self.parent = parent
        self.theme = theme or AutomationTheme()
        self.widgets = {}

    def create(self):
        """Crea el formulario completo de credenciales"""
        content = tk.Frame(self.parent, bg=self.theme.colors['bg_primary'])
        content.pack(fill='x', padx=18, pady=15)

        # Campo de usuario
        self._create_username_field(content)

        # Campo de contraseña
        self._create_password_field(content)

        # Botones de acción
        self._create_action_buttons(content)

        # Estado de Selenium
        self._create_selenium_status(content)

        return self.widgets

    def _create_username_field(self, parent):
        """Crea el campo de usuario"""
        tk.Label(parent, text="👤 Usuario:", bg=self.theme.colors['bg_primary'],
                 fg=self.theme.colors['text_primary'], font=('Arial', 10, 'bold')).pack(anchor='w', pady=(0, 5))

        self.widgets['username_entry'] = self._create_styled_entry(parent)
        self.widgets['username_entry'].pack(fill='x', pady=(0, 15))

    def _create_password_field(self, parent):
        """Crea el campo de contraseña con toggle de visibilidad"""
        tk.Label(parent, text="🔒 Contraseña:", bg=self.theme.colors['bg_primary'],
                 fg=self.theme.colors['text_primary'], font=('Arial', 10, 'bold')).pack(anchor='w', pady=(0, 5))

        password_frame = tk.Frame(parent, bg=self.theme.colors['bg_primary'])
        password_frame.pack(fill='x', pady=(0, 15))

        self.widgets['password_entry'] = self._create_styled_entry(password_frame, show='*')
        self.widgets['password_entry'].pack(side='left', fill='x', expand=True)

        # Botón mostrar contraseña
        self.widgets['show_password_var'] = tk.BooleanVar()
        show_btn = tk.Checkbutton(
            password_frame, text="👁️", variable=self.widgets['show_password_var'],
            command=self._toggle_password_visibility,
            bg=self.theme.colors['bg_primary'], fg=self.theme.colors['text_secondary'],
            font=('Arial', 10), padx=10
        )
        show_btn.pack(side='right')

    def _create_action_buttons(self, parent):
        """Crea los botones de acción"""
        buttons_frame = tk.Frame(parent, bg=self.theme.colors['bg_primary'])
        buttons_frame.pack(fill='x')

        buttons_frame.grid_columnconfigure(0, weight=1)
        buttons_frame.grid_columnconfigure(1, weight=1)
        buttons_frame.grid_columnconfigure(2, weight=1)

        # Botón probar credenciales
        self.widgets['test_credentials_button'] = self._create_styled_button(
            buttons_frame, "🔍 Probar", None, self.theme.colors['info']
        )
        self.widgets['test_credentials_button'].grid(row=0, column=0, sticky='ew', padx=(0, 5))

        # Botón guardar credenciales
        self.widgets['save_credentials_button'] = self._create_styled_button(
            buttons_frame, "💾 Guardar", None, self.theme.colors['success']
        )
        self.widgets['save_credentials_button'].grid(row=0, column=1, sticky='ew', padx=2.5)

        # Botón limpiar credenciales
        self.widgets['clear_credentials_button'] = self._create_styled_button(
            buttons_frame, "🗑️ Limpiar", None, self.theme.colors['error']
        )
        self.widgets['clear_credentials_button'].grid(row=0, column=2, sticky='ew', padx=(5, 0))

    def _create_selenium_status(self, parent):
        """Crea indicador de estado de Selenium"""
        selenium_status_frame = tk.Frame(parent, bg=self.theme.colors['bg_secondary'])
        selenium_status_frame.pack(fill='x', pady=(15, 0))

        # Importar aquí para evitar dependencias circulares
        try:
            import selenium
            selenium_available = True
        except ImportError:
            selenium_available = False

        selenium_text = "🤖 Selenium:" if selenium_available else "⚠️ Selenium:"
        tk.Label(selenium_status_frame, text=selenium_text, bg=self.theme.colors['bg_secondary'],
                 fg=self.theme.colors['text_primary'], font=('Arial', 9)).pack(side='left', padx=10, pady=8)

        selenium_status = "✅ Disponible (Login automático)" if selenium_available else "❌ No disponible (Solo navegador)"
        selenium_color = self.theme.colors['success'] if selenium_available else self.theme.colors['warning']

        self.widgets['selenium_status_label'] = tk.Label(
            selenium_status_frame, text=selenium_status, bg=self.theme.colors['bg_secondary'],
            fg=selenium_color, font=('Arial', 9, 'bold')
        )
        self.widgets['selenium_status_label'].pack(side='right', padx=10, pady=8)

    def _create_styled_entry(self, parent, **kwargs):
        """Crea un Entry con estilo consistente"""
        entry = tk.Entry(
            parent,
            bg=self.theme.colors['bg_tertiary'],
            fg=self.theme.colors['text_primary'],
            font=('Arial', 10),
            relief='flat',
            bd=10,
            **kwargs
        )
        return entry

    def _create_styled_button(self, parent, text, command, color):
        """Crea un botón con estilo consistente"""
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

    def _toggle_password_visibility(self):
        """Alterna visibilidad de contraseña"""
        if self.widgets['show_password_var'].get():
            self.widgets['password_entry'].configure(show='')
        else:
            self.widgets['password_entry'].configure(show='*')

    def get_credentials(self):
        """Obtiene las credenciales del formulario"""
        username = self.widgets['username_entry'].get().strip()
        password = self.widgets['password_entry'].get().strip()
        return username, password

    def set_credentials(self, username, password):
        """Establece credenciales en el formulario"""
        self.widgets['username_entry'].delete(0, 'end')
        self.widgets['username_entry'].insert(0, username)
        self.widgets['password_entry'].delete(0, 'end')
        self.widgets['password_entry'].insert(0, password)

    def clear_credentials(self):
        """Limpia los campos de credenciales"""
        self.widgets['username_entry'].delete(0, 'end')
        self.widgets['password_entry'].delete(0, 'end')

    def set_button_command(self, button_name, command):
        """Establece comando para un botón específico"""
        if button_name in self.widgets:
            self.widgets[button_name].configure(command=command)


class DateConfigForm:
    """Formulario de configuración de fechas para automatización"""

    def __init__(self, parent, theme=None):
        self.parent = parent
        self.theme = theme or AutomationTheme()
        self.widgets = {}
        self.date_pattern = re.compile(r'^(\d{2})/(\d{2})/(\d{4})$')

    def create(self):
        """Crea el formulario completo de configuración de fechas"""
        content = tk.Frame(self.parent, bg=self.theme.colors['bg_primary'])
        content.pack(fill='x', padx=18, pady=15)

        # Checkbox para omitir configuración de fecha
        self._create_skip_checkbox(content)

        # Campos de fecha
        self._create_date_fields(content)

        # Botones de acción
        self._create_action_buttons(content)

        # Estado inicial
        self._update_fields_state()

        return self.widgets

    def _create_skip_checkbox(self, parent):
        """Crea checkbox para omitir configuración de fecha"""
        checkbox_frame = tk.Frame(parent, bg=self.theme.colors['bg_tertiary'])
        checkbox_frame.pack(fill='x', pady=(0, 15))

        self.widgets['skip_date_var'] = tk.BooleanVar(value=True)  # Marcado por defecto
        skip_checkbox = tk.Checkbutton(
            checkbox_frame,
            text="📅 No tocar fechas (mantener comportamiento actual)",
            variable=self.widgets['skip_date_var'],
            command=self._on_skip_change,
            bg=self.theme.colors['bg_tertiary'],
            fg=self.theme.colors['text_primary'],
            font=('Arial', 10, 'bold'),
            padx=15, pady=10
        )
        skip_checkbox.pack(anchor='w')

    def _create_date_fields(self, parent):
        """Crea los campos de fecha Desde y Hasta"""
        dates_frame = tk.Frame(parent, bg=self.theme.colors['bg_primary'])
        dates_frame.pack(fill='x', pady=(0, 15))

        # Instrucciones
        instructions_label = tk.Label(
            dates_frame,
            text="📋 Formato: DD/MM/YYYY (ejemplo: 10/08/2025)",
            bg=self.theme.colors['bg_primary'],
            fg=self.theme.colors['text_secondary'],
            font=('Arial', 9)
        )
        instructions_label.pack(anchor='w', pady=(0, 10))

        # Frame para los campos
        fields_frame = tk.Frame(dates_frame, bg=self.theme.colors['bg_tertiary'])
        fields_frame.pack(fill='x')

        fields_inner = tk.Frame(fields_frame, bg=self.theme.colors['bg_tertiary'])
        fields_inner.pack(padx=15, pady=15)

        # Campo Desde
        tk.Label(
            fields_inner,
            text="📅 Fecha Desde:",
            bg=self.theme.colors['bg_tertiary'],
            fg=self.theme.colors['text_primary'],
            font=('Arial', 10, 'bold')
        ).grid(row=0, column=0, sticky='w', pady=(0, 8))

        self.widgets['date_from_entry'] = self._create_styled_entry(fields_inner)
        self.widgets['date_from_entry'].grid(row=0, column=1, sticky='ew', padx=(10, 0), pady=(0, 8))

        # Placeholder en el campo Desde
        self.widgets['date_from_entry'].insert(0, "DD/MM/YYYY")
        self.widgets['date_from_entry'].bind('<FocusIn>', lambda e: self._on_entry_focus_in(e, 'date_from_entry'))
        self.widgets['date_from_entry'].bind('<FocusOut>', lambda e: self._on_entry_focus_out(e, 'date_from_entry'))
        self.widgets['date_from_entry'].bind('<KeyRelease>', lambda e: self._validate_date_format(e, 'date_from_entry'))

        # Campo Hasta
        tk.Label(
            fields_inner,
            text="📅 Fecha Hasta:",
            bg=self.theme.colors['bg_tertiary'],
            fg=self.theme.colors['text_primary'],
            font=('Arial', 10, 'bold')
        ).grid(row=1, column=0, sticky='w')

        self.widgets['date_to_entry'] = self._create_styled_entry(fields_inner)
        self.widgets['date_to_entry'].grid(row=1, column=1, sticky='ew', padx=(10, 0))

        # Placeholder en el campo Hasta
        self.widgets['date_to_entry'].insert(0, "DD/MM/YYYY")
        self.widgets['date_to_entry'].bind('<FocusIn>', lambda e: self._on_entry_focus_in(e, 'date_to_entry'))
        self.widgets['date_to_entry'].bind('<FocusOut>', lambda e: self._on_entry_focus_out(e, 'date_to_entry'))
        self.widgets['date_to_entry'].bind('<KeyRelease>', lambda e: self._validate_date_format(e, 'date_to_entry'))

        fields_inner.grid_columnconfigure(1, weight=1)

        # Labels de validación
        self.widgets['date_from_validation'] = tk.Label(
            fields_inner,
            text="",
            bg=self.theme.colors['bg_tertiary'],
            font=('Arial', 8)
        )
        self.widgets['date_from_validation'].grid(row=0, column=2, padx=(5, 0), pady=(0, 8))

        self.widgets['date_to_validation'] = tk.Label(
            fields_inner,
            text="",
            bg=self.theme.colors['bg_tertiary'],
            font=('Arial', 8)
        )
        self.widgets['date_to_validation'].grid(row=1, column=2, padx=(5, 0))

    def _create_action_buttons(self, parent):
        """Crea botones de acción"""
        buttons_frame = tk.Frame(parent, bg=self.theme.colors['bg_primary'])
        buttons_frame.pack(fill='x')

        buttons_frame.grid_columnconfigure(0, weight=1)
        buttons_frame.grid_columnconfigure(1, weight=1)

        # Botón establecer fecha actual
        self.widgets['set_today_button'] = self._create_styled_button(
            buttons_frame, "📅 Establecer Hoy", None, self.theme.colors['info']
        )
        self.widgets['set_today_button'].grid(row=0, column=0, sticky='ew', padx=(0, 5))

        # Botón limpiar fechas
        self.widgets['clear_dates_button'] = self._create_styled_button(
            buttons_frame, "🗑️ Limpiar Fechas", None, self.theme.colors['warning']
        )
        self.widgets['clear_dates_button'].grid(row=0, column=1, sticky='ew', padx=(5, 0))

    def _create_styled_entry(self, parent, **kwargs):
        """Crea un Entry con estilo consistente"""
        entry = tk.Entry(
            parent,
            bg=self.theme.colors['bg_tertiary'],
            fg=self.theme.colors['text_primary'],
            font=('Arial', 10),
            relief='flat',
            bd=8,
            **kwargs
        )
        return entry

    def _create_styled_button(self, parent, text, command, color):
        """Crea un botón con estilo consistente"""
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

    def _on_skip_change(self):
        """Maneja cambio en checkbox de omitir fecha"""
        self._update_fields_state()

    def _update_fields_state(self):
        """Actualiza estado de los campos según checkbox"""
        skip_enabled = self.widgets['skip_date_var'].get()
        state = 'disabled' if skip_enabled else 'normal'

        # Deshabilitar/habilitar campos
        for widget_name in ['date_from_entry', 'date_to_entry', 'set_today_button', 'clear_dates_button']:
            if widget_name in self.widgets:
                self.widgets[widget_name].configure(state=state)

    def _on_entry_focus_in(self, event, entry_name):
        """Maneja focus in en campos de fecha"""
        entry = self.widgets[entry_name]
        if entry.get() == "DD/MM/YYYY":
            entry.delete(0, 'end')
            entry.configure(fg=self.theme.colors['text_primary'])

    def _on_entry_focus_out(self, event, entry_name):
        """Maneja focus out en campos de fecha"""
        entry = self.widgets[entry_name]
        if not entry.get().strip():
            entry.insert(0, "DD/MM/YYYY")
            entry.configure(fg=self.theme.colors['text_secondary'])

    def _validate_date_format(self, event, entry_name):
        """Valida formato de fecha en tiempo real"""
        entry = self.widgets[entry_name]
        validation_label = self.widgets[f"{entry_name.replace('_entry', '_validation')}"]

        date_text = entry.get().strip()

        # Ignorar placeholder
        if date_text == "DD/MM/YYYY" or not date_text:
            validation_label.configure(text="", fg=self.theme.colors['text_secondary'])
            return

        # Validar formato
        if self._is_valid_date_format(date_text):
            validation_label.configure(text="✅", fg=self.theme.colors['success'])
        else:
            validation_label.configure(text="❌", fg=self.theme.colors['error'])

    def _is_valid_date_format(self, date_text):
        """Verifica si el formato de fecha es válido"""
        if not self.date_pattern.match(date_text):
            return False

        try:
            day, month, year = map(int, date_text.split('/'))
            # Verificar rangos básicos
            if not (1 <= day <= 31 and 1 <= month <= 12 and 1900 <= year <= 2100):
                return False

            # Intentar crear fecha para validación completa
            datetime(year, month, day)
            return True
        except ValueError:
            return False

    def get_date_config(self):
        """Obtiene configuración actual de fechas"""
        skip_dates = self.widgets['skip_date_var'].get()

        if skip_dates:
            return {
                'skip_dates': True,
                'date_from': None,
                'date_to': None
            }

        date_from = self.widgets['date_from_entry'].get().strip()
        date_to = self.widgets['date_to_entry'].get().strip()

        # Limpiar placeholders
        if date_from == "DD/MM/YYYY":
            date_from = ""
        if date_to == "DD/MM/YYYY":
            date_to = ""

        return {
            'skip_dates': False,
            'date_from': date_from if date_from else None,
            'date_to': date_to if date_to else None
        }

    def set_date_config(self, config):
        """Establece configuración de fechas"""
        skip_dates = config.get('skip_dates', True)
        self.widgets['skip_date_var'].set(skip_dates)

        if not skip_dates:
            date_from = config.get('date_from', '')
            date_to = config.get('date_to', '')

            # Limpiar y establecer fecha desde
            self.widgets['date_from_entry'].delete(0, 'end')
            if date_from:
                self.widgets['date_from_entry'].insert(0, date_from)
                self.widgets['date_from_entry'].configure(fg=self.theme.colors['text_primary'])
            else:
                self.widgets['date_from_entry'].insert(0, "DD/MM/YYYY")
                self.widgets['date_from_entry'].configure(fg=self.theme.colors['text_secondary'])

            # Limpiar y establecer fecha hasta
            self.widgets['date_to_entry'].delete(0, 'end')
            if date_to:
                self.widgets['date_to_entry'].insert(0, date_to)
                self.widgets['date_to_entry'].configure(fg=self.theme.colors['text_primary'])
            else:
                self.widgets['date_to_entry'].insert(0, "DD/MM/YYYY")
                self.widgets['date_to_entry'].configure(fg=self.theme.colors['text_secondary'])

        self._update_fields_state()

    def clear_dates(self):
        """Limpia los campos de fecha"""
        for entry_name in ['date_from_entry', 'date_to_entry']:
            entry = self.widgets[entry_name]
            entry.delete(0, 'end')
            entry.insert(0, "DD/MM/YYYY")
            entry.configure(fg=self.theme.colors['text_secondary'])

            # Limpiar validación
            validation_name = entry_name.replace('_entry', '_validation')
            if validation_name in self.widgets:
                self.widgets[validation_name].configure(text="")

    def set_today_dates(self):
        """Establece fechas actuales en ambos campos"""
        today = datetime.now().strftime("%d/%m/%Y")

        for entry_name in ['date_from_entry', 'date_to_entry']:
            entry = self.widgets[entry_name]
            entry.delete(0, 'end')
            entry.insert(0, today)
            entry.configure(fg=self.theme.colors['text_primary'])

            # Actualizar validación
            validation_name = entry_name.replace('_entry', '_validation')
            if validation_name in self.widgets:
                self.widgets[validation_name].configure(text="✅", fg=self.theme.colors['success'])

    def validate_date_range(self):
        """Valida que el rango de fechas sea correcto"""
        config = self.get_date_config()

        if config['skip_dates']:
            return True, "Fechas omitidas"

        date_from = config['date_from']
        date_to = config['date_to']

        # Si ambas están vacías, está bien
        if not date_from and not date_to:
            return True, "Sin fechas especificadas"

        # Si solo una está llena, también está bien
        if not date_from or not date_to:
            return True, "Una fecha especificada"

        # Validar formato
        if not self._is_valid_date_format(date_from):
            return False, f"Formato de fecha 'Desde' inválido: {date_from}"

        if not self._is_valid_date_format(date_to):
            return False, f"Formato de fecha 'Hasta' inválido: {date_to}"

        # Validar rango
        try:
            from_parts = date_from.split('/')
            to_parts = date_to.split('/')

            from_date = datetime(int(from_parts[2]), int(from_parts[1]), int(from_parts[0]))
            to_date = datetime(int(to_parts[2]), int(to_parts[1]), int(to_parts[0]))

            if from_date > to_date:
                return False, "La fecha 'Desde' no puede ser posterior a 'Hasta'"

            return True, "Rango de fechas válido"
        except Exception as e:
            return False, f"Error validando rango: {str(e)}"

    def set_button_command(self, button_name, command):
        """Establece comando para un botón específico"""
        if button_name in self.widgets:
            self.widgets[button_name].configure(command=command)


class StatusPanel:
    """Panel de estado del sistema de automatización"""

    def __init__(self, parent, theme=None):
        self.parent = parent
        self.theme = theme or AutomationTheme()
        self.widgets = {}

    def create(self):
        """Crea el panel de estado"""
        content = tk.Frame(self.parent, bg=self.theme.colors['bg_primary'])
        content.pack(fill='x', padx=18, pady=15)

        # Estado de automatización
        self._create_automation_status(content)

        # URL objetivo
        self._create_url_status(content)

        return self.widgets

    def _create_automation_status(self, parent):
        """Crea indicador de estado de automatización"""
        status_frame = tk.Frame(parent, bg=self.theme.colors['bg_tertiary'])
        status_frame.pack(fill='x', pady=(0, 10))

        tk.Label(status_frame, text="🤖 Automatización:", bg=self.theme.colors['bg_tertiary'],
                 fg=self.theme.colors['text_primary'], font=('Arial', 10)).pack(
            side='left', padx=10, pady=8)

        self.widgets['automation_status'] = tk.Label(
            status_frame, text="Detenida", bg=self.theme.colors['bg_tertiary'],
            fg=self.theme.colors['text_secondary'], font=('Arial', 10, 'bold')
        )
        self.widgets['automation_status'].pack(side='right', padx=10, pady=8)

    def _create_url_status(self, parent):
        """Crea indicador de URL objetivo"""
        url_frame = tk.Frame(parent, bg=self.theme.colors['bg_tertiary'])
        url_frame.pack(fill='x')

        tk.Label(url_frame, text="🌐 URL Objetivo:", bg=self.theme.colors['bg_tertiary'],
                 fg=self.theme.colors['text_primary'], font=('Arial', 10)).pack(
            side='left', padx=10, pady=8)

        self.widgets['url_status'] = tk.Label(
            url_frame, text="Cabletica Dispatch", bg=self.theme.colors['bg_tertiary'],
            fg=self.theme.colors['info'], font=('Arial', 10, 'bold')
        )
        self.widgets['url_status'].pack(side='right', padx=10, pady=8)

    def update_automation_status(self, text, color=None):
        """Actualiza el estado de automatización"""
        if color is None:
            color = self.theme.colors['text_secondary']
        self.widgets['automation_status'].configure(text=text, fg=color)

    def update_url_status(self, text):
        """Actualiza el estado de URL"""
        self.widgets['url_status'].configure(text=text)


class ControlPanel:
    """Panel de controles de automatización"""

    def __init__(self, parent, theme=None):
        self.parent = parent
        self.theme = theme or AutomationTheme()
        self.widgets = {}

    def create(self):
        """Crea el panel de controles"""
        content = tk.Frame(self.parent, bg=self.theme.colors['bg_primary'])
        content.pack(fill='x', padx=18, pady=15)

        # Botón iniciar
        self.widgets['start_button'] = self._create_styled_button(
            content, "▶️ Iniciar Automatización con Login",
            None, self.theme.colors['success']
        )
        self.widgets['start_button'].pack(fill='x', pady=(0, 15))

        # Botón pausar
        self.widgets['pause_button'] = self._create_styled_button(
            content, "⏸️ Pausar Automatización",
            None, self.theme.colors['warning']
        )
        self.widgets['pause_button'].pack(fill='x')
        self.widgets['pause_button'].configure(state='disabled')

        return self.widgets

    def _create_styled_button(self, parent, text, command, color):
        """Crea un botón con estilo consistente"""
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

    def set_button_command(self, button_name, command):
        """Establece comando para un botón específico"""
        if button_name in self.widgets:
            self.widgets[button_name].configure(command=command)

    def set_button_state(self, button_name, state):
        """Establece estado de un botón"""
        if button_name in self.widgets:
            self.widgets[button_name].configure(state=state)

    def set_button_text(self, button_name, text):
        """Establece texto de un botón"""
        if button_name in self.widgets:
            self.widgets[button_name].configure(text=text)


class LogPanel:
    """Panel de log con funcionalidades avanzadas"""

    def __init__(self, parent, theme=None):
        self.parent = parent
        self.theme = theme or AutomationTheme()
        self.widgets = {}

    def create(self):
        """Crea el panel de log"""
        # Crear card frame
        card = self._create_card_frame(self.parent, "📋 Log de Actividades")

        # Área de texto con scroll
        self.widgets['log_text'] = scrolledtext.ScrolledText(
            card,
            bg=self.theme.colors['bg_tertiary'],
            fg=self.theme.colors['text_primary'],
            font=('Consolas', 9),
            relief='flat',
            wrap=tk.WORD,
            state=tk.DISABLED
        )
        self.widgets['log_text'].pack(fill='both', expand=True, pady=(0, 10))

        # Botón para limpiar log
        self.widgets['clear_log_button'] = self._create_styled_button(
            card, "🗑️ Limpiar Log", None, self.theme.colors['text_secondary']
        )
        self.widgets['clear_log_button'].pack(fill='x')

        return self.widgets

    def _create_card_frame(self, parent, title):
        """Crea un frame tipo tarjeta"""
        container = tk.Frame(parent, bg=self.theme.colors['bg_primary'])
        container.pack(fill='both', expand=True)

        card = tk.Frame(container, bg=self.theme.colors['bg_primary'], relief='solid', bd=1)
        card.configure(highlightbackground=self.theme.colors['border'],
                       highlightcolor=self.theme.colors['border'],
                       highlightthickness=1)
        card.pack(fill='both', expand=True)

        # Header
        header = tk.Frame(card, bg=self.theme.colors['bg_secondary'], height=45)
        header.pack(fill='x')
        header.pack_propagate(False)

        tk.Label(header, text=title, bg=self.theme.colors['bg_secondary'],
                 fg=self.theme.colors['text_primary'], font=('Arial', 12, 'bold')).pack(
            side='left', padx=15, pady=12)

        # Content area
        content = tk.Frame(card, bg=self.theme.colors['bg_primary'])
        content.pack(fill='both', expand=True, padx=18, pady=15)

        return content

    def _create_styled_button(self, parent, text, command, color):
        """Crea un botón con estilo consistente"""
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

    def set_clear_command(self, command):
        """Establece comando para limpiar log"""
        self.widgets['clear_log_button'].configure(command=command)


class AutomationUIFactory:
    """Factory para crear componentes UI de automatización"""

    @staticmethod
    def create_collapsible_section(parent, section_id, title, theme=None):
        """Crea una sección colapsable"""
        return CollapsibleSection(parent, section_id, title, theme)

    @staticmethod
    def create_credentials_form(parent, theme=None):
        """Crea un formulario de credenciales"""
        return CredentialsForm(parent, theme)

    @staticmethod
    def create_date_config_form(parent, theme=None):
        """Crea un formulario de configuración de fechas"""
        return DateConfigForm(parent, theme)

    @staticmethod
    def create_status_panel(parent, theme=None):
        """Crea un panel de estado"""
        return StatusPanel(parent, theme)

    @staticmethod
    def create_control_panel(parent, theme=None):
        """Crea un panel de controles"""
        return ControlPanel(parent, theme)

    @staticmethod
    def create_log_panel(parent, theme=None):
        """Crea un panel de log"""
        return LogPanel(parent, theme)