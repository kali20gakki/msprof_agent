"""Tests for configuration management."""

import json
import os
import tempfile
from pathlib import Path

import pytest

from msagent.config import ConfigManager, LLMConfig, MCPConfig, AppConfig


class TestConfigManager:
    """Test configuration manager."""
    
    def test_load_default_config(self):
        """Test loading default configuration."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = ConfigManager()
            manager.CONFIG_DIR = Path(tmpdir)
            manager.CONFIG_FILE = Path(tmpdir) / "config.json"
            
            config = manager.load_config()
            
            assert isinstance(config, AppConfig)
            assert config.llm.provider == "openai"
            assert config.llm.model == "gpt-4o-mini"
    
    def test_save_and_load_config(self):
        """Test saving and loading configuration."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = ConfigManager()
            manager.CONFIG_DIR = Path(tmpdir)
            manager.CONFIG_FILE = Path(tmpdir) / "config.json"
            
            config = AppConfig()
            config.llm.api_key = "test-key"
            config.llm.model = "gpt-4"
            
            manager.save_config(config)
            
            # Reset and reload
            manager._config = None
            loaded = manager.load_config()
            
            assert loaded.llm.api_key == "test-key"
            assert loaded.llm.model == "gpt-4"
    
    def test_llm_config_is_configured(self):
        """Test LLM configuration check."""
        config = LLMConfig()
        assert not config.is_configured()
        
        config.api_key = "test-key"
        assert config.is_configured()
    
    def test_mcp_config(self):
        """Test MCP configuration."""
        config = MCPConfig(
            name="test-server",
            command="python",
            args=["server.py"],
            enabled=True,
        )
        
        assert config.name == "test-server"
        assert config.command == "python"
        assert config.args == ["server.py"]
        assert config.enabled is True


class TestEnvironmentConfig:
    """Test environment variable configuration."""
    
    def test_openai_env_vars(self, monkeypatch):
        """Test OpenAI environment variables."""
        monkeypatch.setenv("OPENAI_API_KEY", "test-openai-key")
        monkeypatch.setenv("OPENAI_MODEL", "gpt-4")
        
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = ConfigManager()
            manager.CONFIG_DIR = Path(tmpdir)
            manager.CONFIG_FILE = Path(tmpdir) / "config.json"
            
            config = manager.load_config()
            
            assert config.llm.provider == "openai"
            assert config.llm.api_key == "test-openai-key"
            assert config.llm.model == "gpt-4"
    
    def test_anthropic_env_vars(self, monkeypatch):
        """Test Anthropic environment variables."""
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-anthropic-key")
        monkeypatch.setenv("ANTHROPIC_MODEL", "claude-3-opus")
        
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = ConfigManager()
            manager.CONFIG_DIR = Path(tmpdir)
            manager.CONFIG_FILE = Path(tmpdir) / "config.json"
            
            config = manager.load_config()
            
            assert config.llm.provider == "anthropic"
            assert config.llm.api_key == "test-anthropic-key"
            assert config.llm.model == "claude-3-opus"
