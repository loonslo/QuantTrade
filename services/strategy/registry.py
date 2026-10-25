# -*- coding: utf-8 -*-
"""
Strategy Registry
Manages strategy registration and discovery
"""

from typing import Dict, Any, List, Optional, Type
from abc import ABC, abstractmethod

from utils.core.logger_manager import get_logger

class IStrategy(ABC):
    """Strategy interface"""

    @abstractmethod
    def get_name(self) -> str:
        """Get strategy name"""
        pass

    @abstractmethod
    def get_parameters(self) -> Dict[str, Any]:
        """Get strategy parameters"""
        pass

    @abstractmethod
    def validate_parameters(self, params: Dict[str, Any]) -> bool:
        """Validate strategy parameters"""
        pass

class StrategyRegistry:
    """
    Strategy Registry

    Manages strategy registration and discovery
    """

    def __init__(self):
        """Initialize strategy registry"""
        self.logger = get_logger("services.strategy.registry")
        self._strategies: Dict[str, Type[IStrategy]] = {}
        self._strategy_metadata: Dict[str, Dict[str, Any]] = {}

        # Load built-in strategies
        self._load_builtin_strategies()

        self.logger.info("StrategyRegistry initialized")

    def register_strategy(self, name: str, strategy_class: Type[IStrategy],
                         metadata: Optional[Dict[str, Any]] = None) -> None:
        """
        Register a strategy

        Args:
            name: Strategy name
            strategy_class: Strategy class
            metadata: Strategy metadata
        """
        try:
            if name in self._strategies:
                self.logger.warning(f"Strategy {name} already registered, overwriting")

            self._strategies[name] = strategy_class
            self._strategy_metadata[name] = metadata or {}

            self.logger.info(f"Strategy registered: {name}")

        except Exception as e:
            self.logger.error(f"Failed to register strategy {name}: {e}")
            raise

    def unregister_strategy(self, name: str) -> bool:
        """
        Unregister a strategy

        Args:
            name: Strategy name

        Returns:
            True if unregistered successfully
        """
        try:
            if name not in self._strategies:
                self.logger.warning(f"Strategy {name} not found")
                return False

            del self._strategies[name]
            if name in self._strategy_metadata:
                del self._strategy_metadata[name]

            self.logger.info(f"Strategy unregistered: {name}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to unregister strategy {name}: {e}")
            return False

    def get_strategy_class(self, name: str) -> Optional[Type[IStrategy]]:
        """
        Get strategy class by name

        Args:
            name: Strategy name

        Returns:
            Strategy class or None if not found
        """
        return self._strategies.get(name)

    def get_strategy_metadata(self, name: str) -> Optional[Dict[str, Any]]:
        """
        Get strategy metadata by name

        Args:
            name: Strategy name

        Returns:
            Strategy metadata or None if not found
        """
        return self._strategy_metadata.get(name)

    def list_strategies(self) -> List[str]:
        """
        List all registered strategy names

        Returns:
            List of strategy names
        """
        return list(self._strategies.keys())

    def get_strategies_by_category(self, category: str) -> List[str]:
        """
        Get strategies by category

        Args:
            category: Strategy category

        Returns:
            List of strategy names in the category
        """
        strategies = []
        for name, metadata in self._strategy_metadata.items():
            if metadata.get('category') == category:
                strategies.append(name)
        return strategies

    def get_strategy_info(self, name: str) -> Optional[Dict[str, Any]]:
        """
        Get complete strategy information

        Args:
            name: Strategy name

        Returns:
            Strategy information including class and metadata
        """
        if name not in self._strategies:
            return None

        return {
            'name': name,
            'class': self._strategies[name],
            'metadata': self._strategy_metadata.get(name, {})
        }

    def _load_builtin_strategies(self) -> None:
        """Load built-in strategies"""
        # This would typically load strategies from a configuration file
        # or scan a strategies directory
        builtin_strategies = {
            'ma_crossover': {
                'class': None,  # Would be actual strategy class
                'metadata': {
                    'category': 'trend_following',
                    'risk_level': 'medium',
                    'complexity': 'low'
                }
            },
            'rsi_strategy': {
                'class': None,
                'metadata': {
                    'category': 'mean_reversion',
                    'risk_level': 'high',
                    'complexity': 'medium'
                }
            }
        }

        for name, config in builtin_strategies.items():
            if config['class']:  # Only register if class is available
                self.register_strategy(name, config['class'], config['metadata'])

# Global registry instance
_strategy_registry: Optional[StrategyRegistry] = None

def get_strategy_registry() -> StrategyRegistry:
    """Get strategy registry instance (singleton)"""
    global _strategy_registry
    if _strategy_registry is None:
        _strategy_registry = StrategyRegistry()
    return _strategy_registry