"""
This module contains utility functions used by the OpenOperator package.
"""
from typing import List
from urllib.parse import quote
from sklearn.cluster import DBSCAN
from sklearn.neighbors import NearestNeighbors
from kneed import KneeLocator
import numpy as np


def split_string_with_limit(text: str, limit: int, encoding) -> List[str]:
    """
    Splits a string into multiple parts with a limit on the number of tokens in each part.
    """
    tokens = encoding.encode(text)
    parts = []
    current_part = []
    current_count = 0

    for token in tokens:
        current_part.append(token)
        current_count += 1

        if current_count >= limit:
            parts.append(current_part)
            current_part = []
            current_count = 0

    if current_part:
        parts.append(current_part)

    text_parts = [encoding.decode(part) for part in parts]

    return text_parts


def create_uri(name: str) -> str:
    """
    Create a URI from string.
    """
    # name = re.sub(r'[^a-zA-Z0-9]', '', str(name).lower())
    # name = name.replace("'", "_")  # Replace ' with _
    name = quote(name.lower())
    return name


def dbscan_cluster(x):
    """
    DBSCAN clustering algorithm.
    """
    print("Clustering...")
    # Find the optimal epsilon
    nbrs = NearestNeighbors(n_neighbors=5).fit(x)

    distances = nbrs.kneighbors(x)

    distances = np.sort(distances, axis=0)

    kneedle = KneeLocator(
        range(1, distances.shape[0] + 1), distances[:, 1], curve="convex", direction="increasing"
    )

    db = DBSCAN(eps=kneedle.knee_y, min_samples=3).fit(x)
    labels = db.labels_

    # Number of clusters in labels, ignoring noise if present.
    n_clusters_ = len(set(labels)) - (1 if -1 in labels else 0)
    n_noise_ = list(labels).count(-1)

    print(f"Estimated number of clusters: {n_clusters_}")
    print(f"Estimated number of noise points: {n_noise_}")

    return labels
