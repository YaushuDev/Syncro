# profile_data_manager.py
# Ubicación: /syncro_bot/gui/components/profile_data_manager.py
"""
Gestor de datos y validación para perfiles de reportes automáticos.
Maneja la persistencia, CRUD y validación de perfiles simplificados
que solo programan horarios para envío automático de reportes por correo.
"""

import json
import os
from datetime import datetime


class ProfilesManager:
    """Gestor de perfiles de reportes automáticos programados"""

    def __init__(self):
        self.config_file = "automation_profiles.json"
        self.profiles = []
        self.load_profiles()

    def add_profile(self, name, hour, minute, days, enabled=True):
        """Añade un nuevo perfil de reporte automático"""
        profile = {
            "id": self._generate_id(),
            "name": name,
            "hour": hour,
            "minute": minute,
            "days": days,  # Lista de días: ['Lunes', 'Martes', etc.]
            "enabled": enabled,
            "created": datetime.now().isoformat()
        }
        self.profiles.append(profile)
        self.save_profiles()
        return profile

    def remove_profile(self, profile_id):
        """Elimina un perfil por ID"""
        self.profiles = [p for p in self.profiles if p["id"] != profile_id]
        self.save_profiles()

    def update_profile(self, profile_id, **kwargs):
        """Actualiza un perfil existente"""
        for profile in self.profiles:
            if profile["id"] == profile_id:
                # Solo actualizar campos permitidos
                allowed_fields = ['name', 'hour', 'minute', 'days', 'enabled']
                for key, value in kwargs.items():
                    if key in allowed_fields:
                        profile[key] = value
                self.save_profiles()
                return profile
        return None

    def get_profiles(self):
        """Obtiene todos los perfiles"""
        return self.profiles.copy()

    def get_profile_by_id(self, profile_id):
        """Obtiene un perfil específico por ID"""
        for profile in self.profiles:
            if profile["id"] == profile_id:
                return profile.copy()
        return None

    def get_active_profiles(self):
        """Obtiene solo los perfiles activos"""
        return [p for p in self.profiles if p['enabled']]

    def save_profiles(self):
        """Guarda los perfiles en archivo"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.profiles, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"Error guardando perfiles: {e}")
            return False

    def load_profiles(self):
        """Carga los perfiles desde archivo con migración automática"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    loaded_profiles = json.load(f)

                # Migrar perfiles antiguos eliminando campos de reportes obsoletos
                migrated_any = False
                cleaned_profiles = []

                for profile in loaded_profiles:
                    # Crear perfil limpio solo con campos necesarios
                    clean_profile = {
                        "id": profile.get("id", self._generate_id()),
                        "name": profile.get("name", "Perfil sin nombre"),
                        "hour": profile.get("hour", 8),
                        "minute": profile.get("minute", 0),
                        "days": profile.get("days", []),
                        "enabled": profile.get("enabled", True),
                        "created": profile.get("created", datetime.now().isoformat())
                    }

                    # Verificar si se eliminaron campos obsoletos
                    old_fields = ["send_report", "report_frequency", "report_type"]
                    if any(field in profile for field in old_fields):
                        migrated_any = True

                    cleaned_profiles.append(clean_profile)

                self.profiles = cleaned_profiles

                # Guardar cambios de migración
                if migrated_any:
                    self.save_profiles()
                    print(f"Migrados {len(cleaned_profiles)} perfiles eliminando campos obsoletos de reportes")

            else:
                self.profiles = []
        except Exception as e:
            print(f"Error cargando perfiles: {e}")
            self.profiles = []

    def backup_profiles(self, backup_path=None):
        """Crea backup de los perfiles"""
        try:
            if not backup_path:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                backup_path = f"profiles_backup_{timestamp}.json"

            with open(backup_path, 'w', encoding='utf-8') as f:
                json.dump(self.profiles, f, indent=2, ensure_ascii=False)

            return True, backup_path
        except Exception as e:
            return False, str(e)

    def restore_profiles(self, backup_path):
        """Restaura perfiles desde backup"""
        try:
            with open(backup_path, 'r', encoding='utf-8') as f:
                restored_profiles = json.load(f)

            # Validar estructura básica
            for profile in restored_profiles:
                if not all(key in profile for key in ['id', 'name', 'hour', 'minute', 'days']):
                    raise ValueError("Estructura de backup inválida")

            self.profiles = restored_profiles
            self.save_profiles()
            return True, f"Restaurados {len(restored_profiles)} perfiles"

        except Exception as e:
            return False, str(e)

    def get_statistics(self):
        """Obtiene estadísticas de perfiles"""
        total = len(self.profiles)
        active = len([p for p in self.profiles if p.get('enabled', False)])

        return {
            'total': total,
            'active': active,
            'inactive': total - active
        }

    def _generate_id(self):
        """Genera un ID único para el perfil"""
        return str(len(self.profiles) + 1) + str(int(datetime.now().timestamp()))


