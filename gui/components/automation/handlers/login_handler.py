# login_handler.py
# Ubicación: /syncro_bot/gui/components/automation/handlers/login_handler.py
"""
Gestor especializado del proceso de login automático.
Maneja la autenticación completa incluyendo ingreso de credenciales,
clic en botón de login y verificación de éxito con múltiples métodos.
"""

import time

# Importaciones para Selenium
try:
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.common.exceptions import TimeoutException, NoSuchElementException

    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False


class LoginHandler:
    """Gestor especializado del proceso de login automático"""

    def __init__(self, web_driver_manager, logger=None):
        self.web_driver_manager = web_driver_manager
        self.logger = logger

        # XPaths para elementos de login
        self.login_xpaths = {
            'username': '//*[@id="textfield-1039-inputEl"]',
            'password': '//*[@id="textfield-1040-inputEl"]',
            'login_button': '//*[@id="button-1041-btnEl"]'
        }

        # Configuración de timeouts específicos para login
        self.element_wait_timeout = 25
        self.login_response_timeout = 8

    def _log(self, message, level="INFO"):
        """Log interno con fallback"""
        if self.logger:
            self.logger(message, level)
        else:
            print(f"[{level}] {message}")

    def perform_login(self, driver, username, password):
        """Realiza el proceso completo de login automático"""
        try:
            wait = WebDriverWait(driver, self.element_wait_timeout)

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
            self.web_driver_manager.scroll_to_element(login_button)
            time.sleep(1)

            # Hacer clic en el botón de login
            self._log("Haciendo clic en botón de login...")
            login_button.click()

            # Esperar más tiempo para que procese el login
            self._log("Esperando respuesta del servidor...")
            time.sleep(self.login_response_timeout)

            # Verificar resultado del login con múltiples métodos
            login_success, login_message = self._verify_login_success(driver, wait)
            return login_success, login_message

        except Exception as e:
            error_msg = f"Error en proceso de login: {str(e)}"
            self._log(error_msg, "ERROR")
            return False, error_msg

    def _verify_login_success(self, driver, wait):
        """Verifica si el login fue exitoso con múltiples métodos"""
        try:
            current_url = driver.current_url
            self._log(f"URL después del login: {current_url}")

            # Obtener URL objetivo del web_driver_manager o usar una por defecto
            target_url = getattr(self.web_driver_manager, 'target_url',
                                 "https://fieldservice.cabletica.com/dispatchFS/")

            # Método 1: Verificar cambio de URL
            if current_url != target_url and "login" not in current_url.lower():
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
                    "//*[@id='combo-1077-trigger-picker']"  # El dropdown principal es un buen indicador
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

            if final_url != target_url and "login" not in final_url.lower():
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

    def check_login_fields_present(self, driver):
        """Verifica si los campos de login están presentes en la página"""
        try:
            wait = WebDriverWait(driver, 5)

            # Verificar campo de usuario
            try:
                username_field = wait.until(
                    EC.presence_of_element_located((By.XPATH, self.login_xpaths['username']))
                )
                self._log("Campo de usuario encontrado")
            except TimeoutException:
                return False, "Campo de usuario no encontrado"

            # Verificar campo de contraseña
            try:
                password_field = wait.until(
                    EC.presence_of_element_located((By.XPATH, self.login_xpaths['password']))
                )
                self._log("Campo de contraseña encontrado")
            except TimeoutException:
                return False, "Campo de contraseña no encontrado"

            # Verificar botón de login
            try:
                login_button = wait.until(
                    EC.presence_of_element_located((By.XPATH, self.login_xpaths['login_button']))
                )
                self._log("Botón de login encontrado")
            except TimeoutException:
                return False, "Botón de login no encontrado"

            return True, "Todos los campos de login están presentes"

        except Exception as e:
            error_msg = f"Error verificando campos de login: {str(e)}"
            self._log(error_msg, "ERROR")
            return False, error_msg

    def clear_login_fields(self, driver):
        """Limpia los campos de login"""
        try:
            wait = WebDriverWait(driver, 10)

            # Limpiar campo de usuario
            try:
                username_field = wait.until(
                    EC.element_to_be_clickable((By.XPATH, self.login_xpaths['username']))
                )
                username_field.clear()
                self._log("Campo de usuario limpiado")
            except Exception as e:
                self._log(f"Error limpiando campo de usuario: {e}", "WARNING")

            # Limpiar campo de contraseña
            try:
                password_field = wait.until(
                    EC.element_to_be_clickable((By.XPATH, self.login_xpaths['password']))
                )
                password_field.clear()
                self._log("Campo de contraseña limpiado")
            except Exception as e:
                self._log(f"Error limpiando campo de contraseña: {e}", "WARNING")

            return True, "Campos de login limpiados"

        except Exception as e:
            error_msg = f"Error limpiando campos de login: {str(e)}"
            self._log(error_msg, "ERROR")
            return False, error_msg

    def get_login_field_values(self, driver):
        """Obtiene los valores actuales de los campos de login"""
        try:
            values = {}

            # Obtener valor del campo de usuario
            try:
                username_field = driver.find_element(By.XPATH, self.login_xpaths['username'])
                values['username'] = username_field.get_attribute('value')
            except Exception as e:
                self._log(f"Error obteniendo valor de usuario: {e}", "WARNING")
                values['username'] = None

            # Obtener valor del campo de contraseña (generalmente no se puede por seguridad)
            try:
                password_field = driver.find_element(By.XPATH, self.login_xpaths['password'])
                values['password'] = password_field.get_attribute('value')
            except Exception as e:
                self._log(f"Error obteniendo valor de contraseña: {e}", "WARNING")
                values['password'] = None

            return values

        except Exception as e:
            error_msg = f"Error obteniendo valores de campos: {str(e)}"
            self._log(error_msg, "ERROR")
            return None

    def validate_login_page(self, driver):
        """Valida que estemos en la página de login correcta"""
        try:
            current_url = driver.current_url
            page_title = driver.title

            # Verificar URL
            if "fieldservice.cabletica.com" not in current_url:
                return False, "No estamos en la página de Cabletica"

            # Verificar que los campos de login estén presentes
            fields_present, fields_message = self.check_login_fields_present(driver)
            if not fields_present:
                return False, f"Página de login inválida: {fields_message}"

            self._log(f"Página de login validada - URL: {current_url}, Título: {page_title}")
            return True, "Página de login válida"

        except Exception as e:
            error_msg = f"Error validando página de login: {str(e)}"
            self._log(error_msg, "ERROR")
            return False, error_msg

    def wait_for_login_form(self, driver, timeout=30):
        """Espera que aparezca el formulario de login"""
        try:
            wait = WebDriverWait(driver, timeout)

            self._log("Esperando que aparezca el formulario de login...")

            # Esperar a que aparezcan todos los elementos del login
            username_field = wait.until(
                EC.element_to_be_clickable((By.XPATH, self.login_xpaths['username']))
            )

            password_field = wait.until(
                EC.element_to_be_clickable((By.XPATH, self.login_xpaths['password']))
            )

            login_button = wait.until(
                EC.element_to_be_clickable((By.XPATH, self.login_xpaths['login_button']))
            )

            self._log("Formulario de login completamente cargado")
            return True, "Formulario de login disponible"

        except TimeoutException:
            error_msg = f"Timeout esperando formulario de login ({timeout}s)"
            self._log(error_msg, "ERROR")
            return False, error_msg
        except Exception as e:
            error_msg = f"Error esperando formulario de login: {str(e)}"
            self._log(error_msg, "ERROR")
            return False, error_msg

    def is_already_logged_in(self, driver):
        """Verifica si ya estamos logueados"""
        try:
            current_url = driver.current_url

            # Si no estamos en una página de login, probablemente ya estamos logueados
            if "login" not in current_url.lower():
                # Verificar si hay elementos que indiquen que estamos logueados
                try:
                    WebDriverWait(driver, 3).until(
                        EC.presence_of_element_located((By.XPATH, "//*[@id='combo-1077-trigger-picker']"))
                    )
                    self._log("Usuario ya está logueado")
                    return True, "Ya está logueado"
                except:
                    pass

            return False, "Usuario no está logueado"

        except Exception as e:
            error_msg = f"Error verificando estado de login: {str(e)}"
            self._log(error_msg, "ERROR")
            return False, error_msg