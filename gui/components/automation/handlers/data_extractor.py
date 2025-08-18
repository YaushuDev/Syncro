# data_extractor.py
# Ubicación: /syncro_bot/gui/components/automation/handlers/data_extractor.py
"""
Extractor especializado de datos de la tabla de resultados con funcionalidad
de doble clic para obtener números de teléfono. Maneja la extracción completa
incluyendo navegación a detalles de cliente y retorno a tabla principal.
"""

import time
from typing import List, Dict, Optional

# Importaciones para Selenium
try:
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.common.exceptions import TimeoutException, NoSuchElementException
    from selenium.webdriver.common.action_chains import ActionChains

    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False


class DataExtractor:
    """Extractor especializado de datos con funcionalidad de doble clic para teléfonos"""

    def __init__(self, web_driver_manager, logger=None):
        self.web_driver_manager = web_driver_manager
        self.logger = logger

        # XPaths y selectores para la tabla de datos
        self.table_selectors = {
            'container': '.x-grid-item-container',
            'rows': 'table.x-grid-item',
            'cells': 'td.x-grid-cell'
        }

        # Mapeo de columnas según el HTML proporcionado
        self.column_mapping = {
            'numero_orden': 'gridcolumn-1113',  # Número de Orden
            'cliente': 'gridcolumn-1115',  # Cliente (aquí haremos doble clic)
            'tecnico': 'gridcolumn-1121',  # Técnico
            'distrito': 'gridcolumn-1122',  # Distrito
            'barrio': 'gridcolumn-1123',  # Barrio
            'canton': 'gridcolumn-1124',  # Cantón
            'observaciones': 'gridcolumn-1126',  # Observaciones
            'estado': 'gridcolumn-1112',  # Estado
            'despacho': 'gridcolumn-1116'  # Despacho
        }

        # 🆕 Selectores robustos para el campo de teléfono
        self.phone_field_selectors = [
            'input[data-ref="inputEl"][role="textbox"][style*="#E0F5FF"]',  # Preferido
            'input[data-ref="inputEl"][class*="x-form-field x-form-text"]',  # Backup 1
            'input[style*="background-color: #E0F5FF"]',  # Backup 2
            'input[role="textbox"][class*="x-form-text-default"]'  # Backup 3
        ]

        # 🆕 XPath para el botón de retorno a la tabla
        self.return_button_xpath = '//*[@id="tab-1030-btnInnerEl"]'

        # Configuración de timeouts
        self.data_wait_timeout = 15
        self.extraction_wait = 3
        self.phone_popup_timeout = 10  # 🆕 Timeout para popup de teléfono
        self.phone_extraction_delay = 2  # 🆕 Delay después del doble clic

    def _log(self, message, level="INFO"):
        """Log interno con fallback"""
        if self.logger:
            self.logger(message, level)
        else:
            print(f"[{level}] {message}")

    def extract_table_data(self, driver) -> tuple[bool, str, List[Dict]]:
        """Extrae todos los datos de la tabla incluyendo números de teléfono"""
        try:
            self._log("📊 Iniciando extracción completa de datos (incluyendo teléfonos)...")

            # Esperar que aparezca la tabla con datos
            if not self._wait_for_data_table(driver):
                return False, "Tabla de datos no encontrada o no cargó", []

            # Obtener todas las filas de datos
            data_rows = self._get_table_rows(driver)
            if not data_rows:
                return False, "No se encontraron filas de datos en la tabla", []

            self._log(f"📋 Encontradas {len(data_rows)} filas de datos para extracción completa")

            # Extraer datos de cada fila (INCLUYE TELÉFONOS)
            extracted_data = []
            for row_index, row_element in enumerate(data_rows):
                try:
                    row_data = self._extract_row_data_with_phone(driver, row_element, row_index)
                    if row_data:
                        extracted_data.append(row_data)
                        cliente_nombre = row_data.get('cliente', 'N/A')
                        telefono = row_data.get('telefono_cliente', 'Sin teléfono')
                        self._log(f"✅ Fila {row_index + 1} extraída: {cliente_nombre} - Tel: {telefono}")
                    else:
                        self._log(f"⚠️ Fila {row_index + 1} no pudo ser extraída", "WARNING")
                except Exception as e:
                    self._log(f"❌ Error extrayendo fila {row_index + 1}: {str(e)}", "ERROR")
                    continue

            if extracted_data:
                success_message = f"Extracción completa: {len(extracted_data)} registros con teléfonos obtenidos"
                self._log(f"🎉 {success_message}")
                return True, success_message, extracted_data
            else:
                return False, "No se pudieron extraer datos de ninguna fila", []

        except Exception as e:
            error_msg = f"Error durante extracción completa: {str(e)}"
            self._log(error_msg, "ERROR")
            return False, error_msg, []

    def _extract_row_data_with_phone(self, driver, row_element, row_index: int) -> Optional[Dict]:
        """🆕 Extrae datos de una fila incluyendo el número de teléfono mediante doble clic"""
        try:
            # PASO 1: Extraer datos básicos normalmente
            row_data = self._extract_basic_row_data(row_element, row_index)
            if not row_data:
                return None

            # PASO 2: Obtener número de teléfono mediante doble clic
            telefono = self._extract_phone_number(driver, row_element, row_index)
            row_data['telefono_cliente'] = telefono

            return row_data

        except Exception as e:
            self._log(f"Error extrayendo datos completos de fila {row_index + 1}: {str(e)}", "ERROR")
            return None

    def _extract_basic_row_data(self, row_element, row_index: int) -> Optional[Dict]:
        """Extrae los datos básicos de una fila (sin teléfono)"""
        try:
            row_data = {
                'fila_numero': row_index + 1,
                'numero_orden': '',
                'cliente': '',
                'tecnico': '',
                'distrito': '',
                'barrio': '',
                'canton': '',
                'observaciones': '',
                'estado': '',
                'despacho': '',
                'telefono_cliente': ''  # 🆕 Nuevo campo
            }

            # Extraer cada campo según su columna
            for field_name, column_id in self.column_mapping.items():
                try:
                    cell_value = self._extract_cell_value(row_element, column_id)
                    row_data[field_name] = cell_value
                except Exception as e:
                    self._log(f"Error extrayendo {field_name}: {str(e)}", "DEBUG")
                    row_data[field_name] = ''

            # Verificar que al menos tengamos número de orden
            if not row_data['numero_orden']:
                self._log(f"Fila {row_index + 1} descartada: sin número de orden", "WARNING")
                return None

            return row_data

        except Exception as e:
            self._log(f"Error extrayendo datos básicos de fila {row_index + 1}: {str(e)}", "ERROR")
            return None

    def _extract_phone_number(self, driver, row_element, row_index: int) -> str:
        """🆕 Extrae el número de teléfono mediante doble clic en el cliente"""
        try:
            self._log(f"📞 Extrayendo teléfono para fila {row_index + 1}...")

            # PASO 1: Encontrar la celda del cliente
            cliente_cell = self._find_client_cell(row_element)
            if not cliente_cell:
                self._log(f"⚠️ No se encontró celda de cliente en fila {row_index + 1}", "WARNING")
                return "Sin celda cliente"

            # PASO 2: Hacer scroll a la celda para asegurar visibilidad
            self.web_driver_manager.scroll_to_element(cliente_cell)
            time.sleep(0.5)

            # PASO 3: Ejecutar doble clic usando ActionChains
            if not self._perform_double_click(driver, cliente_cell, row_index):
                return "Error en doble clic"

            # PASO 4: Esperar y extraer el número de teléfono
            phone_number = self._wait_and_extract_phone(driver, row_index)

            # PASO 5: Regresar a la tabla principal
            if not self._return_to_main_table(driver, row_index):
                self._log(f"⚠️ Advertencia: no se pudo regresar a tabla principal después de fila {row_index + 1}",
                          "WARNING")

            return phone_number

        except Exception as e:
            self._log(f"❌ Error extrayendo teléfono de fila {row_index + 1}: {str(e)}", "ERROR")
            # Intentar regresar a la tabla en caso de error
            try:
                self._return_to_main_table(driver, row_index)
            except:
                pass
            return "Error extracción"

    def _find_client_cell(self, row_element):
        """Encuentra la celda del cliente en la fila"""
        try:
            # Buscar la celda con el ID de columna del cliente
            cliente_cell = row_element.find_element(
                By.CSS_SELECTOR, f'td[data-columnid="{self.column_mapping["cliente"]}"]'
            )

            # Buscar el div interno que contiene el texto del cliente
            client_div = cliente_cell.find_element(By.CSS_SELECTOR, 'div.x-grid-cell-inner')

            # Verificar que tenga contenido
            if client_div.text.strip():
                return client_div
            else:
                return None

        except NoSuchElementException:
            return None
        except Exception as e:
            self._log(f"Error buscando celda de cliente: {str(e)}", "DEBUG")
            return None

    def _perform_double_click(self, driver, client_cell, row_index: int) -> bool:
        """Ejecuta el doble clic en la celda del cliente"""
        try:
            self._log(f"🖱️ Ejecutando doble clic en cliente de fila {row_index + 1}...")

            # Crear ActionChains para doble clic
            actions = ActionChains(driver)
            actions.double_click(client_cell).perform()

            # Esperar un momento después del doble clic
            time.sleep(self.phone_extraction_delay)

            self._log(f"✅ Doble clic ejecutado en fila {row_index + 1}")
            return True

        except Exception as e:
            self._log(f"❌ Error en doble clic de fila {row_index + 1}: {str(e)}", "ERROR")
            return False

    def _wait_and_extract_phone(self, driver, row_index: int) -> str:
        """Espera que aparezca el popup y extrae el número de teléfono"""
        try:
            self._log(f"⏳ Esperando popup de teléfono para fila {row_index + 1}...")

            # Probar cada selector en orden de preferencia
            for i, selector in enumerate(self.phone_field_selectors):
                try:
                    self._log(f"🔍 Probando selector {i + 1}: {selector}")

                    # Esperar que aparezca el campo de teléfono
                    wait = WebDriverWait(driver, self.phone_popup_timeout)
                    phone_field = wait.until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                    )

                    # Verificar que esté visible
                    if phone_field.is_displayed():
                        # Extraer el valor del teléfono
                        phone_value = phone_field.get_attribute('value')
                        if phone_value and phone_value.strip():
                            cleaned_phone = self._clean_phone_number(phone_value)
                            self._log(f"📞 Teléfono extraído de fila {row_index + 1}: {cleaned_phone}")
                            return cleaned_phone
                        else:
                            self._log(f"⚠️ Campo de teléfono vacío en fila {row_index + 1}", "WARNING")
                            return "Campo vacío"
                    else:
                        self._log(f"Campo encontrado pero no visible en fila {row_index + 1}", "DEBUG")
                        continue

                except TimeoutException:
                    self._log(f"Timeout con selector {i + 1} en fila {row_index + 1}", "DEBUG")
                    continue
                except Exception as e:
                    self._log(f"Error con selector {i + 1} en fila {row_index + 1}: {str(e)}", "DEBUG")
                    continue

            # Si llegamos aquí, ningún selector funcionó
            self._log(f"❌ No se pudo encontrar campo de teléfono en fila {row_index + 1}", "WARNING")
            return "Campo no encontrado"

        except Exception as e:
            self._log(f"❌ Error esperando popup de teléfono en fila {row_index + 1}: {str(e)}", "ERROR")
            return "Error popup"

    def _clean_phone_number(self, phone_value: str) -> str:
        """Limpia y formatea el número de teléfono"""
        if not phone_value:
            return ""

        # Limpiar espacios y caracteres especiales
        cleaned = phone_value.strip()
        cleaned = cleaned.replace('\xa0', ' ')
        cleaned = cleaned.replace('\u00a0', ' ')
        cleaned = ' '.join(cleaned.split())

        return cleaned

    def _return_to_main_table(self, driver, row_index: int) -> bool:
        """Regresa a la tabla principal haciendo clic en el botón de pestaña"""
        try:
            self._log(f"🔄 Regresando a tabla principal desde fila {row_index + 1}...")

            # Buscar el botón de retorno
            wait = WebDriverWait(driver, 10)
            return_button = wait.until(
                EC.element_to_be_clickable((By.XPATH, self.return_button_xpath))
            )

            # Hacer clic en el botón
            return_button.click()

            # Esperar que la tabla principal esté visible de nuevo
            time.sleep(2)

            # Verificar que volvimos a la tabla
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, self.table_selectors['container']))
            )

            self._log(f"✅ Regreso exitoso a tabla principal desde fila {row_index + 1}")
            return True

        except Exception as e:
            self._log(f"❌ Error regresando a tabla desde fila {row_index + 1}: {str(e)}", "ERROR")
            return False

    def _wait_for_data_table(self, driver) -> bool:
        """Espera que aparezca la tabla con datos"""
        try:
            self._log("⏳ Esperando que aparezca la tabla de datos...")
            wait = WebDriverWait(driver, self.data_wait_timeout)

            # Esperar el contenedor principal de la tabla
            container = wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, self.table_selectors['container']))
            )
            self._log("✅ Contenedor de tabla encontrado")

            # Esperar que aparezcan filas de datos
            rows = wait.until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, self.table_selectors['rows']))
            )
            self._log(f"✅ {len(rows)} filas de tabla encontradas")

            # Espera adicional para asegurar carga completa
            time.sleep(self.extraction_wait)

            return True

        except TimeoutException:
            self._log("❌ Timeout esperando tabla de datos", "ERROR")
            return False
        except Exception as e:
            self._log(f"❌ Error esperando tabla: {str(e)}", "ERROR")
            return False

    def _get_table_rows(self, driver) -> List:
        """Obtiene todas las filas de datos de la tabla"""
        try:
            # Buscar todas las filas de la tabla
            rows = driver.find_elements(By.CSS_SELECTOR, self.table_selectors['rows'])

            if not rows:
                self._log("❌ No se encontraron filas en la tabla", "WARNING")
                return []

            # Filtrar filas que realmente contienen datos
            data_rows = []
            for row in rows:
                try:
                    # Verificar que la fila tenga datos relevantes
                    if self._is_valid_data_row(row):
                        data_rows.append(row)
                except Exception as e:
                    self._log(f"Error validando fila: {str(e)}", "DEBUG")
                    continue

            self._log(f"📊 {len(data_rows)} filas válidas encontradas de {len(rows)} totales")
            return data_rows

        except Exception as e:
            self._log(f"Error obteniendo filas: {str(e)}", "ERROR")
            return []

    def _is_valid_data_row(self, row_element) -> bool:
        """Verifica si una fila contiene datos válidos"""
        try:
            # Buscar el número de orden como indicador de fila válida
            orden_cell = row_element.find_element(
                By.CSS_SELECTOR, f'td[data-columnid="{self.column_mapping["numero_orden"]}"]'
            )
            orden_text = orden_cell.text.strip()

            # Una fila es válida si tiene número de orden
            return bool(orden_text and orden_text != '&nbsp;')

        except NoSuchElementException:
            return False
        except Exception:
            return False

    def _extract_cell_value(self, row_element, column_id: str) -> str:
        """Extrae el valor de una celda específica"""
        try:
            # Buscar la celda por su data-columnid
            cell = row_element.find_element(By.CSS_SELECTOR, f'td[data-columnid="{column_id}"]')

            # Buscar el div interno que contiene el texto
            inner_div = cell.find_element(By.CSS_SELECTOR, 'div.x-grid-cell-inner')

            # Obtener el texto y limpiarlo
            cell_text = inner_div.text.strip()

            # Limpiar caracteres especiales y espacios no deseados
            if cell_text == '&nbsp;' or cell_text == '':
                return ''

            return self._clean_cell_text(cell_text)

        except NoSuchElementException:
            # La celda no existe o está oculta
            return ''
        except Exception as e:
            self._log(f"Error extrayendo celda {column_id}: {str(e)}", "DEBUG")
            return ''

    def _clean_cell_text(self, text: str) -> str:
        """Limpia el texto extraído de las celdas"""
        if not text:
            return ''

        # Limpiar espacios en blanco especiales
        text = text.replace('\xa0', ' ')
        text = text.replace('\u00a0', ' ')

        # Limpiar espacios múltiples
        text = ' '.join(text.split())

        # Remover caracteres de control
        text = ''.join(char for char in text if ord(char) >= 32 or char in '\t\n\r')

        return text.strip()

    def get_extraction_summary(self, extracted_data: List[Dict]) -> Dict:
        """Genera un resumen de los datos extraídos incluyendo estadísticas de teléfonos"""
        try:
            if not extracted_data:
                return {
                    'total_records': 0,
                    'fields_extracted': [],
                    'successful_extractions': 0,
                    'errors': 0,
                    'phones_extracted': 0
                }

            # Contar registros válidos
            valid_records = [record for record in extracted_data if record.get('numero_orden')]

            # 🆕 Contar teléfonos extraídos exitosamente
            phones_extracted = 0
            phone_errors = 0
            for record in valid_records:
                phone = record.get('telefono_cliente', '')
                if phone and phone not in ['Sin celda cliente', 'Error en doble clic', 'Campo no encontrado',
                                           'Error extracción', 'Error popup', 'Campo vacío']:
                    phones_extracted += 1
                else:
                    phone_errors += 1

            # Obtener campos que se extrajeron exitosamente
            fields_with_data = set()
            for record in valid_records:
                for field, value in record.items():
                    if value and field != 'fila_numero':
                        fields_with_data.add(field)

            # Contar por tipo de técnico
            tecnicos = {}
            for record in valid_records:
                tecnico = record.get('tecnico', 'Sin especificar')
                tecnicos[tecnico] = tecnicos.get(tecnico, 0) + 1

            # Contar por distrito
            distritos = {}
            for record in valid_records:
                distrito = record.get('distrito', 'Sin especificar')
                distritos[distrito] = distritos.get(distrito, 0) + 1

            return {
                'total_records': len(extracted_data),
                'valid_records': len(valid_records),
                'fields_extracted': list(fields_with_data),
                'tecnicos_count': tecnicos,
                'distritos_count': distritos,
                'successful_extractions': len(valid_records),
                'errors': len(extracted_data) - len(valid_records),
                'phones_extracted': phones_extracted,  # 🆕
                'phone_errors': phone_errors  # 🆕
            }

        except Exception as e:
            self._log(f"Error generando resumen: {str(e)}", "ERROR")
            return {'error': str(e)}

    def validate_extracted_data(self, extracted_data: List[Dict]) -> tuple[bool, str]:
        """Valida que los datos extraídos sean correctos incluyendo teléfonos"""
        try:
            if not extracted_data:
                return False, "No hay datos para validar"

            validation_results = []
            valid_count = 0

            for i, record in enumerate(extracted_data):
                record_issues = []

                # Validar número de orden (obligatorio)
                if not record.get('numero_orden'):
                    record_issues.append("Falta número de orden")

                # Validar que al menos tenga cliente o técnico
                if not record.get('cliente') and not record.get('tecnico'):
                    record_issues.append("Falta cliente y técnico")

                # Validar ubicación (al menos distrito)
                if not record.get('distrito'):
                    record_issues.append("Falta información de distrito")

                # 🆕 Validar teléfono (advertencia, no error crítico)
                phone = record.get('telefono_cliente', '')
                if not phone or phone in ['Sin celda cliente', 'Error en doble clic', 'Campo no encontrado']:
                    record_issues.append("Sin teléfono extraído")

                if record_issues:
                    validation_results.append(f"Registro {i + 1}: {', '.join(record_issues)}")
                else:
                    valid_count += 1

            if validation_results:
                issues_summary = f"Encontrados {len(validation_results)} registros con problemas: {'; '.join(validation_results[:3])}"
                if len(validation_results) > 3:
                    issues_summary += f" y {len(validation_results) - 3} más..."

                if valid_count > 0:
                    return True, f"Validación parcial exitosa: {valid_count}/{len(extracted_data)} registros válidos. {issues_summary}"
                else:
                    return False, f"Validación falló: {issues_summary}"
            else:
                return True, f"Validación exitosa: todos los {len(extracted_data)} registros son válidos"

        except Exception as e:
            return False, f"Error durante validación: {str(e)}"

    def extract_specific_fields(self, driver, fields: List[str]) -> tuple[bool, str, List[Dict]]:
        """Extrae solo campos específicos solicitados (incluye teléfono si se solicita)"""
        try:
            self._log(f"📊 Extrayendo campos específicos: {', '.join(fields)}")

            # Verificar que los campos solicitados existan
            available_fields = set(self.column_mapping.keys())
            available_fields.add('telefono_cliente')  # 🆕 Añadir campo de teléfono

            invalid_fields = set(fields) - available_fields

            if invalid_fields:
                return False, f"Campos no válidos: {', '.join(invalid_fields)}", []

            # Si se solicita teléfono, usar extracción completa
            if 'telefono_cliente' in fields:
                success, message, full_data = self.extract_table_data(driver)
            else:
                # Usar método básico sin teléfonos
                success, message, full_data = self._extract_basic_data_only(driver)

            if not success:
                return False, message, []

            # Filtrar solo los campos solicitados
            filtered_data = []
            for record in full_data:
                filtered_record = {'fila_numero': record.get('fila_numero', 0)}
                for field in fields:
                    filtered_record[field] = record.get(field, '')
                filtered_data.append(filtered_record)

            return True, f"Extracción de campos específicos completada: {len(filtered_data)} registros", filtered_data

        except Exception as e:
            error_msg = f"Error extrayendo campos específicos: {str(e)}"
            self._log(error_msg, "ERROR")
            return False, error_msg, []

    def _extract_basic_data_only(self, driver) -> tuple[bool, str, List[Dict]]:
        """Extrae solo datos básicos sin hacer doble clic (para cuando no se necesita teléfono)"""
        try:
            self._log("📊 Iniciando extracción básica (sin teléfonos)...")

            if not self._wait_for_data_table(driver):
                return False, "Tabla de datos no encontrada", []

            data_rows = self._get_table_rows(driver)
            if not data_rows:
                return False, "No se encontraron filas de datos", []

            extracted_data = []
            for row_index, row_element in enumerate(data_rows):
                try:
                    row_data = self._extract_basic_row_data(row_element, row_index)
                    if row_data:
                        extracted_data.append(row_data)
                except Exception as e:
                    self._log(f"❌ Error extrayendo fila básica {row_index + 1}: {str(e)}", "ERROR")
                    continue

            success_message = f"Extracción básica completada: {len(extracted_data)} registros"
            return True, success_message, extracted_data

        except Exception as e:
            error_msg = f"Error durante extracción básica: {str(e)}"
            self._log(error_msg, "ERROR")
            return False, error_msg, []

    def get_table_statistics(self, driver) -> Dict:
        """Obtiene estadísticas de la tabla sin extraer todos los datos"""
        try:
            self._log("📈 Obteniendo estadísticas de la tabla...")

            if not self._wait_for_data_table(driver):
                return {'error': 'Tabla no encontrada'}

            rows = self._get_table_rows(driver)

            stats = {
                'total_rows': len(rows),
                'table_present': True,
                'extraction_timestamp': time.time(),
                'phone_extraction_available': True  # 🆕
            }

            # Contar filas válidas rápidamente
            valid_rows = 0
            for row in rows[:10]:  # Solo revisar las primeras 10 para estadísticas rápidas
                if self._is_valid_data_row(row):
                    valid_rows += 1

            stats['estimated_valid_rows'] = valid_rows * (len(rows) / min(10, len(rows)))

            return stats

        except Exception as e:
            return {'error': str(e), 'table_present': False}