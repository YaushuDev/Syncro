# automation_service.py
# Ubicación: /syncro_bot/gui/components/automation/automation_service.py
"""
Servicio de automatización con login automático, selección de dropdown y clic en botón de pestaña.
Maneja la configuración del navegador, proceso de login automático, selección automática
del dropdown "140_AUTO INSTALACION", clic en botón de pestaña y verificación de credenciales.
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
    """Servicio de automatización con login automático, selección de dropdown y clic en botón"""

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

        # XPaths para dropdown de despacho
        self.dropdown_xpaths = {
            'trigger': '//*[@id="combo-1077-trigger-picker"]',
            'input': '//*[@id="combo-1077-inputEl"]',
            'options': [
                '//div[contains(text(), "140_AUTO INSTALACION")]',
                '//li[contains(text(), "140_AUTO INSTALACION")]',
                '//span[contains(text(), "140_AUTO INSTALACION")]',
                '//*[contains(text(), "140_AUTO")]',
                '//*[@data-qtip="140_AUTO INSTALACION"]'
            ]
        }

        # XPath para el botón de pestaña
        self.tab_button_xpath = '//*[@id="tab-1030-btnEl"]'

        # Configuración de timeouts
        self.page_load_timeout = 30
        self.element_wait_timeout = 25
        self.implicit_wait_timeout = 10
        self.dropdown_wait_timeout = 15
        self.button_wait_timeout = 15

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
            login_success, login_message = self._verify_login_success(driver, wait)

            if not login_success:
                return False, login_message

            # Si el login fue exitoso, proceder con la selección del dropdown
            self._log("Login exitoso, procediendo con selección de dropdown...")
            dropdown_success, dropdown_message = self._handle_dropdown_selection(driver)

            if not dropdown_success:
                self._log(f"Advertencia en dropdown: {dropdown_message}", "WARNING")
                return True, f"Login exitoso. {dropdown_message}"

            # Si el dropdown fue exitoso, proceder con el clic en el botón de pestaña
            self._log("Dropdown configurado, procediendo con clic en botón de pestaña...")
            button_success, button_message = self._handle_tab_button_click(driver)

            if not button_success:
                self._log(f"Advertencia en botón de pestaña: {button_message}", "WARNING")
                return True, f"Login y dropdown completados. {button_message}"

            return True, f"Automatización completa: Login, dropdown y botón de pestaña ejecutados exitosamente. {button_message}"

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

    def _handle_dropdown_selection(self, driver):
        """Maneja la selección automática del dropdown de despacho"""
        try:
            self._log("🔽 Iniciando selección de dropdown de despacho...")
            wait = WebDriverWait(driver, self.dropdown_wait_timeout)

            # Paso 1: Buscar el trigger del dropdown
            self._log("Buscando trigger del dropdown...")
            dropdown_trigger = None

            try:
                dropdown_trigger = wait.until(
                    EC.element_to_be_clickable((By.XPATH, self.dropdown_xpaths['trigger']))
                )
                self._log("✅ Trigger del dropdown encontrado")
            except TimeoutException:
                self._log("❌ No se encontró el trigger del dropdown", "WARNING")
                return False, "Dropdown de despacho no encontrado en la página"

            # Paso 2: Verificar valor actual del input
            try:
                current_input = driver.find_element(By.XPATH, self.dropdown_xpaths['input'])
                current_value = current_input.get_attribute('value')
                self._log(f"📋 Valor actual del dropdown: '{current_value}'")

                # Si ya tiene el valor correcto, no necesitamos hacer nada
                if "140_AUTO" in current_value:
                    self._log("✅ El dropdown ya tiene el valor correcto")
                    return True, "Dropdown ya configurado con 140_AUTO INSTALACION"

            except Exception as e:
                self._log(f"No se pudo leer valor actual: {e}", "DEBUG")

            # Paso 3: Hacer clic en el trigger para abrir el dropdown
            self._log("Haciendo clic en trigger del dropdown...")
            driver.execute_script("arguments[0].scrollIntoView(true);", dropdown_trigger)
            time.sleep(1)
            dropdown_trigger.click()

            # Esperar un poco para que se abra el dropdown
            time.sleep(2)
            self._log("📋 Dropdown abierto, buscando opciones...")

            # Paso 4: Buscar y seleccionar la opción "140_AUTO INSTALACION"
            option_found = False
            selected_option_text = ""

            # Intentar con diferentes XPaths para encontrar la opción
            for i, option_xpath in enumerate(self.dropdown_xpaths['options']):
                try:
                    self._log(f"Probando XPath {i + 1}: {option_xpath}")

                    # Esperar a que la opción esté disponible
                    option_element = WebDriverWait(driver, 5).until(
                        EC.element_to_be_clickable((By.XPATH, option_xpath))
                    )

                    # Obtener texto de la opción para logging
                    selected_option_text = option_element.text.strip()
                    self._log(f"✅ Opción encontrada: '{selected_option_text}'")

                    # Hacer clic en la opción
                    driver.execute_script("arguments[0].scrollIntoView(true);", option_element)
                    time.sleep(0.5)
                    option_element.click()

                    option_found = True
                    self._log(f"🎯 Opción seleccionada: '{selected_option_text}'")
                    break

                except TimeoutException:
                    self._log(f"XPath {i + 1} no funcionó: {option_xpath}", "DEBUG")
                    continue
                except Exception as e:
                    self._log(f"Error con XPath {i + 1}: {str(e)}", "DEBUG")
                    continue

            # Paso 5: Verificar si se seleccionó alguna opción
            if not option_found:
                # Intentar cerrar el dropdown si sigue abierto
                try:
                    dropdown_trigger.click()
                except:
                    pass

                self._log("❌ No se pudo encontrar la opción 140_AUTO INSTALACION", "WARNING")
                return False, "No se encontró la opción '140_AUTO INSTALACION' en el dropdown"

            # Paso 6: Esperar y verificar que se haya seleccionado correctamente
            time.sleep(2)
            try:
                updated_input = driver.find_element(By.XPATH, self.dropdown_xpaths['input'])
                final_value = updated_input.get_attribute('value')
                self._log(f"✅ Valor final del dropdown: '{final_value}'")

                if "140_AUTO" in final_value:
                    return True, f"Dropdown seleccionado exitosamente: '{final_value}'"
                else:
                    return False, f"Dropdown no se actualizó correctamente. Valor: '{final_value}'"

            except Exception as e:
                self._log(f"Error verificando selección final: {e}", "WARNING")
                return True, f"Opción seleccionada: '{selected_option_text}' (verificación parcial)"

        except Exception as e:
            error_msg = f"Error manejando dropdown: {str(e)}"
            self._log(error_msg, "ERROR")
            return False, error_msg

    def _handle_tab_button_click(self, driver):
        """Maneja el clic en el botón de pestaña después de la selección del dropdown"""
        try:
            self._log("🔘 Iniciando clic en botón de pestaña...")
            wait = WebDriverWait(driver, self.button_wait_timeout)

            # Paso 1: Buscar el botón de pestaña
            self._log(f"Buscando botón de pestaña: {self.tab_button_xpath}")
            tab_button = None

            try:
                tab_button = wait.until(
                    EC.element_to_be_clickable((By.XPATH, self.tab_button_xpath))
                )
                self._log("✅ Botón de pestaña encontrado")
            except TimeoutException:
                self._log("❌ No se encontró el botón de pestaña", "WARNING")
                return False, "Botón de pestaña no encontrado en la página"

            # Paso 2: Verificar que el botón esté visible y clickeable
            try:
                # Hacer scroll al botón si es necesario
                self._log("Haciendo scroll al botón de pestaña...")
                driver.execute_script("arguments[0].scrollIntoView(true);", tab_button)
                time.sleep(1)

                # Verificar si el botón está habilitado
                if not tab_button.is_enabled():
                    self._log("⚠️ El botón de pestaña está deshabilitado", "WARNING")
                    return False, "El botón de pestaña está deshabilitado"

                # Verificar si el botón está visible
                if not tab_button.is_displayed():
                    self._log("⚠️ El botón de pestaña no está visible", "WARNING")
                    return False, "El botón de pestaña no está visible"

                self._log("✅ Botón de pestaña está listo para hacer clic")

            except Exception as e:
                self._log(f"Error verificando estado del botón: {e}", "WARNING")
                # Continuar de todas formas intentando hacer clic

            # Paso 3: Hacer clic en el botón de pestaña
            try:
                self._log("Haciendo clic en botón de pestaña...")
                tab_button.click()
                self._log("🎯 Clic en botón de pestaña ejecutado")

                # Esperar un poco para que se procese la acción
                time.sleep(2)

                # Paso 4: Verificar que el clic fue exitoso (opcional)
                try:
                    # Verificar si hay algún cambio en la página después del clic
                    # Esto depende de lo que hace el botón, pero generalmente podríamos
                    # verificar cambios en la URL, nuevos elementos, etc.
                    current_url = driver.current_url
                    self._log(f"📍 URL después del clic: {current_url}")

                    # Verificar si el botón cambió de estado o si aparecieron nuevos elementos
                    # (esta verificación específica dependería del comportamiento esperado)

                    return True, "Botón de pestaña clickeado exitosamente"

                except Exception as e:
                    self._log(f"Error verificando resultado del clic: {e}", "DEBUG")
                    # Asumir que el clic fue exitoso si no hay errores graves
                    return True, "Botón de pestaña clickeado (verificación parcial)"

            except Exception as e:
                error_msg = f"Error haciendo clic en el botón: {str(e)}"
                self._log(error_msg, "ERROR")
                return False, error_msg

        except Exception as e:
            error_msg = f"Error manejando botón de pestaña: {str(e)}"
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
                    "//*[contains(text(), 'Menu')]",
                    self.dropdown_xpaths['trigger']  # El dropdown es un buen indicador de login exitoso
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
        """Inicia el proceso de automatización completo con login, dropdown y clic en botón"""
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

                self._log("Iniciando proceso de automatización completa...")

                # Configurar driver
                self._log("Configurando navegador...")
                driver, success, setup_message = self._setup_chrome_driver()
                if not success:
                    return False, setup_message

                self.driver = driver
                self._log("Navegador configurado, iniciando login y configuración completa...")

                # Realizar login y configuración completa
                login_success, login_message = self._perform_login(driver, username, password)
                if not login_success:
                    self._log(f"Proceso falló: {login_message}", "ERROR")
                    self._cleanup_driver()
                    return False, login_message

                self._log(f"Automatización completada: {login_message}")
                self.is_running = True
                return True, f"Automatización completa iniciada exitosamente: {login_message}"

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
        """Prueba las credenciales ejecutando el proceso completo de automatización"""
        try:
            if not SELENIUM_AVAILABLE:
                return False, "Selenium no está disponible para probar credenciales"

            # Validar formato de credenciales
            valid, message = self.credentials_manager.validate_credentials(username, password)
            if not valid:
                return False, message

            self._log("Iniciando prueba completa de automatización...")

            # Configurar driver temporal
            driver, success, setup_message = self._setup_chrome_driver()
            if not success:
                return False, setup_message

            try:
                self._log("Driver configurado, ejecutando prueba completa...")
                # Realizar prueba completa (login, dropdown y botón)
                automation_success, automation_message = self._perform_login(driver, username, password)

                if automation_success:
                    self._log("Prueba completa de automatización exitosa")
                else:
                    self._log(f"Prueba falló: {automation_message}", "ERROR")

                return automation_success, automation_message
            finally:
                # Limpiar driver temporal
                try:
                    self._log("Cerrando navegador de prueba...")
                    driver.quit()
                except:
                    pass

        except Exception as e:
            error_msg = f"Error probando automatización completa: {str(e)}"
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

    def get_current_dropdown_value(self):
        """Obtiene el valor actual del dropdown de despacho"""
        if not self.driver or not self.is_running:
            return None

        try:
            input_element = self.driver.find_element(By.XPATH, self.dropdown_xpaths['input'])
            current_value = input_element.get_attribute('value')
            self._log(f"Valor actual del dropdown: '{current_value}'")
            return current_value
        except Exception as e:
            self._log(f"Error obteniendo valor del dropdown: {e}", "WARNING")
            return None

    def click_tab_button_manually(self):
        """Ejecuta solo el clic en el botón de pestaña (para uso manual)"""
        if not self.driver or not self.is_running:
            return False, "No hay automatización activa"

        try:
            button_success, button_message = self._handle_tab_button_click(self.driver)
            return button_success, button_message
        except Exception as e:
            error_msg = f"Error haciendo clic manual en botón: {str(e)}"
            self._log(error_msg, "ERROR")
            return False, error_msg

    def change_dropdown_value(self, target_value):
        """Cambia el valor del dropdown a un valor específico (funcionalidad futura)"""
        if not self.driver or not self.is_running:
            return False, "No hay automatización activa"

        # Esta funcionalidad se puede implementar en el futuro si se necesita
        # cambiar dinámicamente el valor del dropdown
        self._log(f"Funcionalidad de cambio dinámico no implementada: {target_value}", "INFO")
        return False, "Funcionalidad no implementada - valor hardcoded a 140_AUTO INSTALACION"