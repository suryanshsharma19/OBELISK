from app.ml.models.dbscan import dbscan_clustering
from app.core.logging import setup_logger
from typing import List, Dict, Any
import numpy as np

logger = setup_logger(__name__)

class ActorClusteringPipeline:
    def __init__(self):
        self.model = dbscan_clustering
        
    def extract_features(self, package_analysis_data: Dict[str, Any]) -> List[float]:
        """
        Extract behavioral and code signatures for clustering.
        Expects 3 core dimensions for a 3D scatter plot.
        1. Obfuscation Entropy (code level)
        2. Network Telemetry IPs (behavioral level)
        3. Sandbox Sandbox Filesystem Targets (heuristic level)
        """
        # Feature 1: Entropy & Naming
        code_score = package_analysis_data.get("code_analysis_score", 0.5)
        # Feature 2: Network / IPs
        net_score = len(package_analysis_data.get("network_connections", [])) * 0.1
        # Feature 3: Filesystem
        fs_score = len(package_analysis_data.get("filesystem_targets", [])) * 0.1
        
        return [float(code_score), float(net_score), float(fs_score)]

    def cluster_packages(self, packages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        if not packages:
            return []
            
        feature_matrix = []
        for pkg in packages:
            feats = self.extract_features(pkg)
            feature_matrix.append(feats)
            
        try:
            clustering_results = self.model.fit_predict(feature_matrix)
            
            for pkg, result in zip(packages, clustering_results):
                pkg["cti_attribution"] = result
                
            return packages
        except Exception as e:
            logger.error(f"Clustering failed: {e}")
            return packages

actor_clustering_pipeline = ActorClusteringPipeline()