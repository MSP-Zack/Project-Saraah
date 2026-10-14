"""
Vector Store for Memory Embeddings
Provides vector-based storage and similarity search for memories.
Features:
- Embedding generation and storage
- Similarity search with various metrics
- Vector clustering and indexing
- Dimensionality reduction
- Batch processing
"""

import json
import asyncio
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import numpy as np
import pickle
from collections import defaultdict
import math

from . import MemoryEntry, MemoryMetadata

class VectorStore:
    """
    Vector database for storing and retrieving memory embeddings.
    Supports similarity search, clustering, and advanced vector operations.
    """

    def __init__(self, storage_path: Path, embedding_dim: int = 384):
        self.storage_path = storage_path
        self.storage_path.mkdir(exist_ok=True)

        self.embedding_dim = embedding_dim

        # Vector storage
        self.vectors: Dict[str, np.ndarray] = {}  # memory_id -> embedding vector
        self.metadata: Dict[str, Dict[str, Any]] = {}  # memory_id -> metadata
        self.index: Dict[str, List[str]] = defaultdict(list)  # cluster/category -> memory_ids

        # Search configuration
        self.similarity_metrics = {
            "cosine": self._cosine_similarity,
            "euclidean": self._euclidean_similarity,
            "dot_product": self._dot_product_similarity
        }
        self.default_metric = "cosine"

        # Clustering
        self.clusters: Dict[str, Dict[str, Any]] = {}
        self.cluster_centroids: Dict[str, np.ndarray] = {}

        print(f"[VECTOR STORE]: Initialized with {embedding_dim} dimensions at {storage_path}")

    async def store(self, memory_id: str, vector: np.ndarray, metadata: Dict[str, Any]):
        """Store a vector embedding with metadata"""
        if vector.shape[0] != self.embedding_dim:
            raise ValueError(f"Vector dimension {vector.shape[0]} does not match store dimension {self.embedding_dim}")

        self.vectors[memory_id] = vector.copy()
        self.metadata[memory_id] = metadata.copy()

        # Update indexes
        await self._update_indexes(memory_id, vector, metadata)

    async def _update_indexes(self, memory_id: str, vector: np.ndarray, metadata: Dict[str, Any]):
        """Update search indexes for the stored vector"""
        # Category-based indexing
        category = metadata.get("category", "general")
        self.index[category].append(memory_id)

        # Tag-based indexing
        tags = metadata.get("tags", [])
        for tag in tags:
            self.index[f"tag_{tag}"].append(memory_id)

        # Memory type indexing
        memory_type = metadata.get("memory_type", "unknown")
        self.index[f"type_{memory_type}"].append(memory_id)

    async def search(self, query_vector: np.ndarray, limit: int = 10,
                    filters: Dict[str, Any] = None, metric: str = None) -> List[Tuple[str, float]]:
        """
        Search for similar vectors

        Args:
            query_vector: Query embedding vector
            limit: Maximum number of results
            filters: Optional filters (category, tags, memory_type, etc.)
            metric: Similarity metric to use

        Returns:
            List of (memory_id, similarity_score) tuples
        """
        if metric is None:
            metric = self.default_metric

        if metric not in self.similarity_metrics:
            raise ValueError(f"Unknown similarity metric: {metric}")

        similarity_func = self.similarity_metrics[metric]

        # Get candidate vectors
        candidates = self._get_candidate_vectors(filters)

        # Calculate similarities
        similarities = []
        for memory_id in candidates:
            if memory_id in self.vectors:
                vector = self.vectors[memory_id]
                similarity = similarity_func(query_vector, vector)
                similarities.append((memory_id, similarity))

        # Sort by similarity (descending)
        similarities.sort(key=lambda x: x[1], reverse=True)

        return similarities[:limit]

    def _get_candidate_vectors(self, filters: Dict[str, Any] = None) -> List[str]:
        """Get candidate vector IDs based on filters"""
        if not filters:
            return list(self.vectors.keys())

        candidates = set()

        # Apply category filter
        if "category" in filters:
            category_candidates = set(self.index.get(filters["category"], []))
            if candidates:
                candidates = candidates.intersection(category_candidates)
            else:
                candidates = category_candidates

        # Apply tag filters
        if "tags" in filters:
            tag_candidates = set()
            for tag in filters["tags"]:
                tag_candidates.update(self.index.get(f"tag_{tag}", []))

            if tag_candidates:
                if candidates:
                    candidates = candidates.intersection(tag_candidates)
                else:
                    candidates = tag_candidates

        # Apply memory type filter
        if "memory_type" in filters:
            type_candidates = set(self.index.get(f"type_{filters['memory_type']}", []))
            if candidates:
                candidates = candidates.intersection(type_candidates)
            else:
                candidates = type_candidates

        # Apply date range filter
        if "date_range" in filters:
            start_date, end_date = filters["date_range"]
            date_candidates = set()

            for memory_id, meta in self.metadata.items():
                if "timestamp" in meta:
                    try:
                        memory_date = datetime.fromisoformat(meta["timestamp"]).date()
                        if start_date <= memory_date <= end_date:
                            date_candidates.add(memory_id)
                    except (ValueError, TypeError):
                        continue

            if date_candidates:
                if candidates:
                    candidates = candidates.intersection(date_candidates)
                else:
                    candidates = date_candidates

        # If no filters matched, return all vectors
        if not candidates and filters:
            return []
        elif not candidates:
            return list(self.vectors.keys())

        return list(candidates)

    def _cosine_similarity(self, v1: np.ndarray, v2: np.ndarray) -> float:
        """Calculate cosine similarity between two vectors"""
        dot_product = np.dot(v1, v2)
        norm1 = np.linalg.norm(v1)
        norm2 = np.linalg.norm(v2)

        if norm1 == 0 or norm2 == 0:
            return 0.0

        return dot_product / (norm1 * norm2)

    def _euclidean_similarity(self, v1: np.ndarray, v2: np.ndarray) -> float:
        """Calculate Euclidean similarity (inverse of distance)"""
        distance = np.linalg.norm(v1 - v2)
        # Convert distance to similarity (higher values = more similar)
        return 1.0 / (1.0 + distance)

    def _dot_product_similarity(self, v1: np.ndarray, v2: np.ndarray) -> float:
        """Calculate dot product similarity"""
        return np.dot(v1, v2)

    async def find_similar(self, memory_id: str, limit: int = 5) -> List[Tuple[str, float]]:
        """Find memories similar to a given memory"""
        if memory_id not in self.vectors:
            return []

        query_vector = self.vectors[memory_id]
        # Exclude the memory itself
        results = await self.search(query_vector, limit + 1)
        return [(mid, score) for mid, score in results if mid != memory_id][:limit]

    async def cluster_vectors(self, n_clusters: int = 10, method: str = "kmeans"):
        """Cluster vectors for better organization"""
        if len(self.vectors) < n_clusters:
            print(f"[VECTOR STORE]: Not enough vectors ({len(self.vectors)}) for {n_clusters} clusters")
            return

        vectors = list(self.vectors.values())
        memory_ids = list(self.vectors.keys())

        # Simple k-means clustering (in production, use sklearn or similar)
        centroids, labels = self._simple_kmeans(vectors, n_clusters)

        # Store cluster information
        self.clusters = {}
        self.cluster_centroids = {}

        for i in range(n_clusters):
            cluster_ids = [memory_ids[j] for j in range(len(labels)) if labels[j] == i]

            self.clusters[f"cluster_{i}"] = {
                "centroid_id": f"centroid_{i}",
                "memory_ids": cluster_ids,
                "size": len(cluster_ids),
                "created": datetime.now().isoformat()
            }

            self.cluster_centroids[f"centroid_{i}"] = centroids[i]

        print(f"[VECTOR STORE]: Created {n_clusters} clusters")

    def _simple_kmeans(self, vectors: List[np.ndarray], n_clusters: int,
                      max_iter: int = 100) -> Tuple[List[np.ndarray], List[int]]:
        """Simple k-means implementation"""
        # Initialize centroids randomly
        np.random.seed(42)
        indices = np.random.choice(len(vectors), n_clusters, replace=False)
        centroids = [vectors[i].copy() for i in indices]

        labels = [0] * len(vectors)

        for _ in range(max_iter):
            # Assign points to nearest centroid
            changed = False
            for i, vector in enumerate(vectors):
                distances = [np.linalg.norm(vector - centroid) for centroid in centroids]
                new_label = np.argmin(distances)

                if labels[i] != new_label:
                    labels[i] = new_label
                    changed = True

            if not changed:
                break

            # Update centroids
            for j in range(n_clusters):
                cluster_points = [vectors[i] for i in range(len(vectors)) if labels[i] == j]
                if cluster_points:
                    centroids[j] = np.mean(cluster_points, axis=0)

        return centroids, labels

    async def get_cluster_info(self, cluster_id: str) -> Optional[Dict[str, Any]]:
        """Get information about a cluster"""
        return self.clusters.get(cluster_id)

    async def search_in_cluster(self, cluster_id: str, query_vector: np.ndarray,
                              limit: int = 5) -> List[Tuple[str, float]]:
        """Search within a specific cluster"""
        if cluster_id not in self.clusters:
            return []

        cluster_memory_ids = self.clusters[cluster_id]["memory_ids"]

        # Search only within cluster
        similarities = []
        for memory_id in cluster_memory_ids:
            if memory_id in self.vectors:
                vector = self.vectors[memory_id]
                similarity = self._cosine_similarity(query_vector, vector)
                similarities.append((memory_id, similarity))

        similarities.sort(key=lambda x: x[1], reverse=True)
        return similarities[:limit]

    async def get_statistics(self) -> Dict[str, Any]:
        """Get vector store statistics"""
        total_vectors = len(self.vectors)
        total_categories = len([k for k in self.index.keys() if not k.startswith("tag_") and not k.startswith("type_")])
        total_tags = len([k for k in self.index.keys() if k.startswith("tag_")])
        total_types = len([k for k in self.index.keys() if k.startswith("type_")])

        # Vector statistics
        if total_vectors > 0:
            vector_norms = [np.linalg.norm(v) for v in self.vectors.values()]
            avg_norm = np.mean(vector_norms)
            min_norm = np.min(vector_norms)
            max_norm = np.max(vector_norms)
        else:
            avg_norm = min_norm = max_norm = 0.0

        # Cluster statistics
        total_clusters = len(self.clusters)
        avg_cluster_size = np.mean([c["size"] for c in self.clusters.values()]) if self.clusters else 0

        return {
            "total_vectors": total_vectors,
            "embedding_dimension": self.embedding_dim,
            "total_categories": total_categories,
            "total_tags": total_tags,
            "total_memory_types": total_types,
            "vector_norm_stats": {
                "average": float(avg_norm),
                "minimum": float(min_norm),
                "maximum": float(max_norm)
            },
            "clustering_stats": {
                "total_clusters": total_clusters,
                "avg_cluster_size": float(avg_cluster_size)
            },
            "storage_size_mb": self._calculate_storage_size()
        }

    def _calculate_storage_size(self) -> float:
        """Calculate approximate storage size in MB"""
        # Rough estimate: each vector is embedding_dim * 4 bytes (float32)
        vector_size = len(self.vectors) * self.embedding_dim * 4

        # Metadata size (rough estimate)
        metadata_size = len(self.metadata) * 1000  # ~1KB per metadata entry

        # Index size
        index_size = sum(len(ids) * 50 for ids in self.index.values())  # ~50 bytes per index entry

        total_bytes = vector_size + metadata_size + index_size
        return total_bytes / (1024 * 1024)

    async def save(self):
        """Save vector store to disk"""
        # Save vectors
        vectors_file = self.storage_path / "vectors.pkl"
        with open(vectors_file, 'wb') as f:
            pickle.dump(self.vectors, f)

        # Save metadata
        metadata_file = self.storage_path / "metadata.json"
        with open(metadata_file, 'w', encoding='utf-8') as f:
            # Convert numpy types to Python types for JSON serialization
            serializable_metadata = {}
            for memory_id, meta in self.metadata.items():
                serializable_metadata[memory_id] = meta.copy()
                # Convert any numpy types in metadata
                for key, value in serializable_metadata[memory_id].items():
                    if isinstance(value, np.ndarray):
                        serializable_metadata[memory_id][key] = value.tolist()
                    elif isinstance(value, (np.int64, np.int32)):
                        serializable_metadata[memory_id][key] = int(value)
                    elif isinstance(value, (np.float64, np.float32)):
                        serializable_metadata[memory_id][key] = float(value)

            json.dump(serializable_metadata, f, indent=2)

        # Save indexes
        index_file = self.storage_path / "index.json"
        with open(index_file, 'w', encoding='utf-8') as f:
            json.dump(dict(self.index), f, indent=2)

        # Save clusters
        if self.clusters:
            clusters_file = self.storage_path / "clusters.pkl"
            with open(clusters_file, 'wb') as f:
                pickle.dump({
                    "clusters": self.clusters,
                    "centroids": self.cluster_centroids
                }, f)

    async def load(self):
        """Load vector store from disk"""
        # Load vectors
        vectors_file = self.storage_path / "vectors.pkl"
        if vectors_file.exists():
            with open(vectors_file, 'rb') as f:
                self.vectors = pickle.load(f)

        # Load metadata
        metadata_file = self.storage_path / "metadata.json"
        if metadata_file.exists():
            with open(metadata_file, 'r', encoding='utf-8') as f:
                self.metadata = json.load(f)

        # Load indexes
        index_file = self.storage_path / "index.json"
        if index_file.exists():
            with open(index_file, 'r', encoding='utf-8') as f:
                self.index = defaultdict(list, json.load(f))

        # Load clusters
        clusters_file = self.storage_path / "clusters.pkl"
        if clusters_file.exists():
            with open(clusters_file, 'rb') as f:
                cluster_data = pickle.load(f)
                self.clusters = cluster_data.get("clusters", {})
                self.cluster_centroids = cluster_data.get("centroids", {})

        print(f"[VECTOR STORE]: Loaded {len(self.vectors)} vectors")

    async def clear(self):
        """Clear all stored vectors and indexes"""
        self.vectors.clear()
        self.metadata.clear()
        self.index.clear()
        self.clusters.clear()
        self.cluster_centroids.clear()
        print(f"[VECTOR STORE]: Cleared all data")

    async def optimize(self):
        """Optimize vector store for better performance"""
        # Remove empty index entries
        self.index = defaultdict(list, {k: v for k, v in self.index.items() if v})

        # Rebuild clusters if needed
        if len(self.vectors) > 10 and not self.clusters:
            await self.cluster_vectors(min(10, len(self.vectors) // 2))

        print(f"[VECTOR STORE]: Optimized vector store")

    async def export_embeddings(self, memory_ids: List[str] = None) -> Dict[str, Any]:
        """Export embeddings for analysis or backup"""
        if memory_ids is None:
            memory_ids = list(self.vectors.keys())

        export_data = {}
        for memory_id in memory_ids:
            if memory_id in self.vectors and memory_id in self.metadata:
                export_data[memory_id] = {
                    "vector": self.vectors[memory_id].tolist(),
                    "metadata": self.metadata[memory_id]
                }

        return export_data

    async def get_stats(self) -> Dict[str, Any]:
        """Get vector store statistics"""
        total_vectors = len(self.vectors)
        vector_dims = self.embedding_dim

        # Calculate average vector magnitude
        if total_vectors > 0:
            magnitudes = [np.linalg.norm(vec) for vec in self.vectors.values()]
            avg_magnitude = sum(magnitudes) / len(magnitudes)
        else:
            avg_magnitude = 0.0

        # Storage size
        total_size = sum(f.stat().st_size for f in self.storage_path.glob("*.pkl"))

        return {
            "total_vectors": total_vectors,
            "vector_dimensions": vector_dims,
            "average_magnitude": avg_magnitude,
            "num_clusters": len(self.clusters),
            "storage_size_mb": total_size / (1024 * 1024),
            "utilization": total_vectors / max(1, 1000)  # Assuming 1000 max capacity
        }

        return export_data