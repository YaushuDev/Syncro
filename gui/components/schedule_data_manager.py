# schedule_data_manager.py
# Ubicación: /syncro_bot/gui/components/schedule_data_manager.py
"""
Gestor de datos y validación para programaciones de ejecución automática del bot.
Maneja la persistencia, CRUD y validación de programaciones que ejecutan
el bot automáticamente en horarios específicos programados.
"""

import json
import os
from datetime import datetime


class ScheduleManager:
    """Gestor de programaciones de ejecución automática del bot"""

    def __init__(self):
        self.config_file = "execution_schedules.json"
        self.schedules = []
        self.load_schedules()

    def add_schedule(self, name, hour, minute, days, enabled=True):
        """Añade una nueva programación de ejecución"""
        schedule = {
            "id": self._generate_id(),
            "name": name,
            "hour": hour,
            "minute": minute,
            "days": days,  # Lista de días: ['Lunes', 'Martes', etc.]
            "enabled": enabled,
            "created": datetime.now().isoformat(),
            "last_execution": None,
            "execution_count": 0
        }
        self.schedules.append(schedule)
        self.save_schedules()
        return schedule

    def remove_schedule(self, schedule_id):
        """Elimina una programación por ID"""
        self.schedules = [s for s in self.schedules if s["id"] != schedule_id]
        self.save_schedules()

    def update_schedule(self, schedule_id, **kwargs):
        """Actualiza una programación existente"""
        for schedule in self.schedules:
            if schedule["id"] == schedule_id:
                # Solo actualizar campos permitidos
                allowed_fields = ['name', 'hour', 'minute', 'days', 'enabled']
                for key, value in kwargs.items():
                    if key in allowed_fields:
                        schedule[key] = value
                self.save_schedules()
                return schedule
        return None

    def get_schedules(self):
        """Obtiene todas las programaciones"""
        return self.schedules.copy()

    def get_schedule_by_id(self, schedule_id):
        """Obtiene una programación específica por ID"""
        for schedule in self.schedules:
            if schedule["id"] == schedule_id:
                return schedule.copy()
        return None

    def get_active_schedules(self):
        """Obtiene solo las programaciones activas"""
        return [s for s in self.schedules if s['enabled']]

    def update_execution_stats(self, schedule_id):
        """Actualiza estadísticas de ejecución de una programación"""
        for schedule in self.schedules:
            if schedule["id"] == schedule_id:
                schedule["last_execution"] = datetime.now().isoformat()
                schedule["execution_count"] = schedule.get("execution_count", 0) + 1
                self.save_schedules()
                return schedule
        return None

    def save_schedules(self):
        """Guarda las programaciones en archivo"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.schedules, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"Error guardando programaciones: {e}")
            return False

    def load_schedules(self):
        """Carga las programaciones desde archivo"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    loaded_schedules = json.load(f)

                # Limpiar y validar programaciones cargadas
                cleaned_schedules = []
                for schedule in loaded_schedules:
                    # Crear programación limpia con campos necesarios
                    clean_schedule = {
                        "id": schedule.get("id", self._generate_id()),
                        "name": schedule.get("name", "Programación sin nombre"),
                        "hour": schedule.get("hour", 8),
                        "minute": schedule.get("minute", 0),
                        "days": schedule.get("days", []),
                        "enabled": schedule.get("enabled", True),
                        "created": schedule.get("created", datetime.now().isoformat()),
                        "last_execution": schedule.get("last_execution"),
                        "execution_count": schedule.get("execution_count", 0)
                    }
                    cleaned_schedules.append(clean_schedule)

                self.schedules = cleaned_schedules
            else:
                self.schedules = []
        except Exception as e:
            print(f"Error cargando programaciones: {e}")
            self.schedules = []

    def backup_schedules(self, backup_path=None):
        """Crea backup de las programaciones"""
        try:
            if not backup_path:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                backup_path = f"schedules_backup_{timestamp}.json"

            with open(backup_path, 'w', encoding='utf-8') as f:
                json.dump(self.schedules, f, indent=2, ensure_ascii=False)

            return True, backup_path
        except Exception as e:
            return False, str(e)

    def restore_schedules(self, backup_path):
        """Restaura programaciones desde backup"""
        try:
            with open(backup_path, 'r', encoding='utf-8') as f:
                restored_schedules = json.load(f)

            # Validar estructura básica
            for schedule in restored_schedules:
                if not all(key in schedule for key in ['id', 'name', 'hour', 'minute', 'days']):
                    raise ValueError("Estructura de backup inválida")

            self.schedules = restored_schedules
            self.save_schedules()
            return True, f"Restauradas {len(restored_schedules)} programaciones"

        except Exception as e:
            return False, str(e)

    def get_statistics(self):
        """Obtiene estadísticas de programaciones"""
        total = len(self.schedules)
        active = len([s for s in self.schedules if s.get('enabled', False)])
        total_executions = sum(s.get('execution_count', 0) for s in self.schedules)

        return {
            'total': total,
            'active': active,
            'inactive': total - active,
            'total_executions': total_executions
        }

    def _generate_id(self):
        """Genera un ID único para la programación"""
        return str(len(self.schedules) + 1) + str(int(datetime.now().timestamp()))


