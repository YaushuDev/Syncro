# registry_ui_components.py
# Ubicación: /syncro_bot/gui/components/registry_ui_components.py
"""
Componentes UI simplificados para el sistema de registro.
Proporciona widgets estilizados y componentes básicos reutilizables
para toda la aplicación con espaciado mejorado.
"""

import tkinter as tk
from tkinter import ttk, scrolledtext


class UITheme:
    """Tema de colores y estilos consistentes"""
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


class StyledWidgets:
    """Widgets estilizados reutilizables con mejor espaciado"""
    def __init__(self, theme=None):
        self.theme = theme or UITheme()

    def create_styled_entry(self, parent, width=None, **kwargs):
        """Crea un Entry con estilo consistente"""
        config = {
            'bg': self.theme.colors['bg_tertiary'],
            'fg': self.theme.colors['text_primary'],
            'font': ('Arial', 9),
            'relief': 'flat',
            'bd': 5
        }
        config.update(kwargs)
        entry = tk.Entry(parent, **config)
        if width:
            entry.configure(width=width)
        return entry

    def create_styled_button(self, parent, text, command, color=None, size='normal'):
        """Crea un botón con estilo consistente y mejor espaciado"""
        if color is None:
            color = self.theme.colors['accent']
        font_size = 9 if size == 'normal' else 10

        return tk.Button(
            parent, text=text, command=command, bg=color, fg='white',
            font=('Arial', font_size, 'bold'), relief='flat',
            padx=20, pady=12, cursor='hand2'  # Aumentado padding interno
        )

    def create_styled_label(self, parent, text, style='normal', **kwargs):
        """Crea un Label con estilo consistente"""
        styles = {
            'normal': {'font': ('Arial', 9), 'fg': self.theme.colors['text_primary']},
            'bold': {'font': ('Arial', 9, 'bold'), 'fg': self.theme.colors['text_primary']},
            'title': {'font': ('Arial', 12, 'bold'), 'fg': self.theme.colors['text_primary']},
            'secondary': {'font': ('Arial', 9), 'fg': self.theme.colors['text_secondary']},
        }

        style_config = styles.get(style, styles['normal'])
        config = {'bg': self.theme.colors['bg_primary'], **style_config}
        config.update(kwargs)
        return tk.Label(parent, text=text, **config)

    def create_styled_combobox(self, parent, values, default_value=None, width=None, **kwargs):
        """Crea un Combobox con estilo consistente"""
        combo = ttk.Combobox(parent, values=values, state="readonly", **kwargs)
        if width:
            combo.configure(width=width)
        if default_value and default_value in values:
            combo.set(default_value)
        return combo

    def create_styled_text(self, parent, height=4, width=None, **kwargs):
        """Crea un Text widget con scroll estilizado"""
        text_widget = scrolledtext.ScrolledText(
            parent, height=height,
            bg=self.theme.colors['bg_tertiary'],
            fg=self.theme.colors['text_primary'],
            font=('Arial', 9), relief='flat', wrap=tk.WORD, **kwargs
        )
        if width:
            text_widget.configure(width=width)
        return text_widget


class CardFrame:
    """Componente de marco tipo tarjeta con mejor espaciado"""
    def __init__(self, parent, title, theme=None):
        self.theme = theme or UITheme()
        self.parent = parent
        self.title = title

    def create(self):
        """Crea el marco tipo tarjeta con espaciado mejorado"""
        container = tk.Frame(self.parent, bg=self.theme.colors['bg_primary'])
        container.pack(fill='both', expand=True)

        card = tk.Frame(container, bg=self.theme.colors['bg_primary'], relief='solid', bd=1)
        card.configure(
            highlightbackground=self.theme.colors['border'],
            highlightcolor=self.theme.colors['border'],
            highlightthickness=1
        )
        card.pack(fill='both', expand=True)

        # Header
        header = tk.Frame(card, bg=self.theme.colors['bg_secondary'], height=45)
        header.pack(fill='x')
        header.pack_propagate(False)

        tk.Label(
            header, text=self.title, bg=self.theme.colors['bg_secondary'],
            fg=self.theme.colors['text_primary'], font=('Arial', 12, 'bold')
        ).pack(side='left', padx=15, pady=12)

        # Content area con padding inferior aumentado
        content_frame = tk.Frame(card, bg=self.theme.colors['bg_primary'])
        content_frame.pack(fill='both', expand=True, padx=18, pady=(15, 20))  # Aumentado padding inferior
        return content_frame


