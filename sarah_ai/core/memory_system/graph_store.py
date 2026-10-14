"""
Graph Store for Memory Relationships
Provides graph-based storage and traversal for memory relationships.
Features:
- Relationship modeling and storage
- Graph traversal and path finding
- Relationship strength calculation
- Community detection
- Graph analytics
"""

import json
import asyncio
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple, Set
from datetime import datetime
from collections import defaultdict, deque
import networkx as nx
import pickle

from . import MemoryEntry, MemoryMetadata

class GraphStore:
    """
    Graph database for storing and analyzing memory relationships.
    Uses NetworkX for graph operations and analysis.
    """

    def __init__(self, storage_path: Path):
        self.storage_path = storage_path
        self.storage_path.mkdir(exist_ok=True)

        # Graph storage
        self.graph = nx.MultiDiGraph()  # Multi-directional graph for complex relationships

        # Node storage (memory_id -> node_data)
        self.nodes: Dict[str, Dict[str, Any]] = {}

        # Edge storage with metadata
        self.edges: Dict[Tuple[str, str, str], Dict[str, Any]] = {}  # (source, target, relation_type) -> edge_data

        # Relationship types and their properties
        self.relationship_types = {
            "related_to": {"strength_default": 0.5, "directional": False},
            "causes": {"strength_default": 0.8, "directional": True},
            "similar_to": {"strength_default": 0.7, "directional": False},
            "contradicts": {"strength_default": 0.6, "directional": False},
            "supports": {"strength_default": 0.7, "directional": True},
            "temporal_sequence": {"strength_default": 0.9, "directional": True},
            "emotional_link": {"strength_default": 0.6, "directional": False},
            "contextual_link": {"strength_default": 0.4, "directional": False}
        }

        print(f"[GRAPH STORE]: Initialized at {storage_path}")

    async def add_node(self, memory_id: str, node_data: Dict[str, Any]):
        """Add a node to the graph"""
        self.nodes[memory_id] = node_data.copy()
        self.graph.add_node(memory_id, **node_data)

    async def add_edge(self, source_id: str, target_id: str,
                      relation_type: str, edge_data: Dict[str, Any] = None):
        """Add an edge between two memories"""
        if edge_data is None:
            edge_data = {}

        # Set default strength if not provided
        if "strength" not in edge_data and relation_type in self.relationship_types:
            edge_data["strength"] = self.relationship_types[relation_type]["strength_default"]

        # Add timestamps
        edge_data["created"] = edge_data.get("created", datetime.now().isoformat())
        edge_data["last_updated"] = datetime.now().isoformat()

        # Store edge data
        edge_key = (source_id, target_id, relation_type)
        self.edges[edge_key] = edge_data.copy()

        # Add to NetworkX graph
        self.graph.add_edge(source_id, target_id, key=relation_type, **edge_data)

        # Add reverse edge if relationship is not directional
        if not self.relationship_types.get(relation_type, {}).get("directional", True):
            reverse_key = (target_id, source_id, relation_type)
            self.edges[reverse_key] = edge_data.copy()
            self.graph.add_edge(target_id, source_id, key=relation_type, **edge_data)

    async def remove_node(self, memory_id: str):
        """Remove a node and all its edges"""
        if memory_id in self.nodes:
            del self.nodes[memory_id]

        # Remove all edges connected to this node
        edges_to_remove = []
        for edge_key in self.edges.keys():
            if memory_id in edge_key[:2]:
                edges_to_remove.append(edge_key)

        for edge_key in edges_to_remove:
            del self.edges[edge_key]

        # Remove from NetworkX graph
        if self.graph.has_node(memory_id):
            self.graph.remove_node(memory_id)

    async def remove_edge(self, source_id: str, target_id: str, relation_type: str):
        """Remove a specific edge"""
        edge_key = (source_id, target_id, relation_type)
        if edge_key in self.edges:
            del self.edges[edge_key]

        # Remove from NetworkX graph
        if self.graph.has_edge(source_id, target_id, key=relation_type):
            self.graph.remove_edge(source_id, target_id, key=relation_type)

    async def get_relationships(self, memory_id: str, relation_type: str = None,
                              direction: str = "both") -> List[Tuple[str, Dict[str, Any]]]:
        """
        Get relationships for a memory

        Args:
            memory_id: The memory to get relationships for
            relation_type: Filter by relationship type (optional)
            direction: "outgoing", "incoming", or "both"

        Returns:
            List of (related_memory_id, edge_data) tuples
        """
        relationships = []

        if direction in ["outgoing", "both"]:
            # Outgoing edges
            for target_id in self.graph.successors(memory_id):
                for relation_type_key, edge_data in self.graph[memory_id][target_id].items():
                    if relation_type is None or relation_type_key == relation_type:
                        relationships.append((target_id, edge_data))

        if direction in ["incoming", "both"]:
            # Incoming edges
            for source_id in self.graph.predecessors(memory_id):
                for relation_type_key, edge_data in self.graph[source_id][memory_id].items():
                    if relation_type is None or relation_type_key == relation_type:
                        relationships.append((source_id, edge_data))

        return relationships

    async def find_paths(self, start_id: str, end_id: str, max_length: int = 5) -> List[List[str]]:
        """Find all paths between two memories"""
        try:
            paths = list(nx.all_simple_paths(self.graph, start_id, end_id, cutoff=max_length))
            return paths
        except nx.NetworkXNoPath:
            return []

    async def get_related_memories(self, memory_id: str, depth: int = 2,
                                 relation_types: List[str] = None) -> Set[str]:
        """Get all memories related to a given memory within a certain depth"""
        related = set()

        # Use BFS to find related memories
        visited = set()
        queue = deque([(memory_id, 0)])

        while queue:
            current_id, current_depth = queue.popleft()

            if current_id in visited or current_depth > depth:
                continue

            visited.add(current_id)

            if current_id != memory_id:
                related.add(current_id)

            # Add neighbors
            for neighbor in self.graph.neighbors(current_id):
                if neighbor not in visited:
                    # Check if relationship type is allowed
                    if relation_types is None:
                        queue.append((neighbor, current_depth + 1))
                    else:
                        # Check if there's at least one allowed relationship type
                        edge_types = set()
                        for edge_data in self.graph[current_id][neighbor].values():
                            edge_types.add(edge_data.get("relation_type", ""))

                        if edge_types.intersection(set(relation_types)):
                            queue.append((neighbor, current_depth + 1))

        return related

    async def calculate_centrality(self, memory_id: str) -> Dict[str, float]:
        """Calculate centrality measures for a memory"""
        if not self.graph.has_node(memory_id):
            return {}

        # Calculate various centrality measures
        centrality = {}

        try:
            # Degree centrality
            centrality["degree"] = nx.degree_centrality(self.graph)[memory_id]
        except:
            centrality["degree"] = 0.0

        try:
            # Betweenness centrality (expensive, so limit graph size)
            if len(self.graph) < 1000:
                centrality["betweenness"] = nx.betweenness_centrality(self.graph)[memory_id]
            else:
                centrality["betweenness"] = 0.0
        except:
            centrality["betweenness"] = 0.0

        try:
            # Closeness centrality
            centrality["closeness"] = nx.closeness_centrality(self.graph)[memory_id]
        except:
            centrality["closeness"] = 0.0

        # Relationship strength centrality (custom)
        centrality["relationship_strength"] = self._calculate_relationship_strength(memory_id)

        return centrality

    def _calculate_relationship_strength(self, memory_id: str) -> float:
        """Calculate relationship strength centrality"""
        if not self.graph.has_node(memory_id):
            return 0.0

        total_strength = 0.0
        edge_count = 0

        # Sum strengths of all edges connected to this node
        for neighbor in self.graph.neighbors(memory_id):
            for edge_data in self.graph[memory_id][neighbor].values():
                strength = edge_data.get("strength", 0.5)
                total_strength += strength
                edge_count += 1

        # Also check incoming edges
        for predecessor in self.graph.predecessors(memory_id):
            for edge_data in self.graph[predecessor][memory_id].values():
                strength = edge_data.get("strength", 0.5)
                total_strength += strength
                edge_count += 1

        return total_strength / max(1, edge_count)

    async def detect_communities(self) -> List[Set[str]]:
        """Detect communities in the memory graph"""
        try:
            # Use Louvain method for community detection
            communities = nx.community.louvain_communities(self.graph.to_undirected())
            return communities
        except ImportError:
            # Fallback to simple connected components
            components = list(nx.connected_components(self.graph.to_undirected()))
            return components
        except Exception:
            # If community detection fails, return individual nodes
            return [{node} for node in self.graph.nodes()]

    async def get_graph_statistics(self) -> Dict[str, Any]:
        """Get comprehensive graph statistics"""
        stats = {
            "nodes": len(self.graph.nodes()),
            "edges": len(self.graph.edges()),
            "relationship_types": {}
        }

        # Count relationship types
        for edge_data in self.edges.values():
            rel_type = edge_data.get("relation_type", "unknown")
            stats["relationship_types"][rel_type] = stats["relationship_types"].get(rel_type, 0) + 1

        # Graph metrics
        if stats["nodes"] > 0:
            stats["average_degree"] = sum(dict(self.graph.degree()).values()) / stats["nodes"]

            try:
                stats["density"] = nx.density(self.graph)
            except:
                stats["density"] = 0.0

            try:
                if stats["nodes"] < 1000:  # Limit for expensive computations
                    stats["average_clustering"] = nx.average_clustering(self.graph)
                    stats["connected_components"] = nx.number_connected_components(self.graph)
                else:
                    stats["average_clustering"] = 0.0
                    stats["connected_components"] = 0
            except:
                stats["average_clustering"] = 0.0
                stats["connected_components"] = 0

        # Memory type distribution
        memory_types = {}
        for node_data in self.nodes.values():
            mem_type = node_data.get("memory_type", "unknown")
            memory_types[mem_type] = memory_types.get(mem_type, 0) + 1

        stats["memory_type_distribution"] = memory_types

        return stats

    async def strengthen_relationship(self, source_id: str, target_id: str,
                                    relation_type: str, strength_increase: float = 0.1):
        """Strengthen a relationship between two memories"""
        edge_key = (source_id, target_id, relation_type)

        if edge_key in self.edges:
            current_strength = self.edges[edge_key].get("strength", 0.5)
            new_strength = min(1.0, current_strength + strength_increase)

            self.edges[edge_key]["strength"] = new_strength
            self.edges[edge_key]["last_updated"] = datetime.now().isoformat()

            # Update NetworkX graph
            if self.graph.has_edge(source_id, target_id, key=relation_type):
                self.graph[source_id][target_id][relation_type]["strength"] = new_strength

    async def weaken_relationship(self, source_id: str, target_id: str,
                                relation_type: str, strength_decrease: float = 0.1):
        """Weaken a relationship between two memories"""
        edge_key = (source_id, target_id, relation_type)

        if edge_key in self.edges:
            current_strength = self.edges[edge_key].get("strength", 0.5)
            new_strength = max(0.0, current_strength - strength_decrease)

            self.edges[edge_key]["strength"] = new_strength
            self.edges[edge_key]["last_updated"] = datetime.now().isoformat()

            # Update NetworkX graph
            if self.graph.has_edge(source_id, target_id, key=relation_type):
                self.graph[source_id][target_id][relation_type]["strength"] = new_strength

            # Remove very weak relationships
            if new_strength < 0.1:
                await self.remove_edge(source_id, target_id, relation_type)

    async def find_bridge_memories(self, source_id: str, target_id: str) -> List[str]:
        """Find memories that connect two distant memories"""
        try:
            # Find shortest path
            path = nx.shortest_path(self.graph, source_id, target_id)
            # Return intermediate nodes (excluding source and target)
            return path[1:-1] if len(path) > 2 else []
        except nx.NetworkXNoPath:
            return []

    async def get_memory_context(self, memory_id: str, context_depth: int = 2) -> Dict[str, Any]:
        """Get contextual information about a memory from its relationships"""
        context = {
            "memory_id": memory_id,
            "direct_relationships": await self.get_relationships(memory_id),
            "related_memories": list(await self.get_related_memories(memory_id, depth=context_depth)),
            "centrality": await self.calculate_centrality(memory_id),
            "relationship_summary": {}
        }

        # Summarize relationships by type
        relationship_counts = defaultdict(int)
        for _, edge_data in context["direct_relationships"]:
            rel_type = edge_data.get("relation_type", "unknown")
            relationship_counts[rel_type] += 1

        context["relationship_summary"] = dict(relationship_counts)

        return context

    async def save(self):
        """Save graph store to disk"""
        # Save graph structure
        graph_file = self.storage_path / "graph.pkl"
        with open(graph_file, 'wb') as f:
            pickle.dump(self.graph, f)

        # Save node data
        nodes_file = self.storage_path / "nodes.json"
        with open(nodes_file, 'w', encoding='utf-8') as f:
            json.dump(self.nodes, f, indent=2)

        # Save edge data
        edges_file = self.storage_path / "edges.json"
        with open(edges_file, 'w', encoding='utf-8') as f:
            # Convert tuple keys to strings for JSON
            serializable_edges = {}
            for edge_key, edge_data in self.edges.items():
                key_str = f"{edge_key[0]}|{edge_key[1]}|{edge_key[2]}"
                serializable_edges[key_str] = edge_data

            json.dump(serializable_edges, f, indent=2)

        # Save relationship types
        types_file = self.storage_path / "relationship_types.json"
        with open(types_file, 'w', encoding='utf-8') as f:
            json.dump(self.relationship_types, f, indent=2)

    async def load(self):
        """Load graph store from disk"""
        # Load graph structure
        graph_file = self.storage_path / "graph.pkl"
        if graph_file.exists():
            with open(graph_file, 'rb') as f:
                self.graph = pickle.load(f)

        # Load node data
        nodes_file = self.storage_path / "nodes.json"
        if nodes_file.exists():
            with open(nodes_file, 'r', encoding='utf-8') as f:
                self.nodes = json.load(f)

        # Load edge data
        edges_file = self.storage_path / "edges.json"
        if edges_file.exists():
            with open(edges_file, 'r', encoding='utf-8') as f:
                serializable_edges = json.load(f)

            # Convert string keys back to tuples
            self.edges = {}
            for key_str, edge_data in serializable_edges.items():
                source_id, target_id, relation_type = key_str.split('|', 2)
                edge_key = (source_id, target_id, relation_type)
                self.edges[edge_key] = edge_data

        # Load relationship types
        types_file = self.storage_path / "relationship_types.json"
        if types_file.exists():
            with open(types_file, 'r', encoding='utf-8') as f:
                self.relationship_types = json.load(f)

        print(f"[GRAPH STORE]: Loaded graph with {len(self.graph.nodes())} nodes and {len(self.graph.edges())} edges")

    async def clear(self):
        """Clear all graph data"""
        self.graph.clear()
        self.nodes.clear()
        self.edges.clear()
        print(f"[GRAPH STORE]: Cleared all graph data")

    async def optimize(self):
        """Optimize graph structure for better performance"""
        # Remove isolated nodes (nodes with no edges)
        isolated_nodes = list(nx.isolates(self.graph))
        for node in isolated_nodes:
            self.graph.remove_node(node)
            if node in self.nodes:
                del self.nodes[node]

        # Clean up edges that reference non-existent nodes
        edges_to_remove = []
        for edge_key in self.edges.keys():
            source_id, target_id, _ = edge_key
            if source_id not in self.nodes or target_id not in self.nodes:
                edges_to_remove.append(edge_key)

        for edge_key in edges_to_remove:
            del self.edges[edge_key]

        print(f"[GRAPH STORE]: Optimized graph, removed {len(isolated_nodes)} isolated nodes and {len(edges_to_remove)} invalid edges")

    async def export_graph(self, format: str = "json") -> Dict[str, Any]:
        """Export graph data for analysis or visualization"""
        if format == "json":
            return {
                "nodes": [
                    {"id": node_id, **node_data}
                    for node_id, node_data in self.nodes.items()
                ],
                "edges": [
                    {
                        "source": source_id,
                        "target": target_id,
                        "relation_type": relation_type,
                        **edge_data
                    }
                    for (source_id, target_id, relation_type), edge_data in self.edges.items()
                ],
                "relationship_types": self.relationship_types
            }
        else:
            # Return NetworkX graph for other formats
            return {
                "networkx_graph": self.graph,
                "nodes": self.nodes,
                "edges": self.edges,
                "relationship_types": self.relationship_types
            }

    async def get_stats(self) -> Dict[str, Any]:
        """Get graph store statistics"""
        num_nodes = len(self.nodes)
        num_edges = len(self.edges)

        # Calculate graph metrics
        if num_nodes > 0:
            # Average degree
            degrees = [len(list(self.graph.neighbors(node))) for node in self.graph.nodes()]
            avg_degree = sum(degrees) / len(degrees) if degrees else 0.0

            # Connected components
            connected_components = list(self.graph.subgraph(c) for c in nx.weakly_connected_components(self.graph))
            num_components = len(connected_components)

            # Largest component size
            largest_component = max(connected_components, key=len) if connected_components else self.graph
            largest_component_size = len(largest_component)
        else:
            avg_degree = 0.0
            num_components = 0
            largest_component_size = 0

        # Relationship type distribution
        relationship_counts = {}
        for (_, _, relation_type), _ in self.edges.items():
            relationship_counts[relation_type] = relationship_counts.get(relation_type, 0) + 1

        # Storage size
        total_size = sum(f.stat().st_size for f in self.storage_path.glob("*.pkl"))

        return {
            "total_nodes": num_nodes,
            "total_edges": num_edges,
            "average_degree": avg_degree,
            "num_connected_components": num_components,
            "largest_component_size": largest_component_size,
            "relationship_types": relationship_counts,
            "storage_size_mb": total_size / (1024 * 1024),
            "density": (2 * num_edges) / max(1, num_nodes * (num_nodes - 1))  # Graph density
        }
