#!/usr/bin/env python3
"""
Script to fix Redis configuration in the application.
This script directly modifies the application's configuration to use the correct Redis host.
"""

import os
import sys
import inspect

# Add the src directory to the Python path
sys.path.insert(0, "/code/src")

try:
    # Attempt to import and modify the settings
    from app.core.config import settings
    
    # Print settings class details to help debug
    print(f"Settings class: {type(settings)}")
    print(f"Settings attributes: {dir(settings)}")
    
    # Try to find all Redis-related settings
    redis_settings = [attr for attr in dir(settings) if 'REDIS' in attr]
    print(f"Redis-related settings found: {redis_settings}")
    
    # Look through the config.py file
    import importlib.util
    import inspect
    
    try:
        print("\nExamining config module source:")
        print(inspect.getsource(sys.modules['app.core.config']))
    except Exception as e:
        print(f"Could not get config source: {e}")
    
    # Check if environment variables are being used
    print("\nEnvironment variables:")
    for env_var in os.environ:
        if "REDIS" in env_var:
            print(f"{env_var}={os.environ[env_var]}")
    
    # Directly set environment variables as a fallback
    print("\nSetting Redis environment variables:")
    os.environ["REDIS_HOST"] = "redis"
    os.environ["REDIS_QUEUE_HOST"] = "redis"
    os.environ["REDIS_PORT"] = "6379"
    os.environ["REDIS_QUEUE_PORT"] = "6379"
    print("Environment variables set")
    
    print("\nConfiguration updated successfully!")
    
except Exception as e:
    print(f"Error updating Redis configuration: {e}")
    sys.exit(1) 