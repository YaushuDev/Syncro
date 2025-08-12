# email_tab.py
# Ubicación: /syncro_bot/gui/tabs/email_tab.py
"""
Pestaña de configuración de email para Syncro Bot.
Gestiona la configuración SMTP, pruebas de conexión, destinatarios y envío de correos.
Incluye encriptación de datos, persistencia de configuración y soporte para adjuntos.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import threading
import json
import os
import smtplib
import re

# Importaciones de email con manejo de errores
try:
    from cryptography.fernet import Fernet
except ImportError:
    print("Error: La librería 'cryptography' no está instalada.")
    print("Instale con: pip install cryptography")
    raise

try:
    import email.mime.text as email_text
    import email.mime.multipart as email_multipart
    import email.mime.base as email_base
    from email import encoders
except ImportError:
    print("Error con las librerías de email del sistema.")
    raise


class EmailConfigManager:
    """Gestor de configuración de email con encriptación"""

    def __init__(self):
        self.config_file = "email_config.json"
        self.key_file = "email.key"

    def _get_or_create_key(self):
        """Obtiene o crea la clave de encriptación"""
        if os.path.exists(self.key_file):
            with open(self.key_file, 'rb') as f:
                return f.read()
        else:
            key = Fernet.generate_key()
            with open(self.key_file, 'wb') as f:
                f.write(key)
            return key

    def _clean_string(self, text):
        """Limpia caracteres problemáticos de un string"""
        if not isinstance(text, str):
            return text
        # Reemplazar caracteres no-ASCII problemáticos
        text = text.replace('\xa0', ' ')  # Espacio no separable
        text = text.replace('\u00a0', ' ')  # Otra forma del espacio no separable
        # Normalizar espacios
        text = ' '.join(text.split())
        return text.strip()

    def _encrypt_data(self, data):
        """Encripta los datos"""
        key = self._get_or_create_key()
        fernet = Fernet(key)

        # Limpiar todos los strings en el diccionario
        clean_data = {}
        for key_name, value in data.items():
            if isinstance(value, str):
                clean_data[key_name] = self._clean_string(value)
            else:
                clean_data[key_name] = value

        json_str = json.dumps(clean_data, ensure_ascii=True)
        encrypted_data = fernet.encrypt(json_str.encode('utf-8'))
        return encrypted_data

    def _decrypt_data(self, encrypted_data):
        """Desencripta los datos"""
        try:
            key = self._get_or_create_key()
            fernet = Fernet(key)
            decrypted_data = fernet.decrypt(encrypted_data)
            return json.loads(decrypted_data.decode('utf-8'))
        except Exception:
            return None

    def save_email_config(self, config_data):
        """Guarda la configuración de email encriptada"""
        try:
            encrypted_data = self._encrypt_data(config_data)
            with open(self.config_file, 'wb') as f:
                f.write(encrypted_data)
            return True
        except Exception as e:
            print(f"Error guardando configuración: {e}")
            return False

    def load_email_config(self):
        """Carga la configuración de email"""
        try:
            if not os.path.exists(self.config_file):
                return None

            with open(self.config_file, 'rb') as f:
                encrypted_data = f.read()

            return self._decrypt_data(encrypted_data)
        except Exception as e:
            print(f"Error cargando configuración: {e}")
            return None

    def clear_email_config(self):
        """Elimina la configuración guardada"""
        try:
            if os.path.exists(self.config_file):
                os.remove(self.config_file)
            if os.path.exists(self.key_file):
                os.remove(self.key_file)
            return True
        except Exception:
            return False

    def validate_email(self, email):
        """Valida formato de email"""
        if not email:
            return False

        # Limpiar el email primero
        clean_email = self._clean_string(email)
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, clean_email) is not None


class EmailService:
    """Servicio de envío de emails con soporte para adjuntos"""

    def __init__(self):
        self.smtp_configs = {
            "Gmail": {"server": "smtp.gmail.com", "port": 587},
            "Outlook/Hotmail": {"server": "smtp-mail.outlook.com", "port": 587},
            "Yahoo": {"server": "smtp.mail.yahoo.com", "port": 587}
        }
        self.config = {}

    def _clean_string(self, text):
        """Limpia caracteres problemáticos de un string"""
        if not isinstance(text, str):
            return text
        # Reemplazar caracteres no-ASCII problemáticos
        text = text.replace('\xa0', ' ')  # Espacio no separable
        text = text.replace('\u00a0', ' ')  # Otra forma del espacio no separable
        # Normalizar espacios
        text = ' '.join(text.split())
        return text.strip()

    def set_configuration(self, provider, email, password, custom_server=None, custom_port=None):
        """Configura el servicio de email"""
        self.config = {
            "provider": self._clean_string(provider),
            "email": self._clean_string(email),
            "password": self._clean_string(password)
        }

        if provider == "Personalizado" and custom_server and custom_port:
            self.config["smtp_server"] = self._clean_string(custom_server)
            self.config["port"] = custom_port
        elif provider in self.smtp_configs:
            self.config["smtp_server"] = self.smtp_configs[provider]["server"]
            self.config["port"] = self.smtp_configs[provider]["port"]

    def test_connection(self):
        """Prueba la conexión SMTP"""
        try:
            if not self.config:
                return False, "No hay configuración establecida"

            # Usar encoding explícito para evitar problemas de caracteres
            server = smtplib.SMTP(self.config["smtp_server"], self.config["port"])
            server.starttls()

            # Asegurar que email y password estén limpios
            clean_email = self._clean_string(self.config["email"])
            clean_password = self._clean_string(self.config["password"])

            server.login(clean_email, clean_password)
            server.quit()

            return True, "Conexión exitosa"
        except UnicodeEncodeError as e:
            return False, f"Error de codificación: Verifique que no haya caracteres especiales en email o contraseña"
        except smtplib.SMTPAuthenticationError:
            return False, "Error de autenticación: Verifique email y contraseña"
        except smtplib.SMTPConnectError:
            return False, "Error de conexión: No se puede conectar al servidor SMTP"
        except Exception as e:
            error_msg = str(e)
            # Limpiar mensaje de error también
            clean_error = self._clean_string(error_msg)
            return False, clean_error

    def send_email(self, to_email, cc_emails, subject, body, attachments=None):
        """Envía un email con soporte para adjuntos"""
        try:
            if not self.config:
                return False, "No hay configuración establecida"

            # Limpiar todos los strings de entrada
            clean_to_email = self._clean_string(to_email)
            clean_subject = self._clean_string(subject)
            clean_body = self._clean_string(body)

            clean_cc_emails = []
            if cc_emails:
                clean_cc_emails = [self._clean_string(cc) for cc in cc_emails if cc.strip()]

            # Crear mensaje usando las importaciones corregidas
            msg = email_multipart.MIMEMultipart()
            msg['From'] = self._clean_string(self.config["email"])
            msg['To'] = clean_to_email
            if clean_cc_emails:
                msg['Cc'] = ', '.join(clean_cc_emails)
            msg['Subject'] = clean_subject

            # Adjuntar el cuerpo del mensaje con encoding específico
            msg.attach(email_text.MIMEText(clean_body, 'plain', 'utf-8'))

            # ===== NUEVO: SOPORTE PARA ADJUNTOS =====
            if attachments:
                for attachment_path in attachments:
                    if os.path.exists(attachment_path):
                        try:
                            with open(attachment_path, "rb") as attachment:
                                # Crear objeto MIME para el adjunto
                                part = email_base.MIMEBase('application', 'octet-stream')
                                part.set_payload(attachment.read())

                            # Codificar el adjunto
                            encoders.encode_base64(part)

                            # Agregar header al adjunto
                            filename = os.path.basename(attachment_path)
                            part.add_header(
                                'Content-Disposition',
                                f'attachment; filename= {filename}',
                            )

                            # Adjuntar al mensaje
                            msg.attach(part)
                        except Exception as e:
                            print(f"Error adjuntando archivo {attachment_path}: {e}")
                            return False, f"Error adjuntando archivo: {e}"
            # ===== FIN NUEVO SOPORTE =====

            # Conectar y enviar
            server = smtplib.SMTP(self.config["smtp_server"], self.config["port"])
            server.starttls()

            clean_email = self._clean_string(self.config["email"])
            clean_password = self._clean_string(self.config["password"])

            server.login(clean_email, clean_password)

            recipients = [clean_to_email] + clean_cc_emails
            server.sendmail(clean_email, recipients, msg.as_string())
            server.quit()

            return True, "Email enviado exitosamente"
        except UnicodeEncodeError as e:
            return False, f"Error de codificación: Verifique que no haya caracteres especiales en el contenido"
        except Exception as e:
            error_msg = str(e)
            clean_error = self._clean_string(error_msg)
            return False, clean_error


class EmailTab:
    """Pestaña de configuración de email para Syncro Bot"""

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

        # Servicios
        self.config_manager = EmailConfigManager()
        self.email_service = EmailService()

        # Variables de control
        self.is_testing = False
        self.is_configured = False

        # Widgets
        self.widgets = {}

        # Control de secciones colapsables
        self.expanded_section = None
        self.section_frames = {}

        self.create_tab()
        self.load_saved_config()

    def create_tab(self):
        """Crear la pestaña de email"""
        self.frame = ttk.Frame(self.parent)
        self.parent.add(self.frame, text="Email")

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

        # Columna derecha - Estado y Acciones
        right_column = tk.Frame(main_container, bg=self.colors['bg_primary'])
        right_column.grid(row=0, column=2, sticky='nsew', padx=(5, 0))

        # Crear contenido
        self._create_left_column_collapsible(left_column)
        self._create_right_column(right_column)

    def _clean_entry_value(self, entry_widget):
        """Limpia el valor de un Entry widget"""
        value = entry_widget.get()
        if not isinstance(value, str):
            return value
        # Reemplazar caracteres problemáticos
        value = value.replace('\xa0', ' ')  # Espacio no separable
        value = value.replace('\u00a0', ' ')  # Otra forma del espacio no separable
        # Normalizar espacios
        value = ' '.join(value.split())
        return value.strip()

    def _clean_text_value(self, text_widget):
        """Limpia el valor de un Text widget"""
        value = text_widget.get('1.0', 'end-1c')
        if not isinstance(value, str):
            return value
        # Reemplazar caracteres problemáticos
        value = value.replace('\xa0', ' ')  # Espacio no separable
        value = value.replace('\u00a0', ' ')  # Otra forma del espacio no separable
        # Normalizar espacios y saltos de línea
        lines = [' '.join(line.split()) for line in value.split('\n')]
        return '\n'.join(lines).strip()

    def _create_left_column_collapsible(self, parent):
        """Crea la columna izquierda con secciones colapsables"""
        parent.grid_rowconfigure(0, weight=0)  # Sección de cuenta
        parent.grid_rowconfigure(1, weight=0)  # Sección de destinatarios
        parent.grid_rowconfigure(2, weight=1)  # Espaciador
        parent.grid_columnconfigure(0, weight=1)

        # Sección de cuenta
        self._create_collapsible_section(
            parent, "account", "📧 Configuración de Cuenta",
            self._create_account_content, row=0, default_expanded=False,
            min_height=200
        )

        # Sección de destinatarios
        self._create_collapsible_section(
            parent, "recipients", "👥 Destinatarios",
            self._create_recipients_content, row=1, default_expanded=False,
            min_height=150
        )

        # Espaciador
        spacer = tk.Frame(parent, bg=self.colors['bg_primary'])
        spacer.grid(row=2, column=0, sticky='nsew')

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

    def _create_account_content(self, parent):
        """Crea el contenido de configuración de cuenta"""
        content = tk.Frame(parent, bg=self.colors['bg_primary'])
        content.pack(fill='x', padx=18, pady=15)

        # Proveedor
        tk.Label(content, text="Proveedor:", bg=self.colors['bg_primary'],
                 fg=self.colors['text_primary'], font=('Arial', 10)).pack(anchor='w', pady=(0, 5))

        self.widgets['provider_var'] = tk.StringVar(value="Gmail")
        provider_frame = tk.Frame(content, bg=self.colors['bg_primary'])
        provider_frame.pack(fill='x', pady=(0, 15))

        providers = ["Gmail", "Outlook/Hotmail", "Yahoo", "Personalizado"]
        for i, provider in enumerate(providers):
            rb = tk.Radiobutton(
                provider_frame, text=provider, variable=self.widgets['provider_var'],
                value=provider, command=self._on_provider_change,
                bg=self.colors['bg_primary'], fg=self.colors['text_primary'],
                font=('Arial', 10), activebackground=self.colors['bg_tertiary'],
                selectcolor=self.colors['bg_primary']
            )
            rb.grid(row=0, column=i, padx=(0, 20), sticky='w')

        # Email
        tk.Label(content, text="Email:", bg=self.colors['bg_primary'],
                 fg=self.colors['text_primary'], font=('Arial', 10)).pack(anchor='w', pady=(0, 5))

        self.widgets['email_entry'] = self._create_styled_entry(content)
        self.widgets['email_entry'].pack(fill='x', pady=(0, 15))

        # Contraseña
        tk.Label(content, text="Contraseña:", bg=self.colors['bg_primary'],
                 fg=self.colors['text_primary'], font=('Arial', 10)).pack(anchor='w', pady=(0, 5))

        password_frame = tk.Frame(content, bg=self.colors['bg_primary'])
        password_frame.pack(fill='x', pady=(0, 15))

        self.widgets['password_entry'] = self._create_styled_entry(password_frame, show='*')
        self.widgets['password_entry'].pack(side='left', fill='x', expand=True)

        # Botón mostrar contraseña
        self.widgets['show_password_var'] = tk.BooleanVar()
        show_btn = tk.Checkbutton(
            password_frame, text="👁️", variable=self.widgets['show_password_var'],
            command=self._toggle_password_visibility,
            bg=self.colors['bg_primary'], fg=self.colors['text_secondary'],
            font=('Arial', 10), padx=10
        )
        show_btn.pack(side='right')

        # Configuración personalizada
        self.widgets['custom_frame'] = tk.Frame(content, bg=self.colors['bg_tertiary'])

        custom_inner = tk.Frame(self.widgets['custom_frame'], bg=self.colors['bg_tertiary'])
        custom_inner.pack(fill='x', padx=10, pady=10)

        # SMTP Server
        tk.Label(custom_inner, text="Servidor SMTP:", bg=self.colors['bg_tertiary'],
                 fg=self.colors['text_primary'], font=('Arial', 10)).grid(
            row=0, column=0, sticky='w', pady=5)

        self.widgets['smtp_entry'] = self._create_styled_entry(custom_inner)
        self.widgets['smtp_entry'].grid(row=0, column=1, sticky='ew', padx=(10, 0), pady=5)

        # Puerto
        tk.Label(custom_inner, text="Puerto:", bg=self.colors['bg_tertiary'],
                 fg=self.colors['text_primary'], font=('Arial', 10)).grid(
            row=1, column=0, sticky='w', pady=5)

        self.widgets['port_entry'] = self._create_styled_entry(custom_inner)
        self.widgets['port_entry'].insert(0, "587")
        self.widgets['port_entry'].grid(row=1, column=1, sticky='ew', padx=(10, 0), pady=5)

        custom_inner.grid_columnconfigure(1, weight=1)

    def _create_recipients_content(self, parent):
        """Crea el contenido de destinatarios"""
        content = tk.Frame(parent, bg=self.colors['bg_primary'])
        content.pack(fill='x', padx=18, pady=15)

        # Destinatario principal
        tk.Label(content, text="📨 Destinatario Principal (obligatorio):",
                 bg=self.colors['bg_primary'], fg=self.colors['text_primary'],
                 font=('Arial', 10, 'bold')).pack(anchor='w', pady=(0, 5))

        self.widgets['main_recipient'] = self._create_styled_entry(content)
        self.widgets['main_recipient'].pack(fill='x', pady=(0, 15))

        # Destinatarios CC
        tk.Label(content, text="📋 Destinatarios en Copia (CC) - Separados por comas:",
                 bg=self.colors['bg_primary'], fg=self.colors['text_primary'],
                 font=('Arial', 10)).pack(anchor='w', pady=(0, 5))

        # Text widget
        text_frame = tk.Frame(content, bg=self.colors['border'], bd=1)
        text_frame.pack(fill='x')

        self.widgets['cc_recipients'] = tk.Text(
            text_frame, height=3,
            bg=self.colors['bg_tertiary'], fg=self.colors['text_primary'],
            font=('Arial', 10), relief='flat', padx=10, pady=5
        )
        self.widgets['cc_recipients'].pack(fill='x')

        # Ayuda
        help_text = "💡 Ejemplo: usuario1@email.com, usuario2@email.com"
        tk.Label(content, text=help_text, bg=self.colors['bg_primary'],
                 fg=self.colors['text_secondary'], font=('Arial', 9, 'italic')).pack(
            anchor='w', pady=(5, 0))

    def _create_right_column(self, parent):
        """Crea el contenido de la columna derecha"""
        parent.grid_rowconfigure(0, weight=0)  # Estado
        parent.grid_rowconfigure(1, weight=0)  # Botones
        parent.grid_rowconfigure(2, weight=1)  # Espaciador
        parent.grid_columnconfigure(0, weight=1)

        # Sección de estado
        status_container = tk.Frame(parent, bg=self.colors['bg_primary'])
        status_container.grid(row=0, column=0, sticky='ew', pady=(0, 15))
        self._create_status_section(status_container)

        # Sección de botones
        actions_container = tk.Frame(parent, bg=self.colors['bg_primary'])
        actions_container.grid(row=1, column=0, sticky='ew', pady=(0, 15))
        self._create_action_buttons(actions_container)

        # Espaciador
        spacer = tk.Frame(parent, bg=self.colors['bg_primary'])
        spacer.grid(row=2, column=0, sticky='nsew')

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
        card = self._create_card_frame(parent, "📊 Estado de la Configuración")

        # Grid para estados
        status_grid = tk.Frame(card, bg=self.colors['bg_primary'])
        status_grid.pack(fill='x')

        # Estado de conexión
        conn_frame = tk.Frame(status_grid, bg=self.colors['bg_tertiary'])
        conn_frame.pack(fill='x', pady=(0, 10))

        tk.Label(conn_frame, text="🌐 Conexión:", bg=self.colors['bg_tertiary'],
                 fg=self.colors['text_primary'], font=('Arial', 10)).pack(
            side='left', padx=10, pady=8)

        self.widgets['connection_status'] = tk.Label(
            conn_frame, text="Sin probar", bg=self.colors['bg_tertiary'],
            fg=self.colors['text_secondary'], font=('Arial', 10, 'bold')
        )
        self.widgets['connection_status'].pack(side='right', padx=10, pady=8)

        # Estado de configuración
        config_frame = tk.Frame(status_grid, bg=self.colors['bg_tertiary'])
        config_frame.pack(fill='x')

        tk.Label(config_frame, text="💾 Configuración:", bg=self.colors['bg_tertiary'],
                 fg=self.colors['text_primary'], font=('Arial', 10)).pack(
            side='left', padx=10, pady=8)

        self.widgets['config_status'] = tk.Label(
            config_frame, text="Sin configuración", bg=self.colors['bg_tertiary'],
            fg=self.colors['text_secondary'], font=('Arial', 10, 'bold')
        )
        self.widgets['config_status'].pack(side='right', padx=10, pady=8)

        # Información adicional
        info_frame = tk.Frame(card, bg=self.colors['bg_secondary'])
        info_frame.pack(fill='x', pady=(15, 0))

        info_text = "ℹ️ La configuración se guarda de forma segura y encriptada"
        tk.Label(info_frame, text=info_text, bg=self.colors['bg_secondary'],
                 fg=self.colors['text_secondary'], font=('Arial', 9)).pack(padx=10, pady=8)

    def _create_action_buttons(self, parent):
        """Crea botones de acción"""
        card = self._create_card_frame(parent, "🎮 Acciones")

        # Botón probar conexión
        self.widgets['test_button'] = self._create_styled_button(
            card, "🔍 Probar Conexión",
            self._test_connection, self.colors['info']
        )
        self.widgets['test_button'].pack(fill='x', pady=(0, 10))

        # Botón guardar
        self.widgets['save_button'] = self._create_styled_button(
            card, "💾 Guardar Configuración",
            self._save_configuration, self.colors['success']
        )
        self.widgets['save_button'].pack(fill='x', pady=(0, 10))

        # Botón limpiar
        self.widgets['clear_button'] = self._create_styled_button(
            card, "🗑️ Limpiar Todo",
            self._clear_configuration, self.colors['error']
        )
        self.widgets['clear_button'].pack(fill='x')

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

    def _toggle_password_visibility(self):
        """Alterna visibilidad de contraseña"""
        if self.widgets['show_password_var'].get():
            self.widgets['password_entry'].configure(show='')
        else:
            self.widgets['password_entry'].configure(show='*')

    def _on_provider_change(self):
        """Maneja cambio de proveedor"""
        provider = self.widgets['provider_var'].get()
        if provider == "Personalizado":
            self.widgets['custom_frame'].pack(fill='x', pady=(0, 15))
        else:
            self.widgets['custom_frame'].pack_forget()

        self._update_connection_status("Sin probar", self.colors['text_secondary'])

    def _test_connection(self):
        """Prueba la conexión de email"""
        if self.is_testing:
            messagebox.showwarning("Prueba en Progreso", "Ya se está probando la conexión.")
            return

        if not self._validate_fields():
            return

        self.is_testing = True
        self._update_connection_status("🔄 Probando...", self.colors['warning'])
        self.widgets['test_button'].configure(state='disabled', text='Probando...')

        def test_thread():
            try:
                self._configure_email_service()
                is_connected, message = self.email_service.test_connection()
                self.frame.after(0, lambda: self._handle_test_result(is_connected, message))
            except Exception as e:
                self.frame.after(0, lambda: self._handle_test_result(False, str(e)))

        threading.Thread(target=test_thread, daemon=True).start()

    def _handle_test_result(self, success, message):
        """Maneja resultado del test"""
        self.is_testing = False
        self.widgets['test_button'].configure(state='normal', text='🔍 Probar Conexión')

        if success:
            self._update_connection_status("✅ Conectado", self.colors['success'])
            messagebox.showinfo("Éxito", "¡Conexión exitosa!\n\nEl servidor de correo respondió correctamente.")
        else:
            self._update_connection_status("❌ Error", self.colors['error'])
            messagebox.showerror("Error de Conexión", f"No se pudo conectar:\n\n{message}")

    def _save_configuration(self):
        """Guarda la configuración"""
        if not self._validate_fields():
            return

        if not self._validate_recipients():
            return

        try:
            # Obtener datos limpiando caracteres problemáticos
            provider = self.widgets['provider_var'].get()
            email = self._clean_entry_value(self.widgets['email_entry'])
            password = self._clean_entry_value(self.widgets['password_entry'])
            main_recipient = self._clean_entry_value(self.widgets['main_recipient'])
            cc_recipients = self._clean_text_value(self.widgets['cc_recipients'])

            # Configurar datos de guardado
            config_data = {
                "provider": provider,
                "email": email,
                "password": password,
                "main_recipient": main_recipient,
                "cc_recipients": cc_recipients
            }

            if provider == "Personalizado":
                config_data["smtp_server"] = self._clean_entry_value(self.widgets['smtp_entry'])
                config_data["port"] = int(self._clean_entry_value(self.widgets['port_entry']))

            # Guardar
            success = self.config_manager.save_email_config(config_data)

            if success:
                self._update_config_status("✅ Guardada", self.colors['success'])
                messagebox.showinfo("Éxito",
                                    "¡Configuración guardada correctamente!\n\nEl sistema está listo para enviar correos.")
                self.is_configured = True
            else:
                messagebox.showerror("Error", "No se pudo guardar la configuración")

        except Exception as e:
            messagebox.showerror("Error", f"Error guardando configuración:\n{str(e)}")

    def _clear_configuration(self):
        """Limpia la configuración"""
        if not messagebox.askyesno("Confirmar",
                                   "¿Está seguro de limpiar toda la configuración?\n\n" +
                                   "Se eliminarán todos los datos guardados."):
            return

        try:
            # Limpiar campos
            self.widgets['email_entry'].delete(0, 'end')
            self.widgets['password_entry'].delete(0, 'end')
            self.widgets['smtp_entry'].delete(0, 'end')
            self.widgets['port_entry'].delete(0, 'end')
            self.widgets['port_entry'].insert(0, "587")
            self.widgets['main_recipient'].delete(0, 'end')
            self.widgets['cc_recipients'].delete('1.0', 'end')
            self.widgets['provider_var'].set("Gmail")
            self.widgets['custom_frame'].pack_forget()

            # Limpiar datos guardados
            self.config_manager.clear_email_config()

            # Actualizar estado
            self._update_connection_status("Sin configurar", self.colors['text_secondary'])
            self._update_config_status("Sin configuración", self.colors['text_secondary'])
            self.is_configured = False

            messagebox.showinfo("Éxito", "Configuración eliminada correctamente")

        except Exception as e:
            messagebox.showerror("Error", f"Error limpiando configuración:\n{str(e)}")

    def _validate_fields(self):
        """Valida campos básicos"""
        email = self._clean_entry_value(self.widgets['email_entry'])
        password = self._clean_entry_value(self.widgets['password_entry'])

        if not email:
            messagebox.showerror("Campo Requerido", "El campo email es obligatorio")
            if self.expanded_section != "account":
                self._toggle_section("account")
            self.widgets['email_entry'].focus()
            return False

        if not password:
            messagebox.showerror("Campo Requerido", "El campo contraseña es obligatorio")
            if self.expanded_section != "account":
                self._toggle_section("account")
            self.widgets['password_entry'].focus()
            return False

        if not self.config_manager.validate_email(email):
            messagebox.showerror("Email Inválido", "El formato del email no es válido")
            if self.expanded_section != "account":
                self._toggle_section("account")
            self.widgets['email_entry'].focus()
            return False

        provider = self.widgets['provider_var'].get()
        if provider == "Personalizado":
            smtp = self._clean_entry_value(self.widgets['smtp_entry'])
            port = self._clean_entry_value(self.widgets['port_entry'])

            if not smtp:
                messagebox.showerror("Campo Requerido",
                                     "El servidor SMTP es obligatorio para configuración personalizada")
                if self.expanded_section != "account":
                    self._toggle_section("account")
                self.widgets['smtp_entry'].focus()
                return False

            if not port:
                messagebox.showerror("Campo Requerido",
                                     "El puerto es obligatorio para configuración personalizada")
                if self.expanded_section != "account":
                    self._toggle_section("account")
                self.widgets['port_entry'].focus()
                return False

            try:
                port_num = int(port)
                if port_num < 1 or port_num > 65535:
                    raise ValueError
            except ValueError:
                messagebox.showerror("Puerto Inválido", "El puerto debe ser un número entre 1 y 65535")
                if self.expanded_section != "account":
                    self._toggle_section("account")
                self.widgets['port_entry'].focus()
                return False

        return True

    def _validate_recipients(self):
        """Valida destinatarios"""
        main_recipient = self._clean_entry_value(self.widgets['main_recipient'])

        if not main_recipient:
            messagebox.showerror("Campo Requerido", "El destinatario principal es obligatorio")
            if self.expanded_section != "recipients":
                self._toggle_section("recipients")
            self.widgets['main_recipient'].focus()
            return False

        if not self.config_manager.validate_email(main_recipient):
            messagebox.showerror("Email Inválido", "El destinatario principal tiene formato inválido")
            if self.expanded_section != "recipients":
                self._toggle_section("recipients")
            self.widgets['main_recipient'].focus()
            return False

        # Validar CCs si existen
        cc_text = self._clean_text_value(self.widgets['cc_recipients'])
        if cc_text:
            cc_list = [cc.strip() for cc in cc_text.replace('\n', ',').split(',') if cc.strip()]
            for cc in cc_list:
                if not self.config_manager.validate_email(cc):
                    messagebox.showerror("CC Inválido", f"Email CC inválido: {cc}")
                    if self.expanded_section != "recipients":
                        self._toggle_section("recipients")
                    return False

        return True

    def _configure_email_service(self):
        """Configura el servicio de email"""
        provider = self.widgets['provider_var'].get()
        email = self._clean_entry_value(self.widgets['email_entry'])
        password = self._clean_entry_value(self.widgets['password_entry'])

        if provider == "Personalizado":
            custom_server = self._clean_entry_value(self.widgets['smtp_entry'])
            custom_port = int(self._clean_entry_value(self.widgets['port_entry']))
            self.email_service.set_configuration(provider, email, password, custom_server, custom_port)
        else:
            self.email_service.set_configuration(provider, email, password)

    def _update_connection_status(self, text, color):
        """Actualiza estado de conexión"""
        self.widgets['connection_status'].configure(text=text, fg=color)

    def _update_config_status(self, text, color):
        """Actualiza estado de configuración"""
        self.widgets['config_status'].configure(text=text, fg=color)

    def load_saved_config(self):
        """Carga configuración guardada"""
        try:
            config = self.config_manager.load_email_config()
            if not config:
                self._update_config_status("Sin configuración", self.colors['text_secondary'])
                return

            # Cargar campos
            self.widgets['email_entry'].insert(0, config.get("email", ""))
            self.widgets['password_entry'].insert(0, config.get("password", ""))
            self.widgets['main_recipient'].insert(0, config.get("main_recipient", ""))

            cc_recipients = config.get("cc_recipients", "")
            if cc_recipients:
                self.widgets['cc_recipients'].insert('1.0', cc_recipients.replace(',', '\n'))

            provider = config.get("provider", "Gmail")
            self.widgets['provider_var'].set(provider)

            if provider == "Personalizado":
                self.widgets['custom_frame'].pack(fill='x', pady=(0, 15))
                self.widgets['smtp_entry'].insert(0, config.get("smtp_server", ""))
                self.widgets['port_entry'].delete(0, 'end')
                self.widgets['port_entry'].insert(0, str(config.get("port", 587)))

            self._update_config_status("✅ Cargada", self.colors['success'])
            self.is_configured = True

            # Test silencioso
            self._silent_test()

        except Exception as e:
            print(f"Error cargando config: {e}")
            self._update_config_status("❌ Error", self.colors['error'])

    def _silent_test(self):
        """Test de conexión silencioso"""

        def test():
            try:
                self._configure_email_service()
                success, _ = self.email_service.test_connection()
                self.frame.after(0, lambda: self._update_connection_status(
                    "✅ Conectado" if success else "❌ Desconectado",
                    self.colors['success'] if success else self.colors['error']
                ))
            except:
                self.frame.after(0, lambda: self._update_connection_status(
                    "❌ Error", self.colors['error']
                ))

        threading.Thread(target=test, daemon=True).start()

    def is_email_configured(self):
        """Verifica si email está configurado"""
        return self.is_configured

    def get_configured_recipients(self):
        """Obtiene destinatarios configurados"""
        try:
            main = self._clean_entry_value(self.widgets['main_recipient'])
            cc_text = self._clean_text_value(self.widgets['cc_recipients'])
            cc_list = [cc.strip() for cc in cc_text.replace('\n', ',').split(',') if cc.strip()]
            return main, cc_list
        except:
            return "", []

    def send_email(self, subject, body, attachments=None):
        """Envía un email con la configuración actual y soporte para adjuntos"""
        try:
            if not self.is_configured:
                return False, "Email no configurado"

            main_recipient, cc_recipients = self.get_configured_recipients()
            if not main_recipient:
                return False, "No hay destinatario principal configurado"

            self._configure_email_service()

            # Enviar email con adjuntos si se proporcionan
            return self.email_service.send_email(main_recipient, cc_recipients, subject, body, attachments)

        except Exception as e:
            return False, str(e)