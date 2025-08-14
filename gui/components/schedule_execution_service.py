# schedule_execution_service.py
# Ubicación: /syncro_bot/gui/components/schedule_execution_service.py
"""
Servicio de ejecución de programaciones para automatización del bot CORREGIDO.
Gestiona la ejecución manual/automática de programaciones que ejecutan
el bot automáticamente según la programación configurada de horarios.
Incluye validaciones robustas, configuración de fechas y manejo correcto de credenciales.
"""

import threading
from datetime import datetime, timedelta


class ScheduleExecutionService:
    """Servicio de ejecución de programaciones para automatización del bot (CORREGIDO)"""

    def __init__(self):
        self.is_executing = False
        self.current_execution = None
        self._lock = threading.Lock()
        self._execution_callbacks = []
        self.automation_tab = None
        self.registry_tab = None

    def set_automation_tab(self, automation_tab):
        """Establece la referencia al AutomationTab para ejecutar el bot"""
        self.automation_tab = automation_tab

    def set_registry_tab(self, registry_tab):
        """Establece la referencia al RegistryTab para logging"""
        self.registry_tab = registry_tab

    def execute_schedule(self, schedule):
        """Ejecuta una programación ejecutando el bot automáticamente (MÉTODO CORREGIDO)"""
        try:
            with self._lock:
                if self.is_executing:
                    return False, "Ya hay una ejecución de programación en curso"

                self.is_executing = True
                self.current_execution = {
                    'schedule': schedule,
                    'start_time': datetime.now(),
                    'status': 'executing'
                }

            # Notificar inicio de ejecución
            self._notify_execution_start(schedule)

            # Validar que el sistema de automatización esté disponible
            if not self.automation_tab:
                return self._handle_execution_error(schedule, "Sistema de automatización no disponible")

            # NUEVO: Validar credenciales antes de ejecutar
            validation_result = self._validate_execution_environment(schedule)
            if not validation_result[0]:
                return self._handle_execution_error(schedule, validation_result[1])

            # CORREGIDO: Ejecutar el bot automáticamente con configuración completa
            success, message = self._execute_bot_automation_corrected(schedule)

            if success:
                return self._handle_execution_success(schedule, message)
            else:
                return self._handle_execution_error(schedule, message)

        except Exception as e:
            return self._handle_execution_error(schedule, str(e))

    def _validate_execution_environment(self, schedule):
        """NUEVO: Valida que el ambiente esté listo para ejecutar programaciones"""
        try:
            # Verificar AutomationTab
            if not self.automation_tab:
                return False, "Sistema de automatización no disponible"

            # Verificar que el bot no esté ya ejecutándose
            if self.automation_tab.get_automation_status():
                return False, "El bot ya está en ejecución"

            # Verificar credenciales
            credentials = self.automation_tab.credentials_manager.load_credentials()
            if not credentials:
                return False, "No hay credenciales configuradas para automatización programada"

            username = credentials.get('username')
            password = credentials.get('password')

            # Validar formato de credenciales
            valid, message = self.automation_tab.credentials_manager.validate_credentials(username, password)
            if not valid:
                return False, f"Credenciales inválidas: {message}"

            # Verificar Selenium
            if not self.automation_tab.automation_service.is_selenium_available():
                return False, "Selenium no está disponible para automatización programada"

            return True, "Ambiente listo para ejecutar programaciones automáticas"

        except Exception as e:
            return False, f"Error validando ambiente: {str(e)}"

    def _execute_bot_automation_corrected(self, schedule):
        """CORREGIDO: Ejecuta el bot usando el AutomationTab con configuración completa"""
        try:
            schedule_name = schedule.get('name', 'Programación desconocida')

            # NUEVO: Obtener credenciales
            credentials = self.automation_tab.credentials_manager.load_credentials()
            username = credentials.get('username')
            password = credentials.get('password')

            # NUEVO: Configurar fechas por defecto para automatización programada
            # Las programaciones automáticas usan configuración de "omitir fechas" por defecto
            date_config = {'skip_dates': True}

            # NUEVO: Crear registro de ejecución como lo hace la automatización manual
            current_execution_record = None
            if self.registry_tab:
                try:
                    execution_start_time = datetime.now()
                    profile_name = f"Programado: {schedule_name}"

                    current_execution_record = self.registry_tab.add_execution_record(
                        start_time=execution_start_time,
                        profile_name=profile_name,
                        user_type="Sistema"
                    )
                    print(f"Registro de ejecución programada creado: ID {current_execution_record['id']}")
                except Exception as e:
                    print(f"Advertencia creando registro programado: {str(e)}")

            # CORREGIDO: Ejecutar el bot usando el servicio de automatización con parámetros completos
            success, message = self.automation_tab.automation_service.start_automation(
                username=username,
                password=password,
                date_config=date_config
            )

            # NUEVO: Actualizar registro según resultado
            if self.registry_tab and current_execution_record:
                try:
                    end_time = datetime.now()
                    status = "Exitoso" if success else "Fallido"
                    error_message = "" if success else message

                    self.registry_tab.update_execution_record(
                        record_id=current_execution_record['id'],
                        end_time=end_time,
                        status=status,
                        error_message=error_message
                    )
                    print(f"Registro programado actualizado: {status}")
                except Exception as e:
                    print(f"Error actualizando registro programado: {str(e)}")

            if success:
                return True, f"Bot ejecutado automáticamente desde programación '{schedule_name}': {message}"
            else:
                return False, f"Error ejecutando bot programado '{schedule_name}': {message}"

        except Exception as e:
            return False, f"Error ejecutando automatización programada: {str(e)}"

    def execute_schedule_async(self, schedule, success_callback=None, error_callback=None):
        """Ejecuta una programación de forma asíncrona con callbacks"""

        def execute_thread():
            try:
                success, message = self.execute_schedule(schedule)
                if success and success_callback:
                    success_callback(schedule, message)
                elif not success and error_callback:
                    error_callback(schedule, message)
            except Exception as e:
                if error_callback:
                    error_callback(schedule, str(e))

        thread = threading.Thread(target=execute_thread, daemon=True)
        thread.start()

    def _handle_execution_success(self, schedule, message):
        """Maneja el éxito de la ejecución"""
        with self._lock:
            if self.current_execution:
                self.current_execution['status'] = 'completed'
                self.current_execution['end_time'] = datetime.now()

                # Notificar finalización exitosa
                self._notify_execution_end(schedule, True, message)

            self.is_executing = False
            self.current_execution = None

        return True, f"Programación '{schedule['name']}' ejecutada correctamente: {message}"

    def _handle_execution_error(self, schedule, error_message):
        """Maneja errores en la ejecución"""
        with self._lock:
            if self.current_execution:
                self.current_execution['status'] = 'failed'
                self.current_execution['end_time'] = datetime.now()
                self.current_execution['error'] = error_message

                # Notificar finalización con error
                self._notify_execution_end(schedule, False, error_message)

            self.is_executing = False
            self.current_execution = None

        return False, f"Error en programación '{schedule['name']}': {error_message}"

    def force_stop_execution(self):
        """Fuerza la detención de la ejecución actual"""
        with self._lock:
            if self.is_executing and self.current_execution:
                schedule = self.current_execution['schedule']
                self.current_execution['status'] = 'stopped'
                self.current_execution['end_time'] = datetime.now()

                # Notificar detención forzada
                self._notify_execution_end(schedule, False, "Ejecución detenida por el usuario")

            self.is_executing = False
            self.current_execution = None

    def is_busy(self):
        """Verifica si está ejecutando una programación"""
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

    def _notify_execution_start(self, schedule):
        """Notifica el inicio de ejecución a los callbacks"""
        for callback in self._execution_callbacks:
            try:
                callback('start', schedule, None)
            except Exception as e:
                print(f"Error en callback de inicio: {e}")

    def _notify_execution_end(self, schedule, success, message):
        """Notifica la finalización de ejecución a los callbacks"""
        for callback in self._execution_callbacks:
            try:
                callback('end', schedule, {'success': success, 'message': message})
            except Exception as e:
                print(f"Error en callback de finalización: {e}")

    def validate_execution_environment(self):
        """CORREGIDO: Valida que el ambiente esté listo para ejecutar programaciones"""
        return self._validate_execution_environment({})


