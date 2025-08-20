# main_window.py
# Ubicación: /syncro_bot/gui/main_window.py
"""
Ventana principal de Syncro Bot con scheduler automático integrado para reportes.
Gestiona la configuración de la ventana, pestañas, conexiones entre componentes
y el scheduler automático para envío programado de reportes Excel por correo.
"""

from tkinter import ttk
import time
from .tabs.automation_tab import AutomationTab
from .tabs.email_tab import EmailTab
from .tabs.profiles_tab import ProfilesTab
from .tabs.registro_tab import RegistroTab
from .components.profile_execution_service import ProfileScheduler


class MainWindow:
    def __init__(self, root):
        self.root = root
        self.is_closing = False
        self.profile_scheduler = None

        self.setup_window()
        self.create_tabs()
        self.setup_integrations()
        self.setup_close_handler()
        self._initialize_scheduler()

    def setup_window(self):
        """Configurar las propiedades básicas de la ventana"""
        self.root.title("Syncro Bot - Sistema de Automatización y Reportes")
        self.root.geometry("1300x750")
        self.root.resizable(True, True)

        # Configurar el icono de la ventana si existe
        try:
            # Opcional: agregar icono si tienes uno
            # self.root.iconbitmap("icon.ico")
            pass
        except:
            pass

    def create_tabs(self):
        """Crear el sistema de pestañas"""
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill='both', expand=True, padx=10, pady=10)

        # Inicializar las pestañas en orden lógico
        print("Inicializando pestañas...")

        # 1. Pestaña de Automatización (funcionalidad principal)
        print("  → Creando AutomationTab...")
        self.automation_tab = AutomationTab(self.notebook)

        # 2. Pestaña de Perfiles (programación automática de reportes)
        print("  → Creando ProfilesTab...")
        self.profiles_tab = ProfilesTab(self.notebook)

        # 3. Pestaña de Email (configuración de envío)
        print("  → Creando EmailTab...")
        self.email_tab = EmailTab(self.notebook)

        # 4. Pestaña de Registro (logging y reportes)
        print("  → Creando RegistroTab...")
        self.registro_tab = RegistroTab(self.notebook)

        print("✅ Todas las pestañas creadas exitosamente")

    def setup_integrations(self):
        """Configura las integraciones entre pestañas"""
        print("Configurando integraciones entre pestañas...")

        try:
            # 1. Conectar AutomationTab con RegistroTab (para logging de ejecuciones manuales)
            if hasattr(self, 'automation_tab') and hasattr(self, 'registro_tab'):
                self.automation_tab.set_registry_tab(self.registro_tab)
                print("  ✅ AutomationTab → RegistroTab conectado")
            else:
                print("  ❌ Error: AutomationTab o RegistroTab no disponibles")

            # 2. Conectar ProfilesTab con RegistroTab (para logging de envíos de reportes)
            if hasattr(self, 'profiles_tab') and hasattr(self, 'registro_tab'):
                self.profiles_tab.set_registry_tab(self.registro_tab)
                print("  ✅ ProfilesTab → RegistroTab conectado")
            else:
                print("  ❌ Error: ProfilesTab o RegistroTab no disponibles")

            # 3. Conectar RegistroTab con EmailTab (para envío de reportes)
            if hasattr(self, 'registro_tab') and hasattr(self, 'email_tab'):
                self.registro_tab.set_email_tab(self.email_tab)
                print("  ✅ RegistroTab → EmailTab conectado")
            else:
                print("  ❌ Error: RegistroTab o EmailTab no disponibles")

            print("🔗 Integración completa finalizada")

            # Verificar estado de integraciones
            self._verify_integrations()

        except Exception as e:
            print(f"❌ Error durante la integración: {e}")
            # Continuar sin las integraciones - la app funciona básicamente sin ellas

    def _initialize_scheduler(self):
        """Inicializa y arranca el scheduler automático de reportes"""
        print("Configurando scheduler automático de reportes...")

        try:
            # Verificar que los componentes necesarios estén disponibles
            if not hasattr(self, 'profiles_tab'):
                print("  ❌ ProfilesTab no disponible - scheduler no iniciado")
                return

            # Obtener servicios del profiles_tab
            profiles_manager = self.profiles_tab.profiles_manager
            execution_service = self.profiles_tab.execution_service
            report_service = self.profiles_tab.report_service

            # Crear instancia del scheduler
            self.profile_scheduler = ProfileScheduler(
                profiles_manager=profiles_manager,
                execution_service=execution_service,
                report_service=report_service
            )
            print("  ✅ ProfileScheduler para reportes creado exitosamente")

            # Iniciar scheduler automáticamente
            success, message = self.profile_scheduler.start_scheduler()
            if success:
                print(f"  🚀 Scheduler de reportes iniciado: {message}")
            else:
                print(f"  ❌ Error iniciando scheduler: {message}")
                self.profile_scheduler = None

        except Exception as e:
            print(f"❌ Error configurando scheduler: {e}")
            self.profile_scheduler = None

    def _verify_integrations(self):
        """Verifica que las integraciones estén funcionando correctamente"""
        try:
            # Verificar que AutomationTab tiene referencia a RegistroTab
            if hasattr(self.automation_tab, 'registry_tab') and self.automation_tab.registry_tab:
                print("  ✅ AutomationTab.registry_tab configurado")
            else:
                print("  ⚠️ AutomationTab.registry_tab no configurado")

            # Verificar que ProfilesTab tiene referencia a RegistroTab
            if hasattr(self.profiles_tab, 'registry_tab') and self.profiles_tab.registry_tab:
                print("  ✅ ProfilesTab.registry_tab configurado")
            else:
                print("  ⚠️ ProfilesTab.registry_tab no configurado")

            # Verificar que RegistroTab tiene referencia a EmailTab
            if hasattr(self.registro_tab, 'email_tab') and self.registro_tab.email_tab:
                print("  ✅ RegistroTab.email_tab configurado")
            else:
                print("  ⚠️ RegistroTab.email_tab no configurado")

            # Verificar que RegistroTab puede cargar datos
            if hasattr(self.registro_tab, 'registry_manager'):
                records_count = len(self.registro_tab.registry_manager.get_all_records())
                print(f"  📊 RegistroTab tiene {records_count} registros cargados")

            print("🔍 Verificación de integraciones completada")

        except Exception as e:
            print(f"⚠️ Error durante verificación: {e}")

    def setup_close_handler(self):
        """Configura el manejo correcto del cierre de la aplicación"""
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

        # Manejar Ctrl+C en la consola
        try:
            import signal
            signal.signal(signal.SIGINT, self.signal_handler)
        except:
            pass

    def signal_handler(self, signum, frame):
        """Maneja señales del sistema (como Ctrl+C)"""
        self.on_closing()

    def on_closing(self):
        """Maneja el cierre de la aplicación de forma segura"""
        if self.is_closing:
            return

        self.is_closing = True
        print("🔄 Iniciando cierre seguro de Syncro Bot...")

        try:
            # DETENER SCHEDULER DE REPORTES PRIMERO
            if self.profile_scheduler:
                print("  → Deteniendo ProfileScheduler de reportes...")
                try:
                    success, message = self.profile_scheduler.stop_scheduler()
                    if success:
                        print(f"    ✅ Scheduler de reportes detenido: {message}")
                    else:
                        print(f"    ⚠️ Error deteniendo scheduler: {message}")
                except Exception as e:
                    print(f"    ❌ Excepción deteniendo scheduler: {e}")

            # Limpiar pestaña de automatización
            if hasattr(self, 'automation_tab') and self.automation_tab:
                print("  → Limpiando AutomationTab...")
                try:
                    if self.automation_tab.get_automation_status():
                        self.automation_tab.automation_service.pause_automation()
                    self.automation_tab.cleanup()
                    print("    ✅ AutomationTab limpiado")
                except Exception as e:
                    print(f"    ⚠️ Error limpiando AutomationTab: {e}")

            # Limpiar pestaña de perfiles de reportes
            if hasattr(self, 'profiles_tab') and self.profiles_tab:
                print("  → Limpiando ProfilesTab (reportes)...")
                try:
                    # Detener cualquier envío de reporte en curso
                    if hasattr(self.profiles_tab, 'execution_service'):
                        if self.profiles_tab.execution_service.is_busy():
                            print("    → Deteniendo envío de reporte en curso...")

                    if hasattr(self.profiles_tab, 'cleanup'):
                        self.profiles_tab.cleanup()
                    print("    ✅ ProfilesTab limpiado")
                except Exception as e:
                    print(f"    ⚠️ Error limpiando ProfilesTab: {e}")

            # Limpiar pestaña de registro
            if hasattr(self, 'registro_tab') and self.registro_tab:
                print("  → Limpiando RegistroTab...")
                try:
                    # Limpiar archivos temporales de reportes
                    if hasattr(self.registro_tab, 'report_generator'):
                        self.registro_tab.report_generator.cleanup_temp_files()

                    if hasattr(self.registro_tab, 'cleanup'):
                        self.registro_tab.cleanup()
                    print("    ✅ RegistroTab limpiado")
                except Exception as e:
                    print(f"    ⚠️ Error limpiando RegistroTab: {e}")

            # Limpiar pestaña de email
            if hasattr(self, 'email_tab') and self.email_tab:
                print("  → Limpiando EmailTab...")
                try:
                    if hasattr(self.email_tab, 'cleanup'):
                        self.email_tab.cleanup()
                    print("    ✅ EmailTab limpiado")
                except Exception as e:
                    print(f"    ⚠️ Error limpiando EmailTab: {e}")

            # Pequeña pausa para permitir que los hilos daemon se terminen
            print("  → Esperando finalización de hilos...")
            time.sleep(0.2)
            print("    ✅ Hilos finalizados")

        except Exception as e:
            print(f"❌ Error durante el cierre: {e}")
        finally:
            # Forzar la destrucción de la ventana
            try:
                print("  → Cerrando ventana principal...")
                self.root.quit()
                self.root.destroy()
                print("✅ Syncro Bot cerrado exitosamente")
            except:
                print("⚠️ Error cerrando ventana, forzando salida...")

    # ===== MÉTODOS PÚBLICOS =====
    def get_automation_tab(self):
        """Retorna la instancia de la pestaña de automatización"""
        return self.automation_tab if hasattr(self, 'automation_tab') else None

    def get_profiles_tab(self):
        """Retorna la instancia de la pestaña de perfiles de reportes"""
        return self.profiles_tab if hasattr(self, 'profiles_tab') else None

    def get_email_tab(self):
        """Retorna la instancia de la pestaña de email"""
        return self.email_tab if hasattr(self, 'email_tab') else None

    def get_registro_tab(self):
        """Retorna la instancia de la pestaña de registro"""
        return self.registro_tab if hasattr(self, 'registro_tab') else None

    # ===== MÉTODOS PARA SCHEDULER DE REPORTES =====
    def get_scheduler(self):
        """Retorna la instancia del scheduler de reportes"""
        return self.profile_scheduler

    def get_scheduler_status(self):
        """Obtiene estado del scheduler de reportes"""
        if not self.profile_scheduler:
            return {'available': False, 'running': False, 'error': 'Scheduler de reportes no inicializado'}

        try:
            status = self.profile_scheduler.get_scheduler_status()
            status['available'] = True
            return status
        except Exception as e:
            return {'available': False, 'running': False, 'error': str(e)}

    def restart_scheduler(self):
        """Reinicia el scheduler de reportes"""
        if not self.profile_scheduler:
            return False, "Scheduler de reportes no disponible"

        try:
            # Detener si está corriendo
            if self.profile_scheduler.is_running:
                success, message = self.profile_scheduler.stop_scheduler()
                if not success:
                    return False, f"Error deteniendo scheduler: {message}"

                # Esperar un momento
                time.sleep(1)

            # Reiniciar
            success, message = self.profile_scheduler.start_scheduler()
            return success, message

        except Exception as e:
            return False, f"Error reiniciando scheduler: {str(e)}"

    def is_system_ready(self):
        """Verifica si el sistema está completamente configurado"""
        try:
            # Verificar que todas las pestañas estén disponibles
            tabs_ready = all([
                hasattr(self, 'automation_tab') and self.automation_tab,
                hasattr(self, 'profiles_tab') and self.profiles_tab,
                hasattr(self, 'email_tab') and self.email_tab,
                hasattr(self, 'registro_tab') and self.registro_tab
            ])

            # Verificar que las integraciones estén configuradas
            integrations_ready = all([
                hasattr(self.automation_tab, 'registry_tab') and self.automation_tab.registry_tab,
                hasattr(self.profiles_tab, 'registry_tab') and self.profiles_tab.registry_tab,
                hasattr(self.registro_tab, 'email_tab') and self.registro_tab.email_tab
            ])

            # Verificar scheduler de reportes
            report_scheduler_ready = self.profile_scheduler is not None and self.profile_scheduler.is_running

            return tabs_ready and integrations_ready and report_scheduler_ready

        except Exception:
            return False

    def get_system_status(self):
        """Obtiene el estado completo del sistema"""
        try:
            status = {
                'automation_running': False,
                'email_configured': False,
                'active_report_profiles': 0,
                'total_records': 0,
                'integrations_ready': False,
                'report_scheduler_running': False
            }

            # Estado de automatización
            if hasattr(self, 'automation_tab') and self.automation_tab:
                status['automation_running'] = self.automation_tab.get_automation_status()

            # Estado de email
            if hasattr(self, 'email_tab') and self.email_tab:
                status['email_configured'] = self.email_tab.is_email_configured()

            # Perfiles activos de reportes
            if hasattr(self, 'profiles_tab') and self.profiles_tab:
                active_profiles = self.profiles_tab.get_active_profiles()
                status['active_report_profiles'] = len(active_profiles)

            # Total de registros
            if hasattr(self, 'registro_tab') and self.registro_tab:
                all_records = self.registro_tab.registry_manager.get_all_records()
                status['total_records'] = len(all_records)

            # Estado de integraciones
            status['integrations_ready'] = self.is_system_ready()

            # Estado de scheduler de reportes
            status['report_scheduler_running'] = bool(self.profile_scheduler and self.profile_scheduler.is_running)

            return status

        except Exception as e:
            print(f"Error obteniendo estado del sistema: {e}")
            return None

    def log_system_startup(self):
        """Registra el inicio del sistema en el log"""
        try:
            if hasattr(self, 'registro_tab') and self.registro_tab:
                # Crear registro de inicio del sistema
                from datetime import datetime
                startup_record = self.registro_tab.add_execution_record(
                    start_time=datetime.now(),
                    profile_name="Sistema",
                    user_type="Sistema"
                )

                # Inmediatamente marcarlo como exitoso
                self.registro_tab.update_execution_record(
                    record_id=startup_record['id'],
                    end_time=datetime.now(),
                    status="Exitoso",
                    error_message=""
                )

                print(f"📋 Inicio del sistema registrado con ID: {startup_record['id']}")

        except Exception as e:
            print(f"⚠️ Error registrando inicio del sistema: {e}")

    def show_startup_summary(self):
        """Muestra resumen del estado del sistema al inicio"""
        try:
            print("\n" + "=" * 70)
            print("🤖 SYNCRO BOT - SISTEMA DE AUTOMATIZACIÓN Y REPORTES")
            print("=" * 70)

            status = self.get_system_status()
            if status:
                print(f"🔧 Sistema integrado: {'✅ Sí' if status['integrations_ready'] else '❌ No'}")
                print(f"📧 Email configurado: {'✅ Sí' if status['email_configured'] else '❌ No'}")
                print(f"📊 Perfiles de reportes activos: {status['active_report_profiles']}")
                print(f"📋 Registros totales: {status['total_records']}")
                print(f"🤖 Automatización: {'🟢 Activa' if status['automation_running'] else '🟠 Inactiva'}")
                print(f"📧 Scheduler de Reportes: {'🟢 Ejecutándose' if status['report_scheduler_running'] else '🔴 Detenido'}")
            else:
                print("⚠️ No se pudo obtener el estado del sistema")

            print("=" * 70)
            print("✅ Syncro Bot iniciado correctamente")
            print("💡 Utilice las pestañas para configurar y gestionar el sistema")

            # Información de scheduler de reportes
            if self.profile_scheduler and self.profile_scheduler.is_running:
                print("📧 Los perfiles de reportes se enviarán automáticamente por correo")
            else:
                print("⚠️ Scheduler de reportes no está funcionando")

            print("=" * 70 + "\n")

            # Registrar inicio
            self.log_system_startup()

        except Exception as e:
            print(f"⚠️ Error mostrando resumen: {e}")

    def get_next_scheduled_reports(self, limit=5):
        """Obtiene información de los próximos reportes programados"""
        if not self.profile_scheduler:
            return []

        try:
            return self.profile_scheduler.get_next_scheduled_executions(limit)
        except Exception as e:
            print(f"Error obteniendo próximos reportes programados: {e}")
            return []

    def get_report_execution_history(self, limit=10):
        """Obtiene historial de ejecuciones de reportes"""
        if not self.profile_scheduler:
            return []

        try:
            return self.profile_scheduler.get_execution_history(limit)
        except Exception as e:
            print(f"Error obteniendo historial de reportes: {e}")
            return []