# dropdown_handler.py
# Ubicación: /syncro_bot/gui/components/automation/handlers/dropdown_handler.py
"""
Gestor especializado de los tres dropdowns de automatización.
Maneja la selección automática de: 140_AUTO INSTALACION, 102_UDR_FS y PENDIENTE
con esperas robustas y validación de carga completa de opciones.
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


class DropdownHandler:
    """Gestor especializado de los tres dropdowns de automatización"""

    def __init__(self, web_driver_manager, logger=None):
        self.web_driver_manager = web_driver_manager
        self.logger = logger

        # XPaths para primer dropdown de despacho (140_AUTO INSTALACION)
        self.first_dropdown_xpaths = {
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

        # Configuración de timeouts específicos para dropdowns
        self.dropdown_wait_timeout = 15
        self.second_dropdown_wait_timeout = 20
        self.third_dropdown_wait_timeout = 20

    def _log(self, message, level="INFO"):
        """Log interno con fallback"""
        if self.logger:
            self.logger(message, level)
        else:
            print(f"[{level}] {message}")

    def handle_first_dropdown_selection(self, driver):
        """Maneja la selección automática del primer dropdown (140_AUTO INSTALACION)"""
        try:
            self._log("🔽 Iniciando selección del primer dropdown (140_AUTO INSTALACION)...")
            wait = WebDriverWait(driver, self.dropdown_wait_timeout)

            # Paso 1: Buscar el trigger del dropdown
            self._log("Buscando trigger del primer dropdown...")
            dropdown_trigger = None

            try:
                dropdown_trigger = wait.until(
                    EC.element_to_be_clickable((By.XPATH, self.first_dropdown_xpaths['trigger']))
                )
                self._log("✅ Trigger del primer dropdown encontrado")
            except TimeoutException:
                self._log("❌ No se encontró el trigger del primer dropdown", "WARNING")
                return False, "Primer dropdown de despacho no encontrado en la página"

            # Paso 2: Verificar valor actual del input
            try:
                current_input = driver.find_element(By.XPATH, self.first_dropdown_xpaths['input'])
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
            self.web_driver_manager.scroll_to_element(dropdown_trigger)
            time.sleep(1)
            dropdown_trigger.click()

            # Esperar un poco para que se abra el dropdown
            time.sleep(2)
            self._log("📋 Primer dropdown abierto, buscando opciones...")

            # Paso 4: Buscar y seleccionar la opción "140_AUTO INSTALACION"
            option_found = False
            selected_option_text = ""

            # Intentar con diferentes XPaths para encontrar la opción
            for i, option_xpath in enumerate(self.first_dropdown_xpaths['options']):
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
                    self.web_driver_manager.scroll_to_element(option_element)
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
                updated_input = driver.find_element(By.XPATH, self.first_dropdown_xpaths['input'])
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

    def handle_second_dropdown_selection(self, driver):
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
            self.web_driver_manager.scroll_to_element(second_dropdown_trigger)
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
                        self.web_driver_manager.scroll_to_element(option_element)
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

    def handle_third_dropdown_selection(self, driver):
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
            self.web_driver_manager.scroll_to_element(third_dropdown_trigger)
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
                        self.web_driver_manager.scroll_to_element(option_element)
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

    def get_current_dropdown_values(self, driver):
        """Obtiene los valores actuales de los tres dropdowns"""
        try:
            values = {}

            # Primer dropdown
            try:
                first_input = driver.find_element(By.XPATH, self.first_dropdown_xpaths['input'])
                values['first_dropdown'] = first_input.get_attribute('value')
                self._log(f"Valor actual primer dropdown: '{values['first_dropdown']}'")
            except Exception as e:
                self._log(f"Error obteniendo valor del primer dropdown: {e}", "WARNING")
                values['first_dropdown'] = None

            # Segundo dropdown
            try:
                second_input = driver.find_element(By.XPATH, self.second_dropdown_xpaths['input'])
                values['second_dropdown'] = second_input.get_attribute('value')
                self._log(f"Valor actual segundo dropdown: '{values['second_dropdown']}'")
            except Exception as e:
                self._log(f"Error obteniendo valor del segundo dropdown: {e}", "WARNING")
                values['second_dropdown'] = None

            # Tercer dropdown
            try:
                third_input = driver.find_element(By.XPATH, self.third_dropdown_xpaths['input'])
                values['third_dropdown'] = third_input.get_attribute('value')
                self._log(f"Valor actual tercer dropdown: '{values['third_dropdown']}'")
            except Exception as e:
                self._log(f"Error obteniendo valor del tercer dropdown: {e}", "WARNING")
                values['third_dropdown'] = None

            return values
        except Exception as e:
            self._log(f"Error obteniendo valores de dropdowns: {e}", "WARNING")
            return None

    def validate_dropdown_selections(self, driver):
        """Valida que todos los dropdowns tengan los valores correctos"""
        try:
            values = self.get_current_dropdown_values(driver)
            if not values:
                return False, "No se pudieron obtener valores de dropdowns"

            errors = []

            # Validar primer dropdown
            if not values['first_dropdown'] or "140_AUTO" not in values['first_dropdown']:
                errors.append("Primer dropdown no tiene '140_AUTO INSTALACION'")

            # Validar segundo dropdown
            if not values['second_dropdown'] or "102_UDR_FS" not in values['second_dropdown']:
                errors.append("Segundo dropdown no tiene '102_UDR_FS'")

            # Validar tercer dropdown
            if not values['third_dropdown'] or "PENDIENTE" not in values['third_dropdown']:
                errors.append("Tercer dropdown no tiene 'PENDIENTE'")

            if errors:
                return False, f"Errores de validación: {'; '.join(errors)}"

            return True, "Todos los dropdowns están correctamente configurados"

        except Exception as e:
            error_msg = f"Error validando dropdowns: {str(e)}"
            self._log(error_msg, "ERROR")
            return False, error_msg

    def process_all_dropdowns(self, driver):
        """Procesa los tres dropdowns en secuencia"""
        try:
            self._log("🔽 Iniciando procesamiento de todos los dropdowns...")

            # Primer dropdown
            first_success, first_message = self.handle_first_dropdown_selection(driver)
            if not first_success:
                return False, f"Error en primer dropdown: {first_message}"

            # Segundo dropdown
            second_success, second_message = self.handle_second_dropdown_selection(driver)
            if not second_success:
                return False, f"Error en segundo dropdown: {second_message}"

            # Tercer dropdown
            third_success, third_message = self.handle_third_dropdown_selection(driver)
            if not third_success:
                return False, f"Error en tercer dropdown: {third_message}"

            # Validación final
            validation_success, validation_message = self.validate_dropdown_selections(driver)
            if not validation_success:
                return False, f"Validación falló: {validation_message}"

            return True, "Todos los dropdowns procesados exitosamente"

        except Exception as e:
            error_msg = f"Error procesando dropdowns: {str(e)}"
            self._log(error_msg, "ERROR")
            return False, error_msg