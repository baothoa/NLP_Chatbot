import os

from dotenv import load_dotenv
from flask import Flask, jsonify, request
from flask_cors import CORS

from embedding_model import EmbeddingModel
from ollama_client import OllamaClient
from rag import RAG
from reflection import Reflection
from semantic_router import Route, SemanticRouter
from semantic_router.samples import chitchatSample, productSample

from guards.product_guard import is_product_found
from guards.scope_guard import (
    is_related_to_bakery,
    detect_unsupported_info,
    out_of_scope_response,
    unsupported_info_response,
)
from response_builder.product_card import build_product_cards_from_context

load_dotenv()

DB_CHAT_HISTORY_COLLECTION = os.getenv(
    "DB_CHAT_HISTORY_COLLECTION",
    "chewy_chewy_chat_history",
)
SEMANTIC_CACHE_COLLECTION = os.getenv(
    "SEMANTIC_CACHE_COLLECTION",
    "chewy_chewy_semantic_cache",
)

DB_PATH = os.getenv("DB_PATH", "VECTOR_STORE")

PRODUCT_ROUTE_NAME = "products"
CHITCHAT_ROUTE_NAME = "chitchat"
FALLBACK_ROUTE_NAME = "fallback"

app = Flask(__name__)
CORS(app)

embedding_model = EmbeddingModel()
llm = OllamaClient()

rag = RAG(
    collection1_name=os.getenv("PRODUCT_COLLECTION_1", "chewy_chewy_aihi_01"),
    collection2_name=os.getenv("PRODUCT_COLLECTION_2", "chewy_chewy_aihi_02"),
    db_path=DB_PATH,
)

product_route = Route(name=PRODUCT_ROUTE_NAME, samples=productSample)
chitchat_route = Route(name=CHITCHAT_ROUTE_NAME, samples=chitchatSample)

semantic_router = SemanticRouter(
    routes=[product_route, chitchat_route],
    threshold=float(os.getenv("ROUTER_THRESHOLD", "0.45")),
)

reflection = Reflection(
    llm=llm,
    db_path=DB_PATH,
    dbChatHistoryCollection=DB_CHAT_HISTORY_COLLECTION,
    semanticCacheCollection=SEMANTIC_CACHE_COLLECTION,
)


@app.route("/", methods=["GET"])
def home():
    return jsonify(
        {
            "message": "Chewy Chewy AI Chatbot API is running.",
            "endpoint": "/api/v1/chewy_chewy",
        }
    )


@app.route("/api/v1/chewy_chewy", methods=["POST"])
def chat():
    data = request.get_json(force=True)

    session_id = data.get("session_id", "default_session")
    query = data.get("query", "").strip()

    if not query:
        return jsonify(
            {
                "role": "assistant",
                "route": FALLBACK_ROUTE_NAME,
                "score": 0.0,
                "content": "Bạn vui lòng nhập câu hỏi nhé.",
                "products": [],
            }
        )

    print(f"Query: {query}")

    # 1. Semantic router chạy trước để nhận chitchat nhẹ
    score, guided_route = semantic_router.guide(query)
    print(f"Semantic route: {guided_route} | Score: {score:.4f}")

    # 2. Cho phép chào hỏi / cảm ơn
    if guided_route == CHITCHAT_ROUTE_NAME:
        response = handle_chitchat_query(session_id, query)

        return jsonify(
            {
                "role": "assistant",
                "route": guided_route,
                "score": float(score),
                "content": response,
                "products": [],
            }
        )

    # 3. Chặn câu hỏi ngoài phạm vi
    if not is_related_to_bakery(query):
        return jsonify(
            {
                "role": "assistant",
                "route": "out_of_scope",
                "score": 0.0,
                "content": out_of_scope_response(),
                "products": [],
            }
        )

    # 4. Chặn thông tin chưa có trong data
    unsupported_keyword = detect_unsupported_info(query)
    if unsupported_keyword:
        return jsonify(
            {
                "role": "assistant",
                "route": "unsupported_info",
                "score": 0.0,
                "content": unsupported_info_response(unsupported_keyword),
                "products": [],
            }
        )

    # 5. Xử lý câu hỏi sản phẩm
    if guided_route == PRODUCT_ROUTE_NAME:
        result = handle_product_query(session_id, query)

        return jsonify(
            {
                "role": "assistant",
                "route": guided_route,
                "score": float(score),
                "content": result["answer"],
                "products": result["products"],
            }
        )

    # 6. Fallback
    return jsonify(
        {
            "role": "assistant",
            "route": FALLBACK_ROUTE_NAME,
            "score": float(score),
            "content": handle_fallback_query(),
            "products": [],
        }
    )


