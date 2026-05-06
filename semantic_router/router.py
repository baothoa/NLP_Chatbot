import numpy as np
from sentence_transformers import SentenceTransformer


class SemanticRouter:
    def __init__(self, routes, threshold=0.40):
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
        # rule-based fix for common chitchat
        chitchat_keywords = ["bạn là ai", "bạn làm gì", "bạn là chatbot"]

        for kw in chitchat_keywords:
            if kw in query.lower():
                return 1.0, "chitchat"
            
        # keyword check (rule-based boost)
        out_domain_keywords = ["điện thoại", "laptop", "quần áo", "giày"]

        for kw in out_domain_keywords:
            if kw in query.lower():
                return 0.0, "fallback"

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

        # reject nếu query không liên quan đến bánh
        if best_route == "chitchat" and best_score < 0.5:
            return best_score, "fallback"

        if best_score < self.threshold:
            return best_score, "fallback"

        return best_score, best_route