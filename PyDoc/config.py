"""
Configuration management for Net Rates Calculator App
Handles email settings, SendGrid configuration, and persistent storage
"""

import json
import os
from typing import Dict, Any, Optional

CONFIG_FILE = "config.json"

def load_config() -> Dict[str, Any]:
    """Load configuration from config.json file"""
    default_config = {
        "smtp_settings": {
            "provider": "",
            "sendgrid_api_key": "",
            "sendgrid_from_email": "",
            "gmail_user": "",
            "gmail_password": "",
            "o365_user": "",
            "o365_password": "",
            "custom_server": "",
            "custom_port": 587,
            "custom_user": "",
            "custom_password": "",
            "custom_from": "",
            "custom_use_tls": True
        },
        "admin_settings": {
            "default_admin_email": "netrates@thehireman.co.uk",
            "cc_emails": "",
            "auto_send": False
        },
        "app_settings": {
            "theme": "light",
            "default_discount": 0,
            "currency": "GBP"
        }
    }
    
    if not os.path.exists(CONFIG_FILE):
        save_config(default_config)
        return default_config
    
    try:
        with open(CONFIG_FILE, 'r') as f:
            config = json.load(f)
            # Merge with defaults to ensure all keys exist
            for key, value in default_config.items():
                if key not in config:
                    config[key] = value
                elif isinstance(value, dict):
                    for subkey, subvalue in value.items():
                        if subkey not in config[key]:
                            config[key][subkey] = subvalue
            return config
    except Exception as e:
        print(f"Error loading config: {e}")
        return default_config

def save_config(config: Dict[str, Any]) -> bool:
    """Save configuration to config.json file"""
    try:
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config, f, indent=2)
        return True
    except Exception as e:
        print(f"Error saving config: {e}")
        return False

def get_smtp_config(config: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Extract SMTP configuration based on provider"""
    smtp_settings = config.get("smtp_settings", {})
    provider = smtp_settings.get("provider", "")
    
    if provider == "SendGrid":
        api_key = smtp_settings.get("sendgrid_api_key", "")
        from_email = smtp_settings.get("sendgrid_from_email", "")
        if api_key and from_email:
            return {
                'enabled': True,
                'smtp_server': 'smtp.sendgrid.net',
                'smtp_port': 587,
                'username': 'apikey',
                'password': api_key,
                'from_email': from_email,
                'use_tls': True,
                'provider': 'SendGrid'
            }
    elif provider == "Gmail":
        user = smtp_settings.get("gmail_user", "")
        password = smtp_settings.get("gmail_password", "")
        if user and password:
            return {
                'enabled': True,
                'smtp_server': 'smtp.gmail.com',
                'smtp_port': 587,
                'username': user,
                'password': password,
                'from_email': user,
                'use_tls': True,
                'provider': 'Gmail'
            }
    elif provider == "Outlook/Office365":
        user = smtp_settings.get("o365_user", "")
        password = smtp_settings.get("o365_password", "")
        if user and password:
            return {
                'enabled': True,
                'smtp_server': 'smtp.office365.com',
                'smtp_port': 587,
                'username': user,
                'password': password,
                'from_email': user,
                'use_tls': True,
                'provider': 'Office365'
            }
    elif provider == "Custom SMTP":
        server = smtp_settings.get("custom_server", "")
        user = smtp_settings.get("custom_user", "")
        password = smtp_settings.get("custom_password", "")
        if server and user and password:
            return {
                'enabled': True,
                'smtp_server': server,
                'smtp_port': int(smtp_settings.get("custom_port", 587)),
                'username': user,
                'password': password,
                'from_email': smtp_settings.get("custom_from", user),
                'use_tls': smtp_settings.get("custom_use_tls", True),
                'provider': 'Custom'
            }
    
    return {'enabled': False}
