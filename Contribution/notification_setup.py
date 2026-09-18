import logging
from typing import List, Dict, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class NotificationProvider:
    """Base interface for notification providers."""
    
    def send(self, recipient: str, message: str) -> bool:
        raise NotImplementedError("Subclasses must implement the send method.")


class EmailNotification(NotificationProvider):
    """Handles email-based notifications."""
    
    def send(self, recipient: str, message: str) -> bool:
        if "@" not in recipient:
            logger.warning(f"Invalid email address provided: {recipient}")
            return False
            
        logger.info(f"Simulating Email sent to {recipient} | Payload: {message}")
        return True


class SMSNotification(NotificationProvider):
    """Handles SMS-based notifications."""
    
    def send(self, recipient: str, message: str) -> bool:
        if not recipient.isdigit():
            logger.warning(f"Invalid phone number provided: {recipient}")
            return False
            
        logger.info(f"Simulating SMS sent to {recipient} | Payload: {message}")
        return True


def setup_notifications(config: Dict[str, Any]) -> List[NotificationProvider]:
    """
    Initializes and returns a list of active notification providers 
    based on the provided configuration dictionary.
    """
    providers = []
    
    if config.get("enable_email", False):
        providers.append(EmailNotification())
        
    if config.get("enable_sms", False):
        providers.append(SMSNotification())
        
    logger.info(f"Successfully initialized {len(providers)} notification provider(s).")
    return providers


if __name__ == "__main__":
    # Sample configuration for local testing
    app_config = {
        "enable_email": True,
        "enable_sms": True,
        "enable_push": False # Feature toggle not yet implemented
    }
    
    active_providers = setup_notifications(app_config)
    
    # Broadcast a test message
    test_user_contact = "user@example.com"
    for provider in active_providers:
        provider.send(test_user_contact, "Your setup is complete.")