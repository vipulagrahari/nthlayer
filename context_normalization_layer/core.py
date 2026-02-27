"""
Context Normalization Layer - Core Module

A multi-adapter MCP (Model Context Protocol) framework that acts as a bridge 
between AI applications and existing systems.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Protocol, Union
from datetime import datetime
import asyncio


# =============================================================================
# Core Data Types
# =============================================================================

@dataclass
class Resource:
    """Represents a resource that can be accessed via an adapter."""
    uri: str
    name: str
    mime_type: str
    description: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ResourceContent:
    """Content of a resource."""
    uri: str
    mime_type: str
    text: Optional[str] = None
    blob: Optional[bytes] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Tool:
    """Represents a tool/action available through an adapter."""
    name: str
    description: str
    input_schema: Dict[str, Any]  # JSON Schema


@dataclass
class ToolResult:
    """Result of executing a tool."""
    success: bool
    content: Union[str, Dict[str, Any], List[Any]]
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class HealthStatus(Enum):
    """Health status of an adapter."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


@dataclass
class AdapterCapabilities:
    """Capabilities supported by an adapter."""
    resources: bool = True
    tools: bool = True
    prompts: bool = False
    real_time_updates: bool = False


@dataclass
class AdapterConfig:
    """Configuration for an adapter."""
    type: str
    name: str
    enabled: bool = True
    config: Dict[str, Any] = field(default_factory=dict)


# =============================================================================
# Adapter Interface
# =============================================================================

class SystemAdapter(ABC):
    """
    Abstract base class for system adapters.
    
    All adapters must implement this interface to integrate with the
    Context Normalization Layer.
    """
    
    def __init__(self, config: AdapterConfig):
        self._config = config
        self._connected = False
    
    @property
    @abstractmethod
    def system_type(self) -> str:
        """Return the type of system this adapter connects to."""
        pass
    
    @property
    @abstractmethod
    def version(self) -> str:
        """Return the adapter version."""
        pass
    
    @property
    def name(self) -> str:
        """Return the adapter name."""
        return self._config.name
    
    @property
    def is_connected(self) -> bool:
        """Check if adapter is connected."""
        return self._connected
    
    @abstractmethod
    async def get_capabilities(self) -> AdapterCapabilities:
        """Get the capabilities of this adapter."""
        pass
    
    @abstractmethod
    async def list_resources(self) -> List[Resource]:
        """List available resources."""
        pass
    
    @abstractmethod
    async def read_resource(self, uri: str) -> ResourceContent:
        """Read a resource by URI."""
        pass
    
    @abstractmethod
    async def list_tools(self) -> List[Tool]:
        """List available tools."""
        pass
    
    @abstractmethod
    async def execute_tool(self, name: str, args: Dict[str, Any]) -> ToolResult:
        """Execute a tool by name with arguments."""
        pass
    
    @abstractmethod
    async def connect(self) -> None:
        """Connect to the external system."""
        pass
    
    @abstractmethod
    async def disconnect(self) -> None:
        """Disconnect from the external system."""
        pass
    
    @abstractmethod
    async def health_check(self) -> HealthStatus:
        """Check the health of the connection."""
        pass


# =============================================================================
# Cross-System Linking
# =============================================================================

class RelationshipType(Enum):
    """Types of relationships between entities."""
    IMPLEMENTS = "implements"
    FIXES = "fixes"
    RELATED = "related"
    BLOCKS = "blocks"
    DEPENDS_ON = "depends_on"


@dataclass
class EntityReference:
    """Reference to an entity in a specific adapter."""
    adapter: str
    resource_uri: str


@dataclass
class EntityLink:
    """Link between entities across different adapters."""
    source: EntityReference
    target: EntityReference
    relationship: RelationshipType
    confidence: float  # 0.0 to 1.0, AI-detected vs manual
    created_at: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CrossSystemQuery:
    """Query across multiple systems."""
    adapters: List[str]
    relationships: List[RelationshipType]
    conditions: List[Dict[str, Any]] = field(default_factory=list)
    limit: Optional[int] = None


# =============================================================================
# Normalization Engine
# =============================================================================

