# state_config_manager.py
# Ubicación: /syncro_bot/gui/components/automation/state_config_manager.py
"""
Gestor de configuración de estado para automatización.
Maneja la configuración de selección entre PENDIENTE, FINALIZADO y FINALIZADO_67_PLUS
para el tercer dropdown del sistema de automatización.
"""

import json
import os
from typing import Dict, Tuple, Optional


class StateConfigManager:
    """Gestor de configuración de estado con guardado persistente"""

    def __init__(self, config_dir: str = "config"):
        self.config_dir = config_dir
        self.config_file = os.path.join(config_dir, "state_config.json")

        # Opciones válidas para el estado
        self.valid_states = {
            'PENDIENTE': 'PENDIENTE',
            'FINALIZADO': 'FINALIZADO',
            'FINALIZADO_67_PLUS': 'FINALIZADO_67_PLUS'  # 🆕 Nuevo estado
        }

        # Configuración por defecto
        self.default_config = {
            'selected_state': 'PENDIENTE',
            'auto_save': True
        }

        # Crear directorio si no existe
        self._ensure_config_directory()

    def _ensure_config_directory(self):
        """Asegura que existe el directorio de configuración"""
        try:
            if not os.path.exists(self.config_dir):
                os.makedirs(self.config_dir)
        except Exception as e:
            print(f"Warning: No se pudo crear directorio de configuración: {e}")

    def load_config(self) -> Optional[Dict]:
        """Carga la configuración de estado desde archivo"""
        try:
            if not os.path.exists(self.config_file):
                return self.default_config.copy()

            with open(self.config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)

            # Validar que la configuración cargada sea válida
            is_valid, _ = self.validate_config(config)
            if is_valid:
                return config
            else:
                # Si la configuración no es válida, usar la por defecto
                return self.default_config.copy()

        except Exception as e:
            print(f"Error cargando configuración de estado: {e}")
            return self.default_config.copy()

    def save_config(self, config: Dict) -> Tuple[bool, str]:
        """Guarda la configuración de estado en archivo"""
        try:
            # Validar configuración antes de guardar
            is_valid, validation_message = self.validate_config(config)
            if not is_valid:
                return False, f"Configuración inválida: {validation_message}"

            # Asegurar que existe el directorio
            self._ensure_config_directory()

            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)

            return True, "Configuración de estado guardada correctamente"

        except Exception as e:
            return False, f"Error guardando configuración de estado: {str(e)}"

    def validate_config(self, config: Dict) -> Tuple[bool, str]:
        """Valida que la configuración de estado sea correcta"""
        try:
            if not isinstance(config, dict):
                return False, "La configuración debe ser un diccionario"

            # Verificar que tenga la clave principal
            if 'selected_state' not in config:
                return False, "Falta el campo 'selected_state'"

            # Verificar que el estado seleccionado sea válido
            selected_state = config['selected_state']
            if selected_state not in self.valid_states:
                valid_options = ', '.join(self.valid_states.keys())
                return False, f"Estado '{selected_state}' inválido. Opciones válidas: {valid_options}"

            return True, "Configuración válida"

        except Exception as e:
            return False, f"Error validando configuración: {str(e)}"

    def get_default_config(self) -> Dict:
        """Obtiene la configuración por defecto"""
        return self.default_config.copy()

    def get_valid_states(self) -> Dict[str, str]:
        """Obtiene las opciones de estado válidas"""
        return self.valid_states.copy()

    def create_config_for_state(self, state: str) -> Dict:
        """Crea una configuración para un estado específico"""
        if state not in self.valid_states:
            state = 'PENDIENTE'  # Fallback seguro

        return {
            'selected_state': state,
            'auto_save': True
        }

    def get_state_display_name(self, state: str) -> str:
        """Obtiene el nombre de visualización para un estado"""
        display_names = {
            'PENDIENTE': '⏳ Pendiente',
            'FINALIZADO': '✅ Finalizado',
            'FINALIZADO_67_PLUS': '📺 Finalizado 67 Plus'  # 🆕 Nuevo display name
        }
        return display_names.get(state, state)

    def apply_preset(self, preset_name: str) -> Tuple[bool, str]:
        """Aplica un preset predefinido de estado"""
        presets = {
            'pendiente': self.create_config_for_state('PENDIENTE'),
            'finalizado': self.create_config_for_state('FINALIZADO'),
            'finalizado_67_plus': self.create_config_for_state('FINALIZADO_67_PLUS'),  # 🆕 Nuevo preset
            'default': self.get_default_config()
        }

        if preset_name not in presets:
            available_presets = ', '.join(presets.keys())
            return False, f"Preset '{preset_name}' no existe. Disponibles: {available_presets}"

        config = presets[preset_name]
        success, message = self.save_config(config)

        if success:
            return True, f"Preset '{preset_name}' aplicado correctamente"
        else:
            return False, f"Error aplicando preset: {message}"

    def clear_config(self) -> Tuple[bool, str]:
        """Elimina el archivo de configuración (vuelve a valores por defecto)"""
        try:
            if os.path.exists(self.config_file):
                os.remove(self.config_file)
                return True, "Configuración de estado eliminada (usando valores por defecto)"
            else:
                return True, "No había configuración guardada"

        except Exception as e:
            return False, f"Error eliminando configuración: {str(e)}"

    def get_config_file_path(self) -> str:
        """Obtiene la ruta del archivo de configuración"""
        return self.config_file

    def config_exists(self) -> bool:
        """Verifica si existe un archivo de configuración guardado"""
        return os.path.exists(self.config_file)

    def get_current_state_for_automation(self, config: Optional[Dict] = None) -> str:
        """Obtiene el estado actual para usar en la automatización"""
        try:
            if config is None:
                config = self.load_config()

            if not config:
                return 'PENDIENTE'  # Fallback seguro

            selected_state = config.get('selected_state', 'PENDIENTE')

            # Verificar que sea un estado válido
            if selected_state in self.valid_states:
                return selected_state
            else:
                return 'PENDIENTE'  # Fallback seguro

        except Exception:
            return 'PENDIENTE'  # Fallback seguro

    def create_automation_summary(self, config: Optional[Dict] = None) -> str:
        """Crea un resumen de la configuración para logging"""
        try:
            if config is None:
                config = self.load_config()

            if not config:
                return "Estado: PENDIENTE (por defecto)"

            selected_state = config.get('selected_state', 'PENDIENTE')
            display_name = self.get_state_display_name(selected_state)

            return f"Estado seleccionado: {display_name}"

        except Exception:
            return "Estado: PENDIENTE (error en configuración)"