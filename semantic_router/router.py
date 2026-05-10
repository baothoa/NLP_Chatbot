import os
import os

os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"

import re
import numpy as np
from sentence_transformers import SentenceTransformer


class SemanticRouter:
    def __init__(self, routes, threshold=0.45, debug=True):
        self.routes = routes
        self.threshold = threshold
        self.debug = debug

        print("Loading embedding model...")
        self.embedding_model = SentenceTransformer(
            "keepitreal/vietnamese-sbert",
            local_files_only=True,
        )

        self.routes_embedding_cal = {}

        for route in self.routes:
            embeddings = self.embedding_model.encode(route.samples)
            self.routes_embedding_cal[route.name] = self._normalize(embeddings)

        print("Semantic Router Ready")

    def _normalize(self, vectors):
        norm = np.linalg.norm(vectors, axis=1, keepdims=True)
        norm[norm == 0] = 1e-10
        return vectors / norm

    def _normalize_text(self, text):
        text = text.lower().strip()
        text = re.sub(r"\s+", " ", text)
        return text

    def get_routes(self):
        return self.routes

    def _match_keywords(self, query, keywords):
        for kw in keywords:
            if kw in query:
                return True
        return False

    def _match_regex(self, query, patterns):
        for pattern in patterns:
            if re.search(pattern, query):
                return True
        return False

    def _rule_based_route(self, query):

        # 1. OUT DOMAIN

        out_domain_keywords = [
            "điện thoại", "iphone", "samsung", "laptop", "macbook",
            "quần áo", "giày", "tai nghe", "máy tính", "xe máy",
            "vé máy bay", "khách sạn", "mỹ phẩm", "trà sữa",
            "cà phê", "bóng đá", "game", "bitcoin", "crypto",
            "chứng khoán", "cổ phiếu"
        ]

        if self._match_keywords(query, out_domain_keywords):
            return 0.0, "fallback"

        # 2. SUPPORT

        support_keywords = [
            "chưa nhận", "giao sai", "giao thiếu", "bị lỗi",
            "bánh lỗi", "bánh hư", "bánh móp",
            "khiếu nại", "hoàn tiền", "đổi đơn", "hủy đơn",
            "kiểm tra đơn", "mã đơn", "shipper chưa tới",
            "đơn hàng của mình", "đơn của mình", "chưa thấy giao"
        ]

        if self._match_keywords(query, support_keywords):
            return 0.99, "support"

        # 3. ORDER

        order_keywords = [
            "đặt", "order", "chốt đơn", "lên đơn",
            "mình lấy", "cho mình lấy",
            "mình mua", "cho mình mua",
            "ship cho mình", "giao cho mình"
        ]

        order_patterns = [
            r"\b\d+\s*(hộp|set|cái|bánh|phần)\b",
            r"\blấy\s+\d+",
            r"\bmua\s+\d+",
            r"\bđặt\s+\d+",
            r"\border\s+\d+"
        ]

        if (
            self._match_keywords(query, order_keywords)
            or self._match_regex(query, order_patterns)
        ):
            return 0.98, "order"

        # 4. DELIVERY

        delivery_keywords = [
            "ship", "giao hàng", "phí ship", "giao tới",
            "giao trong ngày", "bao lâu giao", "freeship",
            "địa chỉ giao", "giao được không", "giao tới đâu"
        ]

        if self._match_keywords(query, delivery_keywords):
            return 0.97, "delivery"

        # 5. STORAGE

        storage_keywords = [
            "bảo quản", "để được bao lâu", "để ngoài", "tủ lạnh",
            "hạn dùng", "qua đêm", "dùng trong mấy ngày",
            "mau hỏng", "giữ lạnh", "ăn trong ngày"
        ]

        if self._match_keywords(query, storage_keywords):
            return 0.96, "storage"

        # 6. PRICE

        price_keywords = [
            "giá", "bao nhiêu tiền", "bảng giá", "mắc không",
            "rẻ nhất", "dưới", "tầm giá", "khoảng bao nhiêu",
            "bao nhiêu một hộp", "bao nhiêu 1 hộp", "giá bao nhiêu", "dưới",
            "trên",
            "tầm",
            "tầm giá",
            "ngân sách",
            "khoảng giá",
        ]

        if self._match_keywords(query, price_keywords):
            return 0.95, "price"

        # 9. RECOMMEND

        recommend_keywords = [
            "tư vấn", "gợi ý", "nên chọn", "nên mua",
            "ít ngọt", "ngọt nhẹ", "best seller", "ngon nhất","ngon",
            "vị nào", "cho gia đình", "cho công ty",
            "cho người yêu","bao nhiêu người ăn","10 người","15 người","20 người",
            "sinh nhật", "làm quà", "tặng",
            "bạn gái", "bạn trai", "người yêu",
            "cho bé", "cho trẻ em", "ăn thử",
            "phù hợp", "ngân sách", "mua cho", "thích", "vị trái cây",
            "trái cây", 
            "matcha",
            "socola",
            "chocolate",
            "vanilla",
            "ít ngọt",
            "ngọt nhẹ",
            "vị trái cây",
            "trái cây",
            "fruit",
            "strawberry",
            "mango",
            "orange",
            "blueberry",
            "matcha",
            "vanilla",
            "socola",
            "chocolate",
            "nên chọn vị nào",
            "nên chọn",
            "gợi ý vị",
            "vị nào ngon",
        ]
        # 7. PRODUCT EXISTENCE QUERY

        exist_patterns = [
            r"co banh .* khong",
            r"co vi .* khong",
        ]

        if self._match_regex(query, exist_patterns):
            return 0.95, "price"

        if self._match_regex(query, exist_patterns):
            return 0.95, "price"

        # 7. MENU PRIORITY

        # Đặt MENU trước STORE để tránh lỗi:
        # "cửa hàng có những loại bánh nào" bị hiểu nhầm là store.

        menu_priority_keywords = [
            "loại bánh", "các loại bánh", "bánh gì",
            "menu", "bán gì", "có gì", "có món gì",
            "event cake", "bánh event", "bánh sự kiện",
            "set mini", "bánh su medium", "bánh su",
            "sản phẩm", "danh sách bánh",
            "những loại nào", "có những loại nào","những vị","các vị","vị bánh","hương vị"
        ]

        if self._match_keywords(query, menu_priority_keywords):
            return 0.94, "menu"

        # 8. STORE / OFFLINE BRANCH
        # Không dùng keyword "cửa hàng" đơn lẻ vì dễ nhầm với menu:
        # "cửa hàng bán bánh gì", "cửa hàng có loại nào".

        store_keywords = [
            "chi nhánh", "địa chỉ shop", "địa chỉ cửa hàng",
            "offline", "mua trực tiếp", "tới shop",
            "mở cửa", "đóng cửa", "giờ mở cửa",
            "shop ở đâu", "cửa hàng ở đâu",
            "địa chỉ ở đâu", "có bán trực tiếp không","quận",
            "q.",
            "q1",
            "q7",
            "hà nội",
            "đà nẵng",
            "cần thơ",
            "biên hòa",
            "có chi nhánh",
            "co chi nhanh",
            "quận",
            "quan",
            "q7",
            "quận 7",
            "quan 7",
            "quận",
            "quan",
            "phường",
            "phuong",
            "huyện",
            "huyen",
            "tỉnh",
            "tinh",
            "chi nhánh",
            "cửa hàng",
            "địa chỉ",
            "mua trực tiếp",
            "offline",
            "shop ở đâu",
        ]

        if self._match_keywords(query, store_keywords):
            return 0.93, "store"

    

        if self._match_keywords(query, recommend_keywords):
            return 0.92, "recommend"

        # 10. CHITCHAT

        chitchat_keywords = [
            "xin chào", "hello", "hi", "hey",
            "shop ơi", "alo", "cảm ơn", "thanks",
            "thank you", "tạm biệt", "bye",
            "bạn là ai", "bạn làm gì"
        ]

        if self._match_keywords(query, chitchat_keywords):
            return 1.0, "chitchat"

        return None

    def _semantic_route(self, query):
        query_embedding = self.embedding_model.encode([query])
        query_embedding = self._normalize(query_embedding)

        scores = []

        for route in self.routes:
            route_embeddings = self.routes_embedding_cal[route.name]

            similarities = np.dot(
                route_embeddings,
                query_embedding.T
            ).flatten()

            score = float(np.max(similarities))
            scores.append((score, route.name))

        scores.sort(reverse=True)
        best_score, best_route = scores[0]

        if self.debug:
            print("\n        ROUTER DEBUG       ")
            for score, route_name in scores[:5]:
                print(f"{route_name}: {score:.4f}")
            print("BEST:", best_route, best_score)
            print("                             \n")

        if best_score < self.threshold:
            return best_score, "fallback"

        return best_score, best_route

    def guide(self, query):
        if not query or not query.strip():
            return 0.0, "fallback"

        query = self._normalize_text(query)

        rule_result = self._rule_based_route(query)

        if rule_result is not None:
            if self.debug:
                print("\n        RULE ROUTER        ")
                print("QUERY:", query)
                print("RESULT:", rule_result)
                print("                             \n")

            return rule_result

        return self._semantic_route(query)