class StatBox:
    """Componente de caja de estadística simplificado"""
    def __init__(self, parent, label_text, theme=None):
        self.theme = theme or UITheme()
        self.parent = parent
        self.label_text = label_text
        self.value_label = None

    def create(self, initial_value="0", side='left'):
        """Crea la caja de estadística"""
        frame = tk.Frame(self.parent, bg=self.theme.colors['bg_tertiary'])
        frame.pack(side=side, fill='x', expand=True, padx=(0, 4) if side == 'left' else (4, 0))

        tk.Label(
            frame, text=self.label_text, bg=self.theme.colors['bg_tertiary'],
            fg=self.theme.colors['text_primary'], font=('Arial', 9)
        ).pack(side='left', padx=8, pady=6)

        self.value_label = tk.Label(
            frame, text=initial_value, bg=self.theme.colors['bg_tertiary'],
            fg=self.theme.colors['info'], font=('Arial', 9, 'bold')
        )
        self.value_label.pack(side='right', padx=8, pady=6)
        return self.value_label

    def update_value(self, new_value, color=None):
        """Actualiza el valor mostrado"""
        if self.value_label:
            self.value_label.configure(text=str(new_value))
            if color:
                self.value_label.configure(fg=color)


class CollapsibleSection:
    """Componente de sección colapsable con mejor espaciado"""
    def __init__(self, parent, section_id, title, theme=None):
        self.theme = theme or UITheme()
        self.parent = parent
        self.section_id = section_id
        self.title = title
        self.expanded = False
        self.min_height = 150
        self.container = None
        self.content_frame = None
        self.arrow_label = None
        self.on_toggle_callback = None

    def create(self, row, min_height=150, default_expanded=False):
        """Crea la sección colapsable con espaciado mejorado"""
        self.min_height = min_height

        self.container = tk.Frame(self.parent, bg=self.theme.colors['bg_primary'])
        self.container.configure(height=55)
        self.container.grid(row=row, column=0, sticky='ew', pady=(0, 10))
        self.container.grid_columnconfigure(0, weight=1)
        self.container.grid_propagate(False)

        card = tk.Frame(
            self.container, bg=self.theme.colors['bg_primary'], relief='solid', bd=1
        )
        card.configure(
            highlightbackground=self.theme.colors['border'],
            highlightcolor=self.theme.colors['border'],
            highlightthickness=1
        )
        card.grid(row=0, column=0, sticky='ew')
        card.grid_columnconfigure(0, weight=1)

        # Header clickeable
        header = tk.Frame(card, bg=self.theme.colors['bg_secondary'], height=45, cursor='hand2')
        header.grid(row=0, column=0, sticky='ew')
        header.grid_propagate(False)
        header.grid_columnconfigure(0, weight=1)

        header_content = tk.Frame(header, bg=self.theme.colors['bg_secondary'])
        header_content.grid(row=0, column=0, sticky='ew', padx=15, pady=12)
        header_content.grid_columnconfigure(0, weight=1)

        title_label = tk.Label(
            header_content, text=self.title, bg=self.theme.colors['bg_secondary'],
            fg=self.theme.colors['text_primary'], font=('Arial', 12, 'bold'), cursor='hand2'
        )
        title_label.grid(row=0, column=0, sticky='w')

        self.arrow_label = tk.Label(
            header_content, text="▶", bg=self.theme.colors['bg_secondary'],
            fg=self.theme.colors['accent'], font=('Arial', 10, 'bold'), cursor='hand2'
        )
        self.arrow_label.grid(row=0, column=1, sticky='e')

        # Content area con padding inferior aumentado
        self.content_frame = tk.Frame(card, bg=self.theme.colors['bg_primary'])
        self.content_frame.grid_columnconfigure(0, weight=1)

        # Bind eventos
        def toggle_section(event=None):
            self.toggle()

        header.bind("<Button-1>", toggle_section)
        title_label.bind("<Button-1>", toggle_section)
        self.arrow_label.bind("<Button-1>", toggle_section)

        if default_expanded:
            self.expanded = True
            self.toggle()

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


