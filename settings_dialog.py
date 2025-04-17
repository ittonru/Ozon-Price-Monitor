import tkinter as tk
from tkinter import ttk, messagebox
import requests
import config

class SettingsDialog(tk.Toplevel):
    def __init__(self, parent, callback=None):
        super().__init__(parent)
        self.parent = parent
        self.callback = callback
        self.title("Настройки")
        self.geometry("500x600")
        self.resizable(False, False)

        # Make dialog modal
        self.transient(parent)  # Set to be on top of the parent window
        self.grab_set()         # Make this window modal

        # Center the dialog on the parent window
        self.center_on_parent()

        # Load current config
        self.config = config.load_config()

        # Create notebook (tabs)
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Create tabs
        self.create_api_tab()
        self.create_telegram_tab()
        self.create_monitoring_tab()
        self.create_timer_tab()

        # Create buttons
        self.create_buttons()

        # Wait for window close
        self.protocol("WM_DELETE_WINDOW", self.on_close)
        self.wait_visibility()  # Wait until window is visible
        self.focus_set()        # Set focus to this window

    def center_on_parent(self):
        """Center this window on the parent window"""
        parent = self.parent

        # Get parent geometry
        parent_x = parent.winfo_rootx()
        parent_y = parent.winfo_rooty()
        parent_width = parent.winfo_width()
        parent_height = parent.winfo_height()

        # Calculate position
        width = 500
        height = 600
        x = parent_x + (parent_width - width) // 2
        y = parent_y + (parent_height - height) // 2

        # Set geometry
        self.geometry(f"{width}x{height}+{x}+{y}")

    def create_api_tab(self):
        """Create API settings tab"""
        api_frame = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(api_frame, text="API Озон")

        # Client ID
        ttk.Label(api_frame, text="Client ID:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.client_id_var = tk.StringVar(value=self.config["client_id"])
        ttk.Entry(api_frame, textvariable=self.client_id_var, width=40).grid(row=0, column=1, sticky=tk.W, pady=5)

        # API Key
        ttk.Label(api_frame, text="API Key:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.api_key_var = tk.StringVar(value=self.config["api_key"])
        ttk.Entry(api_frame, textvariable=self.api_key_var, width=40, show="*").grid(row=1, column=1, sticky=tk.W, pady=5)

        # Visibility
        ttk.Label(api_frame, text="Видимость товаров:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.visibility_var = tk.StringVar(value=self.config["visibility"])
        visibility_combo = ttk.Combobox(api_frame, textvariable=self.visibility_var, width=38)
        visibility_combo['values'] = ('ALL', 'IN_SALE')
        visibility_combo['state'] = 'readonly'
        visibility_combo.grid(row=2, column=1, sticky=tk.W, pady=5)

        # Help text
        help_text = "ALL - контролировать все товары\nIN_SALE - контролировать только товары на витрине"
        ttk.Label(api_frame, text=help_text, foreground="gray").grid(row=3, column=0, columnspan=2, sticky=tk.W, pady=5)

    def create_telegram_tab(self):
        """Create Telegram settings tab"""
        telegram_frame = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(telegram_frame, text="Telegram")

        # Bot Token
        ttk.Label(telegram_frame, text="Bot Token:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.bot_token_var = tk.StringVar(value=self.config["telegram_bot_token"])
        ttk.Entry(telegram_frame, textvariable=self.bot_token_var, width=40, show="*").grid(row=0, column=1, sticky=tk.W, pady=5)

        # Channel
        ttk.Label(telegram_frame, text="Channel ID:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.channel_var = tk.StringVar(value=self.config["telegram_channel"])
        ttk.Entry(telegram_frame, textvariable=self.channel_var, width=40).grid(row=1, column=1, sticky=tk.W, pady=5)

        # Help text
        help_text = "Укажите ID канала с @ для публичных каналов\nНапример: @my_channel"
        ttk.Label(telegram_frame, text=help_text, foreground="gray").grid(row=2, column=0, columnspan=2, sticky=tk.W, pady=5)

        # Test button
        ttk.Button(telegram_frame, text="Проверить соединение", command=self.test_telegram).grid(row=3, column=0, columnspan=2, pady=10)

    def create_monitoring_tab(self):
        """Create monitoring settings tab"""
        monitoring_frame = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(monitoring_frame, text="Мониторинг цен")

        # Price monitoring options
        ttk.Label(monitoring_frame, text="Контролируемые цены:").grid(row=0, column=0, columnspan=2, sticky=tk.W, pady=5)

        # marketing_seller_price is always checked and disabled
        ttk.Label(monitoring_frame, text="Цена продавца (marketing_seller_price):").grid(row=1, column=0, sticky=tk.W, pady=5)
        ttk.Checkbutton(monitoring_frame, state="disabled", variable=tk.BooleanVar(value=True)).grid(row=1, column=1, sticky=tk.W, pady=5)

        # min_price
        ttk.Label(monitoring_frame, text="Минимальная цена (min_price):").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.check_min_price_var = tk.BooleanVar(value=self.config["check_min_price"])
        ttk.Checkbutton(monitoring_frame, variable=self.check_min_price_var).grid(row=2, column=1, sticky=tk.W, pady=5)

        # marketing_price
        ttk.Label(monitoring_frame, text="Цена Озон (marketing_price):").grid(row=3, column=0, sticky=tk.W, pady=5)
        self.check_marketing_price_var = tk.BooleanVar(value=self.config["check_marketing_price"])
        ttk.Checkbutton(monitoring_frame, variable=self.check_marketing_price_var).grid(row=3, column=1, sticky=tk.W, pady=5)

        # price
        ttk.Label(monitoring_frame, text="Цена Озон 2 (price):").grid(row=4, column=0, sticky=tk.W, pady=5)
        self.check_price_var = tk.BooleanVar(value=self.config["check_price"])
        ttk.Checkbutton(monitoring_frame, variable=self.check_price_var).grid(row=4, column=1, sticky=tk.W, pady=5)

        # Help text
        help_text = "Выберите цены, которые нужно контролировать.\nЦена продавца всегда контролируется."
        ttk.Label(monitoring_frame, text=help_text, foreground="gray").grid(row=5, column=0, columnspan=2, sticky=tk.W, pady=5)

    def create_timer_tab(self):
        """Create timer settings tab"""
        timer_frame = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(timer_frame, text="Таймер")

        # Timer interval
        ttk.Label(timer_frame, text="Интервал проверки (минуты):").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.timer_interval_var = tk.IntVar(value=self.config["timer_interval"])
        timer_spin = ttk.Spinbox(timer_frame, from_=1, to=1440, textvariable=self.timer_interval_var, width=10)
        timer_spin.grid(row=0, column=1, sticky=tk.W, pady=5)

        # Auto start
        ttk.Label(timer_frame, text="Автозапуск при старте программы:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.auto_start_var = tk.BooleanVar(value=self.config["auto_start"])
        ttk.Checkbutton(timer_frame, variable=self.auto_start_var).grid(row=1, column=1, sticky=tk.W, pady=5)

        # Help text
        help_text = "Укажите интервал проверки цен в минутах.\nМинимум: 1 минута, максимум: 1440 минут (24 часа)"
        ttk.Label(timer_frame, text=help_text, foreground="gray").grid(row=2, column=0, columnspan=2, sticky=tk.W, pady=5)

    def create_buttons(self):
        """Create dialog buttons"""
        button_frame = ttk.Frame(self)
        button_frame.pack(fill=tk.X, padx=10, pady=10)

        ttk.Button(button_frame, text="Сохранить", command=self.save_settings).pack(side=tk.RIGHT, padx=5)
        ttk.Button(button_frame, text="Отмена", command=self.on_close).pack(side=tk.RIGHT, padx=5)

    def test_telegram(self):
        """Test Telegram connection"""
        bot_token = self.bot_token_var.get()
        channel = self.channel_var.get()

        if not bot_token or not channel:
            messagebox.showerror("Ошибка", "Укажите Bot Token и Channel ID")
            return

        try:
            # Create test message
            test_message = "<b>Тестовое сообщение</b>\n\nПроверка соединения с Telegram."

            # Send test message
            telegram_api_url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
            payload = {
                "chat_id": channel,
                "text": test_message,
                "parse_mode": "HTML"
            }

            response = requests.post(telegram_api_url, json=payload)

            if response.status_code == 200:
                messagebox.showinfo("Успех", "Тестовое сообщение успешно отправлено!")
            else:
                messagebox.showerror("Ошибка", f"Не удалось отправить сообщение: {response.text}")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка при отправке сообщения: {str(e)}")

    def save_settings(self):
        """Save settings to config file"""
        # Update config with new values
        self.config["client_id"] = self.client_id_var.get()
        self.config["api_key"] = self.api_key_var.get()
        self.config["visibility"] = self.visibility_var.get()

        self.config["telegram_bot_token"] = self.bot_token_var.get()
        self.config["telegram_channel"] = self.channel_var.get()

        self.config["check_min_price"] = self.check_min_price_var.get()
        self.config["check_marketing_price"] = self.check_marketing_price_var.get()
        self.config["check_price"] = self.check_price_var.get()

        self.config["timer_interval"] = self.timer_interval_var.get()
        self.config["auto_start"] = self.auto_start_var.get()

        # Save config
        if config.save_config(self.config):
            messagebox.showinfo("Успех", "Настройки успешно сохранены")
            # Call callback if provided
            if self.callback:
                self.callback()
            self.on_close()
        else:
            messagebox.showerror("Ошибка", "Не удалось сохранить настройки")

    def on_close(self):
        """Handle dialog close"""
        self.grab_release()  # Release the modal state
        self.destroy()       # Close the window
