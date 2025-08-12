# registry_manager.py
# Ubicación: /syncro_bot/gui/components/registry_manager.py
"""
Gestor completo de registros de ejecuciones con encriptación, filtrado y búsqueda.
Maneja el almacenamiento seguro, filtrado, búsqueda avanzada y estadísticas
de los registros de ejecuciones del bot con encriptación de datos.
"""

import json
import os
from datetime import datetime, timedelta
from cryptography.fernet import Fernet


class RegistryManager:
    """Gestor de registros de ejecuciones con encriptación"""

    def __init__(self):
        self.config_file = "execution_registry.json"
        self.key_file = "registry.key"
        self.registry = []
        self.load_registry()

    def _get_or_create_key(self):
        """Obtiene o crea la clave de encriptación"""
        if os.path.exists(self.key_file):
            with open(self.key_file, 'rb') as f:
                return f.read()
        else:
            key = Fernet.generate_key()
            with open(self.key_file, 'wb') as f:
                f.write(key)
            return key

    def _encrypt_data(self, data):
        """Encripta los datos del registro"""
        key = self._get_or_create_key()
        fernet = Fernet(key)
        json_str = json.dumps(data, ensure_ascii=True, default=str)
        encrypted_data = fernet.encrypt(json_str.encode('utf-8'))
        return encrypted_data

    def _decrypt_data(self, encrypted_data):
        """Desencripta los datos del registro"""
        try:
            key = self._get_or_create_key()
            fernet = Fernet(key)
            decrypted_data = fernet.decrypt(encrypted_data)
            return json.loads(decrypted_data.decode('utf-8'))
        except Exception:
            return []

    def add_execution_record(self, start_time, end_time=None, profile_name="Manual",
                             status="En Ejecución", user_type="Usuario", error_message=""):
        """Añade un registro de ejecución"""
        if end_time is None:
            end_time = start_time
            duration = "En curso"
        else:
            if isinstance(start_time, str):
                start_dt = datetime.fromisoformat(start_time)
            else:
                start_dt = start_time

            if isinstance(end_time, str):
                end_dt = datetime.fromisoformat(end_time)
            else:
                end_dt = end_time

            duration_delta = end_dt - start_dt
            duration = self._format_duration(duration_delta)

        record = {
            "id": self._generate_id(),
            "fecha": start_time.date().isoformat() if hasattr(start_time, 'date') else start_time[:10],
            "hora_inicio": start_time.time().isoformat() if hasattr(start_time, 'time') else start_time[11:19],
            "hora_fin": end_time.time().isoformat() if hasattr(end_time, 'time') else end_time[11:19],
            "perfil": profile_name,
            "duracion": duration,
            "estado": status,
            "usuario": user_type,
            "error_message": error_message,
            "timestamp_inicio": start_time.isoformat() if hasattr(start_time, 'isoformat') else start_time,
            "timestamp_fin": end_time.isoformat() if hasattr(end_time, 'isoformat') else end_time,
            "created": datetime.now().isoformat()
        }

        self.registry.append(record)
        self.save_registry()
        return record

    def update_execution_record(self, record_id, end_time, status, error_message=""):
        """Actualiza un registro de ejecución cuando termina"""
        for record in self.registry:
            if record["id"] == record_id:
                start_dt = datetime.fromisoformat(record["timestamp_inicio"])
                end_dt = end_time if hasattr(end_time, 'isoformat') else datetime.fromisoformat(end_time)

                duration_delta = end_dt - start_dt
                duration = self._format_duration(duration_delta)

                record["hora_fin"] = end_dt.time().isoformat()
                record["timestamp_fin"] = end_dt.isoformat()
                record["duracion"] = duration
                record["estado"] = status
                record["error_message"] = error_message

                self.save_registry()
                return record
        return None

    def _format_duration(self, duration_delta):
        """Formatea la duración de manera legible"""
        total_seconds = int(duration_delta.total_seconds())

        if total_seconds < 60:
            return f"{total_seconds}s"
        elif total_seconds < 3600:
            minutes = total_seconds // 60
            seconds = total_seconds % 60
            return f"{minutes}m {seconds}s"
        else:
            hours = total_seconds // 3600
            minutes = (total_seconds % 3600) // 60
            seconds = total_seconds % 60
            return f"{hours}h {minutes}m {seconds}s"

    def get_all_records(self, limit=None):
        """Obtiene todos los registros ordenados por fecha descendente"""
        sorted_registry = sorted(self.registry,
                                 key=lambda x: x["timestamp_inicio"],
                                 reverse=True)
        if limit:
            return sorted_registry[:limit]
        return sorted_registry

    def get_filtered_records(self, date_from=None, date_to=None, status_filter=None,
                             user_filter=None, profile_filter=None):
        """Obtiene registros filtrados"""
        filtered = self.registry.copy()

        if date_from:
            filtered = [r for r in filtered if r["fecha"] >= date_from]

        if date_to:
            filtered = [r for r in filtered if r["fecha"] <= date_to]

        if status_filter and status_filter != "Todos":
            filtered = [r for r in filtered if r["estado"] == status_filter]

        if user_filter and user_filter != "Todos":
            filtered = [r for r in filtered if r["usuario"] == user_filter]

        if profile_filter and profile_filter != "Todos":
            filtered = [r for r in filtered if r["perfil"] == profile_filter]

        return sorted(filtered, key=lambda x: x["timestamp_inicio"], reverse=True)

    def get_statistics(self):
        """Obtiene estadísticas generales"""
        total = len(self.registry)
        successful = len([r for r in self.registry if r["estado"] == "Exitoso"])
        failed = len([r for r in self.registry if r["estado"] == "Fallido"])
        in_progress = len([r for r in self.registry if r["estado"] == "En Ejecución"])
        manual_executions = len([r for r in self.registry if r["usuario"] == "Usuario"])
        system_executions = len([r for r in self.registry if r["usuario"] == "Sistema"])

        return {
            "total": total,
            "successful": successful,
            "failed": failed,
            "in_progress": in_progress,
            "manual": manual_executions,
            "system": system_executions,
            "success_rate": (successful / total * 100) if total > 0 else 0
        }

    def get_unique_profiles(self):
        """Obtiene lista de perfiles únicos para filtros"""
        profiles = set(["Todos"])
        for record in self.registry:
            profiles.add(record['perfil'])
        return sorted(list(profiles))

    def clear_registry(self):
        """Limpia todos los registros"""
        self.registry = []
        self.save_registry()

    def clear_old_records(self, days_to_keep=30):
        """Elimina registros antiguos"""
        cutoff_date = (datetime.now() - timedelta(days=days_to_keep)).date().isoformat()
        initial_count = len(self.registry)
        self.registry = [r for r in self.registry if r["fecha"] >= cutoff_date]
        final_count = len(self.registry)
        deleted_count = initial_count - final_count
        self.save_registry()
        return deleted_count

    def save_registry(self):
        """Guarda el registro encriptado"""
        try:
            encrypted_data = self._encrypt_data(self.registry)
            with open(self.config_file, 'wb') as f:
                f.write(encrypted_data)
            return True
        except Exception as e:
            print(f"Error guardando registro: {e}")
            return False

    def load_registry(self):
        """Carga el registro desde archivo"""
        try:
            if not os.path.exists(self.config_file):
                self.registry = []
                return

            with open(self.config_file, 'rb') as f:
                encrypted_data = f.read()

            self.registry = self._decrypt_data(encrypted_data)
        except Exception as e:
            print(f"Error cargando registro: {e}")
            self.registry = []

    def _generate_id(self):
        """Genera un ID único para el registro"""
        return f"{datetime.now().strftime('%Y%m%d%H%M%S')}{len(self.registry)}"

    def get_records_by_type(self, report_type):
        """Obtiene registros según tipo de reporte específico"""
        if report_type == "Últimos 7 días":
            cutoff_date = (datetime.now() - timedelta(days=7)).date().isoformat()
            return self.get_filtered_records(date_from=cutoff_date)

        elif report_type == "Últimos 30 días":
            cutoff_date = (datetime.now() - timedelta(days=30)).date().isoformat()
            return self.get_filtered_records(date_from=cutoff_date)

        elif report_type == "Solo Exitosos":
            return self.get_filtered_records(status_filter="Exitoso")

        elif report_type == "Solo Fallidos":
            return self.get_filtered_records(status_filter="Fallido")

        elif report_type == "Solo Ejecuciones Manuales":
            return self.get_filtered_records(user_filter="Usuario")

        elif report_type == "Solo Ejecuciones Automáticas":
            return self.get_filtered_records(user_filter="Sistema")

        else:  # "Todos los Registros"
            return self.get_all_records()

    def backup_registry(self, backup_path=None):
        """Crea backup del registro"""
        try:
            if not backup_path:
                backup_path = f"backup_registry_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

            with open(backup_path, 'w', encoding='utf-8') as f:
                json.dump(self.registry, f, indent=2, ensure_ascii=False, default=str)

            return True, backup_path
        except Exception as e:
            return False, str(e)

    def get_record_by_id(self, record_id):
        """Obtiene un registro específico por ID"""
        for record in self.registry:
            if record["id"] == record_id:
                return record
        return None


