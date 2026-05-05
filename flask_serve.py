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

load_dotenv()

DB_CHAT_HISTORY_COLLECTION = os.getenv(
    "DB_CHAT_HISTORY_COLLECTION",
    "chewy_chewy_chat_history",
)
SEMANTIC_CACHE_COLLECTION = os.getenv(
    "SEMANTIC_CACHE_COLLECTION",
    "chewy_chewy_semantic_cache",
)

DB_PATH = "VECTOR_STORE"

PRODUCT_ROUTE_NAME = "products"
CHITCHAT_ROUTE_NAME = "chitchat"
FALLBACK_ROUTE_NAME = "fallback"

app = Flask(__name__)
CORS(app)

embedding_model = EmbeddingModel()
llm = OllamaClient()

rag = RAG(
    collection1_name="chewy_chewy_aihi_01",
    collection2_name="chewy_chewy_aihi_02",
    db_path=DB_PATH,
)

product_route = Route(name=PRODUCT_ROUTE_NAME, samples=productSample)
chitchat_route = Route(name=CHITCHAT_ROUTE_NAME, samples=chitchatSample)

semantic_router = SemanticRouter(
    routes=[product_route, chitchat_route],
    threshold=0.45,
)

reflection = Reflection(
    llm=llm,
    db_path=DB_PATH,
    dbChatHistoryCollection=DB_CHAT_HISTORY_COLLECTION,
    semanticCacheCollection=SEMANTIC_CACHE_COLLECTION,
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
                "content": "Bạn vui lòng nhập câu hỏi nhé.",
            }
        )

    score, guided_route = semantic_router.guide(query)
    print(f"Semantic route: {guided_route} | Score: {score:.4f}")

    if guided_route == PRODUCT_ROUTE_NAME:
        response = handle_product_query(session_id, query)

    elif guided_route == CHITCHAT_ROUTE_NAME:
        response = reflection.chat(
            session_id=session_id,
            enhanced_message=query,
            original_message=query,
            cache_response=False,
        )

    else:
        response = (
            "Mình chưa hiểu rõ câu hỏi của bạn. "
            "Bạn có thể hỏi mình về các loại bánh, giá bánh, mô tả bánh "
            "hoặc gợi ý bánh cho sinh nhật, tiệc và quà tặng nhé."
        )

    return jsonify(
        {
            "role": "assistant",
            "route": guided_route,
            "score": float(score),
            "content": response,
        }
    )


def handle_product_query(session_id, query):
    query_embedding = embedding_model.get_embedding(query)
    source_information = rag.enhance_prompt(query)

    if not source_information:
        return "Hiện tại mình chưa tìm thấy sản phẩm phù hợp trong dữ liệu Chewy Chewy."

    combined_information = build_product_prompt(query, source_information)

    return reflection.chat(
        session_id=session_id,
        enhanced_message=combined_information,
        original_message=query,
        cache_response=False,
        query_embedding=query_embedding,
    )


def build_product_prompt(query, source_information):
    return f"""
Bạn là chatbot tư vấn bán bánh cho tiệm bánh Chewy Chewy.

Câu hỏi của khách hàng:
{query}

Dữ liệu sản phẩm được truy xuất từ hệ thống RAG:
{source_information}

Quy tắc trả lời:
1. Chỉ sử dụng thông tin có trong dữ liệu sản phẩm ở trên.
2. Không tự tạo tên bánh, giá tiền, kích thước hoặc mô tả không có trong dữ liệu.
3. Nếu có sản phẩm phù hợp, hãy nêu:
   - Tên bánh
   - Giá nếu có
   - Mô tả ngắn
   - Vì sao phù hợp với nhu cầu khách hàng
4. Nếu dữ liệu có EVENT CAKE thì hiểu đó là bánh sinh nhật hoặc bánh cho sự kiện.
5. Nếu không có dữ liệu phù hợp, hãy nói rõ là hiện chưa có thông tin.
6. Trả lời bằng tiếng Việt, thân thiện, tự nhiên, dùng xưng hô "mình" và "bạn".
7. Không trả lời quá dài.
""".strip()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=True)