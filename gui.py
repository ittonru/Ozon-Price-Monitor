import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import threading
import time
from datetime import datetime, timedelta
import requests
import os
import sys
import pystray
from PIL import Image, ImageDraw

from settings_dialog import SettingsDialog
from ozon_price_monitor import OzonPriceMonitor
import config

class OzonMonitorApp(tk.Tk):
    def __init__(self):
        super().__init__()

        # Configure window
        self.title("Ozon Price Monitor")
        self.geometry("600x400")
        self.minsize(500, 300)

        # Set application icon
        self.set_app_icon()

        # Load config
        self.app_config = config.load_config()

        # Create monitor instance
        self.monitor = OzonPriceMonitor()
        self.monitor.set_update_callback(self.update_status)

        # Timer variables
        self.timer_thread = None
        self.next_run_time = None

        # Create UI
        self.create_menu()
        self.create_main_frame()

        # Setup system tray icon
        self.setup_tray_icon()

        # Handle window close event
        self.protocol("WM_DELETE_WINDOW", self.on_close)

        # Check for auto-start
        if self.app_config["auto_start"]:
            self.after(1000, self.start_monitoring)

    def set_app_icon(self):
        """Set application icon for window and taskbar"""
        try:
            # Determine the base path for the icon
            if getattr(sys, 'frozen', False):
                # If the application is run as a bundle (pyinstaller)
                base_path = sys._MEIPASS
            else:
                # If running in a normal Python environment
                base_path = os.path.dirname(os.path.abspath(__file__))

            # Choose icon based on platform
            if sys.platform.startswith('win'):
                icon_path = os.path.join(base_path, "ozon_monitor_icon.ico")
                if os.path.exists(icon_path):
                    self.iconbitmap(icon_path)
            else:
                icon_path = os.path.join(base_path, "ozon_monitor_icon.png")
                if os.path.exists(icon_path):
                    icon = tk.PhotoImage(file=icon_path)
                    self.iconphoto(True, icon)
                else:
                    print(f"Icon file not found: {icon_path}")
        except Exception as e:
            print(f"Error setting application icon: {str(e)}")

    def create_tray_icon_image(self, size=(64, 64)):
        """Create a proper tray icon image that works well in KDE"""
        try:
            # Determine icon path
            if getattr(sys, 'frozen', False):
                base_path = sys._MEIPASS
            else:
                base_path = os.path.dirname(os.path.abspath(__file__))

            icon_path = os.path.join(base_path, "ozon_monitor_icon.png")

            if os.path.exists(icon_path):
                # Open and resize the image to ensure it displays correctly
                image = Image.open(icon_path)
                image = image.resize(size, Image.LANCZOS)

                # For KDE, sometimes a simple image works better
                return image
            else:
                # Create a fallback icon if the image file is not found
                image = Image.new('RGBA', size, color=(0, 0, 0, 0))
                draw = ImageDraw.Draw(image)
                draw.ellipse((0, 0, size[0], size[1]), fill=(0, 120, 212))
                draw.text((size[0]//4, size[1]//4), "OPM", fill=(255, 255, 255))
                return image
        except Exception as e:
            print(f"Error creating tray icon image: {str(e)}")
            # Return a very basic fallback icon
            image = Image.new('RGBA', size, color=(0, 120, 212))
            return image

    def setup_tray_icon(self):
        """Setup system tray icon"""
        try:
            # Create tray icon with a properly sized image
            self.tray_icon_image = self.create_tray_icon_image()
            self.tray_icon = pystray.Icon("ozon_monitor")
            self.tray_icon.icon = self.tray_icon_image
            self.tray_icon.title = "Ozon Price Monitor"

            # Create tray menu with simpler structure for better KDE compatibility
            self.tray_icon.menu = pystray.Menu(
                pystray.MenuItem("Показать окно", self.show_window_from_tray),
                pystray.MenuItem("Запустить", self.start_monitoring_from_tray),
                pystray.MenuItem("Остановить", self.stop_monitoring_from_tray),
                pystray.MenuItem("Выход", self.quit_app)
            )

            # Start tray icon in a separate thread
            threading.Thread(target=self.run_tray_icon, daemon=True).start()
        except Exception as e:
            print(f"Error setting up tray icon: {str(e)}")

    def run_tray_icon(self):
        """Run the tray icon with error handling"""
        try:
            self.tray_icon.run()
        except Exception as e:
            print(f"Error running tray icon: {str(e)}")

    def create_menu(self):
        """Create application menu"""
        menubar = tk.Menu(self)

        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Настройки", command=self.open_settings)
        file_menu.add_separator()
        file_menu.add_command(label="Выход", command=self.quit_app)
        menubar.add_cascade(label="Файл", menu=file_menu)

        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        help_menu.add_command(label="О программе", command=self.show_about)
        menubar.add_cascade(label="Справка", menu=help_menu)

        self.config(menu=menubar)

    def create_main_frame(self):
        """Create main application frame"""
        main_frame = ttk.Frame(self, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Control frame (top)
        control_frame = ttk.Frame(main_frame)
        control_frame.pack(fill=tk.X, pady=(0, 10))

        # Start/Stop button
        self.start_button_text = tk.StringVar(value="Запустить мониторинг")
        self.start_button = ttk.Button(
            control_frame,
            textvariable=self.start_button_text,
            command=self.toggle_monitoring,
            width=20
        )
        self.start_button.pack(side=tk.LEFT, padx=5)

        # Run once button
        self.run_once_button = ttk.Button(
            control_frame,
            text="Проверить сейчас",
            command=self.run_once,
            width=20
        )
        self.run_once_button.pack(side=tk.LEFT, padx=5)

        # Timer status
        timer_frame = ttk.LabelFrame(main_frame, text="Статус таймера")
        timer_frame.pack(fill=tk.X, pady=(0, 10))

        self.timer_status_var = tk.StringVar(value="Таймер не запущен")
        ttk.Label(timer_frame, textvariable=self.timer_status_var, padding=5).pack(fill=tk.X)

        # Results frame
        results_frame = ttk.LabelFrame(main_frame, text="Результаты последней проверки")
        results_frame.pack(fill=tk.BOTH, expand=True)

        self.results_text = scrolledtext.ScrolledText(results_frame, wrap=tk.WORD, height=10)
        self.results_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.results_text.insert(tk.END, "Мониторинг не запущен")
        self.results_text.config(state=tk.DISABLED)

        # Status bar
        self.status_var = tk.StringVar(value="Готов к работе")
        status_bar = ttk.Label(self, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    def open_settings(self):
        """Open settings dialog"""
        SettingsDialog(self, callback=self.reload_config)

    def reload_config(self):
        """Reload configuration"""
        self.app_config = config.load_config()
        self.monitor.update_config()
        self.status_var.set("Настройки обновлены")

    def show_about(self):
        """Show about dialog"""
        messagebox.showinfo(
            "О программе",
            "Ozon Price Monitor\n\n"
            "Программа для мониторинга цен товаров на Ozon\n"
            "и отправки уведомлений о расхождениях в Telegram."
        )

    def toggle_monitoring(self):
        """Toggle monitoring on/off"""
        if self.timer_thread and self.timer_thread.is_alive():
            self.stop_monitoring()
        else:
            self.start_monitoring()

    def start_monitoring(self):
        """Start continuous monitoring"""
        # Check if thread is already running
        if self.timer_thread and self.timer_thread.is_alive():
            return

        # Update UI
        self.start_button_text.set("Остановить мониторинг")
        self.status_var.set("Мониторинг запущен")

        # Start monitor
        self.monitor.running = True

        # Start timer thread
        self.timer_thread = threading.Thread(target=self.timer_worker, daemon=True)
        self.timer_thread.start()

        # Run immediately
        self.run_once()

    def stop_monitoring(self):
        """Stop continuous monitoring"""
        # Update UI
        self.start_button_text.set("Запустить мониторинг")
        self.status_var.set("Мониторинг остановлен")
        self.timer_status_var.set("Таймер не запущен")

        # Stop monitor
        self.monitor.running = False

        # Thread will terminate on next iteration

    def run_once(self):
        """Run monitoring once"""
        # Disable buttons during check
        self.start_button.config(state=tk.DISABLED)
        self.run_once_button.config(state=tk.DISABLED)
        self.status_var.set("Выполняется проверка...")

        # Run in separate thread to avoid freezing UI
        threading.Thread(target=self._run_once_thread, daemon=True).start()

    def _run_once_thread(self):
        """Thread function for running monitoring once"""
        try:
            self.monitor.run_once()
        finally:
            # Re-enable buttons
            self.after(0, lambda: self.start_button.config(state=tk.NORMAL))
            self.after(0, lambda: self.run_once_button.config(state=tk.NORMAL))
            self.after(0, lambda: self.status_var.set("Проверка завершена"))

    def timer_worker(self):
        """Timer worker thread function"""
        interval_minutes = self.app_config["timer_interval"]

        while self.monitor.running:
            # Calculate next run time
            self.next_run_time = datetime.now() + timedelta(minutes=interval_minutes)

            # Wait until next run time or until stopped
            while datetime.now() < self.next_run_time and self.monitor.running:
                # Update timer status
                remaining = self.next_run_time - datetime.now()
                remaining_str = str(timedelta(seconds=int(remaining.total_seconds())))
                status_text = f"Следующая проверка через: {remaining_str}"
                self.after(0, lambda t=status_text: self.timer_status_var.set(t))

                # Sleep for a short time to avoid high CPU usage
                time.sleep(1)

            # Run monitoring if still running
            if self.monitor.running:
                self.after(0, self.run_once)

    def update_status(self):
        """Update status display with latest results"""
        # Update results text
        self.results_text.config(state=tk.NORMAL)
        self.results_text.delete(1.0, tk.END)
        self.results_text.insert(tk.END, self.monitor.last_result)
        self.results_text.config(state=tk.DISABLED)

    def show_window_from_tray(self, icon=None, item=None):
        """Show the window from tray with extra steps for KDE"""
        # For KDE, we need to ensure the window is properly shown
        self.after(0, self._show_window_on_main_thread)

    def _show_window_on_main_thread(self):
        """Show window on main thread to avoid issues in KDE"""
        self.deiconify()
        self.lift()
        self.focus_force()
        self.update()  # Force update to ensure window is shown

    def hide_window(self):
        """Hide the window to tray"""
        self.withdraw()

    def start_monitoring_from_tray(self, icon=None, item=None):
        """Start monitoring from tray icon"""
        if not self.monitor.running:
            # Start on main thread to avoid issues
            self.after(0, self._start_monitoring_on_main_thread)

    def _start_monitoring_on_main_thread(self):
        """Start monitoring on main thread"""
        self.start_monitoring()
        self._show_window_on_main_thread()

    def stop_monitoring_from_tray(self, icon=None, item=None):
        """Stop monitoring from tray icon"""
        if self.monitor.running:
            # Stop on main thread to avoid issues
            self.after(0, self.stop_monitoring)

    def quit_app(self, icon=None, item=None):
        """Quit application from tray"""
        try:
            # Schedule quit on main thread to avoid threading issues
            self.after(0, self._quit_app_on_main_thread)
        except Exception as e:
            print(f"Error during application exit: {str(e)}")
            # Force exit as a last resort
            import os
            os._exit(1)

    def _quit_app_on_main_thread(self):
        """Quit application on main thread"""
        try:
            # Stop monitoring if running
            if self.monitor.running:
                self.stop_monitoring()

            # Stop tray icon
            if hasattr(self, 'tray_icon') and self.tray_icon:
                try:
                    # Schedule tray icon stop in a separate thread
                    threading.Thread(target=self._stop_tray_icon, daemon=True).start()
                except Exception as e:
                    print(f"Error stopping tray icon: {str(e)}")

            # Destroy main window
            self.destroy()

            # Force exit to ensure all threads are terminated
            self.after(100, self._force_exit)
        except Exception as e:
            print(f"Error during application exit: {str(e)}")
            # Force exit as a last resort
            self._force_exit()

    def _stop_tray_icon(self):
        """Stop tray icon in a separate thread"""
        try:
            self.tray_icon.stop()
        except Exception as e:
            print(f"Error stopping tray icon: {str(e)}")

    def _force_exit(self):
        """Force exit the application"""
        import os
        os._exit(0)

    def on_close(self):
        """Handle window close event"""
        # Ask user if they want to minimize to tray or exit
        response = messagebox.askyesnocancel(
            "Закрытие программы",
            "Вы хотите свернуть программу в трей?\n\n"
            "Да - свернуть в трей\n"
            "Нет - полностью закрыть программу\n"
            "Отмена - отменить действие",
            icon=messagebox.QUESTION
        )

        if response is None:  # Cancel was pressed
            return
        elif response:  # Yes was pressed - minimize to tray
            self.hide_window()
        else:  # No was pressed - exit application
            self.quit_app()

if __name__ == "__main__":
    app = OzonMonitorApp()
    app.mainloop()
