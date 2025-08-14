# button_handler.py
# Ubicación: /syncro_bot/gui/components/automation/handlers/button_handler.py
"""
Gestor especializado de botones para automatización.
Maneja el clic en botón de pestaña y botón de acción con validaciones
de estado, visibilidad y esperas robustas.
"""

import time

# Importaciones para Selenium
try:
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.common.exceptions import TimeoutException

    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False


class ButtonHandler:
    """Gestor especializado de botones para automatización"""

    def __init__(self, web_driver_manager, logger=None):
        self.web_driver_manager = web_driver_manager
        self.logger = logger

        # XPaths para botones
        self.button_xpaths = {
            'tab_button': '//*[@id="tab-1030-btnEl"]',
            'action_button': '//*[@id="button-1146-btnEl"]'
        }

        # Configuración de timeouts específicos para botones
        self.button_wait_timeout = 15
        self.action_button_wait_timeout = 15

    def _log(self, message, level="INFO"):
        """Log interno con fallback"""
        if self.logger:
            self.logger(message, level)
        else:
            print(f"[{level}] {message}")

    def handle_tab_button_click(self, driver):
        """Maneja el clic en el botón de pestaña después de la selección del primer dropdown"""
        try:
            self._log("🔘 Iniciando clic en botón de pestaña...")
            wait = WebDriverWait(driver, self.button_wait_timeout)

            # Paso 1: Buscar el botón de pestaña
            self._log(f"Buscando botón de pestaña: {self.button_xpaths['tab_button']}")
            tab_button = None

            try:
                tab_button = wait.until(
                    EC.element_to_be_clickable((By.XPATH, self.button_xpaths['tab_button']))
                )
                self._log("✅ Botón de pestaña encontrado")
            except TimeoutException:
                self._log("❌ No se encontró el botón de pestaña", "WARNING")
                return False, "Botón de pestaña no encontrado en la página"

            # Paso 2: Verificar que el botón esté visible y clickeable
            try:
                # Hacer scroll al botón si es necesario
                self._log("Haciendo scroll al botón de pestaña...")
                self.web_driver_manager.scroll_to_element(tab_button)
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

    def handle_action_button_click(self, driver):
        """Maneja el clic en el botón de acción final después de los dropdowns"""
        try:
            self._log("🔘 Iniciando clic en botón de acción final...")
            wait = WebDriverWait(driver, self.action_button_wait_timeout)

            # Paso 1: Buscar el botón de acción
            self._log(f"Buscando botón de acción: {self.button_xpaths['action_button']}")
            action_button = None

            try:
                action_button = wait.until(
                    EC.element_to_be_clickable((By.XPATH, self.button_xpaths['action_button']))
                )
                self._log("✅ Botón de acción encontrado")
            except TimeoutException:
                self._log("❌ No se encontró el botón de acción", "WARNING")
                return False, "Botón de acción no encontrado en la página"

            # Paso 2: Verificar que el botón esté visible y clickeable
            try:
                # Hacer scroll al botón si es necesario
                self._log("Haciendo scroll al botón de acción...")
                self.web_driver_manager.scroll_to_element(action_button)
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

    def validate_buttons_present(self, driver):
        """Verifica si ambos botones están presentes en la página"""
        try:
            wait = WebDriverWait(driver, 5)
            results = {}

            # Verificar botón de pestaña
            try:
                tab_button = wait.until(
                    EC.presence_of_element_located((By.XPATH, self.button_xpaths['tab_button']))
                )
                results['tab_button'] = True
                self._log("Botón de pestaña encontrado")
            except TimeoutException:
                results['tab_button'] = False
                self._log("Botón de pestaña no encontrado", "WARNING")

            # Verificar botón de acción
            try:
                action_button = wait.until(
                    EC.presence_of_element_located((By.XPATH, self.button_xpaths['action_button']))
                )
                results['action_button'] = True
                self._log("Botón de acción encontrado")
            except TimeoutException:
                results['action_button'] = False
                self._log("Botón de acción no encontrado", "WARNING")

            # Determinar resultado general
            all_present = all(results.values())
            if all_present:
                return True, "Todos los botones están presentes"
            else:
                missing = [name for name, present in results.items() if not present]
                return False, f"Botones faltantes: {', '.join(missing)}"

        except Exception as e:
            error_msg = f"Error verificando botones: {str(e)}"
            self._log(error_msg, "ERROR")
            return False, error_msg

    def get_button_states(self, driver):
        """Obtiene el estado de ambos botones (habilitado, visible, etc.)"""
        try:
            button_states = {}

            for button_name, xpath in self.button_xpaths.items():
                try:
                    button_element = driver.find_element(By.XPATH, xpath)
                    button_states[button_name] = {
                        'present': True,
                        'enabled': button_element.is_enabled(),
                        'displayed': button_element.is_displayed(),
                        'text': button_element.text.strip() if hasattr(button_element, 'text') else '',
                        'tag_name': button_element.tag_name
                    }
                    self._log(
                        f"Estado del {button_name}: habilitado={button_states[button_name]['enabled']}, visible={button_states[button_name]['displayed']}")
                except Exception as e:
                    button_states[button_name] = {
                        'present': False,
                        'enabled': False,
                        'displayed': False,
                        'text': '',
                        'tag_name': '',
                        'error': str(e)
                    }
                    self._log(f"Error obteniendo estado del {button_name}: {e}", "WARNING")

            return button_states

        except Exception as e:
            error_msg = f"Error obteniendo estados de botones: {str(e)}"
            self._log(error_msg, "ERROR")
            return None

    def wait_for_button_to_be_clickable(self, driver, button_name, timeout=None):
        """Espera que un botón específico esté clickeable"""
        try:
            if button_name not in self.button_xpaths:
                return False, f"Botón desconocido: {button_name}"

            xpath = self.button_xpaths[button_name]
            wait_timeout = timeout or self.button_wait_timeout

            self._log(f"Esperando que {button_name} esté clickeable...")
            wait = WebDriverWait(driver, wait_timeout)

            button_element = wait.until(
                EC.element_to_be_clickable((By.XPATH, xpath))
            )

            self._log(f"✅ {button_name} está clickeable")
            return True, f"{button_name} listo para clic"

        except TimeoutException:
            error_msg = f"Timeout esperando que {button_name} esté clickeable ({wait_timeout}s)"
            self._log(error_msg, "ERROR")
            return False, error_msg
        except Exception as e:
            error_msg = f"Error esperando {button_name}: {str(e)}"
            self._log(error_msg, "ERROR")
            return False, error_msg

    def click_button_by_name(self, driver, button_name):
        """Hace clic en un botón específico por nombre"""
        try:
            if button_name == 'tab_button':
                return self.handle_tab_button_click(driver)
            elif button_name == 'action_button':
                return self.handle_action_button_click(driver)
            else:
                return False, f"Botón desconocido: {button_name}"

        except Exception as e:
            error_msg = f"Error haciendo clic en {button_name}: {str(e)}"
            self._log(error_msg, "ERROR")
            return False, error_msg

    def process_all_buttons(self, driver):
        """Procesa ambos botones en secuencia"""
        try:
            self._log("🔘 Iniciando procesamiento de todos los botones...")

            # Botón de pestaña primero
            tab_success, tab_message = self.handle_tab_button_click(driver)
            if not tab_success:
                return False, f"Error en botón de pestaña: {tab_message}"

            # Esperar un poco entre botones
            time.sleep(2)

            # Botón de acción después
            action_success, action_message = self.handle_action_button_click(driver)
            if not action_success:
                return False, f"Error en botón de acción: {action_message}"

            return True, "Todos los botones procesados exitosamente"

        except Exception as e:
            error_msg = f"Error procesando botones: {str(e)}"
            self._log(error_msg, "ERROR")
            return False, error_msg

    def verify_button_click_result(self, driver, button_name):
        """Verifica el resultado después de hacer clic en un botón"""
        try:
            self._log(f"🔍 Verificando resultado del clic en {button_name}...")

            # Obtener información actual
            current_url = driver.current_url
            page_title = driver.title

            # Esperar un poco para que se procesen los cambios
            time.sleep(2)

            # Verificar cambios en la página
            new_url = driver.current_url
            new_title = driver.title

            changes_detected = []

            if current_url != new_url:
                changes_detected.append(f"URL cambió: {current_url} → {new_url}")

            if page_title != new_title:
                changes_detected.append(f"Título cambió: {page_title} → {new_title}")

            if changes_detected:
                result_message = f"Clic en {button_name} exitoso - Cambios detectados: {'; '.join(changes_detected)}"
                self._log(f"✅ {result_message}")
                return True, result_message
            else:
                result_message = f"Clic en {button_name} ejecutado (sin cambios visibles en URL/título)"
                self._log(f"⚠️ {result_message}")
                return True, result_message

        except Exception as e:
            error_msg = f"Error verificando resultado del clic en {button_name}: {str(e)}"
            self._log(error_msg, "ERROR")
            return False, error_msg

    def get_button_info(self, driver, button_name):
        """Obtiene información detallada de un botón específico"""
        try:
            if button_name not in self.button_xpaths:
                return None

            xpath = self.button_xpaths[button_name]
            button_element = driver.find_element(By.XPATH, xpath)

            info = {
                'name': button_name,
                'xpath': xpath,
                'present': True,
                'enabled': button_element.is_enabled(),
                'displayed': button_element.is_displayed(),
                'text': button_element.text.strip(),
                'tag_name': button_element.tag_name,
                'location': button_element.location,
                'size': button_element.size
            }

            # Obtener atributos adicionales si están disponibles
            try:
                info['id'] = button_element.get_attribute('id')
                info['class'] = button_element.get_attribute('class')
                info['type'] = button_element.get_attribute('type')
            except:
                pass

            return info

        except Exception as e:
            self._log(f"Error obteniendo información del {button_name}: {e}", "WARNING")
            return {
                'name': button_name,
                'xpath': self.button_xpaths.get(button_name, ''),
                'present': False,
                'error': str(e)
            }