from abc import ABC, abstractmethod

class IntegrationProvider(ABC):
    provider_name = "base"
    @abstractmethod
    def test_connection(self, config): ...
    @abstractmethod
    def capabilities(self): ...
    @abstractmethod
    def execute(self, operation, params, config): ...