class ScheduleValidator:
    """Validador de datos de programaciones de ejecución"""

    def __init__(self):
        self.valid_days = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo']

    def validate_schedule_data(self, name, hour, minute, days):
        """Valida todos los datos de una programación"""
        errors = []

        # Validar nombre
        name_error = self.validate_name(name)
        if name_error:
            errors.append(name_error)

        # Validar horario
        time_error = self.validate_time(hour, minute)
        if time_error:
            errors.append(time_error)

        # Validar días
        days_error = self.validate_days(days)
        if days_error:
            errors.append(days_error)

        return errors

    def validate_name(self, name):
        """Valida el nombre de la programación"""
        if not name or not name.strip():
            return "El nombre de la programación es obligatorio"

        name = name.strip()
        if len(name) < 3:
            return "El nombre debe tener al menos 3 caracteres"

        if len(name) > 50:
            return "El nombre no puede superar 50 caracteres"

        # Caracteres no permitidos
        invalid_chars = ['<', '>', ':', '"', '|', '?', '*', '\\', '/']
        if any(char in name for char in invalid_chars):
            return f"El nombre contiene caracteres no permitidos: {', '.join(invalid_chars)}"

        return None

    def validate_time(self, hour, minute):
        """Valida la hora y minutos"""
        try:
            hour_int = int(hour)
            minute_int = int(minute)

            if not (0 <= hour_int <= 23):
                return "La hora debe estar entre 0 y 23"

            if not (0 <= minute_int <= 59):
                return "Los minutos deben estar entre 0 y 59"

        except (ValueError, TypeError):
            return "Hora y minutos deben ser números válidos"

        return None

    def validate_days(self, days):
        """Valida los días seleccionados"""
        if not days or len(days) == 0:
            return "Debe seleccionar al menos un día"

        if not isinstance(days, list):
            return "Los días deben ser una lista"

        for day in days:
            if day not in self.valid_days:
                return f"Día inválido: {day}"

        if len(days) > 7:
            return "No puede seleccionar más de 7 días"

        return None

    def validate_schedule_for_execution(self, schedule):
        """Valida que una programación esté lista para ejecutarse"""
        if not schedule.get('enabled', False):
            return "La programación no está habilitada"

        if not schedule.get('days'):
            return "La programación no tiene días configurados"

        # Validar que la hora tenga sentido
        try:
            hour = int(schedule.get('hour', 0))
            minute = int(schedule.get('minute', 0))
            if not (0 <= hour <= 23) or not (0 <= minute <= 59):
                return "Horario de la programación inválido"
        except:
            return "Horario de la programación no es válido"

        return None

    def sanitize_schedule_name(self, name):
        """Sanitiza el nombre de la programación"""
        if not name:
            return ""

        # Limpiar espacios
        name = name.strip()

        # Reemplazar caracteres problemáticos
        replacements = {
            '<': '(', '>': ')', ':': '-', '"': "'", '|': '-',
            '?': '', '*': '', '\\': '-', '/': '-'
        }

        for old_char, new_char in replacements.items():
            name = name.replace(old_char, new_char)

        # Limitar longitud
        if len(name) > 50:
            name = name[:50]

        return name

    def get_validation_rules_summary(self):
        """Obtiene resumen de reglas de validación para mostrar al usuario"""
        return {
            'nombre': {
                'minimo': 3,
                'maximo': 50,
                'caracteres_prohibidos': ['<', '>', ':', '"', '|', '?', '*', '\\', '/']
            },
            'horario': {
                'hora_min': 0,
                'hora_max': 23,
                'minuto_min': 0,
                'minuto_max': 59
            },
            'dias': {
                'minimo': 1,
                'maximo': 7,
                'validos': self.valid_days
            }
        }


