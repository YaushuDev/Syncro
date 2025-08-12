# registro_tab.py
# Ubicación: /syncro_bot/gui/tabs/registro_tab.py
"""
Pestaña del sistema de registro para Syncro Bot simplificada.
Coordina todos los componentes de registro, filtrado, reportes y UI
manteniendo una interfaz limpia y eficiente.
"""

import tkinter as tk
from tkinter import ttk, messagebox

# Importaciones simplificadas de componentes optimizados
from ..components.registry_manager import RegistryManager, RegistryFilters, RegistrySearch
from ..components.registry_reports import ReportManager, ReportTypes
from ..components.registry_ui_components import (
    UITheme, StyledWidgets, CardFrame, StatBox, CollapsibleSection,
    FilterPanel, ButtonGroup
)


class RegistroTab:
    """Pestaña del sistema de registro para Syncro Bot"""

    def __init__(self, parent_notebook):
        # Configuración básica
        self.parent = parent_notebook
        self.theme = UITheme()
        self.styled_widgets = StyledWidgets(self.theme)

        # Componentes principales
        self.registry_manager = RegistryManager()
        self.filters = RegistryFilters(self.registry_manager)
        self.search = RegistrySearch(self.registry_manager)

        # Estado de la UI
        self.widgets = {}
        self.selected_record = None
        self.expanded_section = None
        self.section_frames = {}

        # Integración con email
        self.email_tab = None
        self.report_manager = None

        # Crear interfaz
        self.create_tab()
        self.load_records()

    def set_email_tab(self, email_tab):
        """Establece la referencia al EmailTab para envío de reportes"""
        self.email_tab = email_tab
        self.report_manager = ReportManager(self.registry_manager, email_tab)
        self._update_email_status()
        self._update_excel_availability()  # Actualizar estado de Excel cuando se configura email

    def create_tab(self):
        """Crear la pestaña de registro"""
        self.frame = ttk.Frame(self.parent)
        self.parent.add(self.frame, text="Registro")
        self.create_interface()

    def create_interface(self):
        """Crea la interfaz principal con diseño de 2 columnas"""
        main_container = tk.Frame(self.frame, bg=self.theme.colors['bg_primary'])
        main_container.pack(fill='both', expand=True, padx=15, pady=10)

        # Configurar grid para 2 columnas
        main_container.grid_columnconfigure(0, weight=0, minsize=450)
        main_container.grid_columnconfigure(1, weight=0, minsize=1)
        main_container.grid_columnconfigure(2, weight=1, minsize=650)
        main_container.grid_rowconfigure(0, weight=1)

        # Crear columnas
        self._create_left_column(main_container)
        self._create_separator(main_container)
        self._create_right_column(main_container)

    def _create_left_column(self, parent):
        """Crea la columna izquierda con controles"""
        left_column = tk.Frame(parent, bg=self.theme.colors['bg_primary'], width=450)
        left_column.grid(row=0, column=0, sticky='ns', padx=(0, 5))
        left_column.grid_propagate(False)

        # Configurar filas
        left_column.grid_rowconfigure(0, weight=0)  # Estadísticas
        left_column.grid_rowconfigure(1, weight=0)  # Filtros
        left_column.grid_rowconfigure(2, weight=0)  # Reportes
        left_column.grid_rowconfigure(3, weight=0)  # Acciones
        left_column.grid_rowconfigure(4, weight=1)  # Espaciador
        left_column.grid_columnconfigure(0, weight=1)

        # Crear secciones colapsables
        self._create_statistics_section(left_column)
        self._create_filters_section(left_column)
        self._create_reports_section(left_column)
        self._create_actions_section(left_column)

    def _create_separator(self, parent):
        """Crea separador visual"""
        separator = tk.Frame(parent, bg=self.theme.colors['border'], width=1)
        separator.grid(row=0, column=1, sticky='ns', padx=5)

    def _create_right_column(self, parent):
        """Crea la columna derecha con tabla y detalles"""
        right_column = tk.Frame(parent, bg=self.theme.colors['bg_primary'])
        right_column.grid(row=0, column=2, sticky='nsew', padx=(5, 0))

        right_column.grid_rowconfigure(0, weight=0)  # Header
        right_column.grid_rowconfigure(1, weight=1)  # Tabla
        right_column.grid_rowconfigure(2, weight=0)  # Detalle
        right_column.grid_columnconfigure(0, weight=1)

        self._create_records_header(right_column)
        self._create_records_table(right_column)
        self._create_detail_panel(right_column)

    def _create_statistics_section(self, parent):
        """Crea sección de estadísticas"""
        section = CollapsibleSection(parent, "stats", "📊 Estadísticas Generales", self.theme)
        content = section.create(row=0, min_height=200, default_expanded=True)
        self._setup_statistics_content(content)
        section.set_toggle_callback(self._on_section_toggle)
        self.section_frames["stats"] = section

    def _setup_statistics_content(self, content):
        """Configura contenido de estadísticas"""
        stats_container = tk.Frame(content, bg=self.theme.colors['bg_primary'])
        stats_container.pack(fill='x', padx=18, pady=15)

        # Fila 1: Total y Exitosos
        row1 = tk.Frame(stats_container, bg=self.theme.colors['bg_primary'])
        row1.pack(fill='x', pady=(0, 8))

        total_stat = StatBox(row1, "📈 Total Ejecuciones:", self.theme)
        self.widgets['total_stat'] = total_stat.create("0", side='left')

        success_stat = StatBox(row1, "✅ Exitosas:", self.theme)
        self.widgets['success_stat'] = success_stat.create("0", side='right')

        # Fila 2: Fallidas y En Progreso
        row2 = tk.Frame(stats_container, bg=self.theme.colors['bg_primary'])
        row2.pack(fill='x', pady=(0, 8))

        failed_stat = StatBox(row2, "❌ Fallidas:", self.theme)
        self.widgets['failed_stat'] = failed_stat.create("0", side='left')

        progress_stat = StatBox(row2, "⏳ En Progreso:", self.theme)
        self.widgets['progress_stat'] = progress_stat.create("0", side='right')

        # Fila 3: Usuario vs Sistema
        row3 = tk.Frame(stats_container, bg=self.theme.colors['bg_primary'])
        row3.pack(fill='x', pady=(0, 8))

        manual_stat = StatBox(row3, "👤 Usuario:", self.theme)
        self.widgets['manual_stat'] = manual_stat.create("0", side='left')

        system_stat = StatBox(row3, "🤖 Sistema:", self.theme)
        self.widgets['system_stat'] = system_stat.create("0", side='right')

        # Tasa de éxito
        success_rate_frame = tk.Frame(content, bg=self.theme.colors['bg_tertiary'])
        success_rate_frame.pack(fill='x', pady=(15, 0))

        self.styled_widgets.create_styled_label(
            success_rate_frame, "📊 Tasa de Éxito:", style='normal',
            bg=self.theme.colors['bg_tertiary']
        ).pack(side='left', padx=10, pady=8)

        self.widgets['success_rate_stat'] = self.styled_widgets.create_styled_label(
            success_rate_frame, "0%", style='bold',
            bg=self.theme.colors['bg_tertiary'], fg=self.theme.colors['success']
        )
        self.widgets['success_rate_stat'].pack(side='right', padx=10, pady=8)

    def _create_filters_section(self, parent):
        """Crea sección de filtros"""
        section = CollapsibleSection(parent, "filters", "🔍 Filtros de Búsqueda", self.theme)
        content = section.create(row=1, min_height=280, default_expanded=False)

        self.filter_panel = FilterPanel(content, self.theme)
        self.filter_panel.create_date_filter(content)
        self.filter_panel.create_dropdown_filters(content)

        # Botones de filtro
        filter_buttons_frame = tk.Frame(content, bg=self.theme.colors['bg_primary'])
        filter_buttons_frame.pack(fill='x', padx=18)

        filter_buttons = ButtonGroup(filter_buttons_frame, self.theme)
        filter_buttons.add_button("🔍 Aplicar Filtros", self._apply_filters, self.theme.colors['info'])
        filter_buttons.add_button("🧹 Limpiar", self._clear_filters, self.theme.colors['text_secondary'])
        filter_buttons.layout_horizontal(fill_equal=True)

        section.set_toggle_callback(self._on_section_toggle)
        self.section_frames["filters"] = section

    def _create_reports_section(self, parent):
        """Crea sección de reportes"""
        section = CollapsibleSection(parent, "reports", "📧 Generación de Reportes", self.theme)
        content = section.create(row=2, min_height=220, default_expanded=False)
        self._setup_reports_content(content)
        section.set_toggle_callback(self._on_section_toggle)
        self.section_frames["reports"] = section

    def _setup_reports_content(self, content):
        """Configura contenido de reportes"""
        # Tipo de reporte
        report_type_frame = tk.Frame(content, bg=self.theme.colors['bg_primary'])
        report_type_frame.pack(fill='x', padx=18, pady=(15, 15))

        self.styled_widgets.create_styled_label(
            report_type_frame, "📋 Tipo de Reporte:", style='bold'
        ).pack(anchor='w', pady=(0, 5))

        self.widgets['report_type'] = self.styled_widgets.create_styled_combobox(
            report_type_frame,
            values=ReportTypes.get_all_types(),
            default_value=ReportTypes.CURRENT_FILTERED,
            width=35
        )
        self.widgets['report_type'].pack(fill='x')

        # Estado del email
        email_status_frame = tk.Frame(content, bg=self.theme.colors['bg_tertiary'])
        email_status_frame.pack(fill='x', padx=18, pady=(0, 15))

        self.styled_widgets.create_styled_label(
            email_status_frame, "📧 Email:", style='normal',
            bg=self.theme.colors['bg_tertiary']
        ).pack(side='left', padx=10, pady=8)

        self.widgets['email_status'] = self.styled_widgets.create_styled_label(
            email_status_frame, "No configurado", style='bold',
            bg=self.theme.colors['bg_tertiary'], fg=self.theme.colors['text_secondary']
        )
        self.widgets['email_status'].pack(side='right', padx=10, pady=8)

        # Botones de reportes
        report_buttons_frame = tk.Frame(content, bg=self.theme.colors['bg_primary'])
        report_buttons_frame.pack(fill='x', padx=18)

        report_buttons = ButtonGroup(report_buttons_frame, self.theme)

        self.widgets['export_excel_btn'] = report_buttons.add_button(
            "📊 Exportar a Excel", self._export_to_excel, self.theme.colors['info']
        )

        self.widgets['send_email_btn'] = report_buttons.add_button(
            "📧 Generar y Enviar por Email", self._send_report_email, self.theme.colors['success']
        )

        report_buttons.layout_vertical(spacing=10)

        # Verificar disponibilidad inicial de Excel (importación directa)
        self._update_excel_availability()

    def _create_actions_section(self, parent):
        """Crea sección de acciones"""
        section = CollapsibleSection(parent, "actions", "🎮 Acciones de Gestión", self.theme)
        content = section.create(row=3, min_height=180, default_expanded=False)

        actions_frame = tk.Frame(content, bg=self.theme.colors['bg_primary'])
        actions_frame.pack(fill='x', padx=18, pady=15)

        actions_buttons = ButtonGroup(actions_frame, self.theme)
        actions_buttons.add_button("🔄 Refrescar Registros", self.load_records, self.theme.colors['info'])
        actions_buttons.add_button("🧹 Limpiar Antiguos (30+ días)", self._clean_old_records,
                                   self.theme.colors['warning'])
        actions_buttons.add_button("🗑️ Eliminar Todos los Registros", self._clear_all_records,
                                   self.theme.colors['error'])
        actions_buttons.layout_vertical(spacing=10)

        section.set_toggle_callback(self._on_section_toggle)
        self.section_frames["actions"] = section

    def _create_records_header(self, parent):
        """Crea header de registros"""
        header_container = tk.Frame(parent, bg=self.theme.colors['bg_primary'])
        header_container.grid(row=0, column=0, sticky='ew', pady=(0, 10))

        card = CardFrame(header_container, "📋 Historial de Ejecuciones", self.theme)
        header_content = card.create()

        self.widgets['record_count'] = self.styled_widgets.create_styled_label(
            header_content, "0 registros", style='secondary'
        )
        self.widgets['record_count'].pack(anchor='e')

    def _create_records_table(self, parent):
        """Crea tabla de registros"""
        table_container = tk.Frame(parent, bg=self.theme.colors['bg_primary'])
        table_container.grid(row=1, column=0, sticky='nsew', pady=(0, 10))

        table_frame = tk.Frame(table_container, bg=self.theme.colors['border'], bd=1, relief='solid')
        table_frame.pack(fill='both', expand=True)

        columns = ('fecha', 'inicio', 'fin', 'perfil', 'duracion', 'estado', 'usuario')
        self.widgets['records_tree'] = ttk.Treeview(table_frame, columns=columns, show='headings')

        # Configurar columnas
        column_configs = {
            'fecha': ('Fecha', 90),
            'inicio': ('H. Inicio', 70),
            'fin': ('H. Fin', 70),
            'perfil': ('Perfil', 100),
            'duracion': ('Duración', 80),
            'estado': ('Estado', 80),
            'usuario': ('Usuario', 70)
        }

        for col, (heading, width) in column_configs.items():
            self.widgets['records_tree'].heading(col, text=heading)
            self.widgets['records_tree'].column(col, width=width)

        # Scrollbars
        v_scrollbar = ttk.Scrollbar(table_frame, orient='vertical',
                                    command=self.widgets['records_tree'].yview)
        h_scrollbar = ttk.Scrollbar(table_frame, orient='horizontal',
                                    command=self.widgets['records_tree'].xview)

        self.widgets['records_tree'].configure(
            yscrollcommand=v_scrollbar.set,
            xscrollcommand=h_scrollbar.set
        )

        self.widgets['records_tree'].pack(side='left', fill='both', expand=True)
        v_scrollbar.pack(side='right', fill='y')
        h_scrollbar.pack(side='bottom', fill='x')

        self.widgets['records_tree'].bind('<<TreeviewSelect>>', self._on_record_select)

    def _create_detail_panel(self, parent):
        """Crea panel de detalle"""
        detail_container = tk.Frame(parent, bg=self.theme.colors['bg_primary'])
        detail_container.grid(row=2, column=0, sticky='ew')

        card = CardFrame(detail_container, "🔍 Detalle del Registro Seleccionado", self.theme)
        detail_content = card.create()

        self.widgets['detail_text'] = self.styled_widgets.create_styled_text(
            detail_content, height=4, state=tk.DISABLED
        )
        self.widgets['detail_text'].pack(fill='both', expand=True)

        self._update_detail_panel("Seleccione un registro para ver los detalles...")

    def _on_section_toggle(self, section_id, is_expanded):
        """Maneja toggle de secciones"""
        if is_expanded:
            for sid, section in self.section_frames.items():
                if sid != section_id and section.is_expanded():
                    section.collapse()
            self.expanded_section = section_id
        else:
            self.expanded_section = None

    def _apply_filters(self):
        """Aplica filtros seleccionados"""
        filter_values = self.filter_panel.get_filter_values()
        filtered_records, message = self.filters.apply_filters(filter_values)

        if filtered_records is not None:
            self._populate_records_table(filtered_records)
            messagebox.showinfo("Filtros Aplicados", message)
        else:
            messagebox.showerror("Error en Filtros", message)

    def _clear_filters(self):
        """Limpia todos los filtros"""
        self.filter_panel.clear_filters()
        all_records = self.filters.clear_filters()
        self._populate_records_table(all_records)
        messagebox.showinfo("Filtros", "Filtros limpiados - Mostrando todos los registros")

    def _export_to_excel(self):
        """Exporta registros a Excel"""
        # Verificar openpyxl antes de continuar
        try:
            import openpyxl
        except ImportError:
            messagebox.showerror("Error", "openpyxl no está instalado.\n\nInstale con: pip install openpyxl")
            return

        if not self.report_manager:
            messagebox.showerror("Error", "Sistema de reportes no disponible")
            return

        report_type = self.widgets['report_type'].get()
        filter_info = self.filters.get_filter_info_for_report()

        filename, success, message = self.report_manager.export_to_excel(report_type, filter_info)

        if success:
            messagebox.showinfo("Éxito", message)
        else:
            messagebox.showerror("Error", message)

    def _send_report_email(self):
        """Envía reporte por email"""
        # Verificar openpyxl antes de continuar
        try:
            import openpyxl
        except ImportError:
            messagebox.showerror("Error", "openpyxl no está instalado.\n\nInstale con: pip install openpyxl")
            return

        if not self.report_manager:
            messagebox.showerror("Error", "Sistema de reportes no disponible")
            return

        if not self.email_tab or not self.email_tab.is_email_configured():
            messagebox.showerror("Error", "Email no configurado.\n\nConfigure el email en la pestaña 'Email'")
            return

        report_type = self.widgets['report_type'].get()
        filter_info = self.filters.get_filter_info_for_report()

        def callback(success, message):
            self.frame.after(0,
                             lambda: messagebox.showinfo("Reporte Email", message) if success else messagebox.showerror(
                                 "Error Email", message))

        success, message = self.report_manager.send_report_by_email(
            report_type, filter_info, async_mode=True, callback=callback
        )

        if success:
            messagebox.showinfo("Enviando", "Generando y enviando reporte por email...")

    def _clean_old_records(self):
        """Limpia registros antiguos"""
        if messagebox.askyesno("Confirmar",
                               "¿Eliminar registros con más de 30 días?\n\nEsta acción no se puede deshacer."):
            deleted_count = self.registry_manager.clear_old_records(30)
            messagebox.showinfo("Éxito", f"Se eliminaron {deleted_count} registros antiguos")
            self.load_records()

    def _clear_all_records(self):
        """Elimina todos los registros"""
        if messagebox.askyesno("Confirmar Eliminación",
                               "¿ELIMINAR TODOS los registros?\n\nEsta acción NO se puede deshacer."):
            self.registry_manager.clear_registry()
            messagebox.showinfo("Éxito", "Todos los registros han sido eliminados")
            self.load_records()

    def _on_record_select(self, event):
        """Maneja selección de registro"""
        selection = self.widgets['records_tree'].selection()
        if not selection:
            self.selected_record = None
            self._update_detail_panel("Seleccione un registro para ver los detalles...")
            return

        item = self.widgets['records_tree'].item(selection[0])
        values = item['values']

        if values:
            fecha, hora_inicio = values[0], values[1]
            records = self.registry_manager.get_all_records()

            for record in records:
                if record['fecha'] == fecha and record['hora_inicio'] == hora_inicio:
                    self.selected_record = record
                    self._show_record_detail(record)
                    break

    def _show_record_detail(self, record):
        """Muestra detalle completo de un registro"""
        detail_text = f"""ID: {record['id']}
Fecha: {record['fecha']}
Hora Inicio: {record['hora_inicio']}
Hora Fin: {record['hora_fin']}
Perfil: {record['perfil']}
Duración: {record['duracion']}
Estado: {record['estado']}
Usuario: {record['usuario']}"""

        if record['error_message']:
            detail_text += f"\nError: {record['error_message']}"

        detail_text += f"\nCreado: {record['created'][:19]}"
        self._update_detail_panel(detail_text)

    def _update_detail_panel(self, text):
        """Actualiza panel de detalle"""
        self.widgets['detail_text'].configure(state=tk.NORMAL)
        self.widgets['detail_text'].delete(1.0, tk.END)
        self.widgets['detail_text'].insert(tk.END, text)
        self.widgets['detail_text'].configure(state=tk.DISABLED)

    def _populate_records_table(self, records):
        """Puebla tabla con registros"""
        # Limpiar tabla
        for item in self.widgets['records_tree'].get_children():
            self.widgets['records_tree'].delete(item)

        # Insertar registros con formato
        for record in records:
            estado = record['estado']
            if estado == "Exitoso":
                estado = "✅ Exitoso"
            elif estado == "Fallido":
                estado = "❌ Fallido"
            elif estado == "En Ejecución":
                estado = "⏳ En Progreso"

            usuario = "🤖 Sistema" if record['usuario'] == "Sistema" else "👤 Usuario"

            self.widgets['records_tree'].insert('', 'end', values=(
                record['fecha'], record['hora_inicio'], record['hora_fin'],
                record['perfil'], record['duracion'], estado, usuario
            ))

        self.widgets['record_count'].configure(text=f"{len(records)} registros")

    def _update_statistics(self):
        """Actualiza estadísticas mostradas"""
        stats = self.registry_manager.get_statistics()

        self.widgets['total_stat'].configure(text=str(stats['total']))
        self.widgets['success_stat'].configure(text=str(stats['successful']))
        self.widgets['failed_stat'].configure(text=str(stats['failed']))
        self.widgets['progress_stat'].configure(text=str(stats['in_progress']))
        self.widgets['manual_stat'].configure(text=str(stats['manual']))
        self.widgets['system_stat'].configure(text=str(stats['system']))
        self.widgets['success_rate_stat'].configure(text=f"{stats['success_rate']:.1f}%")

    def _update_email_status(self):
        """Actualiza estado del email"""
        if not self.email_tab:
            self.widgets['email_status'].configure(
                text="No disponible", fg=self.theme.colors['error']
            )
        elif self.email_tab.is_email_configured():
            self.widgets['email_status'].configure(
                text="✅ Configurado", fg=self.theme.colors['success']
            )
        else:
            self.widgets['email_status'].configure(
                text="❌ Sin configurar", fg=self.theme.colors['error']
            )

    def _update_excel_availability(self):
        """Actualiza disponibilidad de Excel y estado de botones"""
        # Verificar openpyxl directamente
        try:
            import openpyxl
            excel_available = True
        except ImportError:
            excel_available = False

        if excel_available:
            # Excel disponible - habilitar botones
            self.widgets['export_excel_btn'].configure(
                state='normal',
                text='📊 Exportar a Excel'
            )
            # El botón de email depende tanto de Excel como de email configurado
            if self.email_tab and self.email_tab.is_email_configured():
                self.widgets['send_email_btn'].configure(
                    state='normal',
                    text='📧 Generar y Enviar por Email'
                )
            else:
                self.widgets['send_email_btn'].configure(
                    state='disabled',
                    text='📧 Configurar Email primero'
                )
        else:
            # Excel no disponible - deshabilitar botones
            self.widgets['export_excel_btn'].configure(
                state='disabled',
                text='📊 Excel no disponible (instalar openpyxl)'
            )
            self.widgets['send_email_btn'].configure(
                state='disabled',
                text='📧 Requiere openpyxl'
            )

    def load_records(self):
        """Carga y muestra todos los registros"""
        try:
            records = self.registry_manager.get_all_records()
            self._populate_records_table(records)
            self._update_statistics()

            profiles = self.registry_manager.get_unique_profiles()
            self.filter_panel.update_profile_options(profiles)

            self._update_email_status()
            self._update_excel_availability()  # Actualizar estado de Excel
            self._update_detail_panel("Seleccione un registro para ver los detalles...")

        except Exception as e:
            messagebox.showerror("Error", f"Error cargando registros: {str(e)}")

    # ===== MÉTODOS PÚBLICOS PARA INTEGRACIÓN =====

    def add_execution_record(self, start_time, profile_name="Manual", user_type="Usuario"):
        """Método público para añadir registro de ejecución"""
        return self.registry_manager.add_execution_record(
            start_time=start_time,
            profile_name=profile_name,
            user_type=user_type
        )

    def update_execution_record(self, record_id, end_time, status, error_message=""):
        """Método público para actualizar registro de ejecución"""
        result = self.registry_manager.update_execution_record(
            record_id, end_time, status, error_message
        )

        if hasattr(self, 'widgets') and 'records_tree' in self.widgets:
            self.load_records()

        return result

    def generate_and_send_report(self, report_type="Últimos 7 días", custom_title=None):
        """Método público para generar y enviar reportes automáticamente"""
        if not self.report_manager:
            return False, "Sistema de reportes no configurado"

        return self.report_manager.send_report_by_email(
            report_type, custom_title=custom_title, async_mode=False
        )

    def cleanup(self):
        """Limpia recursos al cerrar"""
        try:
            if self.report_manager:
                self.report_manager.cleanup_resources()
        except Exception as e:
            print(f"Error durante cleanup: {e}")