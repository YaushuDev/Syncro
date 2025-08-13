# automation_logger.py
# Ubicación: /syncro_bot/gui/components/automation/automation_logger.py
"""
Sistema de logging especializado para automatización.
Maneja diferentes niveles de log, formato de mensajes, persistencia opcional
y integración con la UI para mostrar logs en tiempo real.
"""

import os
import json
from datetime import datetime
from enum import Enum
from typing import Optional, Callable, List, Dict


class LogLevel(Enum):
    """Niveles de logging disponibles"""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class LogEntry:
    """Entrada de log estructurada"""

    def __init__(self, message: str, level: LogLevel = LogLevel.INFO,
                 timestamp: Optional[datetime] = None, context: Optional[Dict] = None):
        self.message = message
        self.level = level
        self.timestamp = timestamp or datetime.now()
        self.context = context or {}

    def to_dict(self):
        """Convierte la entrada a diccionario para serialización"""
        return {
            'message': self.message,
            'level': self.level.value,
            'timestamp': self.timestamp.isoformat(),
            'context': self.context
        }

    @classmethod
    def from_dict(cls, data: Dict):
        """Crea entrada desde diccionario"""
        return cls(
            message=data['message'],
            level=LogLevel(data['level']),
            timestamp=datetime.fromisoformat(data['timestamp']),
            context=data.get('context', {})
        )

    def format_for_display(self, include_context: bool = False):
        """Formatea la entrada para mostrar en UI"""
        timestamp_str = self.timestamp.strftime("%H:%M:%S")
        formatted = f"[{timestamp_str}] {self.level.value}: {self.message}"

        if include_context and self.context:
            context_str = ", ".join([f"{k}={v}" for k, v in self.context.items()])
            formatted += f" ({context_str})"

        return formatted


