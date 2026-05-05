from flask import Flask, request, jsonify
from flask_cors import CORS
from ollama_client import OllamaClient
from rag import RAG
from semantic_router import SemanticRouter, Route
from semantic_router.samples import productSample, chitchatSample
from reflection import Reflection
from embedding_model import EmbeddingModel
import os
from dotenv import load_dotenv

load_dotenv()

db_chat_history_collection = os.getenv(
    "DB_CHAT_HISTORY_COLLECTION",
    "chewy_chewy_chat_history"
)

semantic_cache_collection = os.getenv(
    "semanticCacheCollection",
    "chewy_chewy_semantic_cache"
)

db_path = "VECTOR_STORE"

app = Flask(__name__)
CORS(app)

embedding_model = EmbeddingModel()
llm = OllamaClient()

rag = RAG(
    collection1_name="chewy_chewy_aihi_01",
    collection2_name="chewy_chewy_aihi_02",
    db_path=db_path
)

PRODUCT_ROUTE_NAME = "products"
CHITCHAT_ROUTE_NAME = "chitchat"

productRoute = Route(name=PRODUCT_ROUTE_NAME, samples=productSample)
chitchatRoute = Route(name=CHITCHAT_ROUTE_NAME, samples=chitchatSample)

semanticRouter = SemanticRouter(routes=[productRoute, chitchatRoute])

reflection = Reflection(
    llm=llm,
    db_path=db_path,
    dbChatHistoryCollection=db_chat_history_collection,
    semanticCacheCollection=semantic_cache_collection
)


@app.route("/api/v1/chewy_chewy", methods=["POST"])
def chat():
    data = request.get_json(force=True)

    session_id = data.get("session_id", "default_session")
    query = data.get("query", "")

    if not query.strip():
        return jsonify({
            "role": "assistant",
            "content": "Bạn vui lòng nhập câu hỏi nhé."
        })

    guided_route = semanticRouter.guide(query)[1]
    print("semantic route:", guided_route)

    if guided_route == PRODUCT_ROUTE_NAME:
        query_embedding = embedding_model.get_embedding(query)

        source_information = rag.enhance_prompt(query)

        print("\n        SOURCE INFORMATION         ")
        print(source_information)
        print("--------------------------------------\n")

        combined_information = (
            f"Khách hỏi: {query}\n\n"
            f"Dưới đây là dữ liệu sản phẩm lấy từ hệ thống RAG:\n"
            f"{source_information}\n\n"
            f"Yêu cầu trả lời:\n"
            f"- Chỉ dùng thông tin trong dữ liệu sản phẩm ở trên.\n"
            f"- Nếu có sản phẩm phù hợp, hãy nêu tên, giá, mô tả ngắn.\n"
            f"- Nếu dữ liệu có EVENT CAKE thì hiểu đó là bánh sinh nhật.\n"
            f"- Không tự bịa sản phẩm ngoài dữ liệu.\n"
            f"- Không nói là không tìm thấy nếu dữ liệu bên trên đã có sản phẩm phù hợp.\n"
            f"- Trả lời ngắn gọn, thân thiện, dùng xưng hô 'mình' và 'bạn'."
        )

        response = reflection.chat(
            session_id=session_id,
            enhanced_message=combined_information,
            original_message=query,
            cache_response=False,
            query_embedding=query_embedding
        )

    else:
        response = reflection.chat(
            session_id=session_id,
            enhanced_message=query,
            original_message=query,
            cache_response=False
        )

    return jsonify({
        "role": "assistant",
        "content": response
    })


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=True)