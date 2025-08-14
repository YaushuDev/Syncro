# automation_service.py
# Ubicación: /syncro_bot/gui/components/automation/automation_service.py
"""
Servicio de automatización con login automático, selección de tres dropdowns, configuración de fechas y clic en dos botones.
Maneja la configuración del navegador, proceso de login automático, selección automática de tres dropdowns
(140_AUTO INSTALACION, 102_UDR_FS, PENDIENTE), configuración opcional de fechas Desde/Hasta después de los dropdowns,
y clic en botones de pestaña y acción.
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
    """Servicio de automatización con login automático, selección de tres dropdowns, configuración de fechas y clic en dos botones"""

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

        # 🆕 XPaths para campos de fecha
        self.date_field_xpaths = {
            'date_from': '//*[@id="datefield-1140-inputEl"]',
            'date_to': '//*[@id="datefield-1148-inputEl"]'
        }

        # XPaths para primer dropdown de despacho (140_AUTO INSTALACION)
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

        # XPaths para segundo dropdown (102_UDR_FS)
        self.second_dropdown_xpaths = {
            'trigger': '//*[@id="combo-1152-trigger-picker"]',
            'input': '//*[@id="combo-1152-inputEl"]',
            'options': [
                '//li[text()="102_UDR_FS"]',
                '//li[@class="x-boundlist-item" and text()="102_UDR_FS"]',
                '//ul[contains(@id, "listEl")]//li[text()="102_UDR_FS"]',
                '//li[@data-recordid="22395"]',
                '//li[contains(text(), "102_UDR_FS")]'
            ]
        }

        # XPaths para tercer dropdown (PENDIENTE)
        self.third_dropdown_xpaths = {
            'trigger': '//*[@id="combo-1142-trigger-picker"]',
            'input': '//*[@id="combo-1142-inputEl"]',
            'options': [
                '//li[text()="PENDIENTE"]',
                '//li[@class="x-boundlist-item" and text()="PENDIENTE"]',
                '//ul[contains(@id, "listEl")]//li[text()="PENDIENTE"]',
                '//li[@data-recordid="24808"]',
                '//li[contains(text(), "PENDIENTE")]'
            ]
        }

        # XPaths para botones
        self.tab_button_xpath = '//*[@id="tab-1030-btnEl"]'
        self.action_button_xpath = '//*[@id="button-1146-btnEl"]'

        # Configuración de timeouts
        self.page_load_timeout = 30
        self.element_wait_timeout = 25
        self.implicit_wait_timeout = 10
        self.dropdown_wait_timeout = 15
        self.second_dropdown_wait_timeout = 20
        self.third_dropdown_wait_timeout = 20
        self.button_wait_timeout = 15
        self.action_button_wait_timeout = 15
        self.date_configuration_timeout = 15  # 🆕 Timeout para configuración de fechas

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

    def _perform_login(self, driver, username, password, date_config=None):
        """🔄 Realiza el proceso de automatización completo: login, tres dropdowns, configuración de fechas y botones"""
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

            # PASO 1: LOGIN AUTOMÁTICO
            login_success, login_message = self._handle_login_process(driver, wait, username, password)
            if not login_success:
                return False, login_message

            # PASO 2: PRIMER DROPDOWN
            self._log("Login exitoso, procediendo con primer dropdown...")
            dropdown_success, dropdown_message = self._handle_dropdown_selection(driver)
            if not dropdown_success:
                self._log(f"Advertencia en primer dropdown: {dropdown_message}", "WARNING")
                return True, f"Login exitoso. {dropdown_message}"

            # PASO 3: BOTÓN DE PESTAÑA
            self._log("Primer dropdown configurado, procediendo con clic en botón de pestaña...")
            button_success, button_message = self._handle_tab_button_click(driver)
            if not button_success:
                self._log(f"Advertencia en botón de pestaña: {button_message}", "WARNING")
                return True, f"Login y primer dropdown completados. {button_message}"

            # PASO 4: SEGUNDO DROPDOWN
            self._log("Botón de pestaña ejecutado, procediendo con segundo dropdown...")
            second_dropdown_success, second_dropdown_message = self._handle_second_dropdown_selection(driver)
            if not second_dropdown_success:
                self._log(f"Advertencia en segundo dropdown: {second_dropdown_message}", "WARNING")
                return True, f"Login, primer dropdown y botón completados. {second_dropdown_message}"

            # PASO 5: TERCER DROPDOWN
            self._log("Segundo dropdown configurado, procediendo con tercer dropdown...")
            third_dropdown_success, third_dropdown_message = self._handle_third_dropdown_selection(driver)
            if not third_dropdown_success:
                self._log(f"Advertencia en tercer dropdown: {third_dropdown_message}", "WARNING")
                return True, f"Login, dropdowns 1-2 y botón completados. {third_dropdown_message}"

            # 🆕 PASO 6: CONFIGURACIÓN DE FECHAS (DESPUÉS de los tres dropdowns)
            self._log("Tercer dropdown configurado, verificando configuración de fechas...")
            date_success, date_message = self._handle_date_configuration(driver, date_config)
            if not date_success:
                self._log(f"Advertencia en configuración de fechas: {date_message}", "WARNING")
                return True, f"Login, tres dropdowns y botón completados. {date_message}"

            # PASO 7: BOTÓN DE ACCIÓN FINAL (ÚLTIMO PASO)
            self._log("Configuración de fechas completada, procediendo con botón de acción final...")
            action_button_success, action_button_message = self._handle_action_button_click(driver)
            if not action_button_success:
                self._log(f"Advertencia en botón de acción: {action_button_message}", "WARNING")
                return True, f"Automatización casi completa (falta botón final). {action_button_message}"

            # ✅ PROCESO COMPLETO EXITOSO
            final_message = "Automatización completa exitosa: Login, tres dropdowns, configuración de fechas y botón final ejecutados."
            if date_config and not date_config.get('skip_dates', True):
                final_message += f" Fechas configuradas: {date_config.get('date_from', 'N/A')} - {date_config.get('date_to', 'N/A')}"

            return True, final_message

        except TimeoutException:
            current_url = driver.current_url if driver else "N/A"
            error_msg = f"Timeout: No se encontraron los elementos necesarios. URL actual: {current_url}"
            self._log(error_msg, "ERROR")
            return False, error_msg
        except NoSuchElementException:
            error_msg = "No se encontraron los elementos necesarios en la página"
            self._log(error_msg, "ERROR")
            return False, error_msg
        except Exception as e:
            error_msg = f"Error durante la automatización: {str(e)}"
            self._log(error_msg, "ERROR")
            return False, error_msg

    def _handle_login_process(self, driver, wait, username, password):
        """Maneja el proceso de login automático"""
        try:
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
            return login_success, login_message

        except Exception as e:
            error_msg = f"Error en proceso de login: {str(e)}"
            self._log(error_msg, "ERROR")
            return False, error_msg

    def _handle_date_configuration(self, driver, date_config):
        """🆕 Maneja la configuración de fechas Desde/Hasta"""
        try:
            # Verificar si se debe omitir configuración de fechas
            if not date_config or date_config.get('skip_dates', True):
                self._log("📅 Configuración de fechas OMITIDA según configuración")
                return True, "Configuración de fechas omitida (mantener valores actuales)"

            self._log("📅 Iniciando configuración de fechas...")
            wait = WebDriverWait(driver, self.date_configuration_timeout)

            date_from = date_config.get('date_from', '').strip()
            date_to = date_config.get('date_to', '').strip()

            # Si no hay fechas que configurar, salir exitosamente
            if not date_from and not date_to:
                self._log("📅 No hay fechas específicas para configurar")
                return True, "Sin fechas específicas para configurar"

            results = []

            # CONFIGURAR FECHA DESDE
            if date_from:
                from_success, from_message = self._configure_date_field(
                    driver, wait, 'date_from', date_from, "Desde"
                )
                results.append(f"Desde: {from_message}")
                if not from_success:
                    self._log(f"⚠️ Error en fecha Desde: {from_message}", "WARNING")

            # CONFIGURAR FECHA HASTA
            if date_to:
                to_success, to_message = self._configure_date_field(
                    driver, wait, 'date_to', date_to, "Hasta"
                )
                results.append(f"Hasta: {to_message}")
                if not to_success:
                    self._log(f"⚠️ Error en fecha Hasta: {to_message}", "WARNING")

            # Espera final para que los cambios se procesen
            time.sleep(2)

            # Verificar valores finales
            self._verify_date_configuration(driver)

            # Determinar resultado general
            if results:
                final_message = f"Configuración de fechas completada: {' | '.join(results)}"
                self._log(f"✅ {final_message}")
                return True, final_message
            else:
                return True, "Configuración de fechas procesada (sin cambios específicos)"

        except Exception as e:
            error_msg = f"Error en configuración de fechas: {str(e)}"
            self._log(error_msg, "ERROR")
            return False, error_msg

    def _configure_date_field(self, driver, wait, field_key, date_value, field_name):
        """Configura un campo de fecha específico escribiendo el texto y presionando ENTER"""
        try:
            from selenium.webdriver.common.keys import Keys

            xpath = self.date_field_xpaths[field_key]
            self._log(f"📅 Configurando fecha {field_name}: {date_value}")

            # Buscar el campo de fecha
            try:
                date_field = wait.until(
                    EC.element_to_be_clickable((By.XPATH, xpath))
                )
                self._log(f"✅ Campo de fecha {field_name} encontrado")
            except TimeoutException:
                return False, f"Campo de fecha {field_name} no encontrado"

            # Verificar estado actual del campo
            try:
                current_value = date_field.get_attribute('value')
                self._log(f"📋 Valor actual del campo {field_name}: '{current_value}'")

                # Si ya tiene el valor correcto, no hacer nada
                if current_value == date_value:
                    self._log(f"✅ Campo {field_name} ya tiene el valor correcto")
                    return True, f"Ya configurado con {date_value}"
            except Exception as e:
                self._log(f"No se pudo leer valor actual de {field_name}: {e}", "DEBUG")

            # Hacer scroll al campo si es necesario
            driver.execute_script("arguments[0].scrollIntoView(true);", date_field)
            time.sleep(1)

            # Hacer clic en el campo para enfocarlo
            try:
                date_field.click()
                time.sleep(0.5)
                self._log(f"🎯 Campo {field_name} enfocado")
            except Exception as e:
                self._log(f"Advertencia enfocando campo {field_name}: {e}", "WARNING")

            # Limpiar campo actual (seleccionar todo y borrar)
            try:
                date_field.send_keys(Keys.CONTROL + "a")  # Seleccionar todo
                time.sleep(0.3)
                date_field.send_keys(Keys.DELETE)  # Borrar contenido
                time.sleep(0.5)
                self._log(f"🧹 Campo {field_name} limpiado")
            except Exception as e:
                self._log(f"Advertencia limpiando campo {field_name}: {e}", "WARNING")

            # Ingresar nueva fecha y presionar ENTER
            try:
                date_field.send_keys(date_value)
                time.sleep(0.5)
                self._log(f"⌨️ Fecha {field_name} ingresada: {date_value}")

                # Presionar ENTER para confirmar la fecha
                date_field.send_keys(Keys.ENTER)
                time.sleep(1)
                self._log(f"⏎ ENTER presionado en campo {field_name}")

            except Exception as e:
                return False, f"Error ingresando fecha en {field_name}: {str(e)}"

            # Verificar que se haya establecido correctamente después del ENTER
            try:
                # Esperar un poco más para que procese el ENTER
                time.sleep(1.5)
                final_value = date_field.get_attribute('value')
                self._log(f"🔍 Valor final en campo {field_name}: '{final_value}'")

                if final_value == date_value:
                    return True, f"Configurado exitosamente con {date_value}"
                else:
                    # A veces el formato puede cambiar, verificar si contiene la fecha
                    if date_value in final_value or final_value in date_value:
                        return True, f"Configurado con formato {final_value} (basado en {date_value})"
                    else:
                        return False, f"Valor no se estableció correctamente. Esperado: {date_value}, Actual: {final_value}"
            except Exception as e:
                # Si no podemos verificar, asumir éxito
                self._log(f"No se pudo verificar valor final de {field_name}: {e}", "WARNING")
                return True, f"Fecha {date_value} enviada con ENTER (verificación parcial)"

        except Exception as e:
            error_msg = f"Error configurando fecha {field_name}: {str(e)}"
            self._log(error_msg, "ERROR")
            return False, error_msg

    def _verify_date_configuration(self, driver):
        """Verifica la configuración final de ambas fechas"""
        try:
            self._log("🔍 Verificando configuración final de fechas...")

            for field_key, field_name in [('date_from', 'Desde'), ('date_to', 'Hasta')]:
                try:
                    xpath = self.date_field_xpaths[field_key]
                    date_field = driver.find_element(By.XPATH, xpath)
                    final_value = date_field.get_attribute('value')
                    self._log(f"📋 Fecha {field_name} final: '{final_value}'")
                except Exception as e:
                    self._log(f"No se pudo verificar fecha {field_name}: {e}", "WARNING")

        except Exception as e:
            self._log(f"Error en verificación final de fechas: {e}", "WARNING")

    def _handle_dropdown_selection(self, driver):
        """Maneja la selección automática del primer dropdown de despacho (140_AUTO INSTALACION)"""
        try:
            self._log("🔽 Iniciando selección del primer dropdown (140_AUTO INSTALACION)...")
            wait = WebDriverWait(driver, self.dropdown_wait_timeout)

            # Paso 1: Buscar el trigger del dropdown
            self._log("Buscando trigger del primer dropdown...")
            dropdown_trigger = None

            try:
                dropdown_trigger = wait.until(
                    EC.element_to_be_clickable((By.XPATH, self.dropdown_xpaths['trigger']))
                )
                self._log("✅ Trigger del primer dropdown encontrado")
            except TimeoutException:
                self._log("❌ No se encontró el trigger del primer dropdown", "WARNING")
                return False, "Primer dropdown de despacho no encontrado en la página"

            # Paso 2: Verificar valor actual del input
            try:
                current_input = driver.find_element(By.XPATH, self.dropdown_xpaths['input'])
                current_value = current_input.get_attribute('value')
                self._log(f"📋 Valor actual del primer dropdown: '{current_value}'")

                # Si ya tiene el valor correcto, no necesitamos hacer nada
                if "140_AUTO" in current_value:
                    self._log("✅ El primer dropdown ya tiene el valor correcto")
                    return True, "Primer dropdown ya configurado con 140_AUTO INSTALACION"

            except Exception as e:
                self._log(f"No se pudo leer valor actual del primer dropdown: {e}", "DEBUG")

            # Paso 3: Hacer clic en el trigger para abrir el dropdown
            self._log("Haciendo clic en trigger del primer dropdown...")
            driver.execute_script("arguments[0].scrollIntoView(true);", dropdown_trigger)
            time.sleep(1)
            dropdown_trigger.click()

            # Esperar un poco para que se abra el dropdown
            time.sleep(2)
            self._log("📋 Primer dropdown abierto, buscando opciones...")

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
                    self._log(f"🎯 Opción seleccionada en primer dropdown: '{selected_option_text}'")
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
                return False, "No se encontró la opción '140_AUTO INSTALACION' en el primer dropdown"

            # Paso 6: Esperar y verificar que se haya seleccionado correctamente
            time.sleep(2)
            try:
                updated_input = driver.find_element(By.XPATH, self.dropdown_xpaths['input'])
                final_value = updated_input.get_attribute('value')
                self._log(f"✅ Valor final del primer dropdown: '{final_value}'")

                if "140_AUTO" in final_value:
                    return True, f"Primer dropdown seleccionado exitosamente: '{final_value}'"
                else:
                    return False, f"Primer dropdown no se actualizó correctamente. Valor: '{final_value}'"

            except Exception as e:
                self._log(f"Error verificando selección final del primer dropdown: {e}", "WARNING")
                return True, f"Opción seleccionada en primer dropdown: '{selected_option_text}' (verificación parcial)"

        except Exception as e:
            error_msg = f"Error manejando primer dropdown: {str(e)}"
            self._log(error_msg, "ERROR")
            return False, error_msg

    def _handle_second_dropdown_selection(self, driver):
        """Maneja la selección automática del segundo dropdown (102_UDR_FS)"""
        try:
            self._log("🔽 Iniciando selección del segundo dropdown (102_UDR_FS)...")
            wait = WebDriverWait(driver, self.second_dropdown_wait_timeout)

            # Paso 1: Buscar el trigger del segundo dropdown
            self._log("Buscando trigger del segundo dropdown...")
            second_dropdown_trigger = None

            try:
                second_dropdown_trigger = wait.until(
                    EC.element_to_be_clickable((By.XPATH, self.second_dropdown_xpaths['trigger']))
                )
                self._log("✅ Trigger del segundo dropdown encontrado")
            except TimeoutException:
                self._log("❌ No se encontró el trigger del segundo dropdown", "WARNING")
                return False, "Segundo dropdown no encontrado en la página"

            # Paso 2: Verificar valor actual del input
            try:
                current_input = driver.find_element(By.XPATH, self.second_dropdown_xpaths['input'])
                current_value = current_input.get_attribute('value')
                self._log(f"📋 Valor actual del segundo dropdown: '{current_value}'")

                # Si ya tiene el valor correcto, no necesitamos hacer nada
                if "102_UDR_FS" in current_value:
                    self._log("✅ El segundo dropdown ya tiene el valor correcto")
                    return True, "Segundo dropdown ya configurado con 102_UDR_FS"

            except Exception as e:
                self._log(f"No se pudo leer valor actual del segundo dropdown: {e}", "DEBUG")

            # Paso 3: Hacer clic en el trigger para abrir el segundo dropdown
            self._log("Haciendo clic en trigger del segundo dropdown...")
            driver.execute_script("arguments[0].scrollIntoView(true);", second_dropdown_trigger)
            time.sleep(1)
            second_dropdown_trigger.click()

            # Paso 4: ESPERAR EXPLÍCITAMENTE que aparezca la lista de opciones
            self._log("📋 Segundo dropdown abierto, esperando que aparezca la lista de opciones...")

            # Esperar a que aparezca el contenedor UL con las opciones
            try:
                WebDriverWait(driver, 15).until(
                    EC.presence_of_element_located((By.XPATH, "//ul[contains(@id, 'listEl')]"))
                )
                self._log("✅ Contenedor UL de opciones encontrado")
            except TimeoutException:
                self._log("❌ El contenedor de opciones no apareció", "WARNING")
                return False, "Lista de opciones del segundo dropdown no se cargó"

            # Esperar a que aparezcan elementos li dentro del contenedor
            try:
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located(
                        (By.XPATH, "//ul[contains(@id, 'listEl')]//li[@class='x-boundlist-item']"))
                )
                self._log("✅ Elementos li de opciones encontrados")
            except TimeoutException:
                self._log("❌ Los elementos li no aparecieron", "WARNING")
                return False, "Opciones individuales del segundo dropdown no se cargaron"

            # Espera adicional para asegurar carga completa
            time.sleep(3)
            self._log("📋 Lista de opciones completamente cargada, buscando '102_UDR_FS'...")

            # Paso 5: Buscar y seleccionar la opción "102_UDR_FS"
            option_found = False
            selected_option_text = ""

            # Intentar con los XPaths definidos
            for i, option_xpath in enumerate(self.second_dropdown_xpaths['options']):
                try:
                    self._log(f"Probando XPath {i + 1} en segundo dropdown: {option_xpath}")

                    # Esperar a que la opción específica esté disponible
                    option_element = WebDriverWait(driver, 8).until(
                        EC.element_to_be_clickable((By.XPATH, option_xpath))
                    )

                    # Obtener texto de la opción para logging
                    selected_option_text = option_element.text.strip()
                    self._log(f"✅ Opción encontrada en segundo dropdown: '{selected_option_text}'")

                    # Verificar que sea exactamente la opción que buscamos
                    if "102_UDR_FS" in selected_option_text:
                        # Hacer clic en la opción
                        driver.execute_script("arguments[0].scrollIntoView(true);", option_element)
                        time.sleep(0.5)
                        option_element.click()

                        option_found = True
                        self._log(f"🎯 Opción seleccionada en segundo dropdown: '{selected_option_text}'")
                        break
                    else:
                        self._log(f"⚠️ Opción encontrada pero no es la correcta: '{selected_option_text}'", "DEBUG")
                        continue

                except TimeoutException:
                    self._log(f"XPath {i + 1} no funcionó en segundo dropdown: {option_xpath}", "DEBUG")
                    continue
                except Exception as e:
                    self._log(f"Error con XPath {i + 1} en segundo dropdown: {str(e)}", "DEBUG")
                    continue

            # Paso 6: Verificar si se seleccionó alguna opción
            if not option_found:
                # Intentar cerrar el dropdown si sigue abierto
                try:
                    second_dropdown_trigger.click()
                    time.sleep(1)
                except:
                    pass

                self._log("❌ No se pudo encontrar la opción 102_UDR_FS", "WARNING")
                return False, "No se encontró la opción '102_UDR_FS' en el segundo dropdown"

            # Paso 7: Esperar y verificar que se haya seleccionado correctamente
            time.sleep(3)
            try:
                updated_input = driver.find_element(By.XPATH, self.second_dropdown_xpaths['input'])
                final_value = updated_input.get_attribute('value')
                self._log(f"✅ Valor final del segundo dropdown: '{final_value}'")

                if "102_UDR_FS" in final_value:
                    return True, f"Segundo dropdown seleccionado exitosamente: '{final_value}'"
                else:
                    return False, f"Segundo dropdown no se actualizó correctamente. Valor: '{final_value}'"

            except Exception as e:
                self._log(f"Error verificando selección final del segundo dropdown: {e}", "WARNING")
                return True, f"Opción seleccionada en segundo dropdown: '{selected_option_text}' (verificación parcial)"

        except Exception as e:
            error_msg = f"Error manejando segundo dropdown: {str(e)}"
            self._log(error_msg, "ERROR")
            return False, error_msg

    def _handle_third_dropdown_selection(self, driver):
        """Maneja la selección automática del tercer dropdown (PENDIENTE)"""
        try:
            self._log("🔽 Iniciando selección del tercer dropdown (PENDIENTE)...")
            wait = WebDriverWait(driver, self.third_dropdown_wait_timeout)

            # Paso 1: Buscar el trigger del tercer dropdown
            self._log("Buscando trigger del tercer dropdown...")
            third_dropdown_trigger = None

            try:
                third_dropdown_trigger = wait.until(
                    EC.element_to_be_clickable((By.XPATH, self.third_dropdown_xpaths['trigger']))
                )
                self._log("✅ Trigger del tercer dropdown encontrado")
            except TimeoutException:
                self._log("❌ No se encontró el trigger del tercer dropdown", "WARNING")
                return False, "Tercer dropdown no encontrado en la página"

            # Paso 2: Verificar valor actual del input
            try:
                current_input = driver.find_element(By.XPATH, self.third_dropdown_xpaths['input'])
                current_value = current_input.get_attribute('value')
                self._log(f"📋 Valor actual del tercer dropdown: '{current_value}'")

                # Si ya tiene el valor correcto, no necesitamos hacer nada
                if "PENDIENTE" in current_value:
                    self._log("✅ El tercer dropdown ya tiene el valor correcto")
                    return True, "Tercer dropdown ya configurado con PENDIENTE"

            except Exception as e:
                self._log(f"No se pudo leer valor actual del tercer dropdown: {e}", "DEBUG")

            # Paso 3: Hacer clic en el trigger para abrir el tercer dropdown
            self._log("Haciendo clic en trigger del tercer dropdown...")
            driver.execute_script("arguments[0].scrollIntoView(true);", third_dropdown_trigger)
            time.sleep(1)
            third_dropdown_trigger.click()

            # Paso 4: ESPERAR EXPLÍCITAMENTE que aparezca la lista de opciones
            self._log("📋 Tercer dropdown abierto, esperando que aparezca la lista de opciones...")

            # Esperar a que aparezca el contenedor UL con las opciones
            try:
                WebDriverWait(driver, 15).until(
                    EC.presence_of_element_located((By.XPATH, "//ul[contains(@id, 'listEl')]"))
                )
                self._log("✅ Contenedor UL de opciones encontrado")
            except TimeoutException:
                self._log("❌ El contenedor de opciones no apareció", "WARNING")
                return False, "Lista de opciones del tercer dropdown no se cargó"

            # Esperar a que aparezcan elementos li dentro del contenedor
            try:
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located(
                        (By.XPATH, "//ul[contains(@id, 'listEl')]//li[@class='x-boundlist-item']"))
                )
                self._log("✅ Elementos li de opciones encontrados")
            except TimeoutException:
                self._log("❌ Los elementos li no aparecieron", "WARNING")
                return False, "Opciones individuales del tercer dropdown no se cargaron"

            # Espera adicional para asegurar carga completa
            time.sleep(3)
            self._log("📋 Lista de opciones completamente cargada, buscando 'PENDIENTE'...")

            # Paso 5: Buscar y seleccionar la opción "PENDIENTE"
            option_found = False
            selected_option_text = ""

            # Intentar con los XPaths definidos
            for i, option_xpath in enumerate(self.third_dropdown_xpaths['options']):
                try:
                    self._log(f"Probando XPath {i + 1} en tercer dropdown: {option_xpath}")

                    # Esperar a que la opción específica esté disponible
                    option_element = WebDriverWait(driver, 8).until(
                        EC.element_to_be_clickable((By.XPATH, option_xpath))
                    )

                    # Obtener texto de la opción para logging
                    selected_option_text = option_element.text.strip()
                    self._log(f"✅ Opción encontrada en tercer dropdown: '{selected_option_text}'")

                    # Verificar que sea exactamente la opción que buscamos
                    if "PENDIENTE" in selected_option_text:
                        # Hacer clic en la opción
                        driver.execute_script("arguments[0].scrollIntoView(true);", option_element)
                        time.sleep(0.5)
                        option_element.click()

                        option_found = True
                        self._log(f"🎯 Opción seleccionada en tercer dropdown: '{selected_option_text}'")
                        break
                    else:
                        self._log(f"⚠️ Opción encontrada pero no es la correcta: '{selected_option_text}'", "DEBUG")
                        continue

                except TimeoutException:
                    self._log(f"XPath {i + 1} no funcionó en tercer dropdown: {option_xpath}", "DEBUG")
                    continue
                except Exception as e:
                    self._log(f"Error con XPath {i + 1} en tercer dropdown: {str(e)}", "DEBUG")
                    continue

            # Paso 6: Verificar si se seleccionó alguna opción
            if not option_found:
                # Intentar cerrar el dropdown si sigue abierto
                try:
                    third_dropdown_trigger.click()
                    time.sleep(1)
                except:
                    pass

                self._log("❌ No se pudo encontrar la opción PENDIENTE", "WARNING")
                return False, "No se encontró la opción 'PENDIENTE' en el tercer dropdown"

            # Paso 7: Esperar y verificar que se haya seleccionado correctamente
            time.sleep(3)
            try:
                updated_input = driver.find_element(By.XPATH, self.third_dropdown_xpaths['input'])
                final_value = updated_input.get_attribute('value')
                self._log(f"✅ Valor final del tercer dropdown: '{final_value}'")

                if "PENDIENTE" in final_value:
                    return True, f"Tercer dropdown seleccionado exitosamente: '{final_value}'"
                else:
                    return False, f"Tercer dropdown no se actualizó correctamente. Valor: '{final_value}'"

            except Exception as e:
                self._log(f"Error verificando selección final del tercer dropdown: {e}", "WARNING")
                return True, f"Opción seleccionada en tercer dropdown: '{selected_option_text}' (verificación parcial)"

        except Exception as e:
            error_msg = f"Error manejando tercer dropdown: {str(e)}"
            self._log(error_msg, "ERROR")
            return False, error_msg

    def _handle_tab_button_click(self, driver):
        """Maneja el clic en el botón de pestaña después de la selección del primer dropdown"""
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

                return True, "Botón de pestaña clickeado exitosamente"

            except Exception as e:
                error_msg = f"Error haciendo clic en el botón: {str(e)}"
                self._log(error_msg, "ERROR")
                return False, error_msg

        except Exception as e:
            error_msg = f"Error manejando botón de pestaña: {str(e)}"
            self._log(error_msg, "ERROR")
            return False, error_msg

    def _handle_action_button_click(self, driver):
        """Maneja el clic en el botón de acción final después de los dropdowns"""
        try:
            self._log("🔘 Iniciando clic en botón de acción final...")
            wait = WebDriverWait(driver, self.action_button_wait_timeout)

            # Paso 1: Buscar el botón de acción
            self._log(f"Buscando botón de acción: {self.action_button_xpath}")
            action_button = None

            try:
                action_button = wait.until(
                    EC.element_to_be_clickable((By.XPATH, self.action_button_xpath))
                )
                self._log("✅ Botón de acción encontrado")
            except TimeoutException:
                self._log("❌ No se encontró el botón de acción", "WARNING")
                return False, "Botón de acción no encontrado en la página"

            # Paso 2: Verificar que el botón esté visible y clickeable
            try:
                # Hacer scroll al botón si es necesario
                self._log("Haciendo scroll al botón de acción...")
                driver.execute_script("arguments[0].scrollIntoView(true);", action_button)
                time.sleep(1)

                # Verificar si el botón está habilitado
                if not action_button.is_enabled():
                    self._log("⚠️ El botón de acción está deshabilitado", "WARNING")
                    return False, "El botón de acción está deshabilitado"

                # Verificar si el botón está visible
                if not action_button.is_displayed():
                    self._log("⚠️ El botón de acción no está visible", "WARNING")
                    return False, "El botón de acción no está visible"

                self._log("✅ Botón de acción está listo para hacer clic")

            except Exception as e:
                self._log(f"Error verificando estado del botón de acción: {e}", "WARNING")
                # Continuar de todas formas intentando hacer clic

            # Paso 3: Hacer clic en el botón de acción
            try:
                self._log("Haciendo clic en botón de acción...")
                action_button.click()
                self._log("🎯 Clic en botón de acción ejecutado")

                # Esperar un poco para que se procese la acción
                time.sleep(3)

                # Paso 4: Verificar que el clic fue exitoso
                try:
                    current_url = driver.current_url
                    self._log(f"📍 URL después del clic en botón de acción: {current_url}")

                    return True, "Botón de acción clickeado exitosamente"

                except Exception as e:
                    self._log(f"Error verificando resultado del clic en botón de acción: {e}", "DEBUG")
                    return True, "Botón de acción clickeado (verificación parcial)"

            except Exception as e:
                error_msg = f"Error haciendo clic en el botón de acción: {str(e)}"
                self._log(error_msg, "ERROR")
                return False, error_msg

        except Exception as e:
            error_msg = f"Error manejando botón de acción: {str(e)}"
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

    def start_automation(self, username=None, password=None, date_config=None):
        """🔄 Inicia el proceso de automatización completo: login, tres dropdowns, configuración de fechas y ambos botones"""
        try:
            with self._lock:
                if self.is_running:
                    return False, "La automatización ya está en ejecución"

                if not SELENIUM_AVAILABLE:
                    # Fallback al método original si Selenium no está disponible
                    self._log("Selenium no disponible, usando método básico")
                    webbrowser.open(self.target_url)
                    self.is_running = True
                    return True, "Automatización iniciada (modo básico - sin login automático ni configuración de fechas)"

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

                # 🆕 Procesar configuración de fechas
                if not date_config:
                    date_config = {'skip_dates': True}

                self._log(
                    "Iniciando proceso de automatización completa: login, tres dropdowns, configuración de fechas y botones...")
                if date_config.get('skip_dates', True):
                    self._log("📅 Configuración de fechas: OMITIR")
                else:
                    date_from = date_config.get('date_from', 'No especificada')
                    date_to = date_config.get('date_to', 'No especificada')
                    self._log(f"📅 Configuración de fechas: Desde={date_from}, Hasta={date_to}")

                # Configurar driver
                self._log("Configurando navegador...")
                driver, success, setup_message = self._setup_chrome_driver()
                if not success:
                    return False, setup_message

                self.driver = driver
                self._log("Navegador configurado, iniciando automatización completa...")

                # 🔄 Realizar login y configuración completa (incluyendo fechas)
                login_success, login_message = self._perform_login(driver, username, password, date_config)
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

    def test_credentials(self, username, password, date_config=None):
        """🔄 Prueba las credenciales ejecutando el proceso completo: login, dropdowns, fechas y botones"""
        try:
            if not SELENIUM_AVAILABLE:
                return False, "Selenium no está disponible para probar credenciales"

            # Validar formato de credenciales
            valid, message = self.credentials_manager.validate_credentials(username, password)
            if not valid:
                return False, message

            # 🆕 Si no se proporciona configuración de fechas, usar omitir
            if not date_config:
                date_config = {'skip_dates': True}

            self._log("Iniciando prueba completa de automatización: login, dropdowns, fechas y botones...")

            # Configurar driver temporal
            driver, success, setup_message = self._setup_chrome_driver()
            if not success:
                return False, setup_message

            try:
                self._log("Driver configurado, ejecutando prueba completa...")
                # 🔄 Realizar prueba completa (login, tres dropdowns, configuración de fechas y ambos botones)
                automation_success, automation_message = self._perform_login(driver, username, password, date_config)

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

    def get_current_dropdown_values(self):
        """Obtiene los valores actuales de los tres dropdowns"""
        if not self.driver or not self.is_running:
            return None

        try:
            values = {}

            # Primer dropdown
            try:
                first_input = self.driver.find_element(By.XPATH, self.dropdown_xpaths['input'])
                values['first_dropdown'] = first_input.get_attribute('value')
                self._log(f"Valor actual primer dropdown: '{values['first_dropdown']}'")
            except Exception as e:
                self._log(f"Error obteniendo valor del primer dropdown: {e}", "WARNING")
                values['first_dropdown'] = None

            # Segundo dropdown
            try:
                second_input = self.driver.find_element(By.XPATH, self.second_dropdown_xpaths['input'])
                values['second_dropdown'] = second_input.get_attribute('value')
                self._log(f"Valor actual segundo dropdown: '{values['second_dropdown']}'")
            except Exception as e:
                self._log(f"Error obteniendo valor del segundo dropdown: {e}", "WARNING")
                values['second_dropdown'] = None

            # Tercer dropdown
            try:
                third_input = self.driver.find_element(By.XPATH, self.third_dropdown_xpaths['input'])
                values['third_dropdown'] = third_input.get_attribute('value')
                self._log(f"Valor actual tercer dropdown: '{values['third_dropdown']}'")
            except Exception as e:
                self._log(f"Error obteniendo valor del tercer dropdown: {e}", "WARNING")
                values['third_dropdown'] = None

            return values
        except Exception as e:
            self._log(f"Error obteniendo valores de dropdowns: {e}", "WARNING")
            return None

    # 🆕 MÉTODOS PARA MANEJO MANUAL DE FECHAS

    def get_current_date_values(self):
        """Obtiene los valores actuales de los campos de fecha"""
        if not self.driver or not self.is_running:
            return None

        try:
            values = {}

            # Campo Desde
            try:
                date_from_input = self.driver.find_element(By.XPATH, self.date_field_xpaths['date_from'])
                values['date_from'] = date_from_input.get_attribute('value')
                self._log(f"Valor actual fecha Desde: '{values['date_from']}'")
            except Exception as e:
                self._log(f"Error obteniendo valor de fecha Desde: {e}", "WARNING")
                values['date_from'] = None

            # Campo Hasta
            try:
                date_to_input = self.driver.find_element(By.XPATH, self.date_field_xpaths['date_to'])
                values['date_to'] = date_to_input.get_attribute('value')
                self._log(f"Valor actual fecha Hasta: '{values['date_to']}'")
            except Exception as e:
                self._log(f"Error obteniendo valor de fecha Hasta: {e}", "WARNING")
                values['date_to'] = None

            return values
        except Exception as e:
            self._log(f"Error obteniendo valores de fechas: {e}", "WARNING")
            return None

    def configure_date_manually(self, date_config):
        """Configura fechas manualmente en automatización activa"""
        if not self.driver or not self.is_running:
            return False, "No hay automatización activa"

        try:
            date_success, date_message = self._handle_date_configuration(self.driver, date_config)
            return date_success, date_message
        except Exception as e:
            error_msg = f"Error configurando fechas manualmente: {str(e)}"
            self._log(error_msg, "ERROR")
            return False, error_msg

    def click_tab_button_manually(self):
        """Ejecuta solo el clic en el botón de pestaña (para uso manual)"""
        if not self.driver or not self.is_running:
            return False, "No hay automatización activa"

        try:
            button_success, button_message = self._handle_tab_button_click(self.driver)
            return button_success, button_message
        except Exception as e:
            error_msg = f"Error haciendo clic manual en botón de pestaña: {str(e)}"
            self._log(error_msg, "ERROR")
            return False, error_msg

    def click_action_button_manually(self):
        """Ejecuta solo el clic en el botón de acción (para uso manual)"""
        if not self.driver or not self.is_running:
            return False, "No hay automatización activa"

        try:
            action_success, action_message = self._handle_action_button_click(self.driver)
            return action_success, action_message
        except Exception as e:
            error_msg = f"Error haciendo clic manual en botón de acción: {str(e)}"
            self._log(error_msg, "ERROR")
            return False, error_msg