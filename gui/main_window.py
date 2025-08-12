# main_window.py
# Ubicación: /syncro_bot/gui/main_window.py
"""
Ventana principal de la interfaz gráfica de Syncro Bot.
Gestiona la configuración de la ventana, la creación del sistema de pestañas,
el manejo correcto del cierre de la aplicación y las conexiones entre pestañas
para integración completa del sistema de registro y envío de reportes.
"""

from tkinter import ttk
import time
from .tabs.automation_tab import AutomationTab
from .tabs.email_tab import EmailTab
from .tabs.profiles_tab import ProfilesTab
from .tabs.registro_tab import RegistroTab


class MainWindow:
    def __init__(self, root):
        self.root = root
        self.is_closing = False
        self.setup_window()
        self.create_tabs()
        self.setup_integrations()  # ===== NUEVA FUNCIÓN =====
        self.setup_close_handler()

    def setup_window(self):
        """Configurar las propiedades básicas de la ventana"""
        self.root.title("Syncro Bot")
        self.root.geometry("1100x600")
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

        # 2. Pestaña de Perfiles (programación automática)
        print("  → Creando ProfilesTab...")
        self.profiles_tab = ProfilesTab(self.notebook)

        # 3. Pestaña de Email (configuración de envío)
        print("  → Creando EmailTab...")
        self.email_tab = EmailTab(self.notebook)

        # 4. Pestaña de Registro (logging y reportes)
        print("  → Creando RegistroTab...")
        self.registro_tab = RegistroTab(self.notebook)

        print("✅ Todas las pestañas creadas exitosamente")

    # ===== NUEVA FUNCIÓN DE INTEGRACIÓN =====
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

            # 2. Conectar ProfilesTab con RegistroTab (para logging de ejecuciones automáticas)
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

    # ===== FIN NUEVA FUNCIÓN =====

    # ===== NUEVA FUNCIÓN DE VERIFICACIÓN =====
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

    # ===== FIN NUEVA FUNCIÓN =====

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
            # ===== LIMPIEZA MEJORADA DE PESTAÑAS =====

            # 1. Limpiar pestaña de automatización
            if hasattr(self, 'automation_tab') and self.automation_tab:
                print("  → Limpiando AutomationTab...")
                try:
                    if self.automation_tab.get_automation_status():
                        self.automation_tab.automation_service.pause_automation()
                    self.automation_tab.cleanup()
                    print("    ✅ AutomationTab limpiado")
                except Exception as e:
                    print(f"    ⚠️ Error limpiando AutomationTab: {e}")

            # 2. Limpiar pestaña de perfiles
            if hasattr(self, 'profiles_tab') and self.profiles_tab:
                print("  → Limpiando ProfilesTab...")
                try:
                    # Detener cualquier ejecución en curso
                    if hasattr(self.profiles_tab, 'execution_service'):
                        if self.profiles_tab.execution_service.is_busy():
                            print("    → Deteniendo ejecución de perfil en curso...")

                    if hasattr(self.profiles_tab, 'cleanup'):
                        self.profiles_tab.cleanup()
                    print("    ✅ ProfilesTab limpiado")
                except Exception as e:
                    print(f"    ⚠️ Error limpiando ProfilesTab: {e}")

            # 3. Limpiar pestaña de registro
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

            # 4. Limpiar pestaña de email
            if hasattr(self, 'email_tab') and self.email_tab:
                print("  → Limpiando EmailTab...")
                try:
                    if hasattr(self.email_tab, 'cleanup'):
                        self.email_tab.cleanup()
                    print("    ✅ EmailTab limpiado")
                except Exception as e:
                    print(f"    ⚠️ Error limpiando EmailTab: {e}")

            # ===== FIN LIMPIEZA MEJORADA =====

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

    # ===== MÉTODOS PÚBLICOS MEJORADOS =====
    def get_automation_tab(self):
        """Retorna la instancia de la pestaña de automatización"""
        return self.automation_tab if hasattr(self, 'automation_tab') else None

    def get_profiles_tab(self):
        """Retorna la instancia de la pestaña de perfiles"""
        return self.profiles_tab if hasattr(self, 'profiles_tab') else None

    def get_email_tab(self):
        """Retorna la instancia de la pestaña de email"""
        return self.email_tab if hasattr(self, 'email_tab') else None

    def get_registro_tab(self):
        """Retorna la instancia de la pestaña de registro"""
        return self.registro_tab if hasattr(self, 'registro_tab') else None

    # ===== NUEVOS MÉTODOS DE UTILIDAD =====
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

            return tabs_ready and integrations_ready

        except Exception:
            return False

    def get_system_status(self):
        """Obtiene el estado completo del sistema"""
        try:
            status = {
                'automation_running': False,
                'email_configured': False,
                'active_profiles': 0,
                'total_records': 0,
                'integrations_ready': False
            }

            # Estado de automatización
            if hasattr(self, 'automation_tab') and self.automation_tab:
                status['automation_running'] = self.automation_tab.get_automation_status()

            # Estado de email
            if hasattr(self, 'email_tab') and self.email_tab:
                status['email_configured'] = self.email_tab.is_email_configured()

            # Perfiles activos
            if hasattr(self, 'profiles_tab') and self.profiles_tab:
                active_profiles = self.profiles_tab.get_active_profiles()
                status['active_profiles'] = len(active_profiles)

            # Total de registros
            if hasattr(self, 'registro_tab') and self.registro_tab:
                all_records = self.registro_tab.registry_manager.get_all_records()
                status['total_records'] = len(all_records)

            # Estado de integraciones
            status['integrations_ready'] = self.is_system_ready()

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
            print("\n" + "=" * 60)
            print("🤖 SYNCRO BOT - RESUMEN DEL SISTEMA")
            print("=" * 60)

            status = self.get_system_status()
            if status:
                print(f"🔧 Sistema integrado: {'✅ Sí' if status['integrations_ready'] else '❌ No'}")
                print(f"📧 Email configurado: {'✅ Sí' if status['email_configured'] else '❌ No'}")
                print(f"⚙️ Perfiles activos: {status['active_profiles']}")
                print(f"📊 Registros totales: {status['total_records']}")
                print(f"🤖 Automatización: {'🟢 Activa' if status['automation_running'] else '🟠 Inactiva'}")
            else:
                print("⚠️ No se pudo obtener el estado del sistema")

            print("=" * 60)
            print("✅ Syncro Bot iniciado correctamente")
            print("💡 Utilice las pestañas para configurar y gestionar el sistema")
            print("=" * 60 + "\n")

            # Registrar inicio
            self.log_system_startup()

        except Exception as e:
            print(f"⚠️ Error mostrando resumen: {e}")
    # ===== FIN NUEVOS MÉTODOS =====