"""
Configuration management for the evaluation system.

This module provides utilities for loading and managing evaluation
configuration from various sources including files, environment
variables, and runtime parameters.
"""

import json
import os
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from .data_structures import EvaluationConfig
from ..core.config import settings

logger = logging.getLogger(__name__)


class EvaluationConfigManager:
    """
    Manager for evaluation configuration with support for multiple sources.
    
    Configuration precedence (highest to lowest):
    1. Runtime parameters
    2. Configuration file
    3. Environment variables
    4. Default values
    """
    
    def __init__(self, config_dir: Optional[Union[str, Path]] = None):
        """
        Initialize configuration manager.
        
        Args:
            config_dir: Directory containing configuration files
        """
        self.config_dir = Path(config_dir) if config_dir else Path("config/evaluation")
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        # Default configuration file locations
        self.default_config_file = self.config_dir / "default.json"
        self.user_config_file = self.config_dir / "user.json"
        self.env_config_file = self.config_dir / "environment.json"
    
    def load_config(self, 
                   config_name: Optional[str] = None,
                   config_file: Optional[Union[str, Path]] = None,
                   runtime_params: Optional[Dict[str, Any]] = None) -> EvaluationConfig:
        """
        Load evaluation configuration from multiple sources.
        
        Args:
            config_name: Named configuration (e.g., 'production', 'testing')
            config_file: Specific configuration file path
            runtime_params: Runtime parameter overrides
            
        Returns:
            EvaluationConfig: Merged configuration
        """
        # Start with defaults
        config_data = self._get_default_config()
        
        # Merge environment-based config
        env_config = self._load_env_config()
        if env_config:
            config_data.update(env_config)
        
        # Merge file-based config
        if config_file:
            file_config = self._load_file_config(config_file)
            if file_config:
                config_data.update(file_config)
        elif config_name:
            named_config = self._load_named_config(config_name)
            if named_config:
                config_data.update(named_config)
        else:
            # Try to load user config
            user_config = self._load_file_config(self.user_config_file)
            if user_config:
                config_data.update(user_config)
        
        # Apply runtime overrides
        if runtime_params:
            config_data.update(runtime_params)
        
        try:
            config = EvaluationConfig(**config_data)
            
            # Validate configuration
            errors = config.validate()
            if errors:
                logger.warning(f"Configuration validation warnings: {'; '.join(errors)}")
            
            logger.info(f"Loaded evaluation configuration with ERP weight: {config.erp_accuracy_weight}")
            return config
            
        except Exception as e:
            logger.error(f"Failed to create configuration: {e}")
            logger.info("Falling back to default configuration")
            return EvaluationConfig()
    
    def save_config(self, 
                   config: EvaluationConfig, 
                   config_name: Optional[str] = None,
                   config_file: Optional[Union[str, Path]] = None):
        """
        Save configuration to file.
        
        Args:
            config: Configuration to save
            config_name: Named configuration to save as
            config_file: Specific file path to save to
        """
        if config_file:
            output_file = Path(config_file)
        elif config_name:
            output_file = self.config_dir / f"{config_name}.json"
        else:
            output_file = self.user_config_file
        
        try:
            output_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_file, 'w') as f:
                json.dump(config.to_dict(), f, indent=2)
            
            logger.info(f"Saved configuration to {output_file}")
            
        except Exception as e:
            logger.error(f"Failed to save configuration to {output_file}: {e}")
            raise
    
    def create_default_config_file(self):
        """Create default configuration file if it doesn't exist."""
        if not self.default_config_file.exists():
            default_config = EvaluationConfig()
            self.save_config(default_config, config_file=self.default_config_file)
            logger.info(f"Created default configuration file: {self.default_config_file}")
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration values."""
        return {
            'erp_accuracy_weight': 0.40,
            'reasoning_weight': 0.20,
            'compliance_weight': 0.20,
            'performance_weight': 0.20,
            'min_erp_accuracy_threshold': 0.70,
            'target_erp_accuracy': 0.90,
            'max_processing_time_ms': 2000.0,
            'target_processing_time_ms': 500.0,
            'detailed_logging': True,
            'evaluation_model': 'gpt-4'
        }
    
    def _load_env_config(self) -> Optional[Dict[str, Any]]:
        """Load configuration from environment variables."""
        env_config = {}
        
        # Map environment variables to config fields
        env_mappings = {
            'EVAL_ERP_WEIGHT': 'erp_accuracy_weight',
            'EVAL_REASONING_WEIGHT': 'reasoning_weight',
            'EVAL_COMPLIANCE_WEIGHT': 'compliance_weight',
            'EVAL_PERFORMANCE_WEIGHT': 'performance_weight',
            'EVAL_MIN_ERP_THRESHOLD': 'min_erp_accuracy_threshold',
            'EVAL_TARGET_ERP_ACCURACY': 'target_erp_accuracy',
            'EVAL_MAX_PROCESSING_TIME': 'max_processing_time_ms',
            'EVAL_TARGET_PROCESSING_TIME': 'target_processing_time_ms',
            'EVAL_MODEL': 'evaluation_model',
            'EVAL_DETAILED_LOGGING': 'detailed_logging',
        }
        
        for env_var, config_key in env_mappings.items():
            value = os.getenv(env_var)
            if value is not None:
                try:
                    # Try to convert to appropriate type
                    if config_key.endswith('_weight') or config_key.endswith('_threshold') or config_key.endswith('_accuracy'):
                        env_config[config_key] = float(value)
                    elif config_key.endswith('_time_ms'):
                        env_config[config_key] = float(value)
                    elif config_key.endswith('_logging'):
                        env_config[config_key] = value.lower() in ('true', '1', 'yes', 'on')
                    else:
                        env_config[config_key] = value
                except ValueError as e:
                    logger.warning(f"Invalid value for {env_var}: {value} ({e})")
        
        return env_config if env_config else None
    
    def _load_file_config(self, config_file: Union[str, Path]) -> Optional[Dict[str, Any]]:
        """Load configuration from JSON file."""
        config_file = Path(config_file)
        
        if not config_file.exists():
            logger.debug(f"Configuration file not found: {config_file}")
            return None
        
        try:
            with open(config_file, 'r') as f:
                config_data = json.load(f)
            
            logger.debug(f"Loaded configuration from {config_file}")
            return config_data
            
        except Exception as e:
            logger.error(f"Error loading configuration from {config_file}: {e}")
            return None
    
    def _load_named_config(self, config_name: str) -> Optional[Dict[str, Any]]:
        """Load named configuration file."""
        config_file = self.config_dir / f"{config_name}.json"
        return self._load_file_config(config_file)
    
    def list_available_configs(self) -> List[str]:
        """List available named configuration files."""
        config_files = list(self.config_dir.glob("*.json"))
        return [f.stem for f in config_files if f.stem != "default"]
    
    def create_evaluation_config_template(self, template_name: str = "template"):
        """Create a template configuration file with comments."""
        template_config = {
            "_comment": "Sales Order Intelligence Evaluation Configuration",
            "_description": "This file configures the evaluation weights and thresholds",
            
            "erp_accuracy_weight": 0.40,
            "_erp_accuracy_comment": "Weight for ERP JSON accuracy (PRIMARY metric) - should be highest",
            
            "reasoning_weight": 0.20,
            "_reasoning_comment": "Weight for AI reasoning quality evaluation",
            
            "compliance_weight": 0.20,
            "_compliance_comment": "Weight for business rules and compliance evaluation",
            
            "performance_weight": 0.20,
            "_performance_comment": "Weight for system performance evaluation",
            
            "_weights_note": "All weights must sum to 1.0",
            
            "min_erp_accuracy_threshold": 0.70,
            "_min_threshold_comment": "Minimum acceptable ERP accuracy (fail below this)",
            
            "target_erp_accuracy": 0.90,
            "_target_comment": "Target ERP accuracy for full score",
            
            "max_processing_time_ms": 2000.0,
            "_max_time_comment": "Maximum acceptable processing time in milliseconds",
            
            "target_processing_time_ms": 500.0,
            "_target_time_comment": "Target processing time for full performance score",
            
            "evaluation_model": "gpt-4",
            "_model_comment": "Model to use for evaluation tasks",
            
            "detailed_logging": True,
            "_logging_comment": "Enable detailed logging during evaluation",
            
            "input_data_dir": "data/evaluation",
            "output_results_dir": "results/evaluation",
            "reference_data_dir": "data/reference"
        }
        
        template_file = self.config_dir / f"{template_name}.json"
        
        try:
            with open(template_file, 'w') as f:
                json.dump(template_config, f, indent=2)
            
            logger.info(f"Created configuration template: {template_file}")
            return template_file
            
        except Exception as e:
            logger.error(f"Failed to create template: {e}")
            raise


# Global configuration manager instance
config_manager = EvaluationConfigManager()


def load_evaluation_config(**kwargs) -> EvaluationConfig:
    """
    Convenience function to load evaluation configuration.
    
    Args:
        **kwargs: Arguments passed to config_manager.load_config()
        
    Returns:
        EvaluationConfig: Loaded configuration
    """
    return config_manager.load_config(**kwargs)


def create_config_template(template_name: str = "template") -> Path:
    """
    Convenience function to create configuration template.
    
    Args:
        template_name: Name for the template file
        
    Returns:
        Path: Path to created template file
    """
    return config_manager.create_evaluation_config_template(template_name)