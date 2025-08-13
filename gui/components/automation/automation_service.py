# automation_service.py
# Ubicación: /syncro_bot/gui/components/automation/automation_service.py
"""
Servicio de automatización con login automático usando Selenium.
Maneja la configuración del navegador, proceso de login automático,
verificación de credenciales y control del driver de Chrome.
"""

import threading
import time
import webbrowser

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

from .credentials_manager import CredentialsManager


class AutomationService:
    """Servicio de automatización con login automático usando Selenium"""

    def __init__(self, logger=None):
        self.is_running = False
        self.target_url = "https://fieldservice.cabletica.com/dispatchFS/"
        self._lock = threading.Lock()
        self.driver = None
        self.credentials_manager = CredentialsManager()
        self.logger = logger

        # XPaths para elementos de login
        self.login_xpaths = {
            'username': '//*[@id="textfield-1039-inputEl"]',
            'password': '//*[@id="textfield-1040-inputEl"]',
            'login_button': '//*[@id="button-1041-btnEl"]'
        }

        # Configuración de timeouts
        self.page_load_timeout = 30
        self.element_wait_timeout = 25
        self.implicit_wait_timeout = 10

    def _log(self, message, level="INFO"):
        """Log interno con fallback"""
        if self.logger:
            self.logger(message, level)
        else:
            print(f"[{level}] {message}")

    def is_selenium_available(self):
        """Verifica si Selenium está disponible"""
        return SELENIUM_AVAILABLE

    def set_target_url(self, url):
        """Establece la URL objetivo"""
        self.target_url = url

    def get_target_url(self):
        """Obtiene la URL objetivo actual"""
        return self.target_url

    def _setup_chrome_driver(self):
        """Configura el driver de Chrome con opciones optimizadas y robustas"""
        try:
            self._log("Configurando Chrome driver...")
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
            self._log("Creando instancia de Chrome driver...")
            driver = webdriver.Chrome(options=chrome_options)

            # Configurar timeouts del driver
            driver.set_page_load_timeout(self.page_load_timeout)
            driver.implicitly_wait(self.implicit_wait_timeout)

            # Script anti-detección
            driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

            self._log("Chrome driver configurado exitosamente")
            return driver, True, "Driver de Chrome configurado correctamente"

        except WebDriverException as e:
            error_msg = str(e)
            self._log(f"Error WebDriverException: {error_msg}", "ERROR")

            # Mensajes de error más específicos
            if "chromedriver" in error_msg.lower():
                return None, False, "ChromeDriver no encontrado. Instale ChromeDriver y asegúrese que esté en PATH"
            elif "chrome" in error_msg.lower():
                return None, False, "Google Chrome no encontrado. Instale Google Chrome"
            else:
                return None, False, f"Error configurando Chrome: {error_msg}"

        except Exception as e:
            self._log(f"Error general: {str(e)}", "ERROR")
            return None, False, f"Error inesperado con Selenium: {str(e)}"

    def _perform_login(self, driver, username, password):
        """Realiza el proceso de login automático con esperas robustas"""
        try:
            # Navegar a la página
            self._log(f"Navegando a: {self.target_url}")
            driver.get(self.target_url)

            # Esperar que la página cargue completamente
            wait = WebDriverWait(driver, self.element_wait_timeout)

            # Esperar a que el DOM esté completamente cargado
            wait.until(lambda d: d.execute_script("return document.readyState") == "complete")
            self._log("Página cargada completamente")

            # Espera adicional para elementos dinámicos
            time.sleep(2)

            # Buscar y llenar campo de usuario con múltiples intentos
            self._log("Buscando campo de usuario...")
            username_field = wait.until(
                EC.element_to_be_clickable((By.XPATH, self.login_xpaths['username']))
            )

            # Esperar a que el campo esté completamente listo
            time.sleep(1)
            username_field.clear()
            time.sleep(0.5)
            username_field.send_keys(username)
            self._log(f"Usuario ingresado: {username}")

            # Espera entre campos
            time.sleep(1)

            # Buscar y llenar campo de contraseña
            self._log("Buscando campo de contraseña...")
            password_field = wait.until(
                EC.element_to_be_clickable((By.XPATH, self.login_xpaths['password']))
            )

            time.sleep(1)
            password_field.clear()
            time.sleep(0.5)
            password_field.send_keys(password)
            self._log("Contraseña ingresada")

            # Espera antes de hacer click en login
            time.sleep(2)

            # Buscar botón de login y asegurar que esté clickeable
            self._log("Buscando botón de login...")
            login_button = wait.until(
                EC.element_to_be_clickable((By.XPATH, self.login_xpaths['login_button']))
            )

            # Scroll al botón si es necesario
            driver.execute_script("arguments[0].scrollIntoView(true);", login_button)
            time.sleep(1)

            # Hacer clic en el botón de login
            self._log("Haciendo clic en botón de login...")
            login_button.click()

            # Esperar más tiempo para que procese el login
            self._log("Esperando respuesta del servidor...")
            time.sleep(8)

            # Verificar resultado del login con múltiples métodos
            return self._verify_login_success(driver, wait)

        except TimeoutException:
            current_url = driver.current_url if driver else "N/A"
            error_msg = f"Timeout: No se encontraron los elementos de login. URL actual: {current_url}"
            self._log(error_msg, "ERROR")
            return False, error_msg
        except NoSuchElementException:
            error_msg = "No se encontraron los campos de login en la página"
            self._log(error_msg, "ERROR")
            return False, error_msg
        except Exception as e:
            error_msg = f"Error durante el login: {str(e)}"
            self._log(error_msg, "ERROR")
            return False, error_msg

    def _verify_login_success(self, driver, wait):
        """Verifica si el login fue exitoso con múltiples métodos"""
        try:
            current_url = driver.current_url
            self._log(f"URL después del login: {current_url}")

            # Método 1: Verificar cambio de URL
            if current_url != self.target_url and "login" not in current_url.lower():
                self._log("Login exitoso - URL cambió")
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
                            self._log(f"Login exitoso - Encontrado elemento: {indicator}")
                            return True, "Login exitoso - Panel principal cargado"
                    except:
                        continue

            except Exception as e:
                self._log(f"Error buscando indicadores de éxito: {e}", "DEBUG")

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
                        self._log(f"Error encontrado: {error_text}", "ERROR")
                        return False, f"Login fallido - Error detectado: {error_text}"

            except Exception as e:
                self._log(f"Error buscando mensajes de error: {e}", "DEBUG")

            # Método 4: Esperar más tiempo y verificar de nuevo
            self._log("Esperando más tiempo para verificar login...")
            time.sleep(5)

            final_url = driver.current_url
            self._log(f"URL final después de espera adicional: {final_url}")

            if final_url != self.target_url and "login" not in final_url.lower():
                return True, "Login exitoso después de espera adicional"

            # Método 5: Verificar título de la página
            try:
                page_title = driver.title.lower()
                self._log(f"Título de la página: {page_title}")

                if "login" not in page_title and page_title:
                    return True, f"Login exitoso - Título de página: {driver.title}"

            except Exception as e:
                self._log(f"Error obteniendo título: {e}", "DEBUG")

            # Si llegamos aquí, probablemente el login falló
            return False, "No se pudo verificar login exitoso - Posibles credenciales incorrectas"

        except Exception as e:
            error_msg = f"Error verificando login: {str(e)}"
            self._log(error_msg, "ERROR")
            return False, error_msg

    def start_automation(self, username=None, password=None):
        """Inicia el proceso de automatización con login automático"""
        try:
            with self._lock:
                if self.is_running:
                    return False, "La automatización ya está en ejecución"

                if not SELENIUM_AVAILABLE:
                    # Fallback al método original si Selenium no está disponible
                    self._log("Selenium no disponible, usando método básico")
                    webbrowser.open(self.target_url)
                    self.is_running = True
                    return True, "Automatización iniciada (modo básico - sin login automático)"

                # Verificar credenciales
                if not username or not password:
                    self._log("Cargando credenciales desde archivo...")
                    credentials = self.credentials_manager.load_credentials()
                    if not credentials:
                        return False, "No hay credenciales configuradas para el login automático"
                    username = credentials.get('username')
                    password = credentials.get('password')

                # Validar credenciales
                self._log("Validando credenciales...")
                valid, message = self.credentials_manager.validate_credentials(username, password)
                if not valid:
                    return False, f"Credenciales inválidas: {message}"

                self._log("Iniciando proceso de automatización...")

                # Configurar driver
                self._log("Configurando navegador...")
                driver, success, setup_message = self._setup_chrome_driver()
                if not success:
                    return False, setup_message

                self.driver = driver
                self._log("Navegador configurado, iniciando login...")

                # Realizar login
                login_success, login_message = self._perform_login(driver, username, password)
                if not login_success:
                    self._log(f"Login falló: {login_message}", "ERROR")
                    self._cleanup_driver()
                    return False, login_message

                self._log(f"Login exitoso: {login_message}")
                self.is_running = True
                return True, f"Automatización con login automático iniciada exitosamente: {login_message}"

        except Exception as e:
            self._log(f"Excepción en start_automation: {str(e)}", "ERROR")
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
                self._log("Automatización pausada correctamente")
                return True, "Automatización pausada correctamente"

        except Exception as e:
            error_msg = f"Error al pausar automatización: {str(e)}"
            self._log(error_msg, "ERROR")
            return False, error_msg

    def _cleanup_driver(self):
        """Limpia el driver de Selenium"""
        try:
            if self.driver:
                self._log("Cerrando navegador...")
                self.driver.quit()
                self.driver = None
                self._log("Navegador cerrado correctamente")
        except Exception as e:
            self._log(f"Error limpiando driver: {e}", "WARNING")

    def get_status(self):
        """Obtiene el estado actual de la automatización"""
        with self._lock:
            return self.is_running

    def stop_all(self):
        """Detiene todas las operaciones de automatización"""
        with self._lock:
            self._cleanup_driver()
            self.is_running = False
            self._log("Todas las operaciones de automatización detenidas")

    def test_credentials(self, username, password):
        """Prueba las credenciales sin iniciar la automatización completa"""
        try:
            if not SELENIUM_AVAILABLE:
                return False, "Selenium no está disponible para probar credenciales"

            # Validar formato de credenciales
            valid, message = self.credentials_manager.validate_credentials(username, password)
            if not valid:
                return False, message

            self._log("Iniciando prueba de credenciales...")

            # Configurar driver temporal
            driver, success, setup_message = self._setup_chrome_driver()
            if not success:
                return False, setup_message

            try:
                self._log("Driver configurado, probando login...")
                # Realizar prueba de login
                login_success, login_message = self._perform_login(driver, username, password)

                if login_success:
                    self._log("Prueba de credenciales exitosa")
                else:
                    self._log(f"Prueba de credenciales falló: {login_message}", "ERROR")

                return login_success, login_message
            finally:
                # Limpiar driver temporal
                try:
                    self._log("Cerrando navegador de prueba...")
                    driver.quit()
                except:
                    pass

        except Exception as e:
            error_msg = f"Error probando credenciales: {str(e)}"
            self._log(error_msg, "ERROR")
            return False, error_msg

    def get_driver_info(self):
        """Obtiene información del driver actual"""
        if not self.driver:
            return None

        try:
            return {
                'current_url': self.driver.current_url,
                'title': self.driver.title,
                'window_handles': len(self.driver.window_handles),
                'session_id': self.driver.session_id
            }
        except Exception as e:
            self._log(f"Error obteniendo info del driver: {e}", "WARNING")
            return None

    def navigate_to_url(self, url):
        """Navega a una URL específica si hay un driver activo"""
        if not self.driver or not self.is_running:
            return False, "No hay automatización activa"

        try:
            self.driver.get(url)
            self._log(f"Navegado a: {url}")
            return True, f"Navegación exitosa a: {url}"
        except Exception as e:
            error_msg = f"Error navegando a {url}: {str(e)}"
            self._log(error_msg, "ERROR")
            return False, error_msg

    def execute_script(self, script):
        """Ejecuta JavaScript en la página actual"""
        if not self.driver or not self.is_running:
            return False, "No hay automatización activa"

        try:
            result = self.driver.execute_script(script)
            self._log(f"Script ejecutado correctamente")
            return True, result
        except Exception as e:
            error_msg = f"Error ejecutando script: {str(e)}"
            self._log(error_msg, "ERROR")
            return False, error_msg