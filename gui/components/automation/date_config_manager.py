# date_config_manager.py
# Ubicación: /syncro_bot/gui/components/automation/date_config_manager.py
"""
Gestor de configuración de fechas para automatización con encriptación.
Maneja el almacenamiento seguro, validación y conversión de configuraciones
de fechas para el sistema de automatización con formato DD/MM/YYYY.
"""

import json
import os
import re
from datetime import datetime, timedelta

# Importaciones para encriptación
try:
    from cryptography.fernet import Fernet

    CRYPTO_AVAILABLE = True
except ImportError:
    CRYPTO_AVAILABLE = False
    print("Warning: cryptography no está disponible para configuración de fechas.")
    print("Instale con: pip install cryptography")


class DateConfigManager:
    """Gestor de configuración de fechas con encriptación para automatización"""

    def __init__(self):
        self.config_file = "automation_date_config.json"
        self.key_file = "automation_dates.key"
        self.date_pattern = re.compile(r'^(\d{2})/(\d{2})/(\d{4})$')
        self.default_config = {
            'skip_dates': True,
            'date_from': '',
            'date_to': '',
            'last_updated': None,
            'format': 'DD/MM/YYYY'
        }

    def is_crypto_available(self):
        """Verifica si la encriptación está disponible"""
        return CRYPTO_AVAILABLE

    def _get_or_create_key(self):
        """Obtiene o crea la clave de encriptación para fechas"""
        if not CRYPTO_AVAILABLE:
            raise ImportError("cryptography no está disponible")

        if os.path.exists(self.key_file):
            with open(self.key_file, 'rb') as f:
                return f.read()
        else:
            key = Fernet.generate_key()
            with open(self.key_file, 'wb') as f:
                f.write(key)
            return key

    def _clean_string(self, text):
        """Limpia caracteres problemáticos de un string"""
        if not isinstance(text, str):
            return text
        text = text.replace('\xa0', ' ')
        text = text.replace('\u00a0', ' ')
        text = ' '.join(text.split())
        return text.strip()

    def _encrypt_data(self, data):
        """Encripta los datos de configuración de fechas"""
        if not CRYPTO_AVAILABLE:
            raise ImportError("cryptography no está disponible para encriptar")

        key = self._get_or_create_key()
        fernet = Fernet(key)

        # Limpiar strings en los datos
        clean_data = {}
        for key_name, value in data.items():
            if isinstance(value, str):
                clean_data[key_name] = self._clean_string(value)
            else:
                clean_data[key_name] = value

        json_str = json.dumps(clean_data, ensure_ascii=True, default=str)
        encrypted_data = fernet.encrypt(json_str.encode('utf-8'))
        return encrypted_data

    def _decrypt_data(self, encrypted_data):
        """Desencripta los datos de configuración de fechas"""
        if not CRYPTO_AVAILABLE:
            return None

        try:
            key = self._get_or_create_key()
            fernet = Fernet(key)
            decrypted_data = fernet.decrypt(encrypted_data)
            return json.loads(decrypted_data.decode('utf-8'))
        except Exception:
            return None

    def validate_date_format(self, date_str):
        """Valida que una fecha tenga el formato DD/MM/YYYY correcto"""
        if not date_str or not isinstance(date_str, str):
            return False, "Fecha vacía o no es string"

        date_str = self._clean_string(date_str)

        # Verificar patrón regex
        if not self.date_pattern.match(date_str):
            return False, "Formato incorrecto. Use DD/MM/YYYY"

        try:
            # Extraer componentes
            day, month, year = map(int, date_str.split('/'))

            # Verificar rangos básicos
            if not (1 <= day <= 31):
                return False, f"Día inválido: {day} (debe ser 1-31)"
            if not (1 <= month <= 12):
                return False, f"Mes inválido: {month} (debe ser 1-12)"
            if not (1900 <= year <= 2100):
                return False, f"Año inválido: {year} (debe ser 1900-2100)"

            # Crear objeto datetime para validación completa
            datetime(year, month, day)
            return True, "Fecha válida"

        except ValueError as e:
            return False, f"Fecha inválida: {str(e)}"

    def validate_date_range(self, date_from, date_to):
        """Valida que un rango de fechas sea correcto"""
        # Si ambas están vacías, está bien
        if not date_from and not date_to:
            return True, "Sin fechas especificadas"

        # Si solo una está llena, validar solo esa
        if date_from and not date_to:
            is_valid, message = self.validate_date_format(date_from)
            return is_valid, f"Solo fecha 'Desde': {message}"

        if date_to and not date_from:
            is_valid, message = self.validate_date_format(date_to)
            return is_valid, f"Solo fecha 'Hasta': {message}"

        # Si ambas están llenas, validar ambas y el rango
        from_valid, from_message = self.validate_date_format(date_from)
        if not from_valid:
            return False, f"Fecha 'Desde' inválida: {from_message}"

        to_valid, to_message = self.validate_date_format(date_to)
        if not to_valid:
            return False, f"Fecha 'Hasta' inválida: {to_message}"

        # Validar que 'Desde' no sea posterior a 'Hasta'
        try:
            from_dt = self.parse_date_string(date_from)
            to_dt = self.parse_date_string(date_to)

            if from_dt > to_dt:
                return False, "La fecha 'Desde' no puede ser posterior a 'Hasta'"

            # Verificar que el rango no sea excesivamente largo (por ejemplo, más de 5 años)
            diff_days = (to_dt - from_dt).days
            if diff_days > 1825:  # 5 años aproximadamente
                return False, f"Rango muy amplio: {diff_days} días (máximo recomendado: 1825)"

            return True, f"Rango válido: {diff_days} días"

        except Exception as e:
            return False, f"Error validando rango: {str(e)}"

    def parse_date_string(self, date_str):
        """Convierte string DD/MM/YYYY a objeto datetime"""
        if not date_str:
            return None

        is_valid, message = self.validate_date_format(date_str)
        if not is_valid:
            raise ValueError(f"Fecha inválida: {message}")

        day, month, year = map(int, date_str.split('/'))
        return datetime(year, month, day)

    def format_datetime_to_string(self, dt):
        """Convierte objeto datetime a string DD/MM/YYYY"""
        if not dt or not isinstance(dt, datetime):
            return ""
        return dt.strftime("%d/%m/%Y")

    def get_today_string(self):
        """Obtiene la fecha de hoy como string DD/MM/YYYY"""
        return datetime.now().strftime("%d/%m/%Y")

    def get_date_range_days_ago(self, days):
        """Obtiene rango de fechas desde hace X días hasta hoy"""
        today = datetime.now()
        past_date = today - timedelta(days=days)
        return {
            'date_from': self.format_datetime_to_string(past_date),
            'date_to': self.format_datetime_to_string(today)
        }

    def validate_config(self, config):
        """Valida una configuración completa de fechas"""
        if not isinstance(config, dict):
            return False, "Configuración debe ser un diccionario"

        # Verificar campos requeridos
        required_fields = ['skip_dates']
        for field in required_fields:
            if field not in config:
                return False, f"Campo requerido faltante: {field}"

        skip_dates = config.get('skip_dates', True)

        # Si skip_dates es True, no validar fechas
        if skip_dates:
            return True, "Configuración válida (fechas omitidas)"

        # Si skip_dates es False, validar fechas
        date_from = config.get('date_from', '')
        date_to = config.get('date_to', '')

        return self.validate_date_range(date_from, date_to)

    def save_config(self, config):
        """Guarda la configuración de fechas encriptada"""
        if not CRYPTO_AVAILABLE:
            return False, "cryptography no está disponible"

        try:
            # Validar configuración antes de guardar
            is_valid, message = self.validate_config(config)
            if not is_valid:
                return False, f"Configuración inválida: {message}"

            # Preparar datos para guardar
            config_data = {
                'skip_dates': config.get('skip_dates', True),
                'date_from': self._clean_string(config.get('date_from', '')),
                'date_to': self._clean_string(config.get('date_to', '')),
                'last_updated': datetime.now().isoformat(),
                'format': 'DD/MM/YYYY'
            }

            # Encriptar y guardar
            encrypted_data = self._encrypt_data(config_data)
            with open(self.config_file, 'wb') as f:
                f.write(encrypted_data)

            return True, "Configuración de fechas guardada correctamente"

        except Exception as e:
            return False, f"Error guardando configuración de fechas: {str(e)}"

    def load_config(self):
        """Carga la configuración de fechas desde archivo"""
        if not CRYPTO_AVAILABLE:
            return self.default_config.copy()

        try:
            if not os.path.exists(self.config_file):
                return self.default_config.copy()

            with open(self.config_file, 'rb') as f:
                encrypted_data = f.read()

            config = self._decrypt_data(encrypted_data)

            if not config:
                return self.default_config.copy()

            # Verificar que tenga los campos necesarios
            result = self.default_config.copy()
            result.update(config)

            return result

        except Exception as e:
            print(f"Error cargando configuración de fechas: {e}")
            return self.default_config.copy()

    def clear_config(self):
        """Elimina la configuración guardada y archivos asociados"""
        try:
            files_removed = 0

            if os.path.exists(self.config_file):
                os.remove(self.config_file)
                files_removed += 1

            if os.path.exists(self.key_file):
                os.remove(self.key_file)
                files_removed += 1

            return True, f"Se eliminaron {files_removed} archivos de configuración de fechas"

        except Exception as e:
            return False, f"Error eliminando configuración de fechas: {str(e)}"

    def get_config_info(self):
        """Obtiene información sobre la configuración guardada sin mostrar datos sensibles"""
        try:
            if not os.path.exists(self.config_file):
                return {
                    'exists': False,
                    'skip_dates': True,
                    'has_date_from': False,
                    'has_date_to': False,
                    'last_updated': None,
                    'file_size': 0
                }

            config = self.load_config()
            file_size = os.path.getsize(self.config_file) if os.path.exists(self.config_file) else 0

            return {
                'exists': True,
                'skip_dates': config.get('skip_dates', True),
                'has_date_from': bool(config.get('date_from', '')),
                'has_date_to': bool(config.get('date_to', '')),
                'last_updated': config.get('last_updated'),
                'file_size': file_size
            }

        except Exception as e:
            return {
                'exists': False,
                'skip_dates': True,
                'has_date_from': False,
                'has_date_to': False,
                'last_updated': None,
                'file_size': 0,
                'error': str(e)
            }

    def backup_config(self, backup_path=None):
        """Crea un backup de la configuración encriptada"""
        try:
            if not os.path.exists(self.config_file):
                return False, "No hay configuración para respaldar"

            if not backup_path:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_path = f"backup_date_config_{timestamp}.json"

            # Copiar archivo encriptado
            with open(self.config_file, 'rb') as source:
                with open(backup_path, 'wb') as backup:
                    backup.write(source.read())

            return True, f"Backup de configuración de fechas creado en: {backup_path}"

        except Exception as e:
            return False, f"Error creando backup de configuración de fechas: {str(e)}"

    def restore_config(self, backup_path):
        """Restaura configuración desde un backup"""
        try:
            if not os.path.exists(backup_path):
                return False, "Archivo de backup no encontrado"

            # Verificar que el backup sea válido
            with open(backup_path, 'rb') as f:
                backup_data = f.read()

            # Intentar desencriptar para validar
            test_config = self._decrypt_data(backup_data)
            if not test_config:
                return False, "Backup inválido o corrupto"

            # Validar configuración
            is_valid, message = self.validate_config(test_config)
            if not is_valid:
                return False, f"Backup contiene configuración inválida: {message}"

            # Crear backup del archivo actual si existe
            if os.path.exists(self.config_file):
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                current_backup = f"current_date_config_backup_{timestamp}.json"
                with open(self.config_file, 'rb') as current:
                    with open(current_backup, 'wb') as backup:
                        backup.write(current.read())

            # Restaurar configuración
            with open(self.config_file, 'wb') as f:
                f.write(backup_data)

            return True, "Configuración de fechas restaurada correctamente"

        except Exception as e:
            return False, f"Error restaurando configuración de fechas: {str(e)}"

    def get_preset_configs(self):
        """Obtiene configuraciones predefinidas útiles"""
        presets = {
            'no_dates': {
                'name': 'Sin fechas (por defecto)',
                'description': 'No modifica las fechas en la página',
                'config': {
                    'skip_dates': True,
                    'date_from': '',
                    'date_to': ''
                }
            },
            'today': {
                'name': 'Solo hoy',
                'description': 'Buscar solo registros de hoy',
                'config': {
                    'skip_dates': False,
                    'date_from': self.get_today_string(),
                    'date_to': self.get_today_string()
                }
            },
            'last_week': {
                'name': 'Última semana',
                'description': 'Buscar registros de los últimos 7 días',
                'config': {
                    'skip_dates': False,
                    **self.get_date_range_days_ago(7)
                }
            },
            'last_month': {
                'name': 'Último mes',
                'description': 'Buscar registros de los últimos 30 días',
                'config': {
                    'skip_dates': False,
                    **self.get_date_range_days_ago(30)
                }
            },
            'last_quarter': {
                'name': 'Último trimestre',
                'description': 'Buscar registros de los últimos 90 días',
                'config': {
                    'skip_dates': False,
                    **self.get_date_range_days_ago(90)
                }
            }
        }
        return presets

    def apply_preset(self, preset_name):
        """Aplica una configuración predefinida"""
        presets = self.get_preset_configs()

        if preset_name not in presets:
            return False, f"Preset '{preset_name}' no encontrado"

        preset_config = presets[preset_name]['config']
        success, message = self.save_config(preset_config)

        if success:
            return True, f"Preset '{presets[preset_name]['name']}' aplicado: {message}"
        else:
            return False, f"Error aplicando preset: {message}"

    def export_config_to_text(self, file_path=None):
        """Exporta configuración actual a archivo de texto legible"""
        try:
            config = self.load_config()

            if not file_path:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                file_path = f"date_config_export_{timestamp}.txt"

            with open(file_path, 'w', encoding='utf-8') as f:
                f.write("Configuración de Fechas - Syncro Bot\n")
                f.write(f"Exportado: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write("=" * 50 + "\n\n")

                f.write(f"Omitir fechas: {'Sí' if config.get('skip_dates', True) else 'No'}\n")

                if not config.get('skip_dates', True):
                    f.write(f"Fecha Desde: {config.get('date_from', 'No especificada')}\n")
                    f.write(f"Fecha Hasta: {config.get('date_to', 'No especificada')}\n")

                    # Información adicional si hay fechas
                    if config.get('date_from') and config.get('date_to'):
                        try:
                            from_dt = self.parse_date_string(config['date_from'])
                            to_dt = self.parse_date_string(config['date_to'])
                            diff_days = (to_dt - from_dt).days
                            f.write(f"Rango: {diff_days} días\n")
                        except:
                            pass

                f.write(f"\nÚltima actualización: {config.get('last_updated', 'No disponible')}\n")
                f.write(f"Formato: {config.get('format', 'DD/MM/YYYY')}\n")

            return True, f"Configuración exportada a: {file_path}"

        except Exception as e:
            return False, f"Error exportando configuración: {str(e)}"