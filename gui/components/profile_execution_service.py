# profile_execution_service.py
# Ubicación: /syncro_bot/gui/components/profile_execution_service.py
"""
Servicio de ejecución de perfiles para envío automático de reportes.
Gestiona la ejecución manual/automática de perfiles que generan y envían
reportes Excel por correo electrónico según la programación configurada.
"""

import threading
from datetime import datetime, timedelta

class ProfileExecutionService:
    """Servicio de ejecución de perfiles para reportes automáticos"""

    def __init__(self):
        self.is_executing = False
        self.current_execution = None
        self._lock = threading.Lock()
        self._execution_callbacks = []
        self.registry_tab = None

    def set_registry_tab(self, registry_tab):
        """Establece la referencia al RegistroTab para generación de reportes"""
        self.registry_tab = registry_tab

    def execute_profile(self, profile):
        """Ejecuta un perfil generando y enviando reporte por correo"""
        try:
            with self._lock:
                if self.is_executing:
                    return False, "Ya hay una ejecución de perfil en curso"

                self.is_executing = True
                self.current_execution = {
                    'profile': profile,
                    'start_time': datetime.now(),
                    'status': 'executing'
                }

            # Notificar inicio de ejecución
            self._notify_execution_start(profile)

            # Validar que el sistema de reportes esté disponible
            if not self.registry_tab:
                return self._handle_execution_error(profile, "Sistema de registro no disponible")

            # Generar y enviar reporte
            success, message = self._generate_and_send_report(profile)

            if success:
                return self._handle_execution_success(profile, message)
            else:
                return self._handle_execution_error(profile, message)

        except Exception as e:
            return self._handle_execution_error(profile, str(e))

    def _generate_and_send_report(self, profile):
        """Genera y envía reporte Excel por correo"""
        try:
            profile_name = profile.get('name', 'Perfil desconocido')

            # Generar título personalizado para el reporte
            custom_title = f"Reporte Automático - Perfil '{profile_name}'"

            # Usar el método del RegistroTab para generar y enviar reporte
            # Siempre enviamos reporte de "Últimos 7 días"
            success, message = self.registry_tab.generate_and_send_report(
                report_type="Últimos 7 días",
                custom_title=custom_title
            )

            return success, message

        except Exception as e:
            return False, f"Error generando reporte: {str(e)}"

    def execute_profile_async(self, profile, success_callback=None, error_callback=None):
        """Ejecuta un perfil de forma asíncrona con callbacks"""

        def execute_thread():
            try:
                success, message = self.execute_profile(profile)
                if success and success_callback:
                    success_callback(profile, message)
                elif not success and error_callback:
                    error_callback(profile, message)
            except Exception as e:
                if error_callback:
                    error_callback(profile, str(e))

        thread = threading.Thread(target=execute_thread, daemon=True)
        thread.start()

    def _handle_execution_success(self, profile, message):
        """Maneja el éxito de la ejecución"""
        with self._lock:
            if self.current_execution:
                self.current_execution['status'] = 'completed'
                self.current_execution['end_time'] = datetime.now()

                # Notificar finalización exitosa
                self._notify_execution_end(profile, True, message)

            self.is_executing = False
            self.current_execution = None

        return True, f"Reporte del perfil '{profile['name']}' enviado correctamente: {message}"

    def _handle_execution_error(self, profile, error_message):
        """Maneja errores en la ejecución"""
        with self._lock:
            if self.current_execution:
                self.current_execution['status'] = 'failed'
                self.current_execution['end_time'] = datetime.now()
                self.current_execution['error'] = error_message

                # Notificar finalización con error
                self._notify_execution_end(profile, False, error_message)

            self.is_executing = False
            self.current_execution = None

        return False, f"Error en perfil '{profile['name']}': {error_message}"

    def force_stop_execution(self):
        """Fuerza la detención de la ejecución actual"""
        with self._lock:
            if self.is_executing and self.current_execution:
                profile = self.current_execution['profile']
                self.current_execution['status'] = 'stopped'
                self.current_execution['end_time'] = datetime.now()

                # Notificar detención forzada
                self._notify_execution_end(profile, False, "Ejecución detenida por el usuario")

            self.is_executing = False
            self.current_execution = None

    def is_busy(self):
        """Verifica si está ejecutando un perfil"""
        with self._lock:
            return self.is_executing

    def get_current_execution(self):
        """Obtiene información de la ejecución actual"""
        with self._lock:
            return self.current_execution.copy() if self.current_execution else None

    def add_execution_callback(self, callback):
        """Añade un callback para eventos de ejecución"""
        self._execution_callbacks.append(callback)

    def remove_execution_callback(self, callback):
        """Remueve un callback de eventos de ejecución"""
        if callback in self._execution_callbacks:
            self._execution_callbacks.remove(callback)

    def _notify_execution_start(self, profile):
        """Notifica el inicio de ejecución a los callbacks"""
        for callback in self._execution_callbacks:
            try:
                callback('start', profile, None)
            except Exception as e:
                print(f"Error en callback de inicio: {e}")

    def _notify_execution_end(self, profile, success, message):
        """Notifica la finalización de ejecución a los callbacks"""
        for callback in self._execution_callbacks:
            try:
                callback('end', profile, {'success': success, 'message': message})
            except Exception as e:
                print(f"Error en callback de finalización: {e}")

    def validate_execution_environment(self):
        """Valida que el ambiente esté listo para ejecutar perfiles"""
        if not self.registry_tab:
            return False, "Sistema de registro no disponible"

        if not self.registry_tab.email_tab:
            return False, "Sistema de email no configurado"

        if not self.registry_tab.email_tab.is_email_configured():
            return False, "Email no configurado correctamente"

        return True, "Ambiente listo para enviar reportes"