class NormalizationEngine:
    """
    Engine that normalizes data from various adapters into MCP primitives.
    """
    
    def __init__(self):
        self._adapters: Dict[str, SystemAdapter] = {}
        self._links: List[EntityLink] = []
    
    def register_adapter(self, adapter: SystemAdapter) -> None:
        """Register an adapter with the engine."""
        self._adapters[adapter.name] = adapter
    
    def unregister_adapter(self, name: str) -> None:
        """Unregister an adapter."""
        if name in self._adapters:
            del self._adapters[name]
    
    def get_adapter(self, name: str) -> Optional[SystemAdapter]:
        """Get an adapter by name."""
        return self._adapters.get(name)
    
    def list_adapters(self) -> List[str]:
        """List all registered adapter names."""
        return list(self._adapters.keys())
    
    async def query_all_resources(self) -> Dict[str, List[Resource]]:
        """Query resources from all adapters."""
        results = {}
        for name, adapter in self._adapters.items():
            try:
                resources = await adapter.list_resources()
                results[name] = resources
            except Exception as e:
                results[name] = []
        return results
    
    async def query_all_tools(self) -> Dict[str, List[Tool]]:
        """Query tools from all adapters."""
        results = {}
        for name, adapter in self._adapters.items():
            try:
                tools = await adapter.list_tools()
                results[name] = tools
            except Exception as e:
                results[name] = []
        return results
    
    def add_link(self, link: EntityLink) -> None:
        """Add a cross-system link."""
        self._links.append(link)
    
    def get_links(self, 
                  adapter: Optional[str] = None,
                  relationship: Optional[RelationshipType] = None) -> List[EntityLink]:
        """Get links with optional filtering."""
        links = self._links
        
        if adapter:
            links = [l for l in links if l.source.adapter == adapter or l.target.adapter == adapter]
        
        if relationship:
            links = [l for l in links if l.relationship == relationship]
        
        return links
    
    async def execute_cross_system_query(self, query: CrossSystemQuery) -> List[EntityLink]:
        """Execute a query across multiple systems."""
        # Filter links by adapters and relationships
        results = []
        for link in self._links:
            if link.source.adapter in query.adapters and link.target.adapter in query.adapters:
                if link.relationship in query.relationships:
                    results.append(link)
        
        if query.limit:
            results = results[:query.limit]
        
        return results
    
    async def health_check_all(self) -> Dict[str, HealthStatus]:
        """Check health of all adapters."""
        results = {}
        for name, adapter in self._adapters.items():
            try:
                status = await adapter.health_check()
                results[name] = status
            except Exception:
                results[name] = HealthStatus.UNHEALTHY
        return results


# =============================================================================
# Context Layer Main Class
# =============================================================================

class ContextLayer:
    """
    Main entry point for the Context Normalization Layer.
    
    Manages adapters and provides a unified interface to external systems.
    """
    
    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path
        self.engine = NormalizationEngine()
        self._initialized = False
    
    async def initialize(self) -> None:
        """Initialize the context layer."""
        # Load configuration if path provided
        if self.config_path:
            await self._load_config()
        self._initialized = True
    
    async def _load_config(self) -> None:
        """Load configuration from file."""
        # Implementation would load YAML/JSON config
        pass
    
    def register_adapter(self, adapter: SystemAdapter) -> None:
        """Register an adapter."""
        self.engine.register_adapter(adapter)
    
    async def start(self) -> None:
        """Start the context layer and connect all adapters."""
        if not self._initialized:
            await self.initialize()
        
        for name, adapter in self.engine._adapters.items():
            if not adapter.is_connected:
                await adapter.connect()
    
    async def stop(self) -> None:
        """Stop the context layer and disconnect all adapters."""
        for name, adapter in self.engine._adapters.items():
            if adapter.is_connected:
                await adapter.disconnect()
    
    async def get_resource(self, adapter_name: str, uri: str) -> ResourceContent:
        """Get a resource from a specific adapter."""
        adapter = self.engine.get_adapter(adapter_name)
        if not adapter:
            raise ValueError(f"Adapter '{adapter_name}' not found")
        return await adapter.read_resource(uri)
    
    async def execute_tool(self, adapter_name: str, tool_name: str, 
                          args: Dict[str, Any]) -> ToolResult:
        """Execute a tool on a specific adapter."""
        adapter = self.engine.get_adapter(adapter_name)
        if not adapter:
            raise ValueError(f"Adapter '{adapter_name}' not found")
        return await adapter.execute_tool(tool_name, args)
    
    async def health_check(self) -> Dict[str, HealthStatus]:
        """Check health of all adapters."""
        return await self.engine.health_check_all()
