"""
WhatsApp Web Controller using Selenium
Handles sending messages, finding contacts, and managing chats
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import time
import logging
from typing import List, Dict, Optional, Tuple

class WhatsAppController:
    def __init__(self, headless=False):
        self.driver = None
        self.wait = None
        self.headless = headless
        self.is_logged_in = False
        
        # Set up logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
    def initialize_driver(self):
        """Initialize Chrome driver with WhatsApp Web optimizations"""
        try:
            # Chrome options for better WhatsApp Web compatibility
            chrome_options = Options()
            if self.headless:
                chrome_options.add_argument('--headless')
            
            # WhatsApp Web specific optimizations
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-blink-features=AutomationControlled')
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            
            # User agent to avoid detection
            chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
            
            # Create driver
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            self.wait = WebDriverWait(self.driver, 30)
            
            # Execute script to avoid detection
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            self.logger.info("Chrome driver initialized successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize driver: {e}")
            return False
    
    def login_to_whatsapp(self):
        """Open WhatsApp Web and wait for user to scan QR code"""
        try:
            if not self.driver:
                if not self.initialize_driver():
                    return False
            if self.driver is None or self.wait is None:
                self.logger.error("Driver or wait not initialized.")
                return False
            # Navigate to WhatsApp Web
            self.driver.get('https://web.whatsapp.com')
            self.logger.info("Navigated to WhatsApp Web")
            # Wait for QR code or chat interface
            print("Please scan the QR code in the browser window...")
            print("Waiting for login... (This may take up to 60 seconds)")
            try:
                # Wait for either QR code or main interface
                self.wait.until(
                    lambda driver: self._is_qr_code_present() or self._is_chat_interface_present()
                )
                # If QR code is present, wait for login
                if self._is_qr_code_present():
                    print("QR Code detected. Please scan it with your phone...")
                    # Wait for chat interface after QR scan
                    self.wait.until(lambda driver: self._is_chat_interface_present())
                self.is_logged_in = True
                self.logger.info("Successfully logged into WhatsApp Web")
                print("✅ Successfully logged into WhatsApp Web!")
                return True
            except Exception as e:
                self.logger.error(f"Login timeout or error: {e}")
                print("❌ Login failed. Please try again.")
                return False
        except Exception as e:
            self.logger.error(f"Failed to login to WhatsApp: {e}")
            return False

    def _is_qr_code_present(self):
        """Check if QR code is present on the page"""
        if self.driver is None:
            return False
        try:
            qr_code = self.driver.find_element(By.XPATH, "//div[@data-testid='qr-code']")
            return qr_code.is_displayed()
        except Exception:
            return False

    def _is_chat_interface_present(self):
        """Check if main chat interface is loaded"""
        if self.driver is None:
            return False
        try:
            # Look for the search box or chat list
            search_box = self.driver.find_element(By.XPATH, "//div[@data-testid='chat-list-search']")
            return search_box.is_displayed()
        except Exception:
            try:
                # Alternative: look for the side panel
                side_panel = self.driver.find_element(By.ID, "side")
                return side_panel.is_displayed()
            except Exception:
                return False

    def send_message(self, contact_name: str, message: str) -> bool:
        """Send a message to a specific contact"""
        if self.driver is None or self.wait is None:
            self.logger.error("Driver or wait not initialized.")
            return False
        try:
            if not self.is_logged_in:
                self.logger.error("Not logged into WhatsApp")
                return False
            # Search for the contact
            if not self._search_contact(contact_name):
                self.logger.error(f"Could not find contact: {contact_name}")
                return False
            # Find the message input box
            message_box = self.wait.until(
                EC.presence_of_element_located((By.XPATH, "//div[@data-testid='conversation-compose-box-input']"))
            )
            # Clear any existing text and send message
            message_box.clear()
            message_box.send_keys(message)
            message_box.send_keys(Keys.ENTER)
            self.logger.info(f"Message sent to {contact_name}: {message}")
            print(f"✅ Message sent to {contact_name}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to send message: {e}")
            print(f"❌ Failed to send message: {e}")
            return False

    def _search_contact(self, contact_name: str) -> bool:
        """Search and select a contact"""
        if self.driver is None or self.wait is None:
            self.logger.error("Driver or wait not initialized.")
            return False
        try:
            # Find search box
            search_box = self.wait.until(
                EC.presence_of_element_located((By.XPATH, "//div[@data-testid='chat-list-search']//div[@contenteditable='true']"))
            )
            # Clear search and enter contact name
            search_box.clear()
            search_box.send_keys(contact_name)
            # Wait a moment for search results
            time.sleep(2)
            # Try to click on the first search result
            try:
                # Look for the contact in search results
                contact_element = self.wait.until(
                    EC.element_to_be_clickable((By.XPATH, f"//span[@title='{contact_name}']"))
                )
                contact_element.click()
                # Wait for chat to load
                time.sleep(2)
                return True
            except Exception:
                # Alternative approach: click the first result
                try:
                    first_result = self.driver.find_element(By.XPATH, "//div[@data-testid='cell-frame-container'][1]")
                    first_result.click()
                    time.sleep(2)
                    return True
                except Exception:
                    return False
        except Exception as e:
            self.logger.error(f"Failed to search contact {contact_name}: {e}")
            return False

    def get_recent_messages(self, count=5) -> List[str]:
        """Get recent messages from current chat"""
        if self.driver is None:
            self.logger.error("Driver not initialized.")
            return []
        try:
            # Find message elements
            messages = self.driver.find_elements(By.XPATH, "//div[@data-testid='conversation-panel-messages']//div[contains(@class, 'message')]")
            recent_messages = []
            for msg in messages[-count:]:
                try:
                    text = msg.find_element(By.XPATH, ".//span[@data-testid='conversation-text'").text
                    recent_messages.append(text)
                except Exception:
                    continue
            return recent_messages
        except Exception as e:
            self.logger.error(f"Failed to get recent messages: {e}")
            return []
    
    def close(self):
        """Close the browser and clean up"""
        if self.driver:
            self.driver.quit()
            self.logger.info("WhatsApp controller closed")

# Test function
def test_whatsapp_controller():
    """Test the WhatsApp controller"""
    controller = WhatsAppController()
    
    print("Testing WhatsApp Controller...")
    
    if controller.login_to_whatsapp():
        print("Login successful!")
        
        # Test sending a message (replace with actual contact name)
        test_contact = input("Enter a contact name to test: ")
        test_message = "Hello! This is a test message from my AI assistant."
        
        if controller.send_message(test_contact, test_message):
            print("Message sent successfully!")
        else:
            print("Failed to send message")
    
    controller.close()

if __name__ == "__main__":
    test_whatsapp_controller()
