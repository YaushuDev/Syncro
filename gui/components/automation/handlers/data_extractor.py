# data_extractor.py
# Ubicación: /syncro_bot/gui/components/automation/handlers/data_extractor.py
"""
Extractor especializado de datos de la tabla de resultados.
Maneja la extracción de información específica de la tabla HTML generada
después de los clics en el botón de búsqueda: Número de Orden, Cliente,
Técnico, Distrito, Barrio, Cantón y Observaciones.
"""

import time
from typing import List, Dict, Optional

# Importaciones para Selenium
try:
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.common.exceptions import TimeoutException, NoSuchElementException

    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False


class DataExtractor:
    """Extractor especializado de datos de la tabla de resultados"""

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
            'cliente': 'gridcolumn-1115',  # Cliente
            'tecnico': 'gridcolumn-1121',  # Técnico
            'distrito': 'gridcolumn-1122',  # Distrito
            'barrio': 'gridcolumn-1123',  # Barrio
            'canton': 'gridcolumn-1124',  # Cantón
            'observaciones': 'gridcolumn-1126',  # Observaciones (puede estar oculto)
            'estado': 'gridcolumn-1112',  # Estado (adicional para contexto)
            'despacho': 'gridcolumn-1116'  # Despacho (adicional para contexto)
        }

        # Configuración de timeouts
        self.data_wait_timeout = 15
        self.extraction_wait = 3

    def _log(self, message, level="INFO"):
        """Log interno con fallback"""
        if self.logger:
            self.logger(message, level)
        else:
            print(f"[{level}] {message}")

    def extract_table_data(self, driver) -> tuple[bool, str, List[Dict]]:
        """Extrae todos los datos de la tabla después del triple clic"""
        try:
            self._log("📊 Iniciando extracción de datos de la tabla...")

            # Esperar que aparezca la tabla con datos
            if not self._wait_for_data_table(driver):
                return False, "Tabla de datos no encontrada o no cargó", []

            # Obtener todas las filas de datos
            data_rows = self._get_table_rows(driver)
            if not data_rows:
                return False, "No se encontraron filas de datos en la tabla", []

            self._log(f"📋 Encontradas {len(data_rows)} filas de datos para extraer")

            # Extraer datos de cada fila
            extracted_data = []
            for row_index, row_element in enumerate(data_rows):
                try:
                    row_data = self._extract_row_data(row_element, row_index)
                    if row_data:
                        extracted_data.append(row_data)
                        self._log(f"✅ Fila {row_index + 1} extraída: {row_data.get('numero_orden', 'N/A')}")
                    else:
                        self._log(f"⚠️ Fila {row_index + 1} no pudo ser extraída", "WARNING")
                except Exception as e:
                    self._log(f"❌ Error extrayendo fila {row_index + 1}: {str(e)}", "ERROR")
                    continue

            if extracted_data:
                success_message = f"Extracción completada: {len(extracted_data)} registros obtenidos"
                self._log(f"🎉 {success_message}")
                return True, success_message, extracted_data
            else:
                return False, "No se pudieron extraer datos de ninguna fila", []

        except Exception as e:
            error_msg = f"Error durante extracción de datos: {str(e)}"
            self._log(error_msg, "ERROR")
            return False, error_msg, []

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

    def _extract_row_data(self, row_element, row_index: int) -> Optional[Dict]:
        """Extrae datos de una fila específica"""
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
                'despacho': ''
            }

            # Extraer cada campo según su columna
            for field_name, column_id in self.column_mapping.items():
                try:
                    cell_value = self._extract_cell_value(row_element, column_id)
                    row_data[field_name] = cell_value
                    self._log(f"  {field_name}: '{cell_value}'", "DEBUG")
                except Exception as e:
                    self._log(f"Error extrayendo {field_name}: {str(e)}", "DEBUG")
                    row_data[field_name] = ''

            # Verificar que al menos tengamos número de orden
            if not row_data['numero_orden']:
                self._log(f"Fila {row_index + 1} descartada: sin número de orden", "WARNING")
                return None

            return row_data

        except Exception as e:
            self._log(f"Error extrayendo datos de fila {row_index + 1}: {str(e)}", "ERROR")
            return None

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
        """Genera un resumen de los datos extraídos"""
        try:
            if not extracted_data:
                return {
                    'total_records': 0,
                    'fields_extracted': [],
                    'successful_extractions': 0,
                    'errors': 0
                }

            # Contar registros válidos
            valid_records = [record for record in extracted_data if record.get('numero_orden')]

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
                'errors': len(extracted_data) - len(valid_records)
            }

        except Exception as e:
            self._log(f"Error generando resumen: {str(e)}", "ERROR")
            return {'error': str(e)}

    def validate_extracted_data(self, extracted_data: List[Dict]) -> tuple[bool, str]:
        """Valida que los datos extraídos sean correctos"""
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
        """Extrae solo campos específicos solicitados"""
        try:
            self._log(f"📊 Extrayendo campos específicos: {', '.join(fields)}")

            # Verificar que los campos solicitados existan
            available_fields = set(self.column_mapping.keys())
            invalid_fields = set(fields) - available_fields

            if invalid_fields:
                return False, f"Campos no válidos: {', '.join(invalid_fields)}", []

            # Extraer datos completos
            success, message, full_data = self.extract_table_data(driver)

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
                'extraction_timestamp': time.time()
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