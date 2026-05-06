import os
import re

import chromadb
from chromadb.utils import embedding_functions
from dotenv import load_dotenv

load_dotenv()

DEFAULT_SEARCH_LIMIT = int(os.getenv("DEFAULT_SEARCH_LIMIT", 10))

sentence_transformer_ef = embedding_functions.SentenceTransformerEmbeddingFunction(
    model_name="keepitreal/vietnamese-sbert"
)


class RAG:
    def __init__(self, collection1_name: str, collection2_name: str, db_path: str):
        self.client = chromadb.PersistentClient(path=db_path)

        self.collection1 = self.client.get_or_create_collection(
            name=collection1_name,
            embedding_function=sentence_transformer_ef,
        )

        self.collection2 = self.client.get_or_create_collection(
            name=collection2_name,
            embedding_function=sentence_transformer_ef,
        )

    def preprocess_text(self, text: str) -> str:
        if not text:
            return ""

        text = str(text).lower()
        text = re.sub(r"[^\w\s,.]", "", text)
        text = re.sub(r"\s+", " ", text).strip()

        return text

    def rewrite_query(self, query: str) -> str:
        query_lower = query.lower()

        birthday_keywords = [
            "sinh nhật",
            "birthday",
            "tiệc sinh nhật",
            "bánh sinh nhật",
            "tặng sinh nhật",
            "sự kiện",
            "event",
        ]

        chocolate_keywords = [
            "chocolate",
            "socola",
            "sô cô la",
            "cacao",
        ]

        cheap_keywords = [
            "rẻ",
            "dưới 200k",
            "dưới 200",
            "giá rẻ",
            "tầm 100k",
            "tầm 200k",
            "không quá 200",
        ]

        gift_keywords = [
            "tặng",
            "quà",
            "người yêu",
            "bạn gái",
            "bạn trai",
        ]

        expanded_query = query

        if any(keyword in query_lower for keyword in birthday_keywords):
            expanded_query += " EVENT CAKE bánh sinh nhật bánh sự kiện birthday cake"

        if any(keyword in query_lower for keyword in chocolate_keywords):
            expanded_query += " chocolate cake bánh chocolate bánh socola cacao"

        if any(keyword in query_lower for keyword in cheap_keywords):
            expanded_query += " giá bánh bánh giá rẻ price"

        if any(keyword in query_lower for keyword in gift_keywords):
            expanded_query += " bánh làm quà tặng bánh đẹp bánh phù hợp tặng người yêu"

        return expanded_query

    def parse_chroma_results(self, results):
        parsed = []

        if not results["ids"] or not results["ids"][0]:
            return parsed

        for i in range(len(results["ids"][0])):
            metadata = results["metadatas"][0][i]

            parsed.append(
                {
                    "_id": results["ids"][0][i],
                    "url": metadata.get("url", ""),
                    "title": metadata.get("title", ""),
                    "description": metadata.get("description", ""),
                    "price": metadata.get("price", ""),
                    "image_url": metadata.get("image_url", ""),
                    "category": metadata.get("category", ""),
                    "distance": results["distances"][0][i],
                }
            )

        return parsed

    def weighted_reciprocal_rank(self, doc_lists, weights=None, c=60):
        if weights is None:
            weights = [1] * len(doc_lists)

        if len(doc_lists) != len(weights):
            raise ValueError("Số lượng doc_lists phải bằng số lượng weights.")

        rrf_scores = {}
        doc_map = {}

        for doc_list, weight in zip(doc_lists, weights):
            for rank, doc in enumerate(doc_list, start=1):
                doc_id = doc["_id"]
                score = weight * (1 / (rank + c))

                if doc_id not in rrf_scores:
                    rrf_scores[doc_id] = 0.0
                    doc_map[doc_id] = doc

                rrf_scores[doc_id] += score

        sorted_ids = sorted(rrf_scores, key=rrf_scores.get, reverse=True)

        return [doc_map[doc_id] for doc_id in sorted_ids]

    def is_birthday_query(self, query: str) -> bool:
        query_lower = query.lower()

        birthday_keywords = [
            "sinh nhật",
            "birthday",
            "tiệc",
            "sự kiện",
            "event",
        ]

        return any(keyword in query_lower for keyword in birthday_keywords)

    def is_event_cake_doc(self, doc) -> bool:
        title = doc.get("title", "").upper()
        category = doc.get("category", "").upper()
        description = doc.get("description", "").upper()

        text = f"{title} {category} {description}"

        return "EVENT CAKE" in text or "SINH NHẬT" in text or "BIRTHDAY" in text

    def prioritize_event_cake(self, query: str, results):
        if not self.is_birthday_query(query):
            return results

        event_results = []
        other_results = []

        for result in results:
            if self.is_event_cake_doc(result):
                event_results.append(result)
            else:
                other_results.append(result)

        if event_results:
            return event_results + other_results

        event_cake_doc = {
            "_id": "manual_event_cake",
            "url": "",
            "title": "EVENT CAKE",
            "description": (
                "Bánh sinh nhật / bánh sự kiện của Chewy Chewy, phù hợp cho "
                "sinh nhật, tiệc và các dịp đặc biệt."
            ),
            "price": "Liên hệ tiệm để được tư vấn",
            "image_url": "",
            "category": "Bánh sinh nhật / Bánh sự kiện",
            "distance": 0.0,
        }

        return [event_cake_doc] + results

    def search_one(self, query, collection, limit):
        rewritten_query = self.rewrite_query(query)
        clean_query = self.preprocess_text(rewritten_query)

        raw_results = collection.query(
            query_texts=[query],
            n_results=limit,
        )

        rewritten_results = collection.query(
            query_texts=[rewritten_query],
            n_results=limit,
        )

        clean_results = collection.query(
            query_texts=[clean_query],
            n_results=limit,
        )

        parsed_raw = self.parse_chroma_results(raw_results)
        parsed_rewritten = self.parse_chroma_results(rewritten_results)
        parsed_clean = self.parse_chroma_results(clean_results)

        return self.weighted_reciprocal_rank(
            [parsed_raw, parsed_rewritten, parsed_clean],
            weights=[1, 3, 2],
        )

    def hybrid_search(self, query: str, limit=DEFAULT_SEARCH_LIMIT):
        if not query.strip():
            return []

        results1 = self.search_one(query, self.collection1, limit)
        results2 = self.search_one(query, self.collection2, limit)

        final_results = self.weighted_reciprocal_rank(
            doc_lists=[results1, results2],
            weights=[2, 1],
        )

        final_results = self.prioritize_event_cake(query, final_results)

        return final_results[:limit]

    def enhance_prompt(self, query: str, limit=DEFAULT_SEARCH_LIMIT):
        results = self.hybrid_search(query, limit)

        if not results:
            return "Không tìm thấy sản phẩm phù hợp."

        prompt = ""

        for i, result in enumerate(results, 1):
            prompt += (
                f"[Sản phẩm {i}]\n"
                f"Tên: {result['title']}\n"
                f"Giá: {result['price']}\n"
                f"Danh mục: {result['category']}\n"
                f"Mô tả: {result['description']}\n"
                f"Link: {result['url']}\n"
                f"Hình ảnh: {result['image_url']}\n\n"
            )

        return prompt

    def display_results(self, results):
        if not results:
            print("Không tìm thấy sản phẩm phù hợp.")
            return

        for i, result in enumerate(results, 1):
            print(f"Sản phẩm {i}:")
            print("Tên:", result["title"])
            print("Giá:", result["price"])
            print("Danh mục:", result["category"])
            print("Mô tả:", result["description"])
            print("Hình ảnh:", result["image_url"])
            print("Link:", result["url"])
            print("-" * 50)


if __name__ == "__main__":
    rag = RAG(
        "chewy_chewy_aihi_01",
        "chewy_chewy_aihi_02",
        "VECTOR_STORE",
    )

    query = "tôi muốn mua bánh sinh nhật cho bạn gái"

    results = rag.hybrid_search(query)

    rag.display_results(results)

    print("\nPROMPT\n")
    print(rag.enhance_prompt(query))