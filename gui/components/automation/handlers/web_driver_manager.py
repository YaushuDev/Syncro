# web_driver_manager.py
# Ubicación: /syncro_bot/gui/components/automation/handlers/web_driver_manager.py
"""
Gestor especializado del navegador Chrome para automatización.
Maneja la configuración, inicialización, limpieza y operaciones básicas
del driver de Selenium con opciones optimizadas y robustas.
"""

import time

# Importaciones para Selenium
try:
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.common.exceptions import WebDriverException

    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False


class WebDriverManager:
    """Gestor especializado del navegador Chrome con configuración optimizada"""

    def __init__(self, logger=None):
        self.driver = None
        self.logger = logger

        # Configuración de timeouts
        self.page_load_timeout = 30
        self.implicit_wait_timeout = 10

    def _log(self, message, level="INFO"):
        """Log interno con fallback"""
        if self.logger:
            self.logger(message, level)
        else:
            print(f"[{level}] {message}")

    def is_selenium_available(self):
        """Verifica si Selenium está disponible"""
        return SELENIUM_AVAILABLE

    def setup_chrome_driver(self):
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
            self.driver = driver
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

    def cleanup_driver(self):
        """Limpia el driver de Selenium"""
        try:
            if self.driver:
                self._log("Cerrando navegador...")
                self.driver.quit()
                self.driver = None
                self._log("Navegador cerrado correctamente")
        except Exception as e:
            self._log(f"Error limpiando driver: {e}", "WARNING")

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
        """Navega a una URL específica"""
        if not self.driver:
            return False, "No hay driver activo"

        try:
            self._log(f"Navegando a: {url}")
            self.driver.get(url)

            # Esperar que la página cargue completamente
            from selenium.webdriver.support.ui import WebDriverWait
            wait = WebDriverWait(self.driver, self.page_load_timeout)
            wait.until(lambda d: d.execute_script("return document.readyState") == "complete")

            self._log("Página cargada completamente")
            return True, f"Navegación exitosa a: {url}"
        except Exception as e:
            error_msg = f"Error navegando a {url}: {str(e)}"
            self._log(error_msg, "ERROR")
            return False, error_msg

    def execute_script(self, script):
        """Ejecuta JavaScript en la página actual"""
        if not self.driver:
            return False, "No hay driver activo"

        try:
            result = self.driver.execute_script(script)
            self._log(f"Script ejecutado correctamente")
            return True, result
        except Exception as e:
            error_msg = f"Error ejecutando script: {str(e)}"
            self._log(error_msg, "ERROR")
            return False, error_msg

    def scroll_to_element(self, element):
        """Hace scroll a un elemento específico"""
        if not self.driver:
            return False, "No hay driver activo"

        try:
            self.driver.execute_script("arguments[0].scrollIntoView(true);", element)
            time.sleep(1)  # Esperar que termine el scroll
            return True, "Scroll completado"
        except Exception as e:
            error_msg = f"Error haciendo scroll: {str(e)}"
            self._log(error_msg, "ERROR")
            return False, error_msg

    def wait_for_page_load(self):
        """Espera que la página cargue completamente"""
        if not self.driver:
            return False, "No hay driver activo"

        try:
            from selenium.webdriver.support.ui import WebDriverWait
            wait = WebDriverWait(self.driver, self.page_load_timeout)

            # Esperar que el DOM esté completamente cargado
            wait.until(lambda d: d.execute_script("return document.readyState") == "complete")

            # Espera adicional para elementos dinámicos
            time.sleep(2)

            self._log("Página completamente cargada")
            return True, "Página cargada"
        except Exception as e:
            error_msg = f"Error esperando carga de página: {str(e)}"
            self._log(error_msg, "ERROR")
            return False, error_msg

    def get_current_url(self):
        """Obtiene la URL actual"""
        if not self.driver:
            return None

        try:
            return self.driver.current_url
        except Exception as e:
            self._log(f"Error obteniendo URL actual: {e}", "WARNING")
            return None

    def get_page_title(self):
        """Obtiene el título de la página actual"""
        if not self.driver:
            return None

        try:
            return self.driver.title
        except Exception as e:
            self._log(f"Error obteniendo título: {e}", "WARNING")
            return None

    def refresh_page(self):
        """Actualiza la página actual"""
        if not self.driver:
            return False, "No hay driver activo"

        try:
            self._log("Actualizando página...")
            self.driver.refresh()
            return self.wait_for_page_load()
        except Exception as e:
            error_msg = f"Error actualizando página: {str(e)}"
            self._log(error_msg, "ERROR")
            return False, error_msg

    def is_driver_active(self):
        """Verifica si el driver está activo y funcionando"""
        if not self.driver:
            return False

        try:
            # Intentar obtener la URL actual como test
            _ = self.driver.current_url
            return True
        except Exception:
            return False

    def close_current_tab(self):
        """Cierra la pestaña actual"""
        if not self.driver:
            return False, "No hay driver activo"

        try:
            self.driver.close()
            return True, "Pestaña cerrada"
        except Exception as e:
            error_msg = f"Error cerrando pestaña: {str(e)}"
            self._log(error_msg, "ERROR")
            return False, error_msg

    def switch_to_tab(self, tab_index):
        """Cambia a una pestaña específica por índice"""
        if not self.driver:
            return False, "No hay driver activo"

        try:
            handles = self.driver.window_handles
            if 0 <= tab_index < len(handles):
                self.driver.switch_to.window(handles[tab_index])
                return True, f"Cambiado a pestaña {tab_index}"
            else:
                return False, f"Índice de pestaña inválido: {tab_index}"
        except Exception as e:
            error_msg = f"Error cambiando de pestaña: {str(e)}"
            self._log(error_msg, "ERROR")
            return False, error_msg

    def get_window_size(self):
        """Obtiene el tamaño actual de la ventana"""
        if not self.driver:
            return None

        try:
            return self.driver.get_window_size()
        except Exception as e:
            self._log(f"Error obteniendo tamaño de ventana: {e}", "WARNING")
            return None

    def maximize_window(self):
        """Maximiza la ventana del navegador"""
        if not self.driver:
            return False, "No hay driver activo"

        try:
            self.driver.maximize_window()
            return True, "Ventana maximizada"
        except Exception as e:
            error_msg = f"Error maximizando ventana: {str(e)}"
            self._log(error_msg, "ERROR")
            return False, error_msg