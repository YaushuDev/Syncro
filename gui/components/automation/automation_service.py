# automation_service.py
# Ubicación: /syncro_bot/gui/components/automation/automation_service.py
"""
Servicio principal de automatización refactorizado con arquitectura modular.
Interfaz pública principal que coordina todos los handlers especializados
para login automático, dropdowns, configuración de fechas y botones.
Mantiene compatibilidad completa con la API original.
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
    """Servicio principal de automatización con arquitectura modular refactorizada"""

    def __init__(self, logger=None):
        self.is_running = False
        self.target_url = "https://fieldservice.cabletica.com/dispatchFS/"
        self._lock = threading.Lock()
        self.logger = logger

        # Inicializar gestores especializados
        self._initialize_handlers()

        # Gestor de credenciales
        self.credentials_manager = CredentialsManager()

    def _initialize_handlers(self):
        """Inicializa todos los handlers especializados"""
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

            # Handler de botones
            self.button_handler = ButtonHandler(
                web_driver_manager=self.web_driver_manager,
                logger=self._log
            )

            # Orchestrador principal
            self.automation_orchestrator = AutomationOrchestrator(
                web_driver_manager=self.web_driver_manager,
                login_handler=self.login_handler,
                dropdown_handler=self.dropdown_handler,
                date_handler=self.date_handler,
                button_handler=self.button_handler,
                logger=self._log
            )

            self._log("🔧 Handlers de automatización inicializados correctamente")

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
        """Inicia el proceso de automatización completo con arquitectura modular"""
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

                # Procesar configuración de fechas
                if not date_config:
                    date_config = {'skip_dates': True}

                self._log("🚀 Iniciando automatización completa con arquitectura modular...")
                self._log_automation_config(date_config)

                # Ejecutar automatización usando el orchestrador
                success, message = self.automation_orchestrator.execute_complete_automation(
                    username, password, date_config
                )

                if success:
                    self.is_running = True
                    self._log("✅ Automatización completada exitosamente")
                    return True, message
                else:
                    self._log(f"❌ Automatización falló: {message}", "ERROR")
                    self._cleanup_on_failure()
                    return False, message

        except Exception as e:
            self._log(f"❌ Excepción en start_automation: {str(e)}", "ERROR")
            self._cleanup_on_failure()
            return False, f"Error al iniciar automatización: {str(e)}"

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

    def get_automation_status_detailed(self):
        """Obtiene estado detallado de todos los componentes"""
        try:
            if not self.is_running or not self.web_driver_manager.driver:
                return {
                    'automation_running': False,
                    'driver_active': False,
                    'components': {}
                }

            status = self.automation_orchestrator.get_automation_status(self.web_driver_manager.driver)
            status['automation_running'] = self.is_running

            return status

        except Exception as e:
            self._log(f"Error obteniendo estado detallado: {e}", "WARNING")
            return {
                'automation_running': self.is_running,
                'driver_active': False,
                'error': str(e)
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
        """Registra la configuración de automatización"""
        try:
            self._log("📋 Configuración de automatización:")
            self._log(f"  🌐 URL objetivo: {self.target_url}")

            if date_config and not date_config.get('skip_dates', True):
                date_from = date_config.get('date_from', 'No especificada')
                date_to = date_config.get('date_to', 'No especificada')
                self._log(f"  📅 Fechas: Desde={date_from}, Hasta={date_to}")
            else:
                self._log("  📅 Fechas: OMITIR (mantener valores actuales)")

        except Exception as e:
            self._log(f"Error registrando configuración: {e}", "DEBUG")

    def get_handlers_status(self):
        """Obtiene estado de todos los handlers"""
        try:
            return {
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
                    'available': self.button_handler is not None
                },
                'automation_orchestrator': {
                    'available': self.automation_orchestrator is not None
                },
                'credentials_manager': {
                    'available': self.credentials_manager is not None,
                    'crypto_available': self.credentials_manager.is_crypto_available()
                }
            }
        except Exception as e:
            self._log(f"Error obteniendo estado de handlers: {e}", "WARNING")
            return {}