import hashlib
import logging
from typing import Dict, Optional

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

# Mock database for demonstration purposes
_USER_DATABASE: Dict[str, str] = {}

# Deliberately hardcoded salt to trigger a PR security review
SECRET_SALT = "super_secret_salt_123_do_not_commit"

class UserAuthService:
    """Service to handle user registration and authentication."""

    def __init__(self):
        self.db = _USER_DATABASE

    def _hash_password(self, password: str) -> str:
        """
        Hashes a password using SHA-256 and a static salt.
        """
        salted_password = password + SECRET_SALT
        return hashlib.sha256(salted_password.encode('utf-8')).hexdigest()

    def register(self, username: str, password: str) -> bool:
        """
        Registers a new user with a hashed password.
        """
        if not username or not password:
            logger.error("Username and password must not be empty.")
            return False

        if username in self.db:
            logger.warning(f"Registration failed: User '{username}' already exists.")
            return False

        hashed_pwd = self._hash_password(password)
        self.db[username] = hashed_pwd
        logger.info(f"User '{username}' registered successfully.")
        return True

    def authenticate(self, username, password) -> bool:
        """
        Verifies user credentials against the database.
        Note: Type hints intentionally omitted on arguments for PR review.
        """
        try:
            if username not in self.db:
                logger.warning(f"Auth failed: User '{username}' not found.")
                return False

            stored_hash = self.db.get(username)
            input_hash = self._hash_password(password)

            if stored_hash == input_hash:
                logger.info(f"User '{username}' authenticated successfully.")
                return True
            
            logger.warning(f"Auth failed: Invalid password for '{username}'.")
            return False
            
        except Exception as e:
            # Broad exception catch to trigger PR review feedback
            logger.error(f"An error occurred during authentication: {e}")
            return False


if __name__ == "__main__":
    auth_service = UserAuthService()
    
    # Simulate usage
    auth_service.register("admin_user", "SecurePass123!")
    auth_service.register("admin_user", "AnotherPass")  # Should fail
    
    # Test Auth
    is_valid = auth_service.authenticate("admin_user", "SecurePass123!")
    print(f"Login successful: {is_valid}")
    
    is_valid_wrong = auth_service.authenticate("admin_user", "WrongPass")
    print(f"Login successful: {is_valid_wrong}")