class ProfileReportService:
    """Servicio especializado en envío automático de reportes para perfiles (SIMPLIFICADO)"""

    def __init__(self, registry_tab=None):
        self.registry_tab = registry_tab
        self._report_history = []

    def set_registry_tab(self, registry_tab):
        """Establece la referencia al RegistroTab"""
        self.registry_tab = registry_tab

    def send_profile_report(self, profile, execution_record=None):
        """Envía reporte para un perfil específico"""
        if not self.registry_tab:
            return False, "Sistema de registro no disponible para enviar reportes"

        try:
            profile_name = profile.get('name', 'Perfil desconocido')
            custom_title = f"Reporte Automático - Perfil '{profile_name}'"

            # Enviar reporte usando el método público del RegistroTab
            success, message = self.registry_tab.generate_and_send_report(
                report_type="Últimos 7 días",
                custom_title=custom_title
            )

            self._add_to_report_history(profile, success, message)
            return success, message

        except Exception as e:
            error_msg = f"Error enviando reporte automático: {str(e)}"
            self._add_to_report_history(profile, False, error_msg)
            return False, error_msg

    def _add_to_report_history(self, profile, success, message):
        """Añade entrada al historial de reportes"""
        history_entry = {
            'profile_id': profile.get('id'),
            'profile_name': profile.get('name'),
            'timestamp': datetime.now().isoformat(),
            'success': success,
            'message': message
        }

        self._report_history.append(history_entry)

        # Mantener solo los últimos 100 reportes
        if len(self._report_history) > 100:
            self._report_history = self._report_history[-100:]

    def get_report_statistics(self):
        """Obtiene estadísticas de reportes enviados"""
        if not self._report_history:
            return {'total_sent': 0, 'successful': 0, 'failed': 0, 'success_rate': 0}

        total = len(self._report_history)
        successful = len([h for h in self._report_history if h['success']])
        success_rate = (successful / total * 100) if total > 0 else 0

        return {
            'total_sent': total,
            'successful': successful,
            'failed': total - successful,
            'success_rate': success_rate
        }