class RegistryFilters:
    """Sistema de filtrado para registros integrado"""

    def __init__(self, registry_manager):
        self.registry_manager = registry_manager
        self.current_filters = {}
        self.last_applied_filters = {}

    def validate_date(self, date_str):
        """Valida formato de fecha YYYY-MM-DD"""
        if not date_str:
            return True
        try:
            datetime.strptime(date_str, "%Y-%m-%d")
            return True
        except ValueError:
            return False

    def validate_date_range(self, date_from, date_to):
        """Valida rango de fechas"""
        if not date_from and not date_to:
            return True, "Sin filtro de fechas"

        if date_from and not self.validate_date(date_from):
            return False, "Formato de fecha 'Desde' inválido. Use YYYY-MM-DD"

        if date_to and not self.validate_date(date_to):
            return False, "Formato de fecha 'Hasta' inválido. Use YYYY-MM-DD"

        if date_from and date_to:
            try:
                start_date = datetime.strptime(date_from, "%Y-%m-%d")
                end_date = datetime.strptime(date_to, "%Y-%m-%d")

                if start_date > end_date:
                    return False, "La fecha 'Desde' no puede ser posterior a 'Hasta'"

                if (end_date - start_date).days > 730:
                    return False, "El rango de fechas no puede ser mayor a 2 años"

            except ValueError:
                return False, "Error en el rango de fechas"

        return True, "Rango de fechas válido"

    def prepare_filters(self, filter_values):
        """Prepara y valida filtros antes de aplicar"""
        prepared = {}

        for key, value in filter_values.items():
            if isinstance(value, str):
                cleaned_value = value.strip()
                if cleaned_value:
                    prepared[key] = cleaned_value
            else:
                prepared[key] = value

        date_from = prepared.get('date_from')
        date_to = prepared.get('date_to')

        valid, message = self.validate_date_range(date_from, date_to)
        if not valid:
            return None, message

        for key in ['status_filter', 'user_filter', 'profile_filter']:
            if key in prepared and prepared[key] == "Todos":
                del prepared[key]

        return prepared, "Filtros válidos"

    def apply_filters(self, filter_values):
        """Aplica filtros y devuelve registros filtrados"""
        prepared_filters, message = self.prepare_filters(filter_values)

        if prepared_filters is None:
            return None, message

        try:
            filtered_records = self.registry_manager.get_filtered_records(
                date_from=prepared_filters.get('date_from'),
                date_to=prepared_filters.get('date_to'),
                status_filter=prepared_filters.get('status_filter'),
                user_filter=prepared_filters.get('user_filter'),
                profile_filter=prepared_filters.get('profile_filter')
            )

            self.current_filters = prepared_filters.copy()
            self.last_applied_filters = prepared_filters.copy()

            return filtered_records, f"Se encontraron {len(filtered_records)} registros"

        except Exception as e:
            return None, f"Error aplicando filtros: {str(e)}"

    def clear_filters(self):
        """Limpia todos los filtros aplicados"""
        self.current_filters = {}
        self.last_applied_filters = {}
        return self.registry_manager.get_all_records()

    def get_filter_summary(self):
        """Obtiene resumen de filtros aplicados"""
        if not self.current_filters:
            return "Sin filtros aplicados"

        summary_parts = []
        if 'date_from' in self.current_filters:
            summary_parts.append(f"Desde: {self.current_filters['date_from']}")
        if 'date_to' in self.current_filters:
            summary_parts.append(f"Hasta: {self.current_filters['date_to']}")
        if 'status_filter' in self.current_filters:
            summary_parts.append(f"Estado: {self.current_filters['status_filter']}")
        if 'user_filter' in self.current_filters:
            summary_parts.append(f"Usuario: {self.current_filters['user_filter']}")
        if 'profile_filter' in self.current_filters:
            summary_parts.append(f"Perfil: {self.current_filters['profile_filter']}")

        return " | ".join(summary_parts)

    def has_active_filters(self):
        """Verifica si hay filtros activos"""
        return bool(self.current_filters)

    def get_current_filters(self):
        """Obtiene filtros actuales aplicados"""
        return self.current_filters.copy()

    def get_filter_info_for_report(self):
        """Obtiene información de filtros para reportes"""
        return {
            'date_from': self.current_filters.get('date_from'),
            'date_to': self.current_filters.get('date_to'),
            'status': self.current_filters.get('status_filter'),
            'user': self.current_filters.get('user_filter'),
            'profile': self.current_filters.get('profile_filter'),
            'summary': self.get_filter_summary()
        }


