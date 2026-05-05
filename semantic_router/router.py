import numpy as np
from sentence_transformers import SentenceTransformer


class SemanticRouter:
    def __init__(self, routes, threshold=0.45):
        self.routes = routes
        self.threshold = threshold
        self.embedding_model = SentenceTransformer("keepitreal/vietnamese-sbert")
        self.routes_embedding_cal = {}

        for route in self.routes:
            embeddings = self.embedding_model.encode(route.samples)
            self.routes_embedding_cal[route.name] = self._normalize(embeddings)

    def _normalize(self, vectors):
        return vectors / np.linalg.norm(vectors, axis=1, keepdims=True)

    def get_routes(self):
        return self.routes

    def guide(self, query):
        query_embedding = self.embedding_model.encode([query])
        query_embedding = self._normalize(query_embedding)

        scores = []

        for route in self.routes:
            route_embeddings = self.routes_embedding_cal[route.name]
            similarities = np.dot(route_embeddings, query_embedding.T).flatten()
            score = float(np.max(similarities))
            scores.append((score, route.name))

        scores.sort(reverse=True)

        best_score, best_route = scores[0]

        if best_score < self.threshold:
            return best_score, "fallback"

        return best_score, best_route