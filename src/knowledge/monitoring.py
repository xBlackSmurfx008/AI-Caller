"""Monitoring and metrics for knowledge base"""

from typing import Dict, Any, Optional
from datetime import datetime
import time

from src.utils.logging import get_logger

logger = get_logger(__name__)


class KnowledgeBaseMetrics:
    """Metrics collection for knowledge base"""

    def __init__(self):
        """Initialize metrics"""
        self.metrics = {
            "queries_total": 0,
            "queries_cached": 0,
            "queries_failed": 0,
            "retrieval_latency_ms": [],
            "cache_hit_rate": 0.0,
            "average_relevance_score": 0.0,
            "documents_indexed": 0,
        }

    def record_query(
        self,
        cached: bool = False,
        failed: bool = False,
        latency_ms: Optional[float] = None,
    ) -> None:
        """Record query metrics"""
        self.metrics["queries_total"] += 1
        
        if cached:
            self.metrics["queries_cached"] += 1
        
        if failed:
            self.metrics["queries_failed"] += 1
        
        if latency_ms is not None:
            self.metrics["retrieval_latency_ms"].append(latency_ms)
            # Keep only last 1000 measurements
            if len(self.metrics["retrieval_latency_ms"]) > 1000:
                self.metrics["retrieval_latency_ms"] = self.metrics["retrieval_latency_ms"][-1000:]
            
            # Update cache hit rate
            if self.metrics["queries_total"] > 0:
                self.metrics["cache_hit_rate"] = (
                    self.metrics["queries_cached"] / self.metrics["queries_total"]
                )

    def record_relevance_score(self, score: float) -> None:
        """Record relevance score"""
        # Update running average
        total = self.metrics["queries_total"]
        current_avg = self.metrics["average_relevance_score"]
        
        if total == 0:
            self.metrics["average_relevance_score"] = score
        else:
            self.metrics["average_relevance_score"] = (
                (current_avg * total + score) / (total + 1)
            )

    def record_document_indexed(self) -> None:
        """Record document indexing"""
        self.metrics["documents_indexed"] += 1

    def get_metrics(self) -> Dict[str, Any]:
        """Get current metrics"""
        latency_ms = self.metrics["retrieval_latency_ms"]
        
        return {
            **self.metrics,
            "p95_latency_ms": self._percentile(latency_ms, 95) if latency_ms else 0.0,
            "p99_latency_ms": self._percentile(latency_ms, 99) if latency_ms else 0.0,
            "average_latency_ms": sum(latency_ms) / len(latency_ms) if latency_ms else 0.0,
        }

    def _percentile(self, data: list, percentile: float) -> float:
        """Calculate percentile"""
        if not data:
            return 0.0
        
        sorted_data = sorted(data)
        index = int(len(sorted_data) * percentile / 100)
        return sorted_data[min(index, len(sorted_data) - 1)]


class LatencyTracker:
    """Track operation latency"""

    def __init__(self):
        """Initialize latency tracker"""
        self.start_time: Optional[float] = None

    def start(self) -> None:
        """Start timing"""
        self.start_time = time.time()

    def stop(self) -> float:
        """Stop timing and return elapsed time in milliseconds"""
        if self.start_time is None:
            return 0.0
        
        elapsed = (time.time() - self.start_time) * 1000  # Convert to ms
        self.start_time = None
        return elapsed


# Global metrics instance
metrics = KnowledgeBaseMetrics()