class AutomationLogger:
    """Logger especializado para automatización con funcionalidades avanzadas"""

    def __init__(self, name: str = "AutomationLogger", max_entries: int = 1000,
                 enable_persistence: bool = False, log_file: Optional[str] = None):
        self.name = name
        self.max_entries = max_entries
        self.enable_persistence = enable_persistence
        self.log_file = log_file or f"automation_log_{datetime.now().strftime('%Y%m%d')}.json"

        # Storage
        self.entries: List[LogEntry] = []
        self.ui_callback: Optional[Callable] = None
        self.file_callback: Optional[Callable] = None

        # Configuración
        self.min_level = LogLevel.INFO
        self.auto_scroll = True
        self.include_context_in_ui = False

        # Estadísticas
        self.stats = {level: 0 for level in LogLevel}

        # Cargar logs existentes si la persistencia está habilitada
        if self.enable_persistence:
            self._load_from_file()

    def set_ui_callback(self, callback: Callable[[str, str], None]):
        """Establece callback para actualizar UI"""
        self.ui_callback = callback

    def set_file_callback(self, callback: Callable[[LogEntry], None]):
        """Establece callback para escribir a archivo personalizado"""
        self.file_callback = callback

    def set_min_level(self, level: LogLevel):
        """Establece nivel mínimo de logging"""
        self.min_level = level

    def debug(self, message: str, context: Optional[Dict] = None):
        """Log de nivel DEBUG"""
        self._log(message, LogLevel.DEBUG, context)

    def info(self, message: str, context: Optional[Dict] = None):
        """Log de nivel INFO"""
        self._log(message, LogLevel.INFO, context)

    def warning(self, message: str, context: Optional[Dict] = None):
        """Log de nivel WARNING"""
        self._log(message, LogLevel.WARNING, context)

    def error(self, message: str, context: Optional[Dict] = None):
        """Log de nivel ERROR"""
        self._log(message, LogLevel.ERROR, context)

    def critical(self, message: str, context: Optional[Dict] = None):
        """Log de nivel CRITICAL"""
        self._log(message, LogLevel.CRITICAL, context)

    def _log(self, message: str, level: LogLevel, context: Optional[Dict] = None):
        """Método interno de logging"""
        # Verificar nivel mínimo
        if self._should_log(level):
            entry = LogEntry(message, level, context=context)
            self._add_entry(entry)

    def _should_log(self, level: LogLevel) -> bool:
        """Verifica si debe logear según el nivel mínimo"""
        level_order = {
            LogLevel.DEBUG: 0,
            LogLevel.INFO: 1,
            LogLevel.WARNING: 2,
            LogLevel.ERROR: 3,
            LogLevel.CRITICAL: 4
        }
        return level_order[level] >= level_order[self.min_level]

    def _add_entry(self, entry: LogEntry):
        """Añade entrada al log"""
        # Añadir a storage
        self.entries.append(entry)

        # Actualizar estadísticas
        self.stats[entry.level] += 1

        # Mantener límite de entradas
        if len(self.entries) > self.max_entries:
            removed_entry = self.entries.pop(0)
            self.stats[removed_entry.level] = max(0, self.stats[removed_entry.level] - 1)

        # Notificar a UI
        if self.ui_callback:
            try:
                formatted_message = entry.format_for_display(self.include_context_in_ui)
                self.ui_callback(formatted_message, entry.level.value)
            except Exception as e:
                print(f"Error en UI callback: {e}")

        # Persistir si está habilitado
        if self.enable_persistence:
            self._persist_entry(entry)

        # Callback personalizado de archivo
        if self.file_callback:
            try:
                self.file_callback(entry)
            except Exception as e:
                print(f"Error en file callback: {e}")

    def _persist_entry(self, entry: LogEntry):
        """Persiste entrada a archivo JSON"""
        try:
            # Leer entradas existentes
            existing_entries = []
            if os.path.exists(self.log_file):
                try:
                    with open(self.log_file, 'r', encoding='utf-8') as f:
                        existing_data = json.load(f)
                        existing_entries = existing_data.get('entries', [])
                except (json.JSONDecodeError, KeyError):
                    existing_entries = []

            # Añadir nueva entrada
            existing_entries.append(entry.to_dict())

            # Mantener límite en archivo también
            if len(existing_entries) > self.max_entries:
                existing_entries = existing_entries[-self.max_entries:]

            # Escribir archivo
            log_data = {
                'logger_name': self.name,
                'created_at': datetime.now().isoformat(),
                'entries': existing_entries
            }

            with open(self.log_file, 'w', encoding='utf-8') as f:
                json.dump(log_data, f, indent=2, ensure_ascii=False)

        except Exception as e:
            print(f"Error persistiendo log: {e}")

    def _load_from_file(self):
        """Carga logs desde archivo"""
        try:
            if os.path.exists(self.log_file):
                with open(self.log_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    entries_data = data.get('entries', [])

                    for entry_data in entries_data:
                        entry = LogEntry.from_dict(entry_data)
                        self.entries.append(entry)
                        self.stats[entry.level] += 1

                        # Notificar a UI si ya está configurada
                        if self.ui_callback:
                            formatted_message = entry.format_for_display(self.include_context_in_ui)
                            self.ui_callback(formatted_message, entry.level.value)

        except Exception as e:
            print(f"Error cargando logs: {e}")

    def clear(self):
        """Limpia todos los logs"""
        self.entries.clear()
        self.stats = {level: 0 for level in LogLevel}

        # Limpiar archivo si existe
        if self.enable_persistence and os.path.exists(self.log_file):
            try:
                os.remove(self.log_file)
            except Exception as e:
                print(f"Error eliminando archivo de log: {e}")

    def get_entries(self, level_filter: Optional[LogLevel] = None,
                    limit: Optional[int] = None) -> List[LogEntry]:
        """Obtiene entradas con filtros opcionales"""
        entries = self.entries

        if level_filter:
            entries = [e for e in entries if e.level == level_filter]

        if limit:
            entries = entries[-limit:]

        return entries

    def get_stats(self) -> Dict:
        """Obtiene estadísticas de logging"""
        total = sum(self.stats.values())
        return {
            'total_entries': total,
            'by_level': dict(self.stats),
            'current_file': self.log_file if self.enable_persistence else None,
            'max_entries': self.max_entries,
            'min_level': self.min_level.value
        }

    def search(self, query: str, case_sensitive: bool = False) -> List[LogEntry]:
        """Busca en los logs por texto"""
        if not case_sensitive:
            query = query.lower()

        results = []
        for entry in self.entries:
            message = entry.message if case_sensitive else entry.message.lower()
            if query in message:
                results.append(entry)

        return results

    def export_to_text(self, file_path: str, include_context: bool = True) -> bool:
        """Exporta logs a archivo de texto"""
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(f"Log de Automatización - {self.name}\n")
                f.write(f"Exportado: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write("=" * 50 + "\n\n")

                for entry in self.entries:
                    f.write(entry.format_for_display(include_context) + "\n")

            return True
        except Exception as e:
            print(f"Error exportando logs: {e}")
            return False

    def get_recent_errors(self, count: int = 5) -> List[LogEntry]:
        """Obtiene errores recientes"""
        error_entries = [e for e in self.entries
                         if e.level in [LogLevel.ERROR, LogLevel.CRITICAL]]
        return error_entries[-count:] if error_entries else []

    def log_automation_start(self, context: Optional[Dict] = None):
        """Log específico para inicio de automatización"""
        self.info("🚀 Iniciando automatización", context)

    def log_automation_end(self, success: bool, context: Optional[Dict] = None):
        """Log específico para fin de automatización"""
        if success:
            self.info("✅ Automatización completada exitosamente", context)
        else:
            self.error("❌ Automatización falló", context)

    def log_login_attempt(self, username: str, success: bool):
        """Log específico para intentos de login"""
        context = {'username': username}
        if success:
            self.info("🔐 Login exitoso", context)
        else:
            self.warning("🔐 Login fallido", context)

    def log_navigation(self, url: str, success: bool):
        """Log específico para navegación"""
        context = {'url': url}
        if success:
            self.info("🌐 Navegación exitosa", context)
        else:
            self.error("🌐 Error de navegación", context)

    def log_selenium_action(self, action: str, element: str, success: bool):
        """Log específico para acciones de Selenium"""
        context = {'action': action, 'element': element}
        if success:
            self.debug(f"🎯 Acción Selenium: {action}", context)
        else:
            self.error(f"🎯 Error en acción Selenium: {action}", context)


class AutomationLoggerFactory:
    """Factory para crear loggers de automatización"""

    _instances = {}

    @classmethod
    def get_logger(cls, name: str = "default", **kwargs) -> AutomationLogger:
        """Obtiene o crea un logger"""
        if name not in cls._instances:
            cls._instances[name] = AutomationLogger(name=name, **kwargs)
        return cls._instances[name]

    @classmethod
    def create_ui_logger(cls, ui_callback: Callable) -> AutomationLogger:
        """Crea logger configurado para UI"""
        logger = cls.get_logger("ui_logger", max_entries=500, enable_persistence=False)
        logger.set_ui_callback(ui_callback)
        return logger

    @classmethod
    def create_file_logger(cls, log_file: str) -> AutomationLogger:
        """Crea logger configurado para archivo"""
        return cls.get_logger("file_logger", enable_persistence=True, log_file=log_file)

    @classmethod
    def create_combined_logger(cls, ui_callback: Callable, log_file: str) -> AutomationLogger:
        """Crea logger que escribe tanto a UI como a archivo"""
        logger = cls.get_logger("combined_logger", max_entries=1000,
                                enable_persistence=True, log_file=log_file)
        logger.set_ui_callback(ui_callback)
        return logger