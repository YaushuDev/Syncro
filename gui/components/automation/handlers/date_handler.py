# date_handler.py
# Ubicación: /syncro_bot/gui/components/automation/handlers/date_handler.py
"""
Gestor especializado de configuración de fechas para automatización.
Maneja la configuración completa de campos de fecha Desde/Hasta con
formato DD/MM/YYYY, validación y limpieza de campos.
"""

import time

# Importaciones para Selenium
try:
    from selenium.webdriver.common.by import By
    from selenium.webdriver.common.keys import Keys
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.common.exceptions import TimeoutException

    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False


class DateHandler:
    """Gestor especializado de configuración de fechas para automatización"""

    def __init__(self, web_driver_manager, logger=None):
        self.web_driver_manager = web_driver_manager
        self.logger = logger

        # XPaths para campos de fecha
        self.date_field_xpaths = {
            'date_from': '//*[@id="datefield-1140-inputEl"]',
            'date_to': '//*[@id="datefield-1148-inputEl"]'
        }

        # Configuración de timeouts específicos para fechas
        self.date_configuration_timeout = 15

    def _log(self, message, level="INFO"):
        """Log interno con fallback"""
        if self.logger:
            self.logger(message, level)
        else:
            print(f"[{level}] {message}")

    def handle_date_configuration(self, driver, date_config):
        """Maneja la configuración completa de fechas Desde/Hasta"""
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
            self.web_driver_manager.scroll_to_element(date_field)
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

    def get_current_date_values(self, driver):
        """Obtiene los valores actuales de los campos de fecha"""
        try:
            values = {}

            # Campo Desde
            try:
                date_from_input = driver.find_element(By.XPATH, self.date_field_xpaths['date_from'])
                values['date_from'] = date_from_input.get_attribute('value')
                self._log(f"Valor actual fecha Desde: '{values['date_from']}'")
            except Exception as e:
                self._log(f"Error obteniendo valor de fecha Desde: {e}", "WARNING")
                values['date_from'] = None

            # Campo Hasta
            try:
                date_to_input = driver.find_element(By.XPATH, self.date_field_xpaths['date_to'])
                values['date_to'] = date_to_input.get_attribute('value')
                self._log(f"Valor actual fecha Hasta: '{values['date_to']}'")
            except Exception as e:
                self._log(f"Error obteniendo valor de fecha Hasta: {e}", "WARNING")
                values['date_to'] = None

            return values
        except Exception as e:
            self._log(f"Error obteniendo valores de fechas: {e}", "WARNING")
            return None

    def clear_date_fields(self, driver):
        """Limpia ambos campos de fecha"""
        try:
            self._log("🧹 Limpiando campos de fecha...")
            results = []

            for field_key, field_name in [('date_from', 'Desde'), ('date_to', 'Hasta')]:
                try:
                    xpath = self.date_field_xpaths[field_key]
                    date_field = driver.find_element(By.XPATH, xpath)

                    # Enfocar campo
                    date_field.click()
                    time.sleep(0.5)

                    # Limpiar
                    date_field.send_keys(Keys.CONTROL + "a")
                    time.sleep(0.3)
                    date_field.send_keys(Keys.DELETE)
                    time.sleep(0.5)

                    results.append(f"{field_name}: limpiado")
                    self._log(f"🧹 Campo {field_name} limpiado")

                except Exception as e:
                    results.append(f"{field_name}: error")
                    self._log(f"Error limpiando campo {field_name}: {e}", "WARNING")

            return True, f"Limpieza de fechas: {', '.join(results)}"

        except Exception as e:
            error_msg = f"Error limpiando campos de fecha: {str(e)}"
            self._log(error_msg, "ERROR")
            return False, error_msg

    def validate_date_fields_present(self, driver):
        """Verifica si los campos de fecha están presentes en la página"""
        try:
            wait = WebDriverWait(driver, 5)

            # Verificar campo Desde
            try:
                date_from_field = wait.until(
                    EC.presence_of_element_located((By.XPATH, self.date_field_xpaths['date_from']))
                )
                self._log("Campo de fecha Desde encontrado")
            except TimeoutException:
                return False, "Campo de fecha Desde no encontrado"

            # Verificar campo Hasta
            try:
                date_to_field = wait.until(
                    EC.presence_of_element_located((By.XPATH, self.date_field_xpaths['date_to']))
                )
                self._log("Campo de fecha Hasta encontrado")
            except TimeoutException:
                return False, "Campo de fecha Hasta no encontrado"

            return True, "Todos los campos de fecha están presentes"

        except Exception as e:
            error_msg = f"Error verificando campos de fecha: {str(e)}"
            self._log(error_msg, "ERROR")
            return False, error_msg

    def set_today_dates(self, driver):
        """Establece la fecha de hoy en ambos campos"""
        try:
            from datetime import datetime
            today = datetime.now().strftime("%d/%m/%Y")

            self._log(f"📅 Estableciendo fecha de hoy: {today}")

            date_config = {
                'skip_dates': False,
                'date_from': today,
                'date_to': today
            }

            return self.handle_date_configuration(driver, date_config)

        except Exception as e:
            error_msg = f"Error estableciendo fecha de hoy: {str(e)}"
            self._log(error_msg, "ERROR")
            return False, error_msg

    def set_date_range(self, driver, date_from, date_to):
        """Establece un rango de fechas específico"""
        try:
            self._log(f"📅 Estableciendo rango de fechas: {date_from} - {date_to}")

            date_config = {
                'skip_dates': False,
                'date_from': date_from,
                'date_to': date_to
            }

            return self.handle_date_configuration(driver, date_config)

        except Exception as e:
            error_msg = f"Error estableciendo rango de fechas: {str(e)}"
            self._log(error_msg, "ERROR")
            return False, error_msg

    def validate_date_format(self, date_string):
        """Valida que una fecha tenga el formato DD/MM/YYYY correcto"""
        try:
            import re
            from datetime import datetime

            # Patrón regex para DD/MM/YYYY
            pattern = re.compile(r'^(\d{2})/(\d{2})/(\d{4})$')

            if not pattern.match(date_string):
                return False, "Formato incorrecto. Use DD/MM/YYYY"

            # Extraer componentes y validar
            day, month, year = map(int, date_string.split('/'))

            # Verificar rangos básicos
            if not (1 <= day <= 31):
                return False, f"Día inválido: {day}"
            if not (1 <= month <= 12):
                return False, f"Mes inválido: {month}"
            if not (1900 <= year <= 2100):
                return False, f"Año inválido: {year}"

            # Crear objeto datetime para validación completa
            datetime(year, month, day)
            return True, "Fecha válida"

        except ValueError as e:
            return False, f"Fecha inválida: {str(e)}"
        except Exception as e:
            return False, f"Error validando fecha: {str(e)}"

    def validate_date_range_logic(self, date_from, date_to):
        """Valida que un rango de fechas tenga lógica correcta"""
        try:
            if not date_from and not date_to:
                return True, "Sin fechas especificadas"

            if date_from and not date_to:
                return self.validate_date_format(date_from)

            if date_to and not date_from:
                return self.validate_date_format(date_to)

            # Validar ambas fechas
            from_valid, from_message = self.validate_date_format(date_from)
            if not from_valid:
                return False, f"Fecha 'Desde' inválida: {from_message}"

            to_valid, to_message = self.validate_date_format(date_to)
            if not to_valid:
                return False, f"Fecha 'Hasta' inválida: {to_message}"

            # Validar que 'Desde' no sea posterior a 'Hasta'
            from datetime import datetime
            from_parts = date_from.split('/')
            to_parts = date_to.split('/')

            from_dt = datetime(int(from_parts[2]), int(from_parts[1]), int(from_parts[0]))
            to_dt = datetime(int(to_parts[2]), int(to_parts[1]), int(to_parts[0]))

            if from_dt > to_dt:
                return False, "La fecha 'Desde' no puede ser posterior a 'Hasta'"

            diff_days = (to_dt - from_dt).days
            return True, f"Rango válido: {diff_days} días"

        except Exception as e:
            return False, f"Error validando rango: {str(e)}"

    def get_date_fields_status(self, driver):
        """Obtiene el estado completo de los campos de fecha"""
        try:
            status = {
                'fields_present': False,
                'current_values': {},
                'fields_enabled': {}
            }

            # Verificar presencia
            fields_present, _ = self.validate_date_fields_present(driver)
            status['fields_present'] = fields_present

            if fields_present:
                # Obtener valores actuales
                values = self.get_current_date_values(driver)
                if values:
                    status['current_values'] = values

                # Verificar si están habilitados
                for field_key, field_name in [('date_from', 'Desde'), ('date_to', 'Hasta')]:
                    try:
                        xpath = self.date_field_xpaths[field_key]
                        field_element = driver.find_element(By.XPATH, xpath)
                        status['fields_enabled'][field_name] = field_element.is_enabled()
                    except Exception:
                        status['fields_enabled'][field_name] = False

            return status

        except Exception as e:
            self._log(f"Error obteniendo estado de campos de fecha: {e}", "WARNING")
            return None