class FilterPanel:
    """Panel de filtros con mejor espaciado"""
    def __init__(self, parent, theme=None):
        self.theme = theme or UITheme()
        self.parent = parent
        self.styled_widgets = StyledWidgets(self.theme)
        self.filters = {}

    def create_date_filter(self, container):
        """Crea filtros de fecha con mejor espaciado"""
        date_frame = tk.Frame(container, bg=self.theme.colors['bg_primary'])
        date_frame.pack(fill='x', padx=18, pady=(15, 0))

        self.styled_widgets.create_styled_label(
            date_frame, "📅 Rango de Fechas:", style='bold'
        ).pack(anchor='w', pady=(0, 8))  # Aumentado padding inferior

        date_inputs = tk.Frame(date_frame, bg=self.theme.colors['bg_tertiary'])
        date_inputs.pack(fill='x')

        date_inner = tk.Frame(date_inputs, bg=self.theme.colors['bg_tertiary'])
        date_inner.pack(padx=15, pady=15)  # Aumentado padding

        # Fecha desde
        tk.Label(
            date_inner, text="Desde:", bg=self.theme.colors['bg_tertiary'],
            fg=self.theme.colors['text_primary'], font=('Arial', 9)
        ).grid(row=0, column=0, sticky='w', pady=(0, 8))  # Aumentado padding inferior

        self.filters['date_from'] = self.styled_widgets.create_styled_entry(date_inner)
        self.filters['date_from'].grid(row=0, column=1, sticky='ew', padx=(8, 0), pady=(0, 8))  # Aumentado padding

        # Fecha hasta
        tk.Label(
            date_inner, text="Hasta:", bg=self.theme.colors['bg_tertiary'],
            fg=self.theme.colors['text_primary'], font=('Arial', 9)
        ).grid(row=1, column=0, sticky='w')

        self.filters['date_to'] = self.styled_widgets.create_styled_entry(date_inner)
        self.filters['date_to'].grid(row=1, column=1, sticky='ew', padx=(8, 0))

        date_inner.grid_columnconfigure(1, weight=1)

    def create_dropdown_filters(self, container):
        """Crea filtros dropdown con mejor espaciado"""
        filters_frame = tk.Frame(container, bg=self.theme.colors['bg_primary'])
        filters_frame.pack(fill='x', padx=18, pady=15)

        self.styled_widgets.create_styled_label(
            filters_frame, "🔍 Filtros Rápidos:", style='bold'
        ).pack(anchor='w', pady=(0, 8))  # Aumentado padding inferior

        filters_grid = tk.Frame(filters_frame, bg=self.theme.colors['bg_tertiary'])
        filters_grid.pack(fill='x')

        filters_inner = tk.Frame(filters_grid, bg=self.theme.colors['bg_tertiary'])
        filters_inner.pack(padx=15, pady=15)  # Aumentado padding

        # Estado
        tk.Label(
            filters_inner, text="Estado:", bg=self.theme.colors['bg_tertiary'],
            fg=self.theme.colors['text_primary'], font=('Arial', 9)
        ).grid(row=0, column=0, sticky='w', pady=(0, 8))  # Aumentado padding inferior

        self.filters['status_filter'] = self.styled_widgets.create_styled_combobox(
            filters_inner, ["Todos", "Exitoso", "Fallido", "En Ejecución"], "Todos", width=18
        )
        self.filters['status_filter'].grid(row=0, column=1, sticky='ew', padx=(8, 0), pady=(0, 8))  # Aumentado padding

        # Usuario
        tk.Label(
            filters_inner, text="Usuario:", bg=self.theme.colors['bg_tertiary'],
            fg=self.theme.colors['text_primary'], font=('Arial', 9)
        ).grid(row=1, column=0, sticky='w', pady=(0, 8))  # Aumentado padding inferior

        self.filters['user_filter'] = self.styled_widgets.create_styled_combobox(
            filters_inner, ["Todos", "Usuario", "Sistema"], "Todos", width=18
        )
        self.filters['user_filter'].grid(row=1, column=1, sticky='ew', padx=(8, 0), pady=(0, 8))  # Aumentado padding

        # Perfil
        tk.Label(
            filters_inner, text="Perfil:", bg=self.theme.colors['bg_tertiary'],
            fg=self.theme.colors['text_primary'], font=('Arial', 9)
        ).grid(row=2, column=0, sticky='w')

        self.filters['profile_filter'] = self.styled_widgets.create_styled_combobox(
            filters_inner, ["Todos"], "Todos", width=18
        )
        self.filters['profile_filter'].grid(row=2, column=1, sticky='ew', padx=(8, 0))

        filters_inner.grid_columnconfigure(1, weight=1)

    def get_filter_values(self):
        """Obtiene valores actuales de todos los filtros"""
        values = {}
        for key, widget in self.filters.items():
            if hasattr(widget, 'get'):
                values[key] = widget.get().strip()
        return values

    def clear_filters(self):
        """Limpia todos los filtros"""
        for key, widget in self.filters.items():
            if hasattr(widget, 'delete') and hasattr(widget, 'insert'):
                widget.delete(0, 'end')
            elif hasattr(widget, 'set'):
                if 'filter' in key:
                    widget.set("Todos")
                else:
                    widget.set("")

    def update_profile_options(self, profiles):
        """Actualiza opciones del filtro de perfil"""
        if 'profile_filter' in self.filters:
            self.filters['profile_filter']['values'] = profiles