class ScheduleDataHelper:
    """Helper para operaciones adicionales con datos de programaciones"""

    @staticmethod
    def format_schedule_display(schedule):
        """Formatea la información de programación para mostrar"""
        try:
            hour = int(schedule.get('hour', 0))
            minute = int(schedule.get('minute', 0))
            days = schedule.get('days', [])

            schedule_str = f"{hour:02d}:{minute:02d}"

            if len(days) == 7:
                days_str = "Todos los días"
            elif len(days) <= 2:
                days_str = ", ".join(days)
            else:
                days_str = f"{', '.join(days[:2])} (+{len(days) - 2})"

            return f"{schedule_str} - {days_str}"

        except:
            return "Horario inválido"

    @staticmethod
    def get_next_execution_info(schedule):
        """Obtiene información sobre la próxima ejecución de una programación"""
        from datetime import datetime, timedelta

        if not schedule.get('enabled', False):
            return "Programación deshabilitada"

        try:
            now = datetime.now()
            hour = int(schedule.get('hour', 0))
            minute = int(schedule.get('minute', 0))
            days = schedule.get('days', [])

            if not days:
                return "Sin días configurados"

            # Mapear días a números (Lunes = 0, Domingo = 6)
            day_mapping = {
                'Lunes': 0, 'Martes': 1, 'Miércoles': 2, 'Jueves': 3,
                'Viernes': 4, 'Sábado': 5, 'Domingo': 6
            }

            target_weekdays = [day_mapping[day] for day in days if day in day_mapping]

            if not target_weekdays:
                return "Días inválidos"

            # Buscar la próxima fecha
            for days_ahead in range(8):  # Buscar en los próximos 7 días
                check_date = now + timedelta(days=days_ahead)
                if check_date.weekday() in target_weekdays:
                    execution_time = check_date.replace(hour=hour, minute=minute, second=0, microsecond=0)

                    # Si es hoy pero ya pasó la hora, buscar el siguiente día
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

    @staticmethod
    def schedule_conflicts_check(schedules, exclude_id=None):
        """Verifica si hay conflictos de horarios entre programaciones"""
        conflicts = []

        active_schedules = [s for s in schedules if s.get('enabled', False) and s.get('id') != exclude_id]

        for i, schedule1 in enumerate(active_schedules):
            for schedule2 in active_schedules[i + 1:]:
                if ScheduleDataHelper._schedules_have_time_conflict(schedule1, schedule2):
                    conflicts.append({
                        'schedule1': schedule1,
                        'schedule2': schedule2,
                        'conflict_type': 'same_time_and_day'
                    })

        return conflicts

    @staticmethod
    def _schedules_have_time_conflict(schedule1, schedule2):
        """Verifica si dos programaciones tienen conflicto de horario"""
        try:
            # Mismo horario
            if (schedule1.get('hour') == schedule2.get('hour') and
                    schedule1.get('minute') == schedule2.get('minute')):

                # Días en común
                days1 = set(schedule1.get('days', []))
                days2 = set(schedule2.get('days', []))

                if days1.intersection(days2):
                    return True

            return False
        except:
            return False

    @staticmethod
    def get_schedule_summary(schedule):
        """Obtiene resumen completo de una programación"""
        return {
            'id': schedule.get('id'),
            'name': schedule.get('name', 'Sin nombre'),
            'schedule': ScheduleDataHelper.format_schedule_display(schedule),
            'next_execution': ScheduleDataHelper.get_next_execution_info(schedule),
            'enabled': schedule.get('enabled', False),
            'created': schedule.get('created', 'Desconocido'),
            'execution_count': schedule.get('execution_count', 0),
            'last_execution': schedule.get('last_execution')
        }