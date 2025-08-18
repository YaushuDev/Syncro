# data_extractor.py
# Ubicación: /syncro_bot/gui/components/automation/handlers/data_extractor.py
"""
Extractor especializado de datos de la tabla de resultados con funcionalidad
de OCR para obtener números de teléfono. Toma screenshots del popup de cliente
y usa análisis de imagen para extraer el campo "Tel. celular:" de forma robusta.
"""

import time
import os
import tempfile
import re
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

# Importaciones para OCR
try:
    import easyocr

    OCR_EASYOCR_AVAILABLE = True
except ImportError:
    OCR_EASYOCR_AVAILABLE = False

try:
    import pytesseract
    from PIL import Image

    OCR_TESSERACT_AVAILABLE = True
except ImportError:
    OCR_TESSERACT_AVAILABLE = False


class DataExtractor:
    """Extractor especializado de datos con funcionalidad OCR para teléfonos"""

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

        # 🆕 Configuración OCR
        self.ocr_reader = None
        self.ocr_method = None
        self._initialize_ocr()

        # 🆕 XPath para el botón de retorno a la tabla
        self.return_button_xpath = '//*[@id="tab-1030-btnInnerEl"]'

        # Configuración de timeouts
        self.data_wait_timeout = 15
        self.extraction_wait = 3
        self.phone_popup_timeout = 10
        self.phone_extraction_delay = 2

        # 🆕 Directorio temporal para screenshots
        self.temp_dir = tempfile.gettempdir()

    def _initialize_ocr(self):
        """🆕 Inicializa el motor OCR (prioriza EasyOCR, fallback a Tesseract)"""
        try:
            if OCR_EASYOCR_AVAILABLE:
                self._log("🔍 Inicializando EasyOCR...")
                self.ocr_reader = easyocr.Reader(['es', 'en'])  # Español e Inglés
                self.ocr_method = 'easyocr'
                self._log("✅ EasyOCR inicializado correctamente")
            elif OCR_TESSERACT_AVAILABLE:
                self._log("🔍 EasyOCR no disponible, usando Tesseract...")
                self.ocr_method = 'tesseract'
                self._log("✅ Tesseract configurado como fallback")
            else:
                self._log("❌ Ningún motor OCR disponible", "ERROR")
                self.ocr_method = None
        except Exception as e:
            self._log(f"❌ Error inicializando OCR: {str(e)}", "ERROR")
            self.ocr_method = None

    def _log(self, message, level="INFO"):
        """Log interno con fallback"""
        if self.logger:
            self.logger(message, level)
        else:
            print(f"[{level}] {message}")

    def extract_table_data(self, driver) -> tuple[bool, str, List[Dict]]:
        """Extrae todos los datos de la tabla incluyendo números de teléfono con OCR"""
        try:
            self._log("📊 Iniciando extracción completa de datos (con OCR para teléfonos)...")

            # Verificar que OCR esté disponible
            if not self.ocr_method:
                self._log("⚠️ OCR no disponible, extrayendo sin teléfonos", "WARNING")

            # Esperar que aparezca la tabla con datos
            if not self._wait_for_data_table(driver):
                return False, "Tabla de datos no encontrada o no cargó", []

            # Obtener todas las filas de datos
            data_rows = self._get_table_rows(driver)
            if not data_rows:
                return False, "No se encontraron filas de datos en la tabla", []

            self._log(f"📋 Encontradas {len(data_rows)} filas de datos para extracción con OCR")

            # Extraer datos de cada fila (INCLUYE TELÉFONOS CON OCR)
            extracted_data = []
            for row_index, row_element in enumerate(data_rows):
                try:
                    row_data = self._extract_row_data_with_ocr_phone(driver, row_element, row_index)
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
                phones_extracted = sum(1 for record in extracted_data
                                       if record.get('telefono_cliente') and
                                       record.get('telefono_cliente') not in ['Sin teléfono', 'Error OCR',
                                                                              'Error popup'])
                success_message = f"Extracción completa con OCR: {len(extracted_data)} registros, {phones_extracted} teléfonos obtenidos"
                self._log(f"🎉 {success_message}")
                return True, success_message, extracted_data
            else:
                return False, "No se pudieron extraer datos de ninguna fila", []

        except Exception as e:
            error_msg = f"Error durante extracción completa con OCR: {str(e)}"
            self._log(error_msg, "ERROR")
            return False, error_msg, []

    def _extract_row_data_with_ocr_phone(self, driver, row_element, row_index: int) -> Optional[Dict]:
        """🆕 Extrae datos de una fila incluyendo el número de teléfono mediante OCR"""
        try:
            # PASO 1: Extraer datos básicos normalmente
            row_data = self._extract_basic_row_data(row_element, row_index)
            if not row_data:
                return None

            # PASO 2: Obtener número de teléfono mediante OCR
            if self.ocr_method:
                telefono = self._extract_phone_with_ocr(driver, row_element, row_index)
            else:
                telefono = "OCR no disponible"

            row_data['telefono_cliente'] = telefono

            return row_data

        except Exception as e:
            self._log(f"Error extrayendo datos completos de fila {row_index + 1}: {str(e)}", "ERROR")
            return None

    def _extract_phone_with_ocr(self, driver, row_element, row_index: int) -> str:
        """🆕 Extrae el número de teléfono usando OCR después del doble clic"""
        screenshot_path = None
        try:
            self._log(f"📞 Extrayendo teléfono con OCR para fila {row_index + 1}...")

            # PASO 1: Encontrar la celda del cliente
            cliente_cell = self._find_client_cell(row_element)
            if not cliente_cell:
                self._log(f"⚠️ No se encontró celda de cliente en fila {row_index + 1}", "WARNING")
                return "Sin celda cliente"

            # PASO 2: Hacer scroll a la celda para asegurar visibilidad
            self.web_driver_manager.scroll_to_element(cliente_cell)
            time.sleep(0.5)

            # PASO 3: Ejecutar doble clic
            if not self._perform_double_click(driver, cliente_cell, row_index):
                return "Error en doble clic"

            # PASO 4: Esperar que aparezca el popup
            time.sleep(self.phone_extraction_delay)

            # PASO 5: 🎯 TOMAR SCREENSHOT DEL POPUP
            screenshot_path = self._take_popup_screenshot(driver, row_index)
            if not screenshot_path:
                return "Error captura"

            # PASO 6: 🔍 ANALIZAR SCREENSHOT CON OCR
            phone_number = self._analyze_screenshot_for_phone(screenshot_path, row_index)

            # PASO 7: Regresar a la tabla principal
            if not self._return_to_main_table(driver, row_index):
                self._log(f"⚠️ Advertencia: no se pudo regresar a tabla principal después de fila {row_index + 1}",
                          "WARNING")

            return phone_number

        except Exception as e:
            self._log(f"❌ Error extrayendo teléfono con OCR de fila {row_index + 1}: {str(e)}", "ERROR")
            # Intentar regresar a la tabla en caso de error
            try:
                self._return_to_main_table(driver, row_index)
            except:
                pass
            return "Error OCR"
        finally:
            # 🧹 LIMPIAR SCREENSHOT
            if screenshot_path and os.path.exists(screenshot_path):
                try:
                    os.remove(screenshot_path)
                    self._log(f"🗑️ Screenshot temporal eliminado: {screenshot_path}")
                except Exception as e:
                    self._log(f"⚠️ No se pudo eliminar screenshot: {e}", "WARNING")

    def _take_popup_screenshot(self, driver, row_index: int) -> Optional[str]:
        """🆕 Toma screenshot del popup de cliente"""
        try:
            # Generar nombre único para el screenshot
            timestamp = int(time.time() * 1000)
            screenshot_filename = f"popup_client_{row_index}_{timestamp}.png"
            screenshot_path = os.path.join(self.temp_dir, screenshot_filename)

            # Esperar un momento para asegurar que el popup esté completamente cargado
            time.sleep(1)

            # Tomar screenshot de toda la ventana
            success = driver.save_screenshot(screenshot_path)

            if success and os.path.exists(screenshot_path):
                self._log(f"📸 Screenshot capturado para fila {row_index + 1}: {screenshot_path}")
                return screenshot_path
            else:
                self._log(f"❌ Error capturando screenshot para fila {row_index + 1}", "ERROR")
                return None

        except Exception as e:
            self._log(f"❌ Error en captura de screenshot fila {row_index + 1}: {str(e)}", "ERROR")
            return None

    def _analyze_screenshot_for_phone(self, screenshot_path: str, row_index: int) -> str:
        """🆕 Analiza el screenshot con OCR para encontrar el teléfono"""
        try:
            self._log(f"🔍 Analizando screenshot con OCR para fila {row_index + 1}...")

            if self.ocr_method == 'easyocr':
                return self._analyze_with_easyocr(screenshot_path, row_index)
            elif self.ocr_method == 'tesseract':
                return self._analyze_with_tesseract(screenshot_path, row_index)
            else:
                return "OCR no disponible"

        except Exception as e:
            self._log(f"❌ Error analizando screenshot fila {row_index + 1}: {str(e)}", "ERROR")
            return "Error análisis"

    def _analyze_with_easyocr(self, screenshot_path: str, row_index: int) -> str:
        """🆕 Analiza imagen con EasyOCR buscando 'Tel. celular:'"""
        try:
            # Leer texto de la imagen
            results = self.ocr_reader.readtext(screenshot_path)

            # Buscar el patrón "Tel. celular:" y extraer el número
            for i, (bbox, text, confidence) in enumerate(results):
                text_clean = text.strip()

                # Buscar "Tel. celular:" o variaciones
                if self._is_phone_label(text_clean):
                    self._log(f"🎯 Encontrado label teléfono en fila {row_index + 1}: '{text_clean}'")

                    # Buscar el número en los siguientes elementos de texto
                    phone_number = self._find_phone_number_nearby(results, i)
                    if phone_number:
                        self._log(f"📞 Teléfono extraído con EasyOCR fila {row_index + 1}: {phone_number}")
                        return phone_number

            # Si no encontramos con el método principal, buscar cualquier número que parezca teléfono
            phone_number = self._extract_any_phone_pattern(results, row_index)
            if phone_number:
                return phone_number

            self._log(f"⚠️ No se encontró teléfono en OCR fila {row_index + 1}", "WARNING")
            return "Sin teléfono"

        except Exception as e:
            self._log(f"❌ Error en EasyOCR fila {row_index + 1}: {str(e)}", "ERROR")
            return "Error EasyOCR"

    def _analyze_with_tesseract(self, screenshot_path: str, row_index: int) -> str:
        """🆕 Analiza imagen con Tesseract buscando 'Tel. celular:'"""
        try:
            # Abrir imagen
            image = Image.open(screenshot_path)

            # Extraer texto
            text = pytesseract.image_to_string(image, lang='spa+eng')
            lines = text.split('\n')

            # Buscar líneas que contengan "Tel. celular:"
            for i, line in enumerate(lines):
                if self._is_phone_label(line):
                    self._log(f"🎯 Encontrado label teléfono en fila {row_index + 1}: '{line}'")

                    # Extraer número de la misma línea o líneas cercanas
                    phone_number = self._extract_phone_from_lines(lines, i)
                    if phone_number:
                        self._log(f"📞 Teléfono extraído con Tesseract fila {row_index + 1}: {phone_number}")
                        return phone_number

            # Buscar cualquier patrón de teléfono en todo el texto
            phone_number = self._extract_phone_pattern_from_text(text, row_index)
            if phone_number:
                return phone_number

            self._log(f"⚠️ No se encontró teléfono en OCR fila {row_index + 1}", "WARNING")
            return "Sin teléfono"

        except Exception as e:
            self._log(f"❌ Error en Tesseract fila {row_index + 1}: {str(e)}", "ERROR")
            return "Error Tesseract"

    def _is_phone_label(self, text: str) -> bool:
        """🆕 Verifica si el texto contiene etiquetas de teléfono"""
        text_lower = text.lower().strip()
        phone_labels = [
            'tel. celular',
            'tel celular',
            'teléfono celular',
            'telefono celular',
            'tel móvil',
            'tel movil',
            'celular',
            'tel.:',
            'tel:'
        ]

        return any(label in text_lower for label in phone_labels)

    def _find_phone_number_nearby(self, results: List, label_index: int) -> Optional[str]:
        """🆕 Busca número de teléfono cerca del label encontrado (EasyOCR)"""
        # Buscar en los siguientes 3 elementos
        for i in range(label_index + 1, min(len(results), label_index + 4)):
            bbox, text, confidence = results[i]
            phone = self._extract_phone_pattern(text.strip())
            if phone:
                return phone

        # Buscar en el mismo elemento del label
        bbox, text, confidence = results[label_index]
        phone = self._extract_phone_pattern(text)
        if phone:
            return phone

        return None

    def _extract_phone_from_lines(self, lines: List[str], label_line_index: int) -> Optional[str]:
        """🆕 Extrae teléfono de líneas cercanas al label (Tesseract)"""
        # Buscar en la misma línea
        phone = self._extract_phone_pattern(lines[label_line_index])
        if phone:
            return phone

        # Buscar en las siguientes 3 líneas
        for i in range(label_line_index + 1, min(len(lines), label_line_index + 4)):
            phone = self._extract_phone_pattern(lines[i])
            if phone:
                return phone

        return None

    def _extract_any_phone_pattern(self, results: List, row_index: int) -> Optional[str]:
        """🆕 Busca cualquier patrón de teléfono en los resultados OCR"""
        for bbox, text, confidence in results:
            phone = self._extract_phone_pattern(text.strip())
            if phone:
                self._log(f"📞 Teléfono encontrado por patrón en fila {row_index + 1}: {phone}")
                return phone
        return None

    def _extract_phone_pattern_from_text(self, text: str, row_index: int) -> Optional[str]:
        """🆕 Extrae patrón de teléfono de texto completo"""
        phone = self._extract_phone_pattern(text)
        if phone:
            self._log(f"📞 Teléfono encontrado por patrón en texto completo fila {row_index + 1}: {phone}")
        return phone

    def _extract_phone_pattern(self, text: str) -> Optional[str]:
        """🆕 Extrae número de teléfono usando patrones regex"""
        if not text:
            return None

        # Patrones para números de teléfono costarricenses
        patterns = [
            r'\+506\s*\d{8}',  # +506 12345678
            r'\+506\d{8}',  # +50612345678
            r'506\s*\d{8}',  # 506 12345678
            r'506\d{8}',  # 50612345678
            r'\d{8}',  # 12345678 (8 dígitos)
            r'\d{4}-\d{4}',  # 1234-5678
            r'\d{4}\s+\d{4}'  # 1234 5678
        ]

        for pattern in patterns:
            matches = re.findall(pattern, text)
            if matches:
                # Limpiar y formatear el número encontrado
                phone = matches[0].strip()
                # Remover espacios y guiones para normalizar
                phone_clean = re.sub(r'[\s-]', '', phone)

                # Validar que sea un número válido (al menos 8 dígitos)
                if len(re.sub(r'\D', '', phone_clean)) >= 8:
                    return phone.strip()

        return None

    # ========== MÉTODOS HEREDADOS DEL CÓDIGO ORIGINAL ==========

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
                'telefono_cliente': ''
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

            # Contar teléfonos extraídos exitosamente
            phones_extracted = 0
            phone_errors = 0
            for record in valid_records:
                phone = record.get('telefono_cliente', '')
                if phone and phone not in ['Sin teléfono', 'Error OCR', 'Error popup', 'Error captura',
                                           'Error análisis', 'OCR no disponible']:
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
                'phones_extracted': phones_extracted,
                'phone_errors': phone_errors,
                'ocr_method_used': self.ocr_method
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

                # Validar teléfono (advertencia, no error crítico)
                phone = record.get('telefono_cliente', '')
                if not phone or phone in ['Sin teléfono', 'Error OCR', 'Error popup', 'OCR no disponible']:
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
                'phone_extraction_available': self.ocr_method is not None,
                'ocr_method': self.ocr_method
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

    def is_ocr_available(self) -> bool:
        """🆕 Verifica si algún motor OCR está disponible"""
        return self.ocr_method is not None

    def get_ocr_info(self) -> Dict:
        """🆕 Obtiene información sobre el motor OCR disponible"""
        return {
            'ocr_available': self.ocr_method is not None,
            'ocr_method': self.ocr_method,
            'easyocr_available': OCR_EASYOCR_AVAILABLE,
            'tesseract_available': OCR_TESSERACT_AVAILABLE,
            'temp_directory': self.temp_dir
        }