class ProfileScheduler:
    """Scheduler automático para ejecutar perfiles de reportes según horarios programados"""

    def __init__(self, profiles_manager, execution_service, report_service):
        self.profiles_manager = profiles_manager
        self.execution_service = execution_service
        self.report_service = report_service

        # Estado del scheduler
        self.is_running = False
        self._scheduler_thread = None
        self._stop_event = threading.Event()

        # Historial de ejecuciones automáticas
        self._execution_history = []
        self._last_execution_check = {}  # Para evitar ejecuciones duplicadas

        # Mapeo de días
        self._day_mapping = {
            'Lunes': 0, 'Martes': 1, 'Miércoles': 2, 'Jueves': 3,
            'Viernes': 4, 'Sábado': 5, 'Domingo': 6
        }

    def start_scheduler(self):
        """Inicia el scheduler automático"""
        if self.is_running:
            return False, "Scheduler ya está ejecutándose"

        try:
            self.is_running = True
            self._stop_event.clear()
            self._scheduler_thread = threading.Thread(target=self._scheduler_loop, daemon=True)
            self._scheduler_thread.start()

            print("✅ ProfileScheduler (Reportes) iniciado correctamente")
            return True, "Scheduler de reportes iniciado correctamente"

        except Exception as e:
            self.is_running = False
            return False, f"Error iniciando scheduler: {str(e)}"

    def stop_scheduler(self):
        """Detiene el scheduler automático"""
        if not self.is_running:
            return True, "Scheduler no estaba ejecutándose"

        try:
            self.is_running = False
            self._stop_event.set()

            if self._scheduler_thread and self._scheduler_thread.is_alive():
                self._scheduler_thread.join(timeout=5)

            print("✅ ProfileScheduler (Reportes) detenido correctamente")
            return True, "Scheduler de reportes detenido correctamente"

        except Exception as e:
            return False, f"Error deteniendo scheduler: {str(e)}"

    def _scheduler_loop(self):
        """Loop principal del scheduler"""
        print("🔄 Scheduler loop de reportes iniciado")

        while not self._stop_event.is_set():
            try:
                self._check_and_execute_profiles()
            except Exception as e:
                print(f"❌ Error en scheduler loop de reportes: {e}")

            # Esperar 60 segundos o hasta que se detenga
            self._stop_event.wait(60)

        print("🛑 Scheduler loop de reportes terminado")

    def _check_and_execute_profiles(self):
        """Revisa y ejecuta perfiles que deben enviar reportes ahora"""
        now = datetime.now()
        current_weekday = now.weekday()

        try:
            active_profiles = self.profiles_manager.get_active_profiles()

            for profile in active_profiles:
                if self._should_execute_profile(profile, now, current_weekday):
                    self._execute_scheduled_profile(profile, now)

        except Exception as e:
            print(f"❌ Error revisando perfiles: {e}")

    def _should_execute_profile(self, profile, now, current_weekday):
        """Determina si un perfil debe ejecutar reporte en este momento"""
        try:
            # Verificar que no se haya ejecutado ya en este minuto
            profile_id = profile['id']
            last_execution_key = f"{profile_id}_{now.strftime('%Y-%m-%d_%H:%M')}"

            if last_execution_key in self._last_execution_check:
                return False

            # Verificar horario
            profile_hour = int(profile.get('hour', 0))
            profile_minute = int(profile.get('minute', 0))

            if now.hour != profile_hour or now.minute != profile_minute:
                return False

            # Verificar día de la semana
            profile_days = profile.get('days', [])
            if not profile_days:
                return False

            # Convertir días del perfil a números de semana
            profile_weekdays = []
            for day_name in profile_days:
                if day_name in self._day_mapping:
                    profile_weekdays.append(self._day_mapping[day_name])

            if current_weekday not in profile_weekdays:
                return False

            # Verificar que no esté ocupado el execution service
            if self.execution_service.is_busy():
                print(f"⏳ Perfil '{profile['name']}' debe ejecutarse pero el servicio está ocupado")
                return False

            return True

        except Exception as e:
            print(f"❌ Error evaluando perfil '{profile.get('name', 'Desconocido')}': {e}")
            return False

    def _execute_scheduled_profile(self, profile, execution_time):
        """Ejecuta un perfil programado (envío de reporte)"""
        profile_id = profile['id']
        execution_key = f"{profile_id}_{execution_time.strftime('%Y-%m-%d_%H:%M')}"

        # Marcar como ejecutado para evitar duplicados
        self._last_execution_check[execution_key] = execution_time

        try:
            print(f"📧 Enviando reporte programado: '{profile['name']}' a las {execution_time.strftime('%H:%M')}")

            # Ejecutar usando el servicio existente (ahora envía reporte en lugar de automatización)
            success, message = self.execution_service.execute_profile(profile)

            # Registrar en historial
            execution_record = {
                'profile_id': profile_id,
                'profile_name': profile['name'],
                'scheduled_time': execution_time.isoformat(),
                'success': success,
                'message': message,
                'execution_type': 'scheduled_report'
            }

            self._execution_history.append(execution_record)

            if success:
                print(f"✅ Reporte '{profile['name']}' enviado exitosamente")
            else:
                print(f"❌ Error enviando reporte '{profile['name']}': {message}")

            # Limpiar historial si es muy grande
            if len(self._last_execution_check) > 1000:
                cutoff_time = execution_time - timedelta(hours=24)
                self._last_execution_check = {
                    k: v for k, v in self._last_execution_check.items()
                    if v > cutoff_time
                }

        except Exception as e:
            print(f"❌ Excepción enviando reporte '{profile['name']}': {e}")

    def get_next_scheduled_executions(self, limit=5):
        """Obtiene las próximas ejecuciones programadas de reportes"""
        try:
            active_profiles = self.profiles_manager.get_active_profiles()
            next_executions = []

            for profile in active_profiles[:limit]:
                next_time = self._calculate_next_execution_time(profile)
                next_executions.append({
                    'profile': profile,
                    'next_execution': next_time,
                    'status': 'scheduled_report' if next_time != 'Error calculando' else 'error'
                })

            return next_executions

        except Exception as e:
            print(f"Error obteniendo próximas ejecuciones: {e}")
            return []

    def _calculate_next_execution_time(self, profile):
        """Calcula la próxima hora de ejecución para un perfil"""
        try:
            now = datetime.now()
            hour = int(profile.get('hour', 0))
            minute = int(profile.get('minute', 0))
            days = profile.get('days', [])

            if not days:
                return "Sin días configurados"

            # Convertir días a números
            target_weekdays = [self._day_mapping[day] for day in days if day in self._day_mapping]

            if not target_weekdays:
                return "Días inválidos"

            # Buscar la próxima fecha de ejecución
            for days_ahead in range(8):
                check_date = now + timedelta(days=days_ahead)
                if check_date.weekday() in target_weekdays:
                    execution_time = check_date.replace(hour=hour, minute=minute, second=0, microsecond=0)

                    # Si es hoy pero ya pasó la hora, continuar
                    if days_ahead == 0 and execution_time <= now:
                        continue

                    if days_ahead == 0:
                        return f"Hoy a las {hour:02d}:{minute:02d}"
                    elif days_ahead == 1:
                        return f"Mañana a las {hour:02d}:{minute:02d}"
                    else:
                        return f"{execution_time.strftime('%A %d/%m')} a las {hour:02d}:{minute:02d}"

            return "Error calculando próxima ejecución"

        except Exception as e:
            return f"Error: {str(e)}"

    def get_execution_history(self, limit=50):
        """Obtiene historial de ejecuciones programadas de reportes"""
        return sorted(self._execution_history, key=lambda x: x['scheduled_time'], reverse=True)[:limit]

    def force_execute_profile(self, profile_id):
        """Fuerza el envío inmediato de reporte de un perfil"""
        try:
            profile = self.profiles_manager.get_profile_by_id(profile_id)
            if not profile:
                return False, "Perfil no encontrado"

            if not profile.get('enabled', False):
                return False, "Perfil deshabilitado"

            return self.execution_service.execute_profile(profile)

        except Exception as e:
            return False, f"Error en envío forzado: {str(e)}"

    def get_scheduler_status(self):
        """Obtiene estado actual del scheduler"""
        return {
            'is_running': self.is_running,
            'thread_alive': self._scheduler_thread.is_alive() if self._scheduler_thread else False,
            'total_executions': len(self._execution_history),
            'last_check_count': len(self._last_execution_check)
        }