class ButtonGroup:
    """Grupo de botones con layout automático y mejor espaciado"""
    def __init__(self, parent, theme=None):
        self.theme = theme or UITheme()
        self.parent = parent
        self.styled_widgets = StyledWidgets(self.theme)
        self.buttons = []

    def add_button(self, text, command, color=None, **kwargs):
        """Añade un botón al grupo"""
        button = self.styled_widgets.create_styled_button(
            self.parent, text, command, color, **kwargs
        )
        self.buttons.append(button)
        return button

    def layout_horizontal(self, fill_equal=True):
        """Organiza botones horizontalmente con mejor espaciado"""
        if not self.buttons:
            return

        for i, button in enumerate(self.buttons):
            if fill_equal:
                button.pack(side='left', fill='x', expand=True,
                            padx=(0, 8) if i < len(self.buttons) - 1 else 0,  # Aumentado espaciado horizontal
                            pady=(0, 15))  # Añadido padding inferior
            else:
                button.pack(side='left',
                            padx=(0, 8) if i < len(self.buttons) - 1 else 0,  # Aumentado espaciado horizontal
                            pady=(0, 15))  # Añadido padding inferior

    def layout_vertical(self, spacing=15):  # Aumentado espaciado por defecto
        """Organiza botones verticalmente con mejor espaciado"""
        for i, button in enumerate(self.buttons):
            if i < len(self.buttons) - 1:
                # Botones intermedios
                button.pack(fill='x', pady=(0, spacing))
            else:
                # Último botón con padding inferior extra
                button.pack(fill='x', pady=(0, 20))  # Aumentado padding inferior para el último botón