class ProfileValidator:
    """Validador de datos de perfiles simplificado"""

    def __init__(self):
        self.valid_days = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo']

    def validate_profile_data(self, name, hour, minute, days):
        """Valida todos los datos de un perfil"""
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
        """Valida el nombre del perfil"""
        if not name or not name.strip():
            return "El nombre del perfil es obligatorio"

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

    def validate_profile_for_execution(self, profile):
        """Valida que un perfil esté listo para ejecutarse"""
        if not profile.get('enabled', False):
            return "El perfil no está habilitado"

        if not profile.get('days'):
            return "El perfil no tiene días configurados"

        # Validar que la hora tenga sentido
        try:
            hour = int(profile.get('hour', 0))
            minute = int(profile.get('minute', 0))
            if not (0 <= hour <= 23) or not (0 <= minute <= 59):
                return "Horario del perfil inválido"
        except:
            return "Horario del perfil no es válido"

        return None

    def sanitize_profile_name(self, name):
        """Sanitiza el nombre del perfil"""
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


class ProfileDataHelper:
    """Helper para operaciones adicionales con datos de perfiles"""

    @staticmethod
    def format_profile_schedule(profile):
        """Formatea la información de horario de un perfil para mostrar"""
        try:
            hour = int(profile.get('hour', 0))
            minute = int(profile.get('minute', 0))
            days = profile.get('days', [])

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
    def get_next_execution_info(profile):
        """Obtiene información sobre la próxima ejecución de un perfil"""
        from datetime import datetime, timedelta

        if not profile.get('enabled', False):
            return "Perfil deshabilitado"

        try:
            now = datetime.now()
            hour = int(profile.get('hour', 0))
            minute = int(profile.get('minute', 0))
            days = profile.get('days', [])

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
    def profile_conflicts_check(profiles, exclude_id=None):
        """Verifica si hay conflictos de horarios entre perfiles"""
        conflicts = []

        active_profiles = [p for p in profiles if p.get('enabled', False) and p.get('id') != exclude_id]

        for i, profile1 in enumerate(active_profiles):
            for profile2 in active_profiles[i + 1:]:
                if ProfileDataHelper._profiles_have_time_conflict(profile1, profile2):
                    conflicts.append({
                        'profile1': profile1,
                        'profile2': profile2,
                        'conflict_type': 'same_time_and_day'
                    })

        return conflicts

    @staticmethod
    def _profiles_have_time_conflict(profile1, profile2):
        """Verifica si dos perfiles tienen conflicto de horario"""
        try:
            # Mismo horario
            if (profile1.get('hour') == profile2.get('hour') and
                    profile1.get('minute') == profile2.get('minute')):

                # Días en común
                days1 = set(profile1.get('days', []))
                days2 = set(profile2.get('days', []))

                if days1.intersection(days2):
                    return True

            return False
        except:
            return False

    @staticmethod
    def get_profile_summary(profile):
        """Obtiene resumen completo de un perfil"""
        return {
            'id': profile.get('id'),
            'name': profile.get('name', 'Sin nombre'),
            'schedule': ProfileDataHelper.format_profile_schedule(profile),
            'next_execution': ProfileDataHelper.get_next_execution_info(profile),
            'enabled': profile.get('enabled', False),
            'created': profile.get('created', 'Desconocido')
        }