class RegistrySearch:
    """Sistema de búsqueda avanzada en registros"""

    def __init__(self, registry_manager):
        self.registry_manager = registry_manager

    def search_by_text(self, search_term, fields=None):
        """Busca texto en campos específicos"""
        if not search_term or not search_term.strip():
            return []

        search_term = search_term.strip().lower()
        if fields is None:
            fields = ['perfil', 'error_message', 'usuario']

        all_records = self.registry_manager.get_all_records()
        matching_records = []

        for record in all_records:
            for field in fields:
                if field in record:
                    field_value = str(record[field]).lower()
                    if search_term in field_value:
                        matching_records.append(record)
                        break

        return matching_records

    def search_by_duration(self, min_seconds=None, max_seconds=None):
        """Busca registros por duración"""
        all_records = self.registry_manager.get_all_records()
        matching_records = []

        for record in all_records:
            if record['estado'] != 'En Ejecución':
                try:
                    duration_seconds = self._parse_duration_to_seconds(record['duracion'])

                    if min_seconds is not None and duration_seconds < min_seconds:
                        continue
                    if max_seconds is not None and duration_seconds > max_seconds:
                        continue

                    matching_records.append(record)
                except:
                    continue

        return matching_records

    def _parse_duration_to_seconds(self, duration_str):
        """Convierte string de duración a segundos"""
        if not duration_str or duration_str == "En curso":
            return 0

        total_seconds = 0
        parts = duration_str.split()

        for part in parts:
            if 'h' in part:
                hours = int(part.replace('h', ''))
                total_seconds += hours * 3600
            elif 'm' in part:
                minutes = int(part.replace('m', ''))
                total_seconds += minutes * 60
            elif 's' in part:
                seconds = int(part.replace('s', ''))
                total_seconds += seconds

        return total_seconds

    def find_anomalies(self):
        """Encuentra registros anómalos"""
        all_records = self.registry_manager.get_all_records()
        anomalies = {
            'very_long_executions': [],
            'very_short_executions': [],
            'frequent_errors': [],
            'unusual_times': []
        }

        for record in all_records:
            if record['estado'] != 'En Ejecución':
                try:
                    duration_seconds = self._parse_duration_to_seconds(record['duracion'])

                    if duration_seconds > 3600:
                        anomalies['very_long_executions'].append(record)
                    elif duration_seconds < 5:
                        anomalies['very_short_executions'].append(record)
                except:
                    pass

            try:
                hour = int(record['hora_inicio'][:2])
                if hour < 6 or hour > 22:
                    anomalies['unusual_times'].append(record)
            except:
                pass

        # Buscar errores frecuentes
        error_counts = {}
        for record in all_records:
            if record.get('error_message') and record['estado'] == 'Fallido':
                error_msg = record['error_message']
                error_counts[error_msg] = error_counts.get(error_msg, 0) + 1

        for error_msg, count in error_counts.items():
            if count > 3:
                records_with_error = [r for r in all_records
                                      if r.get('error_message') == error_msg]
                anomalies['frequent_errors'].extend(records_with_error)

        return anomalies