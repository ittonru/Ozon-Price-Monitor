import requests
import json
import logging
import time
from datetime import datetime
import config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("price_monitor.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class OzonPriceMonitor:
    def __init__(self):
        self.config = config.load_config()
        self.running = False
        self.last_result = "Мониторинг не запущен"
        self.update_callback = None

    def set_update_callback(self, callback):
        """Set callback function to update GUI"""
        self.update_callback = callback

    def update_config(self):
        """Reload configuration"""
        self.config = config.load_config()
        logger.info("Configuration updated")

    def send_telegram_message(self, message):
        """Send a message to Telegram channel"""
        if not self.config["telegram_bot_token"] or not self.config["telegram_channel"]:
            logger.warning("Telegram credentials not configured")
            return False

        telegram_api_url = f"https://api.telegram.org/bot{self.config['telegram_bot_token']}/sendMessage"
        payload = {
            "chat_id": self.config["telegram_channel"],
            "text": message,
            "parse_mode": "HTML"
        }

        try:
            response = requests.post(telegram_api_url, json=payload)
            if response.status_code != 200:
                logger.error(f"Failed to send Telegram message: {response.text}")
                # If message is too long, split it and try again
                if "message is too long" in response.text.lower():
                    logger.info("Message too long, splitting and retrying...")
                    messages = self.split_long_message(message)
                    for msg in messages:
                        time.sleep(1)  # Avoid hitting rate limits
                        self.send_telegram_message(msg)
                return False
            else:
                logger.info("Telegram message sent successfully")
                return True
        except Exception as e:
            logger.error(f"Error sending Telegram message: {str(e)}")
            return False

    def split_long_message(self, message, max_length=4000):
        """Split a long message into smaller chunks"""
        if len(message) <= max_length:
            return [message]

        # Find a good splitting point (newline)
        split_point = message[:max_length].rfind('\n')
        if split_point == -1:  # No newline found, force split
            split_point = max_length

        return [message[:split_point]] + self.split_long_message(message[split_point:], max_length)

    def get_ozon_prices(self):
        """Get prices from Ozon API"""
        if not self.config["client_id"] or not self.config["api_key"]:
            logger.error("Ozon API credentials not configured")
            return None

        # API endpoint
        url = "https://api-seller.ozon.ru/v5/product/info/prices"

        # Headers
        headers = {
            "Client-Id": self.config["client_id"],
            "Api-Key": self.config["api_key"],
            "Content-Type": "application/json"
        }

        # Request payload
        payload = {
            "cursor": "",
            "filter": {
                "visibility": self.config["visibility"]
            },
            "limit": 100
        }

        try:
            # Make the request
            response = requests.post(url, headers=headers, json=payload)
            logger.info(f"API Status Code: {response.status_code}")

            if response.status_code == 200:
                return response.json()
            else:
                error_msg = f"API Error: {response.text}"
                logger.error(error_msg)
                self.last_result = error_msg
                if self.update_callback:
                    self.update_callback()
                return None
        except Exception as e:
            error_msg = f"Error making API request: {str(e)}"
            logger.error(error_msg)
            self.last_result = error_msg
            if self.update_callback:
                self.update_callback()
            return None

    def analyze_prices(self, data):
        """Analyze prices and send alerts for discrepancies"""
        if not data or "items" not in data:
            logger.error("No valid data to analyze")
            self.last_result = "Ошибка: нет данных для анализа"
            if self.update_callback:
                self.update_callback()
            return

        discrepancies_found = False
        current_time = datetime.now().strftime("%d.%m.%Y %H:%M:%S")
        message_parts = [f"<b>⚠️ Отчет о расхождениях в ценах товаров</b>\n<i>Время проверки: {current_time}</i>\n"]

        for item in data.get("items", []):
            offer_id = item.get("offer_id", "")
            product_id = item.get("product_id", "")

            # Get price data
            price_data = item.get("price", {})
            marketing_seller_price = price_data.get("marketing_seller_price", 0)

            # Only check prices that are enabled in config
            prices = {
                "Цена (marketing_seller_price)": marketing_seller_price
            }

            if self.config["check_min_price"]:
                prices["Минимальная цена (min_price)"] = price_data.get("min_price", 0)

            if self.config["check_marketing_price"]:
                prices["Цена Озон (marketing_price)"] = price_data.get("marketing_price", 0)

            if self.config["check_price"]:
                prices["Цена Озон 2 (price)"] = price_data.get("price", 0)

            # Remove zero values
            prices = {k: v for k, v in prices.items() if v != 0}

            # Check if all non-zero prices are equal
            if len(set(prices.values())) > 1:
                discrepancies_found = True

                # Create message for this product
                product_msg = f"<b>Товар: {offer_id}</b> (ID: {product_id})\n"
                for price_name, price_value in prices.items():
                    product_msg += f"- {price_name}: {price_value} руб.\n"

                # Add product URL
                product_url = f"https://seller.ozon.ru/app/products/card/{product_id}"
                product_msg += f"<a href='{product_url}'>Ссылка на товар в личном кабинете</a>\n"

                message_parts.append(product_msg)

        # Send message if discrepancies found
        if discrepancies_found:
            message_parts.append("\n<i>Рекомендуется проверить настройки цен для указанных товаров.</i>")
            full_message = "\n".join(message_parts)
            self.send_telegram_message(full_message)
            result_msg = f"Найдены расхождения в ценах. Отчет отправлен в Telegram ({current_time})"
            logger.info("Price discrepancies found and notification sent")
        else:
            result_msg = f"Расхождений в ценах не обнаружено ({current_time})"
            logger.info("No price discrepancies found")

        self.last_result = result_msg
        if self.update_callback:
            self.update_callback()

    def run_once(self):
        """Run price monitoring once"""
        logger.info("Starting Ozon price monitoring")

        try:
            # Get data from Ozon API
            data = self.get_ozon_prices()

            # Analyze prices and send alerts if needed
            if data:
                self.analyze_prices(data)

            logger.info("Price monitoring completed")
        except Exception as e:
            error_msg = f"Critical error in price monitoring: {str(e)}"
            logger.error(error_msg)
            self.send_telegram_message(f"<b>❌ Ошибка мониторинга цен</b>\n\n{error_msg}")
            self.last_result = f"Ошибка: {str(e)}"
            if self.update_callback:
                self.update_callback()

    def start_monitoring(self):
        """Start continuous monitoring"""
        self.running = True
        logger.info("Continuous monitoring started")

        # Run immediately once
        self.run_once()

        # Update status
        self.last_result = "Мониторинг запущен"
        if self.update_callback:
            self.update_callback()

    def stop_monitoring(self):
        """Stop continuous monitoring"""
        self.running = False
        logger.info("Continuous monitoring stopped")

        # Update status
        self.last_result = "Мониторинг остановлен"
        if self.update_callback:
            self.update_callback()
