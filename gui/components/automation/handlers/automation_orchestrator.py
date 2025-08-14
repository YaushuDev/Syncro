# automation_orchestrator.py
# Ubicación: /syncro_bot/gui/components/automation/handlers/automation_orchestrator.py
"""
Coordinador central del flujo completo de automatización.
Orquesta la secuencia de login, dropdowns, configuración de fechas y botones
usando todos los handlers especializados con manejo robusto de errores.
"""

import time


class AutomationOrchestrator:
    """Coordinador central del flujo completo de automatización"""

    def __init__(self, web_driver_manager, login_handler, dropdown_handler,
                 date_handler, button_handler, logger=None):
        self.web_driver_manager = web_driver_manager
        self.login_handler = login_handler
        self.dropdown_handler = dropdown_handler
        self.date_handler = date_handler
        self.button_handler = button_handler
        self.logger = logger

        # URL objetivo por defecto
        self.target_url = "https://fieldservice.cabletica.com/dispatchFS/"

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
        Ejecuta el flujo completo de automatización:
        1. Navegación y setup
        2. Login automático
        3. Tres dropdowns
        4. Configuración de fechas
        5. Botones (tab y action)
        """
        try:
            self._log("🚀 Iniciando flujo completo de automatización...")

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

            # PASO 6: BOTÓN DE ACCIÓN FINAL
            action_button_success, action_button_message = self._execute_action_button_flow(driver)
            if not action_button_success:
                self._log(f"Advertencia en botón de acción: {action_button_message}", "WARNING")
                return True, f"Automatización casi completa (falta botón final). {action_button_message}"

            # ✅ PROCESO COMPLETO EXITOSO
            final_message = "Automatización completa exitosa: Login, tres dropdowns, configuración de fechas y botón final ejecutados."
            if date_config and not date_config.get('skip_dates', True):
                final_message += f" Fechas configuradas: {date_config.get('date_from', 'N/A')} - {date_config.get('date_to', 'N/A')}"

            self._log(f"✅ {final_message}")
            return True, final_message

        except Exception as e:
            error_msg = f"Error durante el flujo de automatización: {str(e)}"
            self._log(error_msg, "ERROR")
            return False, error_msg

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

    def _execute_action_button_flow(self, driver):
        """Ejecuta el flujo del botón de acción final"""
        try:
            self._log("🔘 Iniciando flujo de botón de acción final...")

            # Botón de acción final
            action_success, action_message = self.button_handler.handle_action_button_click(driver)
            if not action_success:
                return False, f"Error en botón de acción: {action_message}"

            # Verificar resultado
            verify_success, verify_message = self.button_handler.verify_button_click_result(driver, 'action_button')
            if verify_success:
                self._log(f"✅ Verificación exitosa: {verify_message}")

            self._log("✅ Botón de acción final completado")
            return True, action_message

        except Exception as e:
            error_msg = f"Error en flujo de botón de acción: {str(e)}"
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
                'button_fields': False
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
                'action_button': lambda: self._execute_action_button_flow(driver)
            }

            step_order = ['login', 'first_dropdown', 'remaining_dropdowns', 'dates', 'action_button']

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