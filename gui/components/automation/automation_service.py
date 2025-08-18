# automation_service.py
# Ubicación: /syncro_bot/gui/components/automation/automation_service.py
"""
Servicio principal de automatización con funcionalidad completa de extracción
de teléfonos mediante doble clic. Interfaz pública que coordina todos los
handlers para login, dropdowns, fechas, triple clic, extracción con teléfonos
y generación de reportes Excel completos.
"""

import threading
import time
import webbrowser

# Importaciones para Selenium
try:
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False
    print("Warning: Selenium no está instalado. Funcionalidad de login automático deshabilitada.")
    print("Instale con: pip install selenium")

# Importar handlers especializados
from .handlers.web_driver_manager import WebDriverManager
from .handlers.login_handler import LoginHandler
from .handlers.dropdown_handler import DropdownHandler
from .handlers.date_handler import DateHandler
from .handlers.button_handler import ButtonHandler
from .handlers.automation_orchestrator import AutomationOrchestrator
from .credentials_manager import CredentialsManager


class AutomationService:
    """Servicio principal con funcionalidad completa de extracción de teléfonos"""

    def __init__(self, logger=None):
        self.is_running = False
        self.target_url = "https://fieldservice.cabletica.com/dispatchFS/"
        self._lock = threading.Lock()
        self.logger = logger

        # Estado de última extracción
        self.last_extraction_file = None
        self.last_extraction_data = None
        self.last_phone_count = 0  # 🆕 Contador de teléfonos extraídos

        # Inicializar gestores especializados
        self._initialize_handlers()

        # Gestor de credenciales
        self.credentials_manager = CredentialsManager()

    def _initialize_handlers(self):
        """Inicializa todos los handlers especializados con soporte para teléfonos"""
        try:
            # Handler del navegador
            self.web_driver_manager = WebDriverManager(logger=self._log)

            # Handler de login
            self.login_handler = LoginHandler(
                web_driver_manager=self.web_driver_manager,
                logger=self._log
            )

            # Handler de dropdowns
            self.dropdown_handler = DropdownHandler(
                web_driver_manager=self.web_driver_manager,
                logger=self._log
            )

            # Handler de fechas
            self.date_handler = DateHandler(
                web_driver_manager=self.web_driver_manager,
                logger=self._log
            )

            # Handler de botones (con triple clic)
            self.button_handler = ButtonHandler(
                web_driver_manager=self.web_driver_manager,
                logger=self._log
            )

            # 🆕 Orchestrador principal con funcionalidad completa de teléfonos
            self.automation_orchestrator = AutomationOrchestrator(
                web_driver_manager=self.web_driver_manager,
                login_handler=self.login_handler,
                dropdown_handler=self.dropdown_handler,
                date_handler=self.date_handler,
                button_handler=self.button_handler,
                logger=self._log
            )

            self._log("🔧 Handlers de automatización con teléfonos inicializados correctamente")

        except Exception as e:
            self._log(f"❌ Error inicializando handlers: {str(e)}", "ERROR")
            raise

    def _log(self, message, level="INFO"):
        """Log interno con fallback"""
        if self.logger:
            self.logger(message, level)
        else:
            print(f"[{level}] {message}")

    def is_selenium_available(self):
        """Verifica si Selenium está disponible"""
        return self.web_driver_manager.is_selenium_available()

    def set_target_url(self, url):
        """Establece la URL objetivo"""
        self.target_url = url
        self.automation_orchestrator.set_target_url(url)

    def get_target_url(self):
        """Obtiene la URL objetivo actual"""
        return self.target_url

    def start_automation(self, username=None, password=None, date_config=None):
        """🔄 Inicia el proceso de automatización completo con extracción de teléfonos"""
        try:
            with self._lock:
                if self.is_running:
                    return False, "La automatización ya está en ejecución"

                if not SELENIUM_AVAILABLE:
                    # Fallback al método original si Selenium no está disponible
                    self._log("Selenium no disponible, usando método básico")
                    webbrowser.open(self.target_url)
                    self.is_running = True
                    return True, "Automatización iniciada (modo básico - sin funcionalidades avanzadas)"

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

                # Procesar configuración de fechas
                if not date_config:
                    date_config = {'skip_dates': True}

                self._log("🚀 Iniciando automatización completa con extracción de teléfonos...")
                self._log_automation_config(date_config)

                # 🆕 Ejecutar automatización completa con teléfonos
                success, message = self.automation_orchestrator.execute_complete_automation(
                    username, password, date_config
                )

                if success:
                    self.is_running = True

                    # 🆕 Extraer información del archivo Excel y contar teléfonos
                    excel_file = self._extract_excel_file_from_message(message)
                    if excel_file:
                        self.last_extraction_file = excel_file
                        self.last_phone_count = self._extract_phone_count_from_message(message)
                        self._log(f"📄 Archivo Excel con teléfonos generado: {excel_file}")
                        self._log(f"📞 Teléfonos extraídos: {self.last_phone_count}")

                    self._log("✅ Automatización con extracción de teléfonos completada exitosamente")
                    return True, message
                else:
                    self._log(f"❌ Automatización falló: {message}", "ERROR")
                    self._cleanup_on_failure()
                    return False, message

        except Exception as e:
            self._log(f"❌ Excepción en start_automation: {str(e)}", "ERROR")
            self._cleanup_on_failure()
            return False, f"Error al iniciar automatización: {str(e)}"

    def _extract_excel_file_from_message(self, message):
        """Extrae la ruta del archivo Excel del mensaje de éxito"""
        try:
            # Buscar patrón "Archivo Excel: ruta_del_archivo"
            if "Archivo Excel:" in message:
                parts = message.split("Archivo Excel:")
                if len(parts) > 1:
                    # Extraer la ruta hasta el siguiente espacio o final
                    excel_path = parts[1].strip().split()[0]
                    return excel_path
            return None
        except Exception:
            return None

    def _extract_phone_count_from_message(self, message):
        """🆕 Extrae el número de teléfonos del mensaje de éxito"""
        try:
            # Buscar patrones como "5 teléfonos" o "con 3 teléfonos"
            import re
            phone_patterns = [
                r'(\d+)\s+teléfonos',
                r'con\s+(\d+)\s+teléfono',
                r'extraídos:\s*(\d+)',
                r'phones_extracted.*?(\d+)'
            ]

            for pattern in phone_patterns:
                match = re.search(pattern, message, re.IGNORECASE)
                if match:
                    return int(match.group(1))

            return 0
        except Exception:
            return 0

    def pause_automation(self):
        """Pausa el proceso de automatización"""
        try:
            with self._lock:
                if not self.is_running:
                    return False, "La automatización no está en ejecución"

                self._log("⏸️ Pausando automatización...")
                cleanup_success, cleanup_message = self.automation_orchestrator.cleanup_automation()

                self.is_running = False

                if cleanup_success:
                    self._log("✅ Automatización pausada correctamente")
                    return True, "Automatización pausada correctamente"
                else:
                    self._log(f"⚠️ Automatización pausada con advertencias: {cleanup_message}", "WARNING")
                    return True, f"Automatización pausada: {cleanup_message}"

        except Exception as e:
            error_msg = f"Error al pausar automatización: {str(e)}"
            self._log(error_msg, "ERROR")
            return False, error_msg

    def test_credentials(self, username, password, date_config=None):
        """Prueba las credenciales ejecutando automatización completa de prueba"""
        try:
            if not SELENIUM_AVAILABLE:
                return False, "Selenium no está disponible para probar credenciales"

            # Validar formato de credenciales
            valid, message = self.credentials_manager.validate_credentials(username, password)
            if not valid:
                return False, message

            # Si no se proporciona configuración de fechas, usar omitir
            if not date_config:
                date_config = {'skip_dates': True}

            self._log("🧪 Iniciando prueba de credenciales con automatización completa...")

            # Usar el orchestrador para la prueba
            success, message = self.automation_orchestrator.test_automation_components(
                username, password, date_config
            )

            if success:
                self._log("✅ Prueba de credenciales exitosa")
            else:
                self._log(f"❌ Prueba de credenciales falló: {message}", "ERROR")

            return success, message

        except Exception as e:
            error_msg = f"Error probando credenciales: {str(e)}"
            self._log(error_msg, "ERROR")
            return False, error_msg

    def get_status(self):
        """Obtiene el estado actual de la automatización"""
        with self._lock:
            return self.is_running

    def stop_all(self):
        """Detiene todas las operaciones de automatización"""
        with self._lock:
            self._log("🛑 Deteniendo todas las operaciones...")
            cleanup_success, cleanup_message = self.automation_orchestrator.cleanup_automation()
            self.is_running = False

            if cleanup_success:
                self._log("✅ Todas las operaciones detenidas correctamente")
            else:
                self._log(f"⚠️ Operaciones detenidas con advertencias: {cleanup_message}", "WARNING")

    def get_driver_info(self):
        """Obtiene información del driver actual"""
        try:
            return self.web_driver_manager.get_driver_info()
        except Exception as e:
            self._log(f"Error obteniendo info del driver: {e}", "WARNING")
            return None

    def navigate_to_url(self, url):
        """Navega a una URL específica si hay un driver activo"""
        try:
            if not self.is_running:
                return False, "No hay automatización activa"

            return self.web_driver_manager.navigate_to_url(url)
        except Exception as e:
            error_msg = f"Error navegando a {url}: {str(e)}"
            self._log(error_msg, "ERROR")
            return False, error_msg

    def execute_script(self, script):
        """Ejecuta JavaScript en la página actual"""
        try:
            if not self.is_running:
                return False, "No hay automatización activa"

            return self.web_driver_manager.execute_script(script)
        except Exception as e:
            error_msg = f"Error ejecutando script: {str(e)}"
            self._log(error_msg, "ERROR")
            return False, error_msg

    def get_current_dropdown_values(self):
        """Obtiene los valores actuales de los tres dropdowns"""
        try:
            if not self.is_running or not self.web_driver_manager.driver:
                return None

            return self.dropdown_handler.get_current_dropdown_values(self.web_driver_manager.driver)
        except Exception as e:
            self._log(f"Error obteniendo valores de dropdowns: {e}", "WARNING")
            return None

    def get_current_date_values(self):
        """Obtiene los valores actuales de los campos de fecha"""
        try:
            if not self.is_running or not self.web_driver_manager.driver:
                return None

            return self.date_handler.get_current_date_values(self.web_driver_manager.driver)
        except Exception as e:
            self._log(f"Error obteniendo valores de fechas: {e}", "WARNING")
            return None

    def configure_date_manually(self, date_config):
        """Configura fechas manualmente en automatización activa"""
        try:
            if not self.is_running or not self.web_driver_manager.driver:
                return False, "No hay automatización activa"

            return self.date_handler.handle_date_configuration(self.web_driver_manager.driver, date_config)
        except Exception as e:
            error_msg = f"Error configurando fechas manualmente: {str(e)}"
            self._log(error_msg, "ERROR")
            return False, error_msg

    def click_tab_button_manually(self):
        """Ejecuta solo el clic en el botón de pestaña (para uso manual)"""
        try:
            if not self.is_running or not self.web_driver_manager.driver:
                return False, "No hay automatización activa"

            return self.button_handler.handle_tab_button_click(self.web_driver_manager.driver)
        except Exception as e:
            error_msg = f"Error haciendo clic manual en botón de pestaña: {str(e)}"
            self._log(error_msg, "ERROR")
            return False, error_msg

    def click_action_button_manually(self):
        """Ejecuta solo el clic en el botón de acción (para uso manual)"""
        try:
            if not self.is_running or not self.web_driver_manager.driver:
                return False, "No hay automatización activa"

            return self.button_handler.handle_action_button_click(self.web_driver_manager.driver)
        except Exception as e:
            error_msg = f"Error haciendo clic manual en botón de acción: {str(e)}"
            self._log(error_msg, "ERROR")
            return False, error_msg

    # 🆕 MÉTODOS PARA EXTRACCIÓN COMPLETA CON TELÉFONOS

    def execute_triple_click_search(self):
        """Ejecuta el triple clic en el botón de búsqueda (para uso manual)"""
        try:
            if not self.is_running or not self.web_driver_manager.driver:
                return False, "No hay automatización activa"

            return self.button_handler.handle_search_button_triple_click(self.web_driver_manager.driver)
        except Exception as e:
            error_msg = f"Error en triple clic manual: {str(e)}"
            self._log(error_msg, "ERROR")
            return False, error_msg

    def extract_data_with_phones(self):
        """🆕 Ejecuta extracción completa con teléfonos (asume que ya se ejecutó el flujo)"""
        try:
            if not self.is_running or not self.web_driver_manager.driver:
                return False, "No hay automatización activa", None

            success, message, excel_file = self.automation_orchestrator.extract_data_only(
                self.web_driver_manager.driver)

            if success and excel_file:
                self.last_extraction_file = excel_file
                self.last_phone_count = self._extract_phone_count_from_message(message)
                self._log(f"📄 Extracción completa con teléfonos completada: {excel_file}")
                self._log(f"📞 Teléfonos extraídos: {self.last_phone_count}")

            return success, message, excel_file

        except Exception as e:
            error_msg = f"Error en extracción completa: {str(e)}"
            self._log(error_msg, "ERROR")
            return False, error_msg, None

    def extract_basic_data_only(self):
        """🆕 Extrae solo datos básicos sin teléfonos (más rápido)"""
        try:
            if not self.is_running or not self.web_driver_manager.driver:
                return False, "No hay automatización activa", None

            success, message, excel_file = self.automation_orchestrator.extract_basic_data_only(
                self.web_driver_manager.driver)

            if success and excel_file:
                self.last_extraction_file = excel_file
                self.last_phone_count = 0  # No se extraen teléfonos en modo básico
                self._log(f"📄 Extracción básica completada: {excel_file}")

            return success, message, excel_file

        except Exception as e:
            error_msg = f"Error en extracción básica: {str(e)}"
            self._log(error_msg, "ERROR")
            return False, error_msg, None

    def test_data_extraction(self):
        """Prueba la funcionalidad de extracción de datos con teléfonos"""
        try:
            if not self.is_running or not self.web_driver_manager.driver:
                return False, "No hay automatización activa"

            return self.automation_orchestrator.test_data_extraction(self.web_driver_manager.driver)

        except Exception as e:
            error_msg = f"Error probando extracción: {str(e)}"
            self._log(error_msg, "ERROR")
            return False, error_msg

    def get_last_extraction_file(self):
        """Obtiene la ruta del último archivo Excel generado"""
        return self.last_extraction_file

    def get_last_phone_count(self):
        """🆕 Obtiene el número de teléfonos extraídos en la última ejecución"""
        return self.last_phone_count

    def get_export_directory(self):
        """Obtiene el directorio donde se guardan los archivos Excel"""
        try:
            return self.automation_orchestrator.get_export_directory()
        except Exception as e:
            self._log(f"Error obteniendo directorio de exportación: {e}", "WARNING")
            return None

    def is_data_extraction_available(self):
        """Verifica si la funcionalidad de extracción de datos está disponible"""
        try:
            if not hasattr(self.automation_orchestrator, 'data_extractor'):
                return False

            if not hasattr(self.automation_orchestrator, 'excel_exporter'):
                return False

            # Verificar dependencias
            if self.automation_orchestrator.data_extractor is None:
                return False

            if self.automation_orchestrator.excel_exporter is None:
                return False

            # Verificar que openpyxl esté disponible
            return self.automation_orchestrator.excel_exporter.is_available()

        except Exception as e:
            self._log(f"Error verificando disponibilidad de extracción: {e}", "WARNING")
            return False

    def is_phone_extraction_available(self):
        """🆕 Verifica si la funcionalidad de extracción de teléfonos está disponible"""
        try:
            if not self.is_data_extraction_available():
                return False

            # Verificar que el data_extractor tenga soporte para teléfonos
            if hasattr(self.automation_orchestrator.data_extractor, 'phone_field_selectors'):
                return True

            return False

        except Exception as e:
            self._log(f"Error verificando disponibilidad de teléfonos: {e}", "WARNING")
            return False

    def get_automation_status_detailed(self):
        """Obtiene estado detallado incluyendo información de teléfonos"""
        try:
            if not self.is_running or not self.web_driver_manager.driver:
                return {
                    'automation_running': False,
                    'driver_active': False,
                    'components': {},
                    'data_extraction_available': self.is_data_extraction_available(),
                    'phone_extraction_available': self.is_phone_extraction_available(),  # 🆕
                    'last_extraction_file': self.last_extraction_file,
                    'last_phone_count': self.last_phone_count  # 🆕
                }

            status = self.automation_orchestrator.get_automation_status(self.web_driver_manager.driver)
            status['automation_running'] = self.is_running
            status['data_extraction_available'] = self.is_data_extraction_available()
            status['phone_extraction_available'] = self.is_phone_extraction_available()  # 🆕
            status['last_extraction_file'] = self.last_extraction_file
            status['last_phone_count'] = self.last_phone_count  # 🆕
            status['export_directory'] = self.get_export_directory()

            return status

        except Exception as e:
            self._log(f"Error obteniendo estado detallado: {e}", "WARNING")
            return {
                'automation_running': self.is_running,
                'driver_active': False,
                'error': str(e),
                'data_extraction_available': False,
                'phone_extraction_available': False,
                'last_extraction_file': self.last_extraction_file,
                'last_phone_count': self.last_phone_count
            }

    def execute_partial_automation(self, start_step, end_step, **kwargs):
        """Ejecuta automatización parcial usando el orchestrador"""
        try:
            if not self.is_running or not self.web_driver_manager.driver:
                return False, "No hay automatización activa"

            return self.automation_orchestrator.execute_partial_automation(
                self.web_driver_manager.driver, start_step, end_step, **kwargs
            )
        except Exception as e:
            error_msg = f"Error en automatización parcial: {str(e)}"
            self._log(error_msg, "ERROR")
            return False, error_msg

    def _cleanup_on_failure(self):
        """Limpia recursos cuando falla la automatización"""
        try:
            self.automation_orchestrator.cleanup_automation()
        except Exception as e:
            self._log(f"Error en limpieza después de fallo: {e}", "WARNING")

    def _log_automation_config(self, date_config):
        """Registra la configuración de automatización incluyendo teléfonos"""
        try:
            self._log("📋 Configuración de automatización:")
            self._log(f"  🌐 URL objetivo: {self.target_url}")
            self._log(
                f"  📊 Extracción de datos: {'✅ Habilitada' if self.is_data_extraction_available() else '❌ No disponible'}")
            self._log(
                f"  📞 Extracción de teléfonos: {'✅ Habilitada' if self.is_phone_extraction_available() else '❌ No disponible'}")

            if date_config and not date_config.get('skip_dates', True):
                date_from = date_config.get('date_from', 'No especificada')
                date_to = date_config.get('date_to', 'No especificada')
                self._log(f"  📅 Fechas: Desde={date_from}, Hasta={date_to}")
            else:
                self._log("  📅 Fechas: OMITIR (mantener valores actuales)")

            export_dir = self.get_export_directory()
            if export_dir:
                self._log(f"  📁 Directorio de exportación: {export_dir}")

        except Exception as e:
            self._log(f"Error registrando configuración: {e}", "DEBUG")

    def get_handlers_status(self):
        """Obtiene estado de todos los handlers incluyendo funcionalidad de teléfonos"""
        try:
            base_status = {
                'web_driver_manager': {
                    'available': self.web_driver_manager is not None,
                    'selenium_available': self.web_driver_manager.is_selenium_available(),
                    'driver_active': self.web_driver_manager.is_driver_active()
                },
                'login_handler': {
                    'available': self.login_handler is not None
                },
                'dropdown_handler': {
                    'available': self.dropdown_handler is not None
                },
                'date_handler': {
                    'available': self.date_handler is not None
                },
                'button_handler': {
                    'available': self.button_handler is not None,
                    'triple_click_support': True
                },
                'automation_orchestrator': {
                    'available': self.automation_orchestrator is not None,
                    'data_extraction_support': True,
                    'phone_extraction_support': True  # 🆕
                },
                'credentials_manager': {
                    'available': self.credentials_manager is not None,
                    'crypto_available': self.credentials_manager.is_crypto_available()
                }
            }

            # Estado de extracción con teléfonos
            try:
                base_status['data_extraction'] = {
                    'available': self.is_data_extraction_available(),
                    'phone_support': self.is_phone_extraction_available(),  # 🆕
                    'last_file': self.last_extraction_file,
                    'last_phone_count': self.last_phone_count,  # 🆕
                    'export_directory': self.get_export_directory()
                }
            except Exception as e:
                base_status['data_extraction'] = {
                    'available': False,
                    'phone_support': False,
                    'error': str(e)
                }

            return base_status

        except Exception as e:
            self._log(f"Error obteniendo estado de handlers: {e}", "WARNING")
            return {'error': str(e)}

    # 🆕 MÉTODOS PÚBLICOS ADICIONALES PARA FUNCIONALIDAD DE TELÉFONOS

    def get_phone_extraction_summary(self):
        """🆕 Obtiene resumen de la última extracción de teléfonos"""
        try:
            return {
                'last_extraction_file': self.last_extraction_file,
                'last_phone_count': self.last_phone_count,
                'phone_support_available': self.is_phone_extraction_available(),
                'extraction_timestamp': time.time()
            }
        except Exception as e:
            self._log(f"Error obteniendo resumen de teléfonos: {e}", "WARNING")
            return {
                'error': str(e),
                'phone_support_available': False
            }

    def force_phone_extraction_test(self):
        """🆕 Fuerza una prueba de la funcionalidad de teléfonos"""
        try:
            if not self.is_running or not self.web_driver_manager.driver:
                return False, "No hay automatización activa para probar"

            # Probar que los selectores de teléfono funcionen
            if hasattr(self.automation_orchestrator, 'data_extractor'):
                data_extractor = self.automation_orchestrator.data_extractor
                if hasattr(data_extractor, 'phone_field_selectors'):
                    selector_count = len(data_extractor.phone_field_selectors)
                    return True, f"Funcionalidad de teléfonos lista: {selector_count} selectores disponibles"

            return False, "Funcionalidad de teléfonos no disponible"

        except Exception as e:
            return False, f"Error probando funcionalidad de teléfonos: {str(e)}"