# automation_tab.py
# Ubicación: /syncro_bot/gui/tabs/automation_tab.py
"""
Pestaña de automatización para Syncro Bot con login automático.
Proporciona la interfaz para configurar credenciales y gestionar tareas automatizadas
con login automático usando Selenium, manejo mejorado de hilos, cierre seguro
e integración con sistema de registro.
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import webbrowser
import threading
import time
import json
import os
from datetime import datetime

# Importaciones para encriptación de credenciales
try:
    from cryptography.fernet import Fernet
except ImportError:
    print("Error: La librería 'cryptography' no está instalada.")
    print("Instale con: pip install cryptography")
    raise

# Importaciones para Selenium
try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.chrome.options import Options
    from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException

    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False
    print("Warning: Selenium no está instalado. Funcionalidad de login automático deshabilitada.")
    print("Instale con: pip install selenium")


class CredentialsManager:
    """Gestor de credenciales con encriptación para login automático"""

    def __init__(self):
        self.config_file = "automation_credentials.json"
        self.key_file = "automation.key"

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
        text = text.replace('\xa0', ' ')
        text = text.replace('\u00a0', ' ')
        text = ' '.join(text.split())
        return text.strip()

    def _encrypt_data(self, data):
        """Encripta los datos de credenciales"""
        key = self._get_or_create_key()
        fernet = Fernet(key)

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
        """Desencripta los datos de credenciales"""
        try:
            key = self._get_or_create_key()
            fernet = Fernet(key)
            decrypted_data = fernet.decrypt(encrypted_data)
            return json.loads(decrypted_data.decode('utf-8'))
        except Exception:
            return None

    def save_credentials(self, username, password):
        """Guarda las credenciales encriptadas"""
        try:
            credentials_data = {
                "username": username,
                "password": password,
                "saved_at": datetime.now().isoformat()
            }
            encrypted_data = self._encrypt_data(credentials_data)
            with open(self.config_file, 'wb') as f:
                f.write(encrypted_data)
            return True
        except Exception as e:
            print(f"Error guardando credenciales: {e}")
            return False

    def load_credentials(self):
        """Carga las credenciales desde archivo"""
        try:
            if not os.path.exists(self.config_file):
                return None

            with open(self.config_file, 'rb') as f:
                encrypted_data = f.read()

            return self._decrypt_data(encrypted_data)
        except Exception as e:
            print(f"Error cargando credenciales: {e}")
            return None

    def clear_credentials(self):
        """Elimina las credenciales guardadas"""
        try:
            if os.path.exists(self.config_file):
                os.remove(self.config_file)
            if os.path.exists(self.key_file):
                os.remove(self.key_file)
            return True
        except Exception:
            return False

    def validate_credentials(self, username, password):
        """Valida que las credenciales no estén vacías"""
        username = self._clean_string(username) if username else ""
        password = self._clean_string(password) if password else ""

        if not username:
            return False, "El usuario es obligatorio"
        if not password:
            return False, "La contraseña es obligatoria"
        if len(username) < 2:
            return False, "El usuario debe tener al menos 2 caracteres"
        if len(password) < 3:
            return False, "La contraseña debe tener al menos 3 caracteres"

        return True, "Credenciales válidas"


class AutomationService:
    """Servicio de automatización con login automático usando Selenium"""

    def __init__(self):
        self.is_running = False
        self.target_url = "https://fieldservice.cabletica.com/dispatchFS/"
        self._lock = threading.Lock()
        self.driver = None
        self.credentials_manager = CredentialsManager()

        # XPaths para elementos de login
        self.login_xpaths = {
            'username': '//*[@id="textfield-1039-inputEl"]',
            'password': '//*[@id="textfield-1040-inputEl"]',
            'login_button': '//*[@id="button-1041-btnEl"]'
        }

    def _setup_chrome_driver(self):
        """Configura el driver de Chrome con opciones optimizadas y robustas"""
        try:
            print("[DEBUG] Configurando Chrome driver...")
            chrome_options = Options()

            # Opciones para estabilidad y velocidad
            chrome_options.add_argument("--start-maximized")
            chrome_options.add_argument("--disable-blink-features=AutomationControlled")
            chrome_options.add_argument("--disable-extensions")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--remote-debugging-port=9222")

            # Configuraciones anti-detección
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)

            # Configurar timeouts más largos
            chrome_options.add_argument("--page-load-strategy=normal")

            # Crear driver con timeouts personalizados
            print("[DEBUG] Creando instancia de Chrome driver...")
            driver = webdriver.Chrome(options=chrome_options)

            # Configurar timeouts del driver (aumentados)
            driver.set_page_load_timeout(30)  # 30 segundos para cargar página
            driver.implicitly_wait(10)  # 10 segundos para elementos

            # Script anti-detección
            driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

            print("[DEBUG] Chrome driver configurado exitosamente")
            return driver, True, "Driver de Chrome configurado correctamente"

        except WebDriverException as e:
            error_msg = str(e)
            print(f"[DEBUG] Error WebDriverException: {error_msg}")

            # Mensajes de error más específicos
            if "chromedriver" in error_msg.lower():
                return None, False, "ChromeDriver no encontrado. Instale ChromeDriver y asegúrese que esté en PATH"
            elif "chrome" in error_msg.lower():
                return None, False, "Google Chrome no encontrado. Instale Google Chrome"
            else:
                return None, False, f"Error configurando Chrome: {error_msg}"

        except Exception as e:
            print(f"[DEBUG] Error general: {str(e)}")
            return None, False, f"Error inesperado con Selenium: {str(e)}"

    def _perform_login(self, driver, username, password):
        """Realiza el proceso de login automático con esperas robustas"""
        try:
            # Navegar a la página
            print(f"[DEBUG] Navegando a: {self.target_url}")
            driver.get(self.target_url)

            # Esperar que la página cargue completamente (aumentado a 25 segundos)
            wait = WebDriverWait(driver, 25)

            # Esperar a que el DOM esté completamente cargado
            wait.until(lambda d: d.execute_script("return document.readyState") == "complete")
            print("[DEBUG] Página cargada completamente")

            # Espera adicional para elementos dinámicos
            time.sleep(2)

            # Buscar y llenar campo de usuario con múltiples intentos
            print("[DEBUG] Buscando campo de usuario...")
            username_field = wait.until(
                EC.element_to_be_clickable((By.XPATH, self.login_xpaths['username']))
            )

            # Esperar a que el campo esté completamente listo
            time.sleep(1)
            username_field.clear()
            time.sleep(0.5)
            username_field.send_keys(username)
            print(f"[DEBUG] Usuario ingresado: {username}")

            # Espera entre campos
            time.sleep(1)

            # Buscar y llenar campo de contraseña
            print("[DEBUG] Buscando campo de contraseña...")
            password_field = wait.until(
                EC.element_to_be_clickable((By.XPATH, self.login_xpaths['password']))
            )

            time.sleep(1)
            password_field.clear()
            time.sleep(0.5)
            password_field.send_keys(password)
            print("[DEBUG] Contraseña ingresada")

            # Espera antes de hacer click en login
            time.sleep(2)

            # Buscar botón de login y asegurar que esté clickeable
            print("[DEBUG] Buscando botón de login...")
            login_button = wait.until(
                EC.element_to_be_clickable((By.XPATH, self.login_xpaths['login_button']))
            )

            # Scroll al botón si es necesario
            driver.execute_script("arguments[0].scrollIntoView(true);", login_button)
            time.sleep(1)

            # Hacer clic en el botón de login
            print("[DEBUG] Haciendo clic en botón de login...")
            login_button.click()

            # Esperar más tiempo para que procese el login (aumentado a 8 segundos)
            print("[DEBUG] Esperando respuesta del servidor...")
            time.sleep(8)

            # Verificar resultado del login con múltiples métodos
            return self._verify_login_success(driver, wait)

        except TimeoutException:
            current_url = driver.current_url if driver else "N/A"
            return False, f"Timeout: No se encontraron los elementos de login. URL actual: {current_url}"
        except NoSuchElementException:
            return False, "No se encontraron los campos de login en la página"
        except Exception as e:
            return False, f"Error durante el login: {str(e)}"

    def _verify_login_success(self, driver, wait):
        """Verifica si el login fue exitoso con múltiples métodos"""
        try:
            current_url = driver.current_url
            print(f"[DEBUG] URL después del login: {current_url}")

            # Método 1: Verificar cambio de URL
            if current_url != self.target_url and "login" not in current_url.lower():
                print("[DEBUG] Login exitoso - URL cambió")
                return True, "Login exitoso - Redirigido correctamente"

            # Método 2: Buscar elementos que indiquen login exitoso
            try:
                # Buscar elementos comunes de dashboard/panel principal
                success_indicators = [
                    "//*[@id='main']",
                    "//*[@class='dashboard']",
                    "//*[@class='main-content']",
                    "//*[contains(@class, 'workspace')]",
                    "//*[contains(@class, 'panel')]",
                    "//*[contains(text(), 'Dashboard')]",
                    "//*[contains(text(), 'Bienvenido')]",
                    "//*[contains(text(), 'Menu')]"
                ]

                for indicator in success_indicators:
                    try:
                        element = WebDriverWait(driver, 3).until(
                            EC.presence_of_element_located((By.XPATH, indicator))
                        )
                        if element:
                            print(f"[DEBUG] Login exitoso - Encontrado elemento: {indicator}")
                            return True, "Login exitoso - Panel principal cargado"
                    except:
                        continue

            except Exception as e:
                print(f"[DEBUG] Error buscando indicadores de éxito: {e}")

            # Método 3: Verificar si hay mensajes de error
            try:
                error_indicators = [
                    "//*[contains(text(), 'error')]",
                    "//*[contains(text(), 'Error')]",
                    "//*[contains(text(), 'incorrecto')]",
                    "//*[contains(text(), 'inválido')]",
                    "//*[contains(text(), 'credenciales')]",
                    "//*[contains(@class, 'error')]",
                    "//*[contains(@class, 'alert')]"
                ]

                for error_xpath in error_indicators:
                    error_elements = driver.find_elements(By.XPATH, error_xpath)
                    if error_elements:
                        error_text = error_elements[0].text
                        print(f"[DEBUG] Error encontrado: {error_text}")
                        return False, f"Login fallido - Error detectado: {error_text}"

            except Exception as e:
                print(f"[DEBUG] Error buscando mensajes de error: {e}")

            # Método 4: Esperar más tiempo y verificar de nuevo
            print("[DEBUG] Esperando más tiempo para verificar login...")
            time.sleep(5)

            final_url = driver.current_url
            print(f"[DEBUG] URL final después de espera adicional: {final_url}")

            if final_url != self.target_url and "login" not in final_url.lower():
                return True, "Login exitoso después de espera adicional"

            # Método 5: Verificar título de la página
            try:
                page_title = driver.title.lower()
                print(f"[DEBUG] Título de la página: {page_title}")

                if "login" not in page_title and page_title:
                    return True, f"Login exitoso - Título de página: {driver.title}"

            except Exception as e:
                print(f"[DEBUG] Error obteniendo título: {e}")

            # Si llegamos aquí, probablemente el login falló
            return False, "No se pudo verificar login exitoso - Posibles credenciales incorrectas"

        except Exception as e:
            return False, f"Error verificando login: {str(e)}"

    def start_automation(self, username=None, password=None):
        """Inicia el proceso de automatización con login automático y logging detallado"""
        try:
            with self._lock:
                if self.is_running:
                    return False, "La automatización ya está en ejecución"

                if not SELENIUM_AVAILABLE:
                    # Fallback al método original si Selenium no está disponible
                    print("[DEBUG] Selenium no disponible, usando método básico")
                    webbrowser.open(self.target_url)
                    self.is_running = True
                    return True, "Automatización iniciada (modo básico - sin login automático)"

                # Verificar credenciales
                if not username or not password:
                    print("[DEBUG] Cargando credenciales desde archivo...")
                    credentials = self.credentials_manager.load_credentials()
                    if not credentials:
                        return False, "No hay credenciales configuradas para el login automático"
                    username = credentials.get('username')
                    password = credentials.get('password')

                # Validar credenciales
                print("[DEBUG] Validando credenciales...")
                valid, message = self.credentials_manager.validate_credentials(username, password)
                if not valid:
                    return False, f"Credenciales inválidas: {message}"

                print("[DEBUG] Iniciando proceso de automatización...")

                # Configurar driver
                print("[DEBUG] Configurando navegador...")
                driver, success, setup_message = self._setup_chrome_driver()
                if not success:
                    return False, setup_message

                self.driver = driver
                print("[DEBUG] Navegador configurado, iniciando login...")

                # Realizar login con logging detallado
                login_success, login_message = self._perform_login(driver, username, password)
                if not login_success:
                    print(f"[DEBUG] Login falló: {login_message}")
                    self._cleanup_driver()
                    return False, login_message

                print(f"[DEBUG] Login exitoso: {login_message}")
                self.is_running = True
                return True, f"Automatización con login automático iniciada exitosamente: {login_message}"

        except Exception as e:
            print(f"[DEBUG] Excepción en start_automation: {str(e)}")
            self._cleanup_driver()
            return False, f"Error al iniciar automatización: {str(e)}"

    def pause_automation(self):
        """Pausa el proceso de automatización"""
        try:
            with self._lock:
                if not self.is_running:
                    return False, "La automatización no está en ejecución"

                self._cleanup_driver()
                self.is_running = False
                return True, "Automatización pausada correctamente"

        except Exception as e:
            return False, f"Error al pausar automatización: {str(e)}"

    def _cleanup_driver(self):
        """Limpia el driver de Selenium"""
        try:
            if self.driver:
                self.driver.quit()
                self.driver = None
        except Exception as e:
            print(f"Error limpiando driver: {e}")

    def get_status(self):
        """Obtiene el estado actual de la automatización"""
        with self._lock:
            return self.is_running

    def stop_all(self):
        """Detiene todas las operaciones de automatización"""
        with self._lock:
            self._cleanup_driver()
            self.is_running = False

    def test_credentials(self, username, password):
        """Prueba las credenciales sin iniciar la automatización completa con logging detallado"""
        try:
            if not SELENIUM_AVAILABLE:
                return False, "Selenium no está disponible para probar credenciales"

            # Validar formato de credenciales
            valid, message = self.credentials_manager.validate_credentials(username, password)
            if not valid:
                return False, message

            print("[DEBUG] Iniciando prueba de credenciales...")

            # Configurar driver temporal
            driver, success, setup_message = self._setup_chrome_driver()
            if not success:
                return False, setup_message

            try:
                print("[DEBUG] Driver configurado, probando login...")
                # Realizar prueba de login con la lógica mejorada
                login_success, login_message = self._perform_login(driver, username, password)

                if login_success:
                    print("[DEBUG] Prueba de credenciales exitosa")
                else:
                    print(f"[DEBUG] Prueba de credenciales falló: {login_message}")

                return login_success, login_message
            finally:
                # Limpiar driver temporal
                try:
                    print("[DEBUG] Cerrando navegador de prueba...")
                    driver.quit()
                except:
                    pass

        except Exception as e:
            print(f"[DEBUG] Error probando credenciales: {str(e)}")
            return False, f"Error probando credenciales: {str(e)}"


class AutomationTab:
    """Pestaña de automatización para Syncro Bot con login automático"""

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

        self.automation_service = AutomationService()
        self.credentials_manager = CredentialsManager()
        self.widgets = {}
        self._is_closing = False

        # Variables para registro de ejecuciones
        self.current_execution_record = None
        self.execution_start_time = None
        self.registry_tab = None

        # Estado de secciones colapsables
        self.expanded_section = None
        self.section_frames = {}

        self.create_tab()
        self.load_saved_credentials()

    def set_registry_tab(self, registry_tab):
        """Establece la referencia al RegistroTab para logging"""
        self.registry_tab = registry_tab

    def create_tab(self):
        """Crear la pestaña de automatización"""
        self.frame = ttk.Frame(self.parent)
        self.parent.add(self.frame, text="Automatización")
        self.create_interface()

    def create_interface(self):
        """Crea la interfaz con diseño de 2 columnas"""
        main_container = tk.Frame(self.frame, bg=self.colors['bg_primary'])
        main_container.pack(fill='both', expand=True, padx=15, pady=10)

        main_container.grid_columnconfigure(0, weight=0, minsize=500)
        main_container.grid_columnconfigure(1, weight=0, minsize=1)
        main_container.grid_columnconfigure(2, weight=1, minsize=350)
        main_container.grid_rowconfigure(0, weight=1)

        left_column = tk.Frame(main_container, bg=self.colors['bg_primary'], width=500)
        left_column.grid(row=0, column=0, sticky='ns', padx=(0, 5))
        left_column.grid_propagate(False)

        separator = tk.Frame(main_container, bg=self.colors['border'], width=1)
        separator.grid(row=0, column=1, sticky='ns', padx=5)

        right_column = tk.Frame(main_container, bg=self.colors['bg_primary'])
        right_column.grid(row=0, column=2, sticky='nsew', padx=(5, 0))

        self._create_left_column(left_column)
        self._create_right_column(right_column)

    def _create_left_column(self, parent):
        """Crea la columna izquierda con secciones colapsables"""
        parent.grid_rowconfigure(0, weight=0)  # Credenciales
        parent.grid_rowconfigure(1, weight=0)  # Estado del sistema
        parent.grid_rowconfigure(2, weight=0)  # Controles
        parent.grid_rowconfigure(3, weight=1)  # Espaciador
        parent.grid_columnconfigure(0, weight=1)

        # Sección de credenciales (expandida por defecto)
        self._create_collapsible_section(
            parent, "credentials", "🔐 Credenciales de Login",
            self._create_credentials_section, row=0, default_expanded=True,
            min_height=200
        )

        # Sección de estado del sistema
        self._create_collapsible_section(
            parent, "status", "📊 Estado del Sistema",
            self._create_status_section, row=1, default_expanded=False,
            min_height=150
        )

        # Sección de controles
        self._create_collapsible_section(
            parent, "controls", "🎮 Controles de Automatización",
            self._create_controls_section, row=2, default_expanded=False,
            min_height=180
        )

    def _create_right_column(self, parent):
        """Crea el contenido de la columna derecha con log"""
        parent.grid_rowconfigure(0, weight=1)
        parent.grid_columnconfigure(0, weight=1)

        log_container = tk.Frame(parent, bg=self.colors['bg_primary'])
        log_container.grid(row=0, column=0, sticky='nsew')
        self._create_log_section(log_container)

    def _create_collapsible_section(self, parent, section_id, title, content_creator,
                                    row, default_expanded=False, min_height=150):
        """Crea una sección colapsable tipo acordeón"""
        section_container = tk.Frame(parent, bg=self.colors['bg_primary'])
        section_container.configure(height=55)
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

        # Estado inicial
        if default_expanded:
            content_frame.grid(row=1, column=0, sticky='ew')
            arrow_label.configure(text="▼")
            self.section_frames[section_id]['expanded'] = True
            section_container.configure(height=min_height)
            section_container.grid_propagate(True)
            self.expanded_section = section_id

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

    def _create_credentials_section(self, container):
        """Crea sección de credenciales de login"""
        content = tk.Frame(container, bg=self.colors['bg_primary'])
        content.pack(fill='x', padx=18, pady=15)

        # Usuario
        tk.Label(content, text="👤 Usuario:", bg=self.colors['bg_primary'],
                 fg=self.colors['text_primary'], font=('Arial', 10, 'bold')).pack(anchor='w', pady=(0, 5))

        self.widgets['username_entry'] = self._create_styled_entry(content)
        self.widgets['username_entry'].pack(fill='x', pady=(0, 15))

        # Contraseña
        tk.Label(content, text="🔒 Contraseña:", bg=self.colors['bg_primary'],
                 fg=self.colors['text_primary'], font=('Arial', 10, 'bold')).pack(anchor='w', pady=(0, 5))

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

        # Botones de credenciales
        buttons_frame = tk.Frame(content, bg=self.colors['bg_primary'])
        buttons_frame.pack(fill='x')

        buttons_frame.grid_columnconfigure(0, weight=1)
        buttons_frame.grid_columnconfigure(1, weight=1)
        buttons_frame.grid_columnconfigure(2, weight=1)

        # Botón probar credenciales
        self.widgets['test_credentials_button'] = self._create_styled_button(
            buttons_frame, "🔍 Probar", self._test_credentials, self.colors['info']
        )
        self.widgets['test_credentials_button'].grid(row=0, column=0, sticky='ew', padx=(0, 5))

        # Botón guardar credenciales
        self.widgets['save_credentials_button'] = self._create_styled_button(
            buttons_frame, "💾 Guardar", self._save_credentials, self.colors['success']
        )
        self.widgets['save_credentials_button'].grid(row=0, column=1, sticky='ew', padx=2.5)

        # Botón limpiar credenciales
        self.widgets['clear_credentials_button'] = self._create_styled_button(
            buttons_frame, "🗑️ Limpiar", self._clear_credentials, self.colors['error']
        )
        self.widgets['clear_credentials_button'].grid(row=0, column=2, sticky='ew', padx=(5, 0))

        # Estado de Selenium
        selenium_status_frame = tk.Frame(content, bg=self.colors['bg_secondary'])
        selenium_status_frame.pack(fill='x', pady=(15, 0))

        selenium_text = "🤖 Selenium:" if SELENIUM_AVAILABLE else "⚠️ Selenium:"
        tk.Label(selenium_status_frame, text=selenium_text, bg=self.colors['bg_secondary'],
                 fg=self.colors['text_primary'], font=('Arial', 9)).pack(side='left', padx=10, pady=8)

        selenium_status = "✅ Disponible (Login automático)" if SELENIUM_AVAILABLE else "❌ No disponible (Solo navegador)"
        selenium_color = self.colors['success'] if SELENIUM_AVAILABLE else self.colors['warning']

        tk.Label(selenium_status_frame, text=selenium_status, bg=self.colors['bg_secondary'],
                 fg=selenium_color, font=('Arial', 9, 'bold')).pack(side='right', padx=10, pady=8)

    def _create_status_section(self, container):
        """Crea sección de estado del sistema"""
        content = tk.Frame(container, bg=self.colors['bg_primary'])
        content.pack(fill='x', padx=18, pady=15)

        status_frame = tk.Frame(content, bg=self.colors['bg_tertiary'])
        status_frame.pack(fill='x', pady=(0, 10))

        tk.Label(status_frame, text="🤖 Automatización:", bg=self.colors['bg_tertiary'],
                 fg=self.colors['text_primary'], font=('Arial', 10)).pack(
            side='left', padx=10, pady=8)

        self.widgets['automation_status'] = tk.Label(
            status_frame, text="Detenida", bg=self.colors['bg_tertiary'],
            fg=self.colors['text_secondary'], font=('Arial', 10, 'bold')
        )
        self.widgets['automation_status'].pack(side='right', padx=10, pady=8)

        url_frame = tk.Frame(content, bg=self.colors['bg_tertiary'])
        url_frame.pack(fill='x')

        tk.Label(url_frame, text="🌐 URL Objetivo:", bg=self.colors['bg_tertiary'],
                 fg=self.colors['text_primary'], font=('Arial', 10)).pack(
            side='left', padx=10, pady=8)

        self.widgets['url_status'] = tk.Label(
            url_frame, text="Cabletica Dispatch", bg=self.colors['bg_tertiary'],
            fg=self.colors['info'], font=('Arial', 10, 'bold')
        )
        self.widgets['url_status'].pack(side='right', padx=10, pady=8)

    def _create_controls_section(self, container):
        """Crea sección de controles"""
        content = tk.Frame(container, bg=self.colors['bg_primary'])
        content.pack(fill='x', padx=18, pady=15)

        self.widgets['start_button'] = self._create_styled_button(
            content, "▶️ Iniciar Automatización con Login",
            self._start_automation, self.colors['success']
        )
        self.widgets['start_button'].pack(fill='x', pady=(0, 15))

        self.widgets['pause_button'] = self._create_styled_button(
            content, "⏸️ Pausar Automatización",
            self._pause_automation, self.colors['warning']
        )
        self.widgets['pause_button'].pack(fill='x')
        self.widgets['pause_button'].configure(state='disabled')

    def _create_log_section(self, parent):
        """Crea sección de log"""
        card = self._create_card_frame(parent, "📋 Log de Actividades")

        # Área de texto con scroll
        self.widgets['log_text'] = scrolledtext.ScrolledText(
            card,
            bg=self.colors['bg_tertiary'],
            fg=self.colors['text_primary'],
            font=('Consolas', 9),
            relief='flat',
            wrap=tk.WORD,
            state=tk.DISABLED
        )
        self.widgets['log_text'].pack(fill='both', expand=True, pady=(0, 10))

        # Botón para limpiar log
        clear_log_btn = self._create_styled_button(
            card, "🗑️ Limpiar Log",
            self._clear_log, self.colors['text_secondary']
        )
        clear_log_btn.pack(fill='x')

        # Agregar mensaje inicial al log
        self._add_log_entry("🚀 Sistema de automatización con login automático iniciado")
        self._add_log_entry("🔧 Configuración: Esperas robustas y detección inteligente de carga")
        if SELENIUM_AVAILABLE:
            self._add_log_entry("✅ Selenium disponible - Login automático habilitado")
        else:
            self._add_log_entry("⚠️ Selenium no disponible - Solo modo navegador básico")

    def _create_card_frame(self, parent, title):
        """Crea un frame tipo tarjeta"""
        container = tk.Frame(parent, bg=self.colors['bg_primary'])
        container.pack(fill='both', expand=True)

        card = tk.Frame(container, bg=self.colors['bg_primary'], relief='solid', bd=1)
        card.configure(highlightbackground=self.colors['border'],
                       highlightcolor=self.colors['border'],
                       highlightthickness=1)
        card.pack(fill='both', expand=True)

        # Header
        header = tk.Frame(card, bg=self.colors['bg_secondary'], height=45)
        header.pack(fill='x')
        header.pack_propagate(False)

        tk.Label(header, text=title, bg=self.colors['bg_secondary'],
                 fg=self.colors['text_primary'], font=('Arial', 12, 'bold')).pack(
            side='left', padx=15, pady=12)

        # Content area
        content = tk.Frame(card, bg=self.colors['bg_primary'])
        content.pack(fill='both', expand=True, padx=18, pady=15)

        return content

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

    def _get_credentials_from_form(self):
        """Obtiene credenciales limpias del formulario"""
        username = self.widgets['username_entry'].get().strip()
        password = self.widgets['password_entry'].get().strip()
        return username, password

    def _test_credentials(self):
        """Prueba las credenciales ingresadas con logging detallado en UI"""
        if not SELENIUM_AVAILABLE:
            messagebox.showwarning("Selenium No Disponible",
                                   "No se pueden probar las credenciales sin Selenium.\n\n" +
                                   "Instale Selenium para usar esta funcionalidad:\n" +
                                   "pip install selenium")
            return

        username, password = self._get_credentials_from_form()

        if not username or not password:
            messagebox.showerror("Credenciales Incompletas", "Debe ingresar usuario y contraseña")
            return

        self._add_log_entry("🔍 Iniciando prueba de credenciales...")
        self.widgets['test_credentials_button'].configure(state='disabled', text='Probando...')

        def test_thread():
            try:
                # Logging paso a paso en la UI
                self.frame.after(0, lambda: self._add_log_entry("🔧 Configurando navegador para prueba..."))
                self.frame.after(100, lambda: self._add_log_entry("🌐 Navegando a página de login..."))
                self.frame.after(200, lambda: self._add_log_entry("⏳ Esperando carga completa de página..."))
                self.frame.after(300, lambda: self._add_log_entry("👤 Ingresando credenciales..."))
                self.frame.after(400, lambda: self._add_log_entry("🔐 Verificando login..."))

                success, message = self.automation_service.test_credentials(username, password)

                self.frame.after(0, lambda: self._handle_test_credentials_result(success, message))
            except Exception as e:
                self.frame.after(0, lambda: self._handle_test_credentials_result(False, str(e)))

        threading.Thread(target=test_thread, daemon=True).start()

    def _handle_test_credentials_result(self, success, message):
        """Maneja resultado de prueba de credenciales"""
        self.widgets['test_credentials_button'].configure(state='normal', text='🔍 Probar')

        if success:
            self._add_log_entry("✅ Credenciales verificadas correctamente")
            messagebox.showinfo("Credenciales Válidas", f"¡Credenciales correctas!\n\n{message}")
        else:
            self._add_log_entry(f"❌ Error en credenciales: {message}")
            messagebox.showerror("Credenciales Inválidas", f"Error verificando credenciales:\n\n{message}")

    def _save_credentials(self):
        """Guarda las credenciales"""
        username, password = self._get_credentials_from_form()

        # Validar credenciales
        valid, message = self.credentials_manager.validate_credentials(username, password)
        if not valid:
            messagebox.showerror("Credenciales Inválidas", message)
            return

        success = self.credentials_manager.save_credentials(username, password)

        if success:
            self._add_log_entry("💾 Credenciales guardadas de forma segura")
            messagebox.showinfo("Éxito", "Credenciales guardadas correctamente de forma encriptada")
        else:
            self._add_log_entry("❌ Error guardando credenciales")
            messagebox.showerror("Error", "No se pudieron guardar las credenciales")

    def _clear_credentials(self):
        """Limpia las credenciales"""
        if messagebox.askyesno("Confirmar", "¿Eliminar todas las credenciales guardadas?"):
            self.widgets['username_entry'].delete(0, 'end')
            self.widgets['password_entry'].delete(0, 'end')

            self.credentials_manager.clear_credentials()
            self._add_log_entry("🗑️ Credenciales eliminadas")
            messagebox.showinfo("Éxito", "Credenciales eliminadas correctamente")

    def _add_log_entry(self, message, level="INFO"):
        """Añade una entrada al log"""
        if self._is_closing or 'log_text' not in self.widgets:
            return

        try:
            timestamp = datetime.now().strftime("%H:%M:%S")
            log_entry = f"[{timestamp}] {level}: {message}\n"

            self.widgets['log_text'].configure(state=tk.NORMAL)
            self.widgets['log_text'].insert(tk.END, log_entry)
            self.widgets['log_text'].configure(state=tk.DISABLED)
            self.widgets['log_text'].see(tk.END)
        except:
            pass

    def _clear_log(self):
        """Limpia el contenido del log"""
        if self._is_closing or 'log_text' not in self.widgets:
            return

        try:
            self.widgets['log_text'].configure(state=tk.NORMAL)
            self.widgets['log_text'].delete(1.0, tk.END)
            self.widgets['log_text'].configure(state=tk.DISABLED)
            self._add_log_entry("Log limpiado")
        except:
            pass

    def _start_automation(self):
        """Inicia la automatización con login automático"""
        if self._is_closing:
            return

        # Verificar credenciales
        username, password = self._get_credentials_from_form()
        if not username or not password:
            # Intentar cargar credenciales guardadas
            credentials = self.credentials_manager.load_credentials()
            if not credentials:
                messagebox.showerror("Credenciales Requeridas",
                                     "Debe configurar credenciales antes de iniciar la automatización")
                return
            username = credentials.get('username')
            password = credentials.get('password')

        def start_thread():
            try:
                if self._is_closing:
                    return

                self._add_log_entry("Iniciando automatización con login automático...")

                # Registrar inicio de ejecución
                if self.registry_tab:
                    try:
                        self.execution_start_time = datetime.now()
                        self.current_execution_record = self.registry_tab.add_execution_record(
                            start_time=self.execution_start_time,
                            profile_name="Manual (Con Login)",
                            user_type="Usuario"
                        )
                        self._add_log_entry(f"Registro de ejecución creado: ID {self.current_execution_record['id']}")
                    except Exception as e:
                        self._add_log_entry(f"Error creando registro: {str(e)}", "WARNING")

                # Agregar logging detallado paso a paso
                self._add_log_entry("📋 Verificando credenciales...")
                self._add_log_entry("🔧 Configurando navegador Chrome...")
                self._add_log_entry("🌐 Navegando a página de login...")
                self._add_log_entry("⏳ Esperando que la página cargue completamente...")

                success, message = self.automation_service.start_automation(username, password)

                # Agregar más contexto al mensaje
                if success:
                    self._add_log_entry("✅ Login automático completado exitosamente")
                    self._add_log_entry("🎮 Navegador listo para automatización")
                else:
                    self._add_log_entry(f"❌ Error en login: {message}", "ERROR")

                if not self._is_closing:
                    self.frame.after(0, lambda: self._handle_start_result(success, message))
            except Exception as e:
                if not self._is_closing:
                    self.frame.after(0, lambda: self._handle_start_result(False, str(e)))

        thread = threading.Thread(target=start_thread, daemon=True)
        thread.start()
        self.widgets['start_button'].configure(state='disabled', text='Iniciando...')

    def _pause_automation(self):
        """Pausa la automatización"""
        if self._is_closing:
            return

        try:
            self._add_log_entry("Pausando automatización...")
            success, message = self.automation_service.pause_automation()

            if success:
                self._update_automation_status("Pausada", self.colors['warning'])
                self.widgets['start_button'].configure(state='normal', text='▶️ Iniciar Automatización con Login')
                self.widgets['pause_button'].configure(state='disabled')
                self._add_log_entry("Automatización pausada exitosamente")

                # Actualizar registro como exitoso
                if self.registry_tab and self.current_execution_record:
                    try:
                        end_time = datetime.now()
                        self.registry_tab.update_execution_record(
                            record_id=self.current_execution_record['id'],
                            end_time=end_time,
                            status="Exitoso",
                            error_message=""
                        )
                        self._add_log_entry(f"Registro actualizado: Ejecutado exitosamente")
                        self.current_execution_record = None
                        self.execution_start_time = None
                    except Exception as e:
                        self._add_log_entry(f"Error actualizando registro: {str(e)}", "WARNING")

                if not self._is_closing:
                    messagebox.showinfo("Éxito", message)
            else:
                self._update_automation_status("Error", self.colors['error'])
                self._add_log_entry(f"Error al pausar: {message}", "ERROR")

                # Actualizar registro como fallido
                if self.registry_tab and self.current_execution_record:
                    try:
                        end_time = datetime.now()
                        self.registry_tab.update_execution_record(
                            record_id=self.current_execution_record['id'],
                            end_time=end_time,
                            status="Fallido",
                            error_message=message
                        )
                        self._add_log_entry(f"Registro actualizado: Falla al pausar")
                        self.current_execution_record = None
                        self.execution_start_time = None
                    except Exception as e:
                        self._add_log_entry(f"Error actualizando registro: {str(e)}", "WARNING")

                if not self._is_closing:
                    messagebox.showerror("Error", message)
        except Exception as e:
            error_msg = str(e)
            self._add_log_entry(f"Excepción al pausar: {error_msg}", "ERROR")

            # Actualizar registro con la excepción
            if self.registry_tab and self.current_execution_record:
                try:
                    end_time = datetime.now()
                    self.registry_tab.update_execution_record(
                        record_id=self.current_execution_record['id'],
                        end_time=end_time,
                        status="Fallido",
                        error_message=f"Excepción: {error_msg}"
                    )
                    self._add_log_entry(f"Registro actualizado: Excepción capturada")
                    self.current_execution_record = None
                    self.execution_start_time = None
                except Exception as reg_error:
                    self._add_log_entry(f"Error actualizando registro: {str(reg_error)}", "WARNING")

            if not self._is_closing:
                messagebox.showerror("Error", f"Error al pausar automatización:\n{error_msg}")

    def _handle_start_result(self, success, message):
        """Maneja el resultado del inicio de automatización"""
        if self._is_closing:
            return

        if success:
            self._update_automation_status("En ejecución", self.colors['success'])
            self.widgets['start_button'].configure(state='disabled', text='▶️ Iniciando...')
            self.widgets['pause_button'].configure(state='normal')
            self._add_log_entry("Automatización iniciada exitosamente")

            if SELENIUM_AVAILABLE:
                self._add_log_entry("Login automático completado - Navegador controlado por Selenium")
            else:
                self._add_log_entry("Página web abierta en el navegador (modo básico)")

            # El registro ya se creó en _start_automation
            if self.registry_tab and self.current_execution_record:
                self._add_log_entry("Esperando finalización para completar registro...")

            display_message = f"{message}\n\n"
            if SELENIUM_AVAILABLE:
                display_message += "🎯 Características avanzadas activas:\n"
                display_message += "• Login automático completado\n"
                display_message += "• Esperas robustas implementadas\n"
                display_message += "• Detección inteligente de carga\n"
                display_message += "• Navegador controlado automáticamente\n\n"
                display_message += "💡 El navegador permanecerá abierto para continuar la automatización."
            else:
                display_message += "La página web se ha abierto en su navegador (modo básico)."

            messagebox.showinfo("Éxito", display_message)
        else:
            self._update_automation_status("Error", self.colors['error'])
            self.widgets['start_button'].configure(state='normal', text='▶️ Iniciar Automatización con Login')
            self.widgets['pause_button'].configure(state='disabled')
            self._add_log_entry(f"Error al iniciar: {message}", "ERROR")

            # Actualizar registro como fallido
            if self.registry_tab and self.current_execution_record:
                try:
                    end_time = datetime.now()
                    self.registry_tab.update_execution_record(
                        record_id=self.current_execution_record['id'],
                        end_time=end_time,
                        status="Fallido",
                        error_message=message
                    )
                    self._add_log_entry(f"Registro actualizado: Falla al iniciar")
                    self.current_execution_record = None
                    self.execution_start_time = None
                except Exception as e:
                    self._add_log_entry(f"Error actualizando registro: {str(e)}", "WARNING")

            messagebox.showerror("Error", message)

    def _update_automation_status(self, text, color):
        """Actualiza el estado de la automatización"""
        if not self._is_closing and hasattr(self, 'widgets') and 'automation_status' in self.widgets:
            try:
                self.widgets['automation_status'].configure(text=text, fg=color)
            except:
                pass

    def load_saved_credentials(self):
        """Carga credenciales guardadas al iniciar"""
        try:
            credentials = self.credentials_manager.load_credentials()
            if credentials:
                self.widgets['username_entry'].insert(0, credentials.get('username', ''))
                self.widgets['password_entry'].insert(0, credentials.get('password', ''))
                self._add_log_entry("Credenciales cargadas desde archivo seguro")
        except Exception as e:
            self._add_log_entry(f"Error cargando credenciales: {e}", "WARNING")

    def get_automation_status(self):
        """Obtiene el estado actual de la automatización"""
        return self.automation_service.get_status()

    def cleanup(self):
        """Limpia recursos al cerrar la pestaña"""
        self._is_closing = True
        self._add_log_entry("Cerrando sistema...")

        # Si hay una ejecución en curso, marcarla como interrumpida
        if self.registry_tab and self.current_execution_record:
            try:
                end_time = datetime.now()
                self.registry_tab.update_execution_record(
                    record_id=self.current_execution_record['id'],
                    end_time=end_time,
                    status="Fallido",
                    error_message="Ejecución interrumpida por cierre de aplicación"
                )
                self._add_log_entry("Registro actualizado: Ejecución interrumpida")
            except Exception as e:
                self._add_log_entry(f"Error finalizando registro: {str(e)}", "WARNING")

        self.automation_service.stop_all()
        time.sleep(0.05)  # Pequeña pausa para que los hilos terminen