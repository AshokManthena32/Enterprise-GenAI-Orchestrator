"""
Azure Key Vault Manager.

This module provides a robust, thread-safe Singleton manager for retrieving secrets
securely from Azure Key Vault using Entra ID (formerly Azure Active Directory) Managed Identities.
"""

import os
import logging
from threading import Lock
from typing import Optional, Dict

from azure.identity import DefaultAzureCredential
from azure.core.exceptions import ClientAuthenticationError, ResourceNotFoundError
from azure.keyvault.secrets import SecretClient

logger = logging.getLogger(__name__)

class KeyVaultManager:
    """
    Singleton class to securely fetch and manage secrets from Azure Key Vault.
    
    Utilizes DefaultAzureCredential for seamless authentication across
    local development and Azure hosted environments (App Service, AKS, VM).
    """
    
    _instance: Optional['KeyVaultManager'] = None
    _lock: Lock = Lock()
    
    def __new__(cls) -> 'KeyVaultManager':
        """
        Ensures only one instance of the KeyVaultManager is created (Singleton pattern).
        """
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(KeyVaultManager, cls).__new__(cls)
                cls._instance._initialize()
        return cls._instance

    def _initialize(self) -> None:
        """
        Initializes the KeyVault client using environment variables.
        """
        self.key_vault_url = os.getenv("AZURE_KEY_VAULT_URL")
        self._secret_cache: Dict[str, str] = {}
        
        if not self.key_vault_url:
            logger.warning("AZURE_KEY_VAULT_URL is not set. KeyVaultManager will not function correctly.")
            self.client = None
            return

        try:
            # DefaultAzureCredential handles authentication via Managed Identity,
            # Environment Variables, Azure CLI, etc.
            self.credential = DefaultAzureCredential()
            self.client = SecretClient(vault_url=self.key_vault_url, credential=self.credential)
            logger.info(f"KeyVaultManager initialized for vault: {self.key_vault_url}")
        except ClientAuthenticationError as e:
            logger.error(f"Failed to authenticate with Azure Key Vault: {e}", exc_info=True)
            self.client = None
        except Exception as e:
            logger.error(f"Unexpected error initializing KeyVaultManager: {e}", exc_info=True)
            self.client = None

    def get_secret(self, secret_name: str, use_cache: bool = True) -> Optional[str]:
        """
        Retrieves a secret from the Azure Key Vault.

        Args:
            secret_name (str): The name of the secret to retrieve.
            use_cache (bool): Whether to use the in-memory cache for the secret.

        Returns:
            Optional[str]: The value of the secret, or None if not found or an error occurred.

        Raises:
            ValueError: If the secret name is invalid.
        """
        if not secret_name or not isinstance(secret_name, str):
            logger.error("Invalid secret name provided.")
            raise ValueError("Secret name must be a non-empty string.")

        if use_cache and secret_name in self._secret_cache:
            logger.debug(f"Retrieved secret '{secret_name}' from local cache.")
            return self._secret_cache[secret_name]

        if not self.client:
            logger.error("KeyVault client is not initialized.")
            return None

        try:
            logger.debug(f"Fetching secret '{secret_name}' from Azure Key Vault...")
            secret = self.client.get_secret(secret_name)
            
            if use_cache:
                self._secret_cache[secret_name] = secret.value
                
            logger.info(f"Successfully retrieved secret '{secret_name}' from Azure Key Vault.")
            return secret.value
            
        except ResourceNotFoundError:
            logger.warning(f"Secret '{secret_name}' not found in Key Vault.")
            return None
        except Exception as e:
            logger.error(f"Error retrieving secret '{secret_name}': {e}", exc_info=True)
            return None
