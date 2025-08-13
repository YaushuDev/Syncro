# credentials_manager.py
# Ubicación: /syncro_bot/gui/components/automation/credentials_manager.py
"""
Gestor de credenciales con encriptación para el sistema de automatización.
Maneja el almacenamiento seguro, validación y recuperación de credenciales
de login con encriptación mediante cryptography.fernet.
"""

import json
import os
from datetime import datetime

# Importaciones para encriptación de credenciales
try:
    from cryptography.fernet import Fernet

    CRYPTO_AVAILABLE = True
except ImportError:
    CRYPTO_AVAILABLE = False
    print("Error: La librería 'cryptography' no está instalada.")
    print("Instale con: pip install cryptography")


class CredentialsManager:
    """Gestor de credenciales con encriptación para login automático"""

    def __init__(self):
        self.config_file = "automation_credentials.json"
        self.key_file = "automation.key"

    def is_crypto_available(self):
        """Verifica si la encriptación está disponible"""
        return CRYPTO_AVAILABLE

    def _get_or_create_key(self):
        """Obtiene o crea la clave de encriptación"""
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
        """Encripta los datos de credenciales"""
        if not CRYPTO_AVAILABLE:
            raise ImportError("cryptography no está disponible para encriptar")

        key = self._get_or_create_key()
        fernet = Fernet(key)

        clean_data = {}
        for key_name, value in data.items():
            if isinstance(value, str):
                clean_data[key_name] = self._clean_string(value)
            else:
                clean_data[key_name] = value

        json_str = json.dumps(clean_data, ensure_ascii=True)
        encrypted_data = fernet.encrypt(json_str.encode('utf-8'))
        return encrypted_data

    def _decrypt_data(self, encrypted_data):
        """Desencripta los datos de credenciales"""
        if not CRYPTO_AVAILABLE:
            return None

        try:
            key = self._get_or_create_key()
            fernet = Fernet(key)
            decrypted_data = fernet.decrypt(encrypted_data)
            return json.loads(decrypted_data.decode('utf-8'))
        except Exception:
            return None

    def save_credentials(self, username, password):
        """Guarda las credenciales encriptadas"""
        if not CRYPTO_AVAILABLE:
            return False, "cryptography no está disponible"

        try:
            credentials_data = {
                "username": self._clean_string(username),
                "password": self._clean_string(password),
                "saved_at": datetime.now().isoformat()
            }
            encrypted_data = self._encrypt_data(credentials_data)
            with open(self.config_file, 'wb') as f:
                f.write(encrypted_data)
            return True, "Credenciales guardadas correctamente"
        except Exception as e:
            print(f"Error guardando credenciales: {e}")
            return False, f"Error guardando credenciales: {str(e)}"

    def load_credentials(self):
        """Carga las credenciales desde archivo"""
        if not CRYPTO_AVAILABLE:
            return None

        try:
            if not os.path.exists(self.config_file):
                return None

            with open(self.config_file, 'rb') as f:
                encrypted_data = f.read()

            return self._decrypt_data(encrypted_data)
        except Exception as e:
            print(f"Error cargando credenciales: {e}")
            return None

    def clear_credentials(self):
        """Elimina las credenciales guardadas"""
        try:
            files_removed = 0
            if os.path.exists(self.config_file):
                os.remove(self.config_file)
                files_removed += 1
            if os.path.exists(self.key_file):
                os.remove(self.key_file)
                files_removed += 1
            return True, f"Se eliminaron {files_removed} archivos de credenciales"
        except Exception as e:
            return False, f"Error eliminando credenciales: {str(e)}"

    def validate_credentials(self, username, password):
        """Valida que las credenciales no estén vacías y tengan formato correcto"""
        username = self._clean_string(username) if username else ""
        password = self._clean_string(password) if password else ""

        if not username:
            return False, "El usuario es obligatorio"
        if not password:
            return False, "La contraseña es obligatoria"
        if len(username) < 2:
            return False, "El usuario debe tener al menos 2 caracteres"
        if len(password) < 3:
            return False, "La contraseña debe tener al menos 3 caracteres"

        # Validaciones adicionales
        if username.strip() != username:
            return False, "El usuario no puede empezar o terminar con espacios"
        if password.strip() != password:
            return False, "La contraseña no puede empezar o terminar con espacios"

        return True, "Credenciales válidas"

    def get_credentials_info(self):
        """Obtiene información sobre las credenciales guardadas sin mostrar datos sensibles"""
        try:
            if not os.path.exists(self.config_file):
                return {
                    'exists': False,
                    'username': None,
                    'saved_at': None,
                    'file_size': 0
                }

            credentials = self.load_credentials()
            if not credentials:
                return {
                    'exists': False,
                    'username': None,
                    'saved_at': None,
                    'file_size': os.path.getsize(self.config_file)
                }

            return {
                'exists': True,
                'username': credentials.get('username', ''),
                'saved_at': credentials.get('saved_at', ''),
                'file_size': os.path.getsize(self.config_file)
            }
        except Exception as e:
            return {
                'exists': False,
                'username': None,
                'saved_at': None,
                'file_size': 0,
                'error': str(e)
            }

    def backup_credentials(self, backup_path=None):
        """Crea un backup de las credenciales encriptadas"""
        try:
            if not os.path.exists(self.config_file):
                return False, "No hay credenciales para respaldar"

            if not backup_path:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_path = f"backup_credentials_{timestamp}.json"

            # Copiar archivo encriptado
            with open(self.config_file, 'rb') as source:
                with open(backup_path, 'wb') as backup:
                    backup.write(source.read())

            return True, f"Backup creado en: {backup_path}"
        except Exception as e:
            return False, f"Error creando backup: {str(e)}"

    def restore_credentials(self, backup_path):
        """Restaura credenciales desde un backup"""
        try:
            if not os.path.exists(backup_path):
                return False, "Archivo de backup no encontrado"

            # Verificar que el backup sea válido
            with open(backup_path, 'rb') as f:
                backup_data = f.read()

            # Intentar desencriptar para validar
            test_credentials = self._decrypt_data(backup_data)
            if not test_credentials:
                return False, "Backup inválido o corrupto"

            # Crear backup del archivo actual si existe
            if os.path.exists(self.config_file):
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                current_backup = f"current_credentials_backup_{timestamp}.json"
                with open(self.config_file, 'rb') as current:
                    with open(current_backup, 'wb') as backup:
                        backup.write(current.read())

            # Restaurar credenciales
            with open(self.config_file, 'wb') as f:
                f.write(backup_data)

            return True, "Credenciales restauradas correctamente"
        except Exception as e:
            return False, f"Error restaurando credenciales: {str(e)}"