class BotScheduler:
    """Scheduler automático para ejecutar programaciones del bot según horarios configurados (MEJORADO)"""

    def __init__(self, schedule_manager, execution_service):
        self.schedule_manager = schedule_manager
        self.execution_service = execution_service

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

            print("✅ BotScheduler (Ejecución Automática) iniciado correctamente")
            return True, "Scheduler de ejecución automática iniciado correctamente"

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

            print("✅ BotScheduler (Ejecución Automática) detenido correctamente")
            return True, "Scheduler de ejecución automática detenido correctamente"

        except Exception as e:
            return False, f"Error deteniendo scheduler: {str(e)}"

    def _scheduler_loop(self):
        """Loop principal del scheduler (MEJORADO)"""
        print("🔄 Scheduler loop de ejecución automática iniciado")

        while not self._stop_event.is_set():
            try:
                self._check_and_execute_schedules()
            except Exception as e:
                print(f"❌ Error en scheduler loop de ejecución: {e}")

            # Esperar 60 segundos o hasta que se detenga
            self._stop_event.wait(60)

        print("🛑 Scheduler loop de ejecución automática terminado")

    def _check_and_execute_schedules(self):
        """MEJORADO: Revisa y ejecuta programaciones que deben ejecutar el bot ahora"""
        now = datetime.now()
        current_weekday = now.weekday()

        try:
            active_schedules = self.schedule_manager.get_active_schedules()
            print(f"🔍 Revisando {len(active_schedules)} programaciones activas a las {now.strftime('%H:%M')}")

            for schedule in active_schedules:
                if self._should_execute_schedule(schedule, now, current_weekday):
                    print(f"⏰ Ejecutando programación: '{schedule['name']}'")
                    self._execute_scheduled_automation(schedule, now)

        except Exception as e:
            print(f"❌ Error revisando programaciones: {e}")

    def _should_execute_schedule(self, schedule, now, current_weekday):
        """MEJORADO: Determina si una programación debe ejecutar el bot en este momento"""
        try:
            # Verificar que no se haya ejecutado ya en este minuto
            schedule_id = schedule['id']
            last_execution_key = f"{schedule_id}_{now.strftime('%Y-%m-%d_%H:%M')}"

            if last_execution_key in self._last_execution_check:
                return False

            # Verificar horario
            schedule_hour = int(schedule.get('hour', 0))
            schedule_minute = int(schedule.get('minute', 0))

            if now.hour != schedule_hour or now.minute != schedule_minute:
                return False

            # Verificar día de la semana
            schedule_days = schedule.get('days', [])
            if not schedule_days:
                return False

            # Convertir días de la programación a números de semana
            schedule_weekdays = []
            for day_name in schedule_days:
                if day_name in self._day_mapping:
                    schedule_weekdays.append(self._day_mapping[day_name])

            if current_weekday not in schedule_weekdays:
                return False

            # NUEVO: Verificar que el ambiente esté listo antes de ejecutar
            validation_result = self.execution_service._validate_execution_environment(schedule)
            if not validation_result[0]:
                print(f"⚠️ Programación '{schedule['name']}' no puede ejecutarse: {validation_result[1]}")
                return False

            return True

        except Exception as e:
            print(f"❌ Error evaluando programación '{schedule.get('name', 'Desconocida')}': {e}")
            return False

    def _execute_scheduled_automation(self, schedule, execution_time):
        """MEJORADO: Ejecuta una programación automática (inicia el bot)"""
        schedule_id = schedule['id']
        execution_key = f"{schedule_id}_{execution_time.strftime('%Y-%m-%d_%H:%M')}"

        # Marcar como ejecutado para evitar duplicados
        self._last_execution_check[execution_key] = execution_time

        try:
            print(f"🤖 Ejecutando bot automáticamente: '{schedule['name']}' a las {execution_time.strftime('%H:%M')}")

            # CORREGIDO: Ejecutar usando el servicio mejorado
            success, message = self.execution_service.execute_schedule(schedule)

            # Actualizar estadísticas de la programación
            if success:
                self.schedule_manager.update_execution_stats(schedule_id)
                print(f"✅ Bot '{schedule['name']}' ejecutado exitosamente: {message}")
            else:
                print(f"❌ Error ejecutando bot '{schedule['name']}': {message}")

            # Registrar en historial
            execution_record = {
                'schedule_id': schedule_id,
                'schedule_name': schedule['name'],
                'scheduled_time': execution_time.isoformat(),
                'success': success,
                'message': message,
                'execution_type': 'scheduled_automation'
            }

            self._execution_history.append(execution_record)

            # Limpiar historial si es muy grande
            if len(self._last_execution_check) > 1000:
                cutoff_time = execution_time - timedelta(hours=24)
                self._last_execution_check = {
                    k: v for k, v in self._last_execution_check.items()
                    if v > cutoff_time
                }

        except Exception as e:
            print(f"❌ Excepción ejecutando bot '{schedule['name']}': {e}")

    def get_next_scheduled_executions(self, limit=5):
        """Obtiene las próximas ejecuciones programadas"""
        try:
            active_schedules = self.schedule_manager.get_active_schedules()
            next_executions = []

            for schedule in active_schedules[:limit]:
                next_time = self._calculate_next_execution_time(schedule)
                next_executions.append({
                    'schedule': schedule,
                    'next_execution': next_time,
                    'status': 'scheduled_automation' if next_time != 'Error calculando' else 'error'
                })

            return next_executions

        except Exception as e:
            print(f"Error obteniendo próximas ejecuciones: {e}")
            return []

    def _calculate_next_execution_time(self, schedule):
        """Calcula la próxima hora de ejecución para una programación"""
        try:
            now = datetime.now()
            hour = int(schedule.get('hour', 0))
            minute = int(schedule.get('minute', 0))
            days = schedule.get('days', [])

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
        """Obtiene historial de ejecuciones automáticas"""
        return sorted(self._execution_history, key=lambda x: x['scheduled_time'], reverse=True)[:limit]

    def force_execute_schedule(self, schedule_id):
        """Fuerza la ejecución inmediata de una programación"""
        try:
            schedule = self.schedule_manager.get_schedule_by_id(schedule_id)
            if not schedule:
                return False, "Programación no encontrada"

            if not schedule.get('enabled', False):
                return False, "Programación deshabilitada"

            return self.execution_service.execute_schedule(schedule)

        except Exception as e:
            return False, f"Error en ejecución forzada: {str(e)}"

    def get_scheduler_status(self):
        """Obtiene estado actual del scheduler"""
        return {
            'is_running': self.is_running,
            'thread_alive': self._scheduler_thread.is_alive() if self._scheduler_thread else False,
            'total_executions': len(self._execution_history),
            'last_check_count': len(self._last_execution_check)
        }