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
            }
        )

    score, guided_route = semantic_router.guide(query)

    print(f"Query: {query}")
    print(f"Semantic route: {guided_route} | Score: {score:.4f}")

    images = []

    if guided_route == PRODUCT_ROUTE_NAME:
        result = handle_product_query(session_id, query)

        if isinstance(result, dict):
            response = result["answer"]
            images = result["images"]
        else:
            response = result

    elif guided_route == CHITCHAT_ROUTE_NAME:
        response = handle_chitchat_query(session_id, query)

    else:
        response = handle_fallback_query()

    return jsonify(
        {
            "role": "assistant",
            "route": guided_route,
            "score": float(score),
            "content": response,
            "images": images,
        }
    )


def handle_product_query(session_id, query):
    
    query_embedding = embedding_model.get_embedding(query)
    source_information = rag.enhance_prompt(query)

    print("RAG context:\n", source_information)

    if "sinh nhật" in query.lower() and "EVENT CAKE" not in source_information:
        source_information += "\nTên bánh: EVENT CAKE\nMô tả: Bánh sinh nhật cho sự kiện, trang trí đẹp, phù hợp cho các dịp đặc biệt"

    if not source_information:
        return (
            "Hiện tại mình chưa tìm thấy thông tin sản phẩm phù hợp trong dữ liệu "
            "của Chewy Chewy. Bạn có thể mô tả rõ hơn loại bánh, dịp sử dụng "
            "hoặc khoảng giá mong muốn nhé."
        )

    product_prompt = build_product_prompt(query, source_information)

    answer = reflection.chat(
        session_id=session_id,
        enhanced_message=product_prompt,
        original_message=query,
        cache_response=False,
        query_embedding=query_embedding,
    )

    return {
        "answer": answer,
        "images": extract_image_urls(source_information),
    }
def extract_image_urls(source_information):
    image_urls = []

    for line in source_information.splitlines():
        if line.startswith("Hình ảnh:"):
            url = line.replace("Hình ảnh:", "").strip()

            if url:
                image_urls.append(url)

    return image_urls[:3]

def handle_chitchat_query(session_id, query):
    chitchat_prompt = f"""
Bạn là chatbot tư vấn bán bánh của tiệm Chewy Chewy.

Khách hàng nói:
{query}

Hãy trả lời ngắn gọn, thân thiện và tự nhiên.
Nếu phù hợp, hãy gợi ý khách có thể hỏi về bánh sinh nhật, bánh chocolate,
giá bánh hoặc bánh làm quà tặng.
Không bịa thông tin sản phẩm cụ thể nếu không có dữ liệu.
""".strip()

    return reflection.chat(
        session_id=session_id,
        enhanced_message=chitchat_prompt,
        original_message=query,
        cache_response=False,
    )


def handle_fallback_query():
    return (
        "Mình hiện chỉ hỗ trợ tư vấn các sản phẩm bánh của Chewy Chewy thôi. "
        "Bạn có thể hỏi mình về bánh sinh nhật, bánh chocolate, giá bánh, "
        "hoặc gợi ý bánh cho sinh nhật, tiệc và quà tặng nhé."
    )


def build_product_prompt(query, source_information):
    return f"""
Bạn là nhân viên tư vấn bán bánh của tiệm Chewy Chewy.

Phong cách trả lời:
- Thân thiện, tự nhiên, giống nhân viên tư vấn thật
- Xưng "mình" và "bạn"
- Có thể dùng emoji nhẹ nếu phù hợp
- Ngắn gọn, rõ ràng, dễ đọc

Câu hỏi của khách:
{query}

Thông tin sản phẩm từ hệ thống:
{source_information}

Yêu cầu trả lời:

1. Nếu có sản phẩm phù hợp:
   - Giới thiệu tự nhiên, không liệt kê quá khô
   - Nêu tên bánh, giá nếu có và mô tả ngắn
   - Thêm 1 câu gợi ý phù hợp với nhu cầu khách

2. Nếu có nhiều lựa chọn:
   - Gợi ý 2–3 bánh tiêu biểu

3. Nếu không có sản phẩm phù hợp:
   - Trả lời nhẹ nhàng:
     "Hiện tại mình chưa thấy mẫu bánh phù hợp, bạn có thể cho mình biết thêm về nhu cầu không?"

4. Tuyệt đối:
   - Không bịa thông tin
   - Không nói về hệ thống, AI, RAG, database
   - Không trả lời dài quá 5–6 dòng

5. Luôn kết thúc bằng 1 câu gợi ý tiếp, mang tính tư vấn hoặc upsell nhẹ.

Ví dụ cách trả lời:

"Hiện bên mình có bánh Chocolate Cake khá phù hợp cho sinh nhật.
Bánh có vị chocolate đậm, trang trí đẹp, rất hợp tặng bạn gái.

Nếu bạn muốn bánh nhẹ hơn, mình có thể gợi ý thêm vài mẫu khác nhé"
""".strip()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=True)