def handle_product_query(session_id, query):
    query_embedding = embedding_model.get_embedding(query)

    source_information = rag.enhance_prompt(query)

    print("RAG context:\n", source_information)

    if not is_product_found(source_information):
        fallback_context = rag.enhance_prompt("bánh bán chạy phù hợp để tặng")
        fallback_products = build_product_cards_from_context(fallback_context)

        return {
            "answer": (
                "Dạ hiện tại mình chưa tìm thấy sản phẩm này trong dữ liệu Chewy Chewy ạ. "
                "Bạn có thể tham khảo một vài mẫu bánh đang có bên dưới nhé."
            ),
            "products": fallback_products,
        }

    product_prompt = build_product_prompt(query, source_information)

    answer = reflection.chat(
        session_id=session_id,
        enhanced_message=product_prompt,
        original_message=query,
        cache_response=False,
        query_embedding=query_embedding,
    )

    product_cards = build_product_cards_from_context(source_information)

    return {
        "answer": answer,
        "products": product_cards,
    }


def handle_chitchat_query(session_id, query):
    query_lower = query.lower().strip()

    # ===== GREETING =====
    greeting_words = [
        "xin chào",
        "hello",
        "hi",
        "hey",
        "chào"
    ]

    if any(word in query_lower for word in greeting_words):
        return (
            "Xin chào bạn 👋 "
            "Mình là trợ lý tư vấn của Chewy Chewy. "
            "Bạn muốn tìm bánh sinh nhật, bánh chocolate "
            "hay bánh làm quà tặng ạ?"
        )

    # ===== THANKS =====
    thanks_words = [
        "cảm ơn",
        "thanks",
        "thank you"
    ]

    if any(word in query_lower for word in thanks_words):
        return (
            "Dạ không có gì ạ 😊 "
            "Bạn cần mình gợi ý thêm mẫu bánh nào không?"
        )

    # ===== BYE =====
    bye_words = [
        "bye",
        "tạm biệt",
        "hẹn gặp lại"
    ]

    if any(word in query_lower for word in bye_words):
        return (
            "Dạ cảm ơn bạn đã ghé Chewy Chewy 💖 "
            "Chúc bạn một ngày thật ngọt ngào nhé!"
        )

    # ===== LLM FALLBACK =====
    chitchat_prompt = f"""
Bạn là nhân viên tư vấn bánh của Chewy Chewy.

Khách hàng nói:
{query}

Hãy trả lời:
- ngắn gọn
- tự nhiên
- thân thiện
- giống nhân viên thật

Không được:
- nói về AI
- nói về hệ thống
- nói về RAG
- nói về database

Nếu phù hợp, hãy nhẹ nhàng gợi ý khách xem bánh sinh nhật,
bánh chocolate hoặc bánh làm quà tặng.
""".strip()

    try:
        return reflection.chat(
            session_id=session_id,
            enhanced_message=chitchat_prompt,
            original_message=query,
            cache_response=False,
        )

    except Exception:
        return (
            "Mình có thể hỗ trợ bạn tư vấn bánh của Chewy Chewy ạ 😊"
        )


def handle_fallback_query():
    return (
        "Mình hiện chỉ hỗ trợ tư vấn các sản phẩm bánh của Chewy Chewy thôi. "
        "Bạn có thể hỏi mình về bánh sinh nhật, bánh chocolate, giá bánh, "
        "hoặc gợi ý bánh cho sinh nhật, tiệc và quà tặng nhé."
    )


def build_product_prompt(query, source_information):
    return f"""
Bạn là nhân viên tư vấn bánh của Chewy Chewy.

KHÔNG được trả lời như AI chatbot.

Phong cách:
- ngắn gọn
- tự nhiên
- giống nhân viên bán bánh thật
- không lan man
- không dùng từ sáo rỗng

Khách hỏi:
{query}

Thông tin sản phẩm:
{source_information}

Quy tắc cực kỳ quan trọng:

1. CHỈ được tư vấn dựa trên thông tin sản phẩm ở trên.

2. Nếu có sản phẩm:
- giới thiệu tối đa 2-3 sản phẩm
- nói ngắn gọn
- nêu:
  + tên bánh
  + giá nếu có
  + điểm nổi bật

3. KHÔNG được:
- nói "AI"
- nói "RAG"
- nói "dữ liệu"
- nói "hệ thống"
- nói dài dòng
- nói sáo rỗng
- nói như trợ lý ảo

4. Nếu khách hỏi bánh sinh nhật:
- ưu tiên EVENT CAKE nếu có

5. Nếu không có sản phẩm phù hợp:
hãy trả lời đúng câu này:

"Hiện tại bên mình chưa có mẫu bánh này ạ 😢
Bạn có thể tham khảo một số mẫu bánh khác bên dưới nhé."

6. Câu trả lời tối đa 4 dòng.

7. Kết thúc bằng đúng 1 câu gợi ý ngắn.
Ví dụ:
- "Bạn thích vị chocolate hay matcha hơn ạ?"
- "Bạn muốn mình gợi ý thêm mẫu mini không?"
""".strip()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=True)