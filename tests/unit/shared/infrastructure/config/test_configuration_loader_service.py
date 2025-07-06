"""Tests for ConfigurationLoaderService."""

import json
import tempfile
import unittest
from pathlib import Path
from uuid import uuid4

from src.shared.infrastructure.config.configuration_loader_service import (
    ConfigurationLoaderService,
    get_configuration_loader,
    set_configuration_loader
)


class TestConfigurationLoaderService(unittest.TestCase):
    """Test cases for ConfigurationLoaderService."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.config_base_path = Path(self.temp_dir)
        
        # Create test directory structure
        (self.config_base_path / "roles").mkdir(parents=True)
        (self.config_base_path / "applications" / "app_configs").mkdir(parents=True)
        (self.config_base_path / "subscription").mkdir(parents=True)
        
        # Create test configuration files
        self._create_test_config_files()
        
        # Create loader instance with test path
        self.loader = ConfigurationLoaderService(str(self.config_base_path))
        
    def _create_test_config_files(self):
        """Create test configuration files."""
        # Test roles configuration
        roles_config = {
            "admin": {
                "description": "Test admin role",
                "permissions": ["test:read", "test:write"],
                "is_system_role": True,
                "can_be_deleted": False
            }
        }
        with open(self.config_base_path / "roles" / "default_roles.json", "w") as f:
            json.dump(roles_config, f)
        
        # Test application types configuration
        app_types_config = {
            "test_app": {
                "name": "Test Application",
                "description": "Test app description",
                "icon": "test-icon",
                "category": "test",
                "default_features": ["feature1", "feature2"],
                "required_permissions": ["test:use"]
            }
        }
        with open(self.config_base_path / "applications" / "application_types.json", "w") as f:
            json.dump(app_types_config, f)
        
        # Test plan configurations
        plan_config = {
            "plans": {
                "test_plan": {
                    "applications": ["test_app"],
                    "features": ["feature1", "feature2"]
                }
            }
        }
        with open(self.config_base_path / "applications" / "plan_configurations.json", "w") as f:
            json.dump(plan_config, f)
        
        # Test app-specific configuration
        test_app_config = {
            "test_config": {
                "setting1": "value1",
                "setting2": 42,
                "api_key_template": "generated_uuid",
                "url_template": "/api/org/{organization_id}"
            }
        }
        with open(self.config_base_path / "applications" / "app_configs" / "test_app.json", "w") as f:
            json.dump(test_app_config, f)
        
        # Test trial settings
        trial_config = {
            "trial_config": {
                "duration_days": 15,
                "billing_cycle": "monthly",
                "metadata": {
                    "is_trial": True,
                    "test_mode": True
                }
            }
        }
        with open(self.config_base_path / "subscription" / "trial_settings.json", "w") as f:
            json.dump(trial_config, f)
    
    def test_load_default_roles(self):
        """Test loading default roles configuration."""
        roles = self.loader.load_default_roles()
        
        self.assertIn("admin", roles)
        self.assertEqual(roles["admin"]["description"], "Test admin role")
        self.assertEqual(roles["admin"]["permissions"], ["test:read", "test:write"])
        self.assertTrue(roles["admin"]["is_system_role"])
        self.assertFalse(roles["admin"]["can_be_deleted"])
    
    def test_load_application_types(self):
        """Test loading application types configuration."""
        app_types = self.loader.load_application_types()
        
        self.assertIn("test_app", app_types)
        self.assertEqual(app_types["test_app"]["name"], "Test Application")
        self.assertEqual(app_types["test_app"]["default_features"], ["feature1", "feature2"])
    
    def test_load_plan_configurations(self):
        """Test loading plan configurations."""
        plans = self.loader.load_plan_configurations()
        
        self.assertIn("test_plan", plans)
        self.assertEqual(plans["test_plan"]["applications"], ["test_app"])
        self.assertEqual(plans["test_plan"]["features"], ["feature1", "feature2"])
    
    def test_load_app_config(self):
        """Test loading app-specific configuration."""
        config = self.loader.load_app_config("test_app")
        
        self.assertIn("test_config", config)
        self.assertEqual(config["test_config"]["setting1"], "value1")
        self.assertEqual(config["test_config"]["setting2"], 42)
    
    def test_load_trial_settings(self):
        """Test loading trial settings."""
        trial_settings = self.loader.load_trial_settings()
        
        self.assertIn("trial_config", trial_settings)
        self.assertEqual(trial_settings["trial_config"]["duration_days"], 15)
        self.assertEqual(trial_settings["trial_config"]["billing_cycle"], "monthly")
    
    def test_get_default_app_configuration_with_templates(self):
        """Test getting app configuration with template processing."""
        org_id = str(uuid4())
        config = self.loader.get_default_app_configuration("test_app", org_id)
        
        # Check that templates were processed
        self.assertIn("test_config", config)
        
        # UUID template should be replaced with actual UUID
        api_key = config["test_config"]["api_key_template"]
        self.assertNotEqual(api_key, "generated_uuid")
        self.assertEqual(len(api_key.split("-")), 5)  # UUID format
        
        # Organization ID template should be replaced
        url = config["test_config"]["url_template"]
        self.assertEqual(url, f"/api/org/{org_id}")
    
    def test_cache_functionality(self):
        """Test configuration caching."""
        # Load configuration twice
        config1 = self.loader.load_default_roles()
        config2 = self.loader.load_default_roles()
        
        # Should return the same content (from cache)
        self.assertEqual(config1, config2)
        
        # Check cache info
        cache_info = self.loader.get_cache_info()
        self.assertTrue(cache_info["cache_enabled"])
        self.assertGreater(cache_info["cache_size"], 0)
    
    def test_cache_disable_enable(self):
        """Test disabling and enabling cache."""
        # Load config to populate cache
        self.loader.load_default_roles()
        self.assertGreater(self.loader.get_cache_info()["cache_size"], 0)
        
        # Disable cache
        self.loader.disable_cache()
        self.assertFalse(self.loader.get_cache_info()["cache_enabled"])
        self.assertEqual(self.loader.get_cache_info()["cache_size"], 0)
        
        # Enable cache
        self.loader.enable_cache()
        self.assertTrue(self.loader.get_cache_info()["cache_enabled"])
    
    def test_reload_cache(self):
        """Test cache reload functionality."""
        # Load config to populate cache
        self.loader.load_default_roles()
        initial_cache_size = self.loader.get_cache_info()["cache_size"]
        
        # Reload cache
        self.loader.reload_cache()
        
        # Cache should be cleared
        self.assertEqual(self.loader.get_cache_info()["cache_size"], 0)
    
    def test_fallback_on_missing_file(self):
        """Test fallback behavior when configuration file is missing."""
        # Try to load non-existent configuration
        config = self.loader.load_app_config("non_existent_app")
        
        # Should return empty dict
        self.assertEqual(config, {})
    
    def test_fallback_on_invalid_json(self):
        """Test fallback behavior when JSON is invalid."""
        # Create invalid JSON file
        invalid_json_path = self.config_base_path / "test_invalid.json"
        with open(invalid_json_path, "w") as f:
            f.write("{ invalid json }")
        
        # Should return empty dict without raising exception
        config = self.loader._load_json_config("test_invalid.json", "test_key")
        self.assertEqual(config, {})


class TestGlobalConfigurationLoader(unittest.TestCase):
    """Test cases for global configuration loader functions."""
    
    def test_get_configuration_loader(self):
        """Test getting global configuration loader."""
        loader = get_configuration_loader()
        self.assertIsInstance(loader, ConfigurationLoaderService)
        
        # Should return same instance on subsequent calls
        loader2 = get_configuration_loader()
        self.assertIs(loader, loader2)
    
    def test_set_configuration_loader(self):
        """Test setting custom configuration loader."""
        original_loader = get_configuration_loader()
        
        # Create custom loader
        custom_loader = ConfigurationLoaderService()
        set_configuration_loader(custom_loader)
        
        # Should return custom loader
        current_loader = get_configuration_loader()
        self.assertIs(current_loader, custom_loader)
        self.assertIsNot(current_loader, original_loader)


if __name__ == "__main__":
    unittest.main()