# automation_orchestrator.py
# Ubicación: /syncro_bot/gui/components/automation/handlers/automation_orchestrator.py
"""
Coordinador central del flujo completo de automatización.
Orquesta la secuencia de login, dropdowns, configuración de fechas, triple clic
en búsqueda, extracción de datos y exportación a Excel usando todos los handlers
especializados con manejo robusto de errores.
"""

import time


class AutomationOrchestrator:
    """Coordinador central del flujo completo de automatización con extracción de datos"""

    def __init__(self, web_driver_manager, login_handler, dropdown_handler,
                 date_handler, button_handler, logger=None):
        self.web_driver_manager = web_driver_manager
        self.login_handler = login_handler
        self.dropdown_handler = dropdown_handler
        self.date_handler = date_handler
        self.button_handler = button_handler
        self.logger = logger

        # 🆕 Nuevos handlers para extracción y exportación
        self.data_extractor = None
        self.excel_exporter = None

        # URL objetivo por defecto
        self.target_url = "https://fieldservice.cabletica.com/dispatchFS/"

        # Inicializar nuevos handlers
        self._initialize_data_handlers()

    def _initialize_data_handlers(self):
        """🆕 Inicializa los handlers de extracción y exportación de datos"""
        try:
            # Importar y crear handlers de datos
            from .data_extractor import DataExtractor
            from .excel_exporter import ExcelExporter

            self.data_extractor = DataExtractor(
                web_driver_manager=self.web_driver_manager,
                logger=self._log
            )

            self.excel_exporter = ExcelExporter(logger=self._log)

            self._log("🔧 Handlers de extracción y exportación inicializados")

        except ImportError as e:
            self._log(f"❌ Error importando handlers de datos: {str(e)}", "ERROR")
            self.data_extractor = None
            self.excel_exporter = None
        except Exception as e:
            self._log(f"❌ Error inicializando handlers de datos: {str(e)}", "ERROR")
            self.data_extractor = None
            self.excel_exporter = None

    def _log(self, message, level="INFO"):
        """Log interno con fallback"""
        if self.logger:
            self.logger(message, level)
        else:
            print(f"[{level}] {message}")

    def set_target_url(self, url):
        """Establece la URL objetivo"""
        self.target_url = url
        self.web_driver_manager.target_url = url

    def execute_complete_automation(self, username, password, date_config=None):
        """
        🔄 Ejecuta el flujo completo de automatización ACTUALIZADO:
        1. Navegación y setup
        2. Login automático
        3. Tres dropdowns
        4. Configuración de fechas
        5. Botón de pestaña
        6. 🆕 TRIPLE CLIC en botón de búsqueda
        7. 🆕 Extracción de datos de la tabla
        8. 🆕 Exportación a Excel
        """
        try:
            self._log("🚀 Iniciando flujo completo de automatización con extracción de datos...")

            # PASO 1: CONFIGURAR DRIVER Y NAVEGAR
            driver = self._setup_and_navigate()
            if not driver:
                return False, "Error configurando navegador o navegando a la página"

            # PASO 2: LOGIN AUTOMÁTICO
            login_success, login_message = self._execute_login_flow(driver, username, password)
            if not login_success:
                return False, login_message

            # PASO 3: PRIMER DROPDOWN Y BOTÓN DE PESTAÑA
            first_dropdown_success, first_dropdown_message = self._execute_first_dropdown_flow(driver)
            if not first_dropdown_success:
                self._log(f"Advertencia en primer dropdown: {first_dropdown_message}", "WARNING")
                return True, f"Login exitoso. {first_dropdown_message}"

            # PASO 4: SEGUNDO Y TERCER DROPDOWN
            remaining_dropdowns_success, remaining_dropdowns_message = self._execute_remaining_dropdowns_flow(driver)
            if not remaining_dropdowns_success:
                self._log(f"Advertencia en dropdowns restantes: {remaining_dropdowns_message}", "WARNING")
                return True, f"Login y primer dropdown completados. {remaining_dropdowns_message}"

            # PASO 5: CONFIGURACIÓN DE FECHAS
            date_success, date_message = self._execute_date_configuration_flow(driver, date_config)
            if not date_success:
                self._log(f"Advertencia en configuración de fechas: {date_message}", "WARNING")
                return True, f"Login y dropdowns completados. {date_message}"

            # 🆕 PASO 6: TRIPLE CLIC EN BÚSQUEDA Y EXTRACCIÓN DE DATOS
            extraction_success, extraction_message, excel_file = self._execute_data_extraction_flow(driver)
            if not extraction_success:
                self._log(f"Error en extracción de datos: {extraction_message}", "ERROR")
                return True, f"Automatización completada pero sin extracción de datos. {extraction_message}"

            # ✅ PROCESO COMPLETO EXITOSO CON DATOS
            final_message = f"🎉 Automatización completa exitosa: Login, dropdowns, fechas, extracción y Excel generado."
            if excel_file:
                final_message += f" Archivo Excel: {excel_file}"
            if date_config and not date_config.get('skip_dates', True):
                final_message += f" Fechas: {date_config.get('date_from', 'N/A')} - {date_config.get('date_to', 'N/A')}"

            self._log(f"✅ {final_message}")
            return True, final_message

        except Exception as e:
            error_msg = f"Error durante el flujo de automatización: {str(e)}"
            self._log(error_msg, "ERROR")
            return False, error_msg

    def _execute_data_extraction_flow(self, driver):
        """🆕 Ejecuta el flujo de triple clic, extracción de datos y exportación a Excel"""
        try:
            self._log("📊 Iniciando flujo de extracción de datos...")

            # Verificar que los handlers estén disponibles
            if not self.data_extractor or not self.excel_exporter:
                return False, "Handlers de extracción no disponibles", None

            # Verificar que Excel esté disponible
            if not self.excel_exporter.is_available():
                return False, "openpyxl no está instalado para crear archivos Excel", None

            # TRIPLE CLIC en el botón de búsqueda
            self._log("🔘🔘🔘 Ejecutando triple clic en botón de búsqueda...")
            triple_click_success, triple_click_message = self.button_handler.handle_search_button_triple_click(driver)

            if not triple_click_success:
                return False, f"Error en triple clic: {triple_click_message}", None

            self._log(f"✅ Triple clic completado: {triple_click_message}")

            # EXTRACCIÓN DE DATOS de la tabla
            self._log("📋 Extrayendo datos de la tabla...")
            extraction_success, extraction_message, extracted_data = self.data_extractor.extract_table_data(driver)

            if not extraction_success:
                return False, f"Error extrayendo datos: {extraction_message}", None

            if not extracted_data:
                return False, "No se extrajeron datos de la tabla", None

            self._log(f"✅ Datos extraídos: {len(extracted_data)} registros")

            # VALIDACIÓN de los datos extraídos
            validation_success, validation_message = self.data_extractor.validate_extracted_data(extracted_data)
            if not validation_success:
                self._log(f"⚠️ Advertencia en validación: {validation_message}", "WARNING")

            # RESUMEN de extracción
            summary_info = self.data_extractor.get_extraction_summary(extracted_data)
            self._log(
                f"📊 Resumen: {summary_info.get('valid_records', 0)} registros válidos de {summary_info.get('total_records', 0)} totales")

            # EXPORTACIÓN A EXCEL
            self._log("📄 Creando archivo Excel...")
            excel_success, excel_message, excel_filepath = self.excel_exporter.export_with_summary(
                extracted_data, summary_info
            )

            if not excel_success:
                return False, f"Error creando Excel: {excel_message}", None

            # VALIDACIÓN del archivo Excel
            validation_success, validation_message = self.excel_exporter.validate_excel_file(excel_filepath)
            if validation_success:
                self._log(f"✅ Excel validado: {validation_message}")
            else:
                self._log(f"⚠️ Advertencia validando Excel: {validation_message}", "WARNING")

            success_message = f"Extracción completada: {len(extracted_data)} registros → {excel_filepath}"
            return True, success_message, excel_filepath

        except Exception as e:
            error_msg = f"Error en flujo de extracción: {str(e)}"
            self._log(error_msg, "ERROR")
            return False, error_msg, None

    def _setup_and_navigate(self):
        """Configura el driver y navega a la página objetivo"""
        try:
            self._log("🔧 Configurando navegador...")

            # Configurar driver
            driver, success, setup_message = self.web_driver_manager.setup_chrome_driver()
            if not success:
                self._log(f"❌ Error configurando driver: {setup_message}", "ERROR")
                return None

            # Navegar a la página
            self._log(f"🌐 Navegando a: {self.target_url}")
            nav_success, nav_message = self.web_driver_manager.navigate_to_url(self.target_url)
            if not nav_success:
                self._log(f"❌ Error navegando: {nav_message}", "ERROR")
                self.web_driver_manager.cleanup_driver()
                return None

            # Esperar carga completa
            load_success, load_message = self.web_driver_manager.wait_for_page_load()
            if not load_success:
                self._log(f"⚠️ Advertencia carga de página: {load_message}", "WARNING")

            self._log("✅ Navegador configurado y página cargada")
            return driver

        except Exception as e:
            error_msg = f"Error en setup y navegación: {str(e)}"
            self._log(error_msg, "ERROR")
            return None

    def _execute_login_flow(self, driver, username, password):
        """Ejecuta el flujo completo de login"""
        try:
            self._log("🔐 Iniciando flujo de login...")

            # Verificar si ya estamos logueados
            already_logged, login_status = self.login_handler.is_already_logged_in(driver)
            if already_logged:
                self._log("✅ Usuario ya está logueado")
                return True, "Usuario ya estaba logueado"

            # Validar página de login
            page_valid, page_message = self.login_handler.validate_login_page(driver)
            if not page_valid:
                return False, f"Página de login inválida: {page_message}"

            # Esperar formulario de login
            form_ready, form_message = self.login_handler.wait_for_login_form(driver)
            if not form_ready:
                return False, f"Formulario de login no disponible: {form_message}"

            # Realizar login
            login_success, login_message = self.login_handler.perform_login(driver, username, password)
            if not login_success:
                return False, f"Login fallido: {login_message}"

            self._log("✅ Login completado exitosamente")
            return True, login_message

        except Exception as e:
            error_msg = f"Error en flujo de login: {str(e)}"
            self._log(error_msg, "ERROR")
            return False, error_msg

    def _execute_first_dropdown_flow(self, driver):
        """Ejecuta el flujo del primer dropdown y botón de pestaña"""
        try:
            self._log("🔽 Iniciando flujo de primer dropdown...")

            # Primer dropdown
            first_dropdown_success, first_dropdown_message = self.dropdown_handler.handle_first_dropdown_selection(
                driver)
            if not first_dropdown_success:
                return False, first_dropdown_message

            # Botón de pestaña después del primer dropdown
            self._log("🔘 Procediendo con botón de pestaña...")
            tab_button_success, tab_button_message = self.button_handler.handle_tab_button_click(driver)
            if not tab_button_success:
                return False, f"Primer dropdown OK, pero {tab_button_message}"

            self._log("✅ Primer dropdown y botón de pestaña completados")
            return True, "Primer dropdown y botón de pestaña ejecutados exitosamente"

        except Exception as e:
            error_msg = f"Error en flujo de primer dropdown: {str(e)}"
            self._log(error_msg, "ERROR")
            return False, error_msg

    def _execute_remaining_dropdowns_flow(self, driver):
        """Ejecuta el flujo de segundo y tercer dropdown"""
        try:
            self._log("🔽 Iniciando flujo de dropdowns restantes...")

            # Segundo dropdown
            second_dropdown_success, second_dropdown_message = self.dropdown_handler.handle_second_dropdown_selection(
                driver)
            if not second_dropdown_success:
                return False, f"Error en segundo dropdown: {second_dropdown_message}"

            # Tercer dropdown
            third_dropdown_success, third_dropdown_message = self.dropdown_handler.handle_third_dropdown_selection(
                driver)
            if not third_dropdown_success:
                return False, f"Segundo dropdown OK, pero error en tercer dropdown: {third_dropdown_message}"

            # Validación final de todos los dropdowns
            validation_success, validation_message = self.dropdown_handler.validate_dropdown_selections(driver)
            if not validation_success:
                self._log(f"⚠️ Advertencia en validación: {validation_message}", "WARNING")

            self._log("✅ Dropdowns restantes completados")
            return True, "Segundo y tercer dropdown ejecutados exitosamente"

        except Exception as e:
            error_msg = f"Error en flujo de dropdowns restantes: {str(e)}"
            self._log(error_msg, "ERROR")
            return False, error_msg

    def _execute_date_configuration_flow(self, driver, date_config):
        """Ejecuta el flujo de configuración de fechas"""
        try:
            self._log("📅 Iniciando flujo de configuración de fechas...")

            # Verificar si los campos de fecha están presentes
            fields_present, fields_message = self.date_handler.validate_date_fields_present(driver)
            if not fields_present:
                self._log(f"⚠️ Campos de fecha no disponibles: {fields_message}", "WARNING")
                return True, f"Fechas omitidas: {fields_message}"

            # Configurar fechas
            date_success, date_message = self.date_handler.handle_date_configuration(driver, date_config)
            if not date_success:
                return False, f"Error configurando fechas: {date_message}"

            self._log("✅ Configuración de fechas completada")
            return True, date_message

        except Exception as e:
            error_msg = f"Error en flujo de fechas: {str(e)}"
            self._log(error_msg, "ERROR")
            return False, error_msg

    def test_automation_components(self, username, password, date_config=None):
        """Prueba todos los componentes de automatización sin ejecutar el flujo completo"""
        try:
            self._log("🧪 Iniciando prueba de componentes de automatización...")

            results = {
                'driver_setup': False,
                'navigation': False,
                'login_fields': False,
                'login_process': False,
                'dropdown_fields': False,
                'date_fields': False,
                'button_fields': False,
                'data_extraction': False,
                'excel_export': False
            }

            # Test 1: Configurar driver
            driver = self._setup_and_navigate()
            if driver:
                results['driver_setup'] = True
                results['navigation'] = True
                self._log("✅ Driver y navegación: OK")

                # Test 2: Campos de login
                fields_present, _ = self.login_handler.check_login_fields_present(driver)
                results['login_fields'] = fields_present
                if fields_present:
                    self._log("✅ Campos de login: OK")

                    # Test 3: Proceso de login
                    login_success, login_message = self.login_handler.perform_login(driver, username, password)
                    results['login_process'] = login_success
                    if login_success:
                        self._log("✅ Proceso de login: OK")

                        # Test 4: Campos de dropdown
                        dropdown_values = self.dropdown_handler.get_current_dropdown_values(driver)
                        results['dropdown_fields'] = dropdown_values is not None
                        if dropdown_values is not None:
                            self._log("✅ Campos de dropdown: OK")

                        # Test 5: Campos de fecha
                        date_fields_present, _ = self.date_handler.validate_date_fields_present(driver)
                        results['date_fields'] = date_fields_present
                        if date_fields_present:
                            self._log("✅ Campos de fecha: OK")

                        # Test 6: Botones
                        buttons_present, _ = self.button_handler.validate_buttons_present(driver)
                        results['button_fields'] = buttons_present
                        if buttons_present:
                            self._log("✅ Botones: OK")

                        # 🆕 Test 7: Extracción de datos
                        if self.data_extractor:
                            stats = self.data_extractor.get_table_statistics(driver)
                            results['data_extraction'] = not stats.get('error')
                            if results['data_extraction']:
                                self._log("✅ Extracción de datos: OK")

                        # 🆕 Test 8: Exportación Excel
                        if self.excel_exporter:
                            results['excel_export'] = self.excel_exporter.is_available()
                            if results['excel_export']:
                                self._log("✅ Exportación Excel: OK")

                # Limpiar
                self.web_driver_manager.cleanup_driver()

            # Generar reporte
            passed_tests = sum(results.values())
            total_tests = len(results)

            if passed_tests == total_tests:
                return True, f"Todos los componentes funcionan correctamente ({passed_tests}/{total_tests})"
            else:
                failed_tests = [test for test, result in results.items() if not result]
                return False, f"Algunos componentes fallaron ({passed_tests}/{total_tests}). Fallidos: {', '.join(failed_tests)}"

        except Exception as e:
            error_msg = f"Error probando componentes: {str(e)}"
            self._log(error_msg, "ERROR")
            return False, error_msg

    def get_automation_status(self, driver):
        """Obtiene el estado completo de todos los componentes"""
        try:
            if not driver or not self.web_driver_manager.is_driver_active():
                return {
                    'driver_active': False,
                    'current_url': None,
                    'page_title': None,
                    'components_ready': False
                }

            status = {
                'driver_active': True,
                'current_url': self.web_driver_manager.get_current_url(),
                'page_title': self.web_driver_manager.get_page_title(),
                'components_ready': True
            }

            # Estado de login
            already_logged, _ = self.login_handler.is_already_logged_in(driver)
            status['logged_in'] = already_logged

            # Estado de dropdowns
            dropdown_values = self.dropdown_handler.get_current_dropdown_values(driver)
            status['dropdown_values'] = dropdown_values

            # Estado de fechas
            date_values = self.date_handler.get_current_date_values(driver)
            status['date_values'] = date_values

            # Estado de botones
            button_states = self.button_handler.get_button_states(driver)
            status['button_states'] = button_states

            # 🆕 Estado de extracción
            if self.data_extractor:
                table_stats = self.data_extractor.get_table_statistics(driver)
                status['table_stats'] = table_stats

            # 🆕 Estado de exportación
            if self.excel_exporter:
                export_info = self.excel_exporter.get_export_info()
                status['export_info'] = export_info

            return status

        except Exception as e:
            self._log(f"Error obteniendo estado de automatización: {e}", "WARNING")
            return {
                'driver_active': False,
                'error': str(e)
            }

    def execute_partial_automation(self, driver, start_step, end_step, **kwargs):
        """Ejecuta solo una parte específica del flujo de automatización"""
        try:
            self._log(f"🎯 Ejecutando automatización parcial: {start_step} → {end_step}")

            steps = {
                'login': lambda: self._execute_login_flow(driver, kwargs.get('username'), kwargs.get('password')),
                'first_dropdown': lambda: self._execute_first_dropdown_flow(driver),
                'remaining_dropdowns': lambda: self._execute_remaining_dropdowns_flow(driver),
                'dates': lambda: self._execute_date_configuration_flow(driver, kwargs.get('date_config')),
                'data_extraction': lambda: self._execute_data_extraction_flow(driver)
            }

            step_order = ['login', 'first_dropdown', 'remaining_dropdowns', 'dates', 'data_extraction']

            # Validar pasos
            if start_step not in step_order or end_step not in step_order:
                return False, "Pasos inválidos especificados"

            start_index = step_order.index(start_step)
            end_index = step_order.index(end_step)

            if start_index > end_index:
                return False, "El paso inicial debe ser anterior al paso final"

            # Ejecutar pasos seleccionados
            executed_steps = []
            for i in range(start_index, end_index + 1):
                step_name = step_order[i]
                step_function = steps[step_name]

                self._log(f"Ejecutando paso: {step_name}")

                if step_name == 'data_extraction':
                    # Para extracción de datos, manejar el retorno especial
                    success, message, excel_file = step_function()
                    if success:
                        executed_steps.append(f"{step_name} (Excel: {excel_file})")
                    else:
                        return False, f"Error en paso {step_name}: {message}"
                else:
                    success, message = step_function()
                    if success:
                        executed_steps.append(step_name)
                    else:
                        return False, f"Error en paso {step_name}: {message}"

            return True, f"Pasos ejecutados exitosamente: {' → '.join(executed_steps)}"

        except Exception as e:
            error_msg = f"Error en automatización parcial: {str(e)}"
            self._log(error_msg, "ERROR")
            return False, error_msg

    def cleanup_automation(self):
        """Limpia todos los recursos de automatización"""
        try:
            self._log("🧹 Limpiando recursos de automatización...")
            self.web_driver_manager.cleanup_driver()
            self._log("✅ Recursos limpiados correctamente")
            return True, "Limpieza completada"
        except Exception as e:
            error_msg = f"Error limpiando recursos: {str(e)}"
            self._log(error_msg, "ERROR")
            return False, error_msg

    # 🆕 MÉTODOS PÚBLICOS PARA EXTRACCIÓN DE DATOS

    def extract_data_only(self, driver):
        """🆕 Ejecuta solo la extracción de datos (asume que ya se ejecutó el flujo completo)"""
        try:
            if not self.data_extractor or not self.excel_exporter:
                return False, "Handlers de extracción no disponibles", None

            return self._execute_data_extraction_flow(driver)

        except Exception as e:
            error_msg = f"Error en extracción independiente: {str(e)}"
            self._log(error_msg, "ERROR")
            return False, error_msg, None

    def test_data_extraction(self, driver):
        """🆕 Prueba solo la funcionalidad de extracción de datos"""
        try:
            if not self.data_extractor:
                return False, "Data extractor no disponible"

            # Obtener estadísticas básicas
            stats = self.data_extractor.get_table_statistics(driver)

            if stats.get('error'):
                return False, f"Error en estadísticas: {stats['error']}"

            return True, f"Extracción disponible: {stats.get('total_rows', 0)} filas detectadas"

        except Exception as e:
            return False, f"Error probando extracción: {str(e)}"

    def get_export_directory(self):
        """🆕 Obtiene el directorio donde se guardan los archivos Excel"""
        if self.excel_exporter:
            return self.excel_exporter.output_directory
        return None