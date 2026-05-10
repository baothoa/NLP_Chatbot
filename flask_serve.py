import os
import json
import unicodedata
import re
from datetime import datetime

from dotenv import load_dotenv
from flask import Flask, jsonify, request
from flask_cors import CORS

from embedding_model import EmbeddingModel
from ollama_client import OllamaClient
from rag import RAG
from reflection import Reflection

from semantic_router import Route, SemanticRouter
from semantic_router.samples import (
    menuSample,
    priceSample,
    recommendSample,
    orderSample,
    deliverySample,
    storeSample,
    storageSample,
    supportSample,
    chitchatSample,
)

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

MENU_ROUTE_NAME = "menu"
PRICE_ROUTE_NAME = "price"
RECOMMEND_ROUTE_NAME = "recommend"
ORDER_ROUTE_NAME = "order"
DELIVERY_ROUTE_NAME = "delivery"
STORE_ROUTE_NAME = "store"
STORAGE_ROUTE_NAME = "storage"
SUPPORT_ROUTE_NAME = "support"
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

routes = [
    Route(name=MENU_ROUTE_NAME, samples=menuSample),
    Route(name=PRICE_ROUTE_NAME, samples=priceSample),
    Route(name=RECOMMEND_ROUTE_NAME, samples=recommendSample),
    Route(name=ORDER_ROUTE_NAME, samples=orderSample),
    Route(name=DELIVERY_ROUTE_NAME, samples=deliverySample),
    Route(name=STORE_ROUTE_NAME, samples=storeSample),
    Route(name=STORAGE_ROUTE_NAME, samples=storageSample),
    Route(name=SUPPORT_ROUTE_NAME, samples=supportSample),
    Route(name=CHITCHAT_ROUTE_NAME, samples=chitchatSample),
]

semantic_router = SemanticRouter(
    routes=routes,
    threshold=float(os.getenv("ROUTER_THRESHOLD", "0.45")),
)

reflection = Reflection(
    llm=llm,
    db_path=DB_PATH,
    dbChatHistoryCollection=DB_CHAT_HISTORY_COLLECTION,
    semanticCacheCollection=SEMANTIC_CACHE_COLLECTION,
)

order_sessions = {}
user_contexts = {}

STORE_DATA_PATH = "output_files/chewychewy_stores.json"
PRODUCT_DATA_PATH = "output_files/chewychewy_products.json"

try:
    with open(STORE_DATA_PATH, "r", encoding="utf-8") as f:
        STORES_DATA = json.load(f)
except FileNotFoundError:
    STORES_DATA = []
    print(f"Không tìm thấy file store data: {STORE_DATA_PATH}")

try:
    with open(PRODUCT_DATA_PATH, "r", encoding="utf-8") as f:
        PRODUCTS_DATA = json.load(f)
except FileNotFoundError:
    PRODUCTS_DATA = []
    print(f"Không tìm thấy file product data: {PRODUCT_DATA_PATH}")

def normalize_vietnamese(text):
    if not text:
        return ""

    text = text.lower().strip()
    text = unicodedata.normalize("NFD", text)
    text = "".join(
        char for char in text
        if unicodedata.category(char) != "Mn"
    )
    text = text.replace("đ", "d")
    return text

# AUTO TAGGING PRODUCT METADATA
for product in PRODUCTS_DATA:
    searchable_text = normalize_vietnamese(
        product.get("title", "")
        + " "
        + product.get("description", "")
    )

    flavors = []

    flavor_map = {
        "vanilla": ["vanilla", "vani"],
        "matcha": ["matcha", "tra xanh"],
        "chocolate": ["socola", "chocolate"],
        "strawberry": ["dau", "strawberry"],
        "mango": ["xoai", "mango"],
        "orange": ["orange", "cam"],
        "oreo": ["oreo"],
        "cheese": ["pho mai", "cheese"],
        "yogurt": ["yogurt", "sua chua"],
        "red velvet": ["red velvet"],
        "almond": ["hanh nhan", "almond"],
    }

    for flavor_name, keywords in flavor_map.items():
        if any(keyword in searchable_text for keyword in keywords):
            flavors.append(flavor_name)

    product["flavors"] = flavors

    low_sweet_keywords = [
        "matcha",
        "vanilla",
        "strawberry",
        "dau",
        "mango",
        "xoai",
        "orange",
        "cam",
        "yogurt",
        "sua chua",
    ]

    if any(keyword in searchable_text for keyword in low_sweet_keywords):
        product["sweetness"] = "low"
    else:
        product["sweetness"] = "normal"

    category_text = normalize_vietnamese(product.get("category", ""))

    if "event" in category_text:
        product["category_tag"] = "event cake"
    elif "mini" in category_text:
        product["category_tag"] = "set mini"
    elif "medium" in category_text:
        product["category_tag"] = "medium"
    else:
        product["category_tag"] = "other"
        
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
    query_norm = normalize_vietnamese(query)

    if session_id not in user_contexts:
        user_contexts[session_id] = {
            "last_category": None
        }

    if "set mini" in query_norm or "mini" in query_norm:
        user_contexts[session_id]["last_category"] = "set mini"

    elif "event cake" in query_norm or "banh event" in query_norm or "sinh nhat" in query_norm:
        user_contexts[session_id]["last_category"] = "event cake"

    elif "banh su" in query_norm or "medium" in query_norm:
        user_contexts[session_id]["last_category"] = "medium"

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

    # 1. Nếu session đang trong order flow
    # thì KHÔNG chạy router nữa
    store_keywords = [
        "shop ở đâu",
        "mua trực tiếp",
        "cửa hàng",
        "chi nhánh",
        "địa chỉ",
        "offline",
    ]

    if any(keyword in query_norm for keyword in store_keywords):
        score = 1.0
        intent = STORE_ROUTE_NAME
    else:
        score, intent = semantic_router.guide(query)

    print(f"Semantic route: {intent} | Score: {score:.4f}")

    # 2. Chitchat
    if intent == CHITCHAT_ROUTE_NAME:
        response = handle_chitchat_query(session_id, query)

        return jsonify(
            {
                "role": "assistant",
                "route": intent,
                "score": float(score),
                "content": response,
                "products": [],
            }
        )

    # 3. Support
    
    if intent == SUPPORT_ROUTE_NAME:
        response = handle_support_query(query)

        return jsonify(
            {
                "role": "assistant",
                "route": intent,
                "score": float(score),
                "content": response,
                "products": [],
            }
        )

    # 4. Order flow
    if intent == ORDER_ROUTE_NAME:
        response = handle_order_query(session_id, query)

        return jsonify(
            {
                "role": "assistant",
                "route": intent,
                "score": float(score),
                "content": response,
                "products": [],
            }
        )

    # 5. Out of scope

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

    # 6. Unsupported info

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

    # 7. Product RAG intents

    product_exist_check_keywords = [
        "co banh",
        "co loai",
        "shop co ban",
        "có bánh",
        "có bán",
    ]

    exclude_keywords = [
        "rẻ nhất",
        "ít ngọt",
        "dưới",
        "bao nhiêu tiền",
        "ngon",
        "gợi ý",
        "tư vấn",
    ]

    should_check_product_exist = (
        any(keyword in query_norm for keyword in product_exist_check_keywords)
        and not any(keyword in query_norm for keyword in exclude_keywords)
    )

    if should_check_product_exist:
        if not product_exists_in_data(query):
            return jsonify(
                {
                    "role": "assistant",
                    "route": "product_not_found",
                    "score": float(score),
                    "content": (
                        "Dạ hiện tại mình chưa tìm thấy sản phẩm bạn hỏi "
                        "trong dữ liệu của Chewy Chewy ạ. "
                        "Bạn có thể tham khảo các dòng bánh hiện có như "
                        "Set Mini, Event Cake hoặc Bánh su Medium nhé."
                    ),
                    "products": [],
                }
            )
    if intent == RECOMMEND_ROUTE_NAME:
        result = handle_recommend_query(query, session_id)

        if isinstance(result, str):
            result = {
                "answer": result,
                "products": []
            }

        return jsonify(
            {
                "role": "assistant",
                "route": intent,
                "score": float(score),
                "content": result["answer"],
                "products": result["products"],
            }
        )
    flavor_result = handle_flavor_existence_query(query, session_id)

    if flavor_result is not None:
        return jsonify(
            {
                "role": "assistant",
                "route": "flavor_check",
                "score": float(score),
                "content": flavor_result["answer"],
                "products": flavor_result["products"],
            }
        )

    if intent == PRICE_ROUTE_NAME:
        result = handle_cheapest_query(query)

        if result is None:
            result = handle_price_filter_query(query, session_id)

        if result is None:
            result = handle_product_query(session_id, query)

        return jsonify(
            {
                "role": "assistant",
                "route": intent,
                "score": float(score),
                "content": result["answer"],
                "products": result["products"],
            }
        )
    # 8. FAQ intents

    if intent == DELIVERY_ROUTE_NAME:
        response = handle_delivery_query(query)

    elif intent == STORE_ROUTE_NAME:
        response = handle_store_query(query)

    elif intent == STORAGE_ROUTE_NAME:
        response = handle_storage_query(query)

    else:
        response = handle_fallback_query()
        intent = FALLBACK_ROUTE_NAME

    return jsonify(
        {
            "role": "assistant",
            "route": intent,
            "score": float(score),
            "content": response,
            "products": [],
        }
    )

def handle_product_query(session_id, query):
    query_embedding = embedding_model.get_embedding(query)

    query_lower = query.lower()

    # MENU BOOST QUERY

    menu_keywords = [
        "menu",
        "các loại bánh",
        "loại bánh",
        "bán gì",
        "có gì",
    ]

    if any(keyword in query_lower for keyword in menu_keywords):

        boosted_query = """
        EVENT CAKE
        SET MINI
        chocolate
        vanilla
        matcha
        strawberry
        tiramisu
        bánh sinh nhật
        bánh quà tặng
        chewy chewy
        """

        source_information = rag.enhance_prompt(boosted_query)

    elif(
        "sinh nhật" in query_lower
        or "birthday" in query_lower
        or "event cake" in query_lower
    ):

        boosted_query = """
        EVENT CAKE
        bánh sinh nhật
        birthday cake
        chocolate
        matcha
        vanilla
        strawberry
        """

        source_information = rag.enhance_prompt(boosted_query)

    else:
        source_information = rag.enhance_prompt(query)

    print("RAG context:\n", source_information)

    if not is_product_found(source_information):
        fallback_context = rag.enhance_prompt(
            "EVENT CAKE SET MINI chocolate vanilla matcha bánh sinh nhật bánh quà tặng"
        )

        fallback_products = build_product_cards_from_context(fallback_context)

        if fallback_products:
            product_names = ", ".join(
                product["name"]
                for product in fallback_products
                if product.get("name")
            )

            answer = (
                "Dạ hiện tại bên mình chưa có sản phẩm đúng như bạn hỏi ạ. "
                f"Bạn có thể tham khảo một vài sản phẩm đang có như: {product_names}. "
                "Bạn muốn mình tư vấn theo vị hay theo ngân sách không ạ?"
            )
        else:
            answer = (
                "Dạ hiện tại bên mình chưa có sản phẩm bạn hỏi ạ. "
                "Bạn có thể hỏi mình về EVENT CAKE, SET MINI hoặc các vị chocolate, vanilla, matcha nhé."
            )

        return {
            "answer": answer,
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

    fake_patterns = [
        "[Tên bánh]",
        "[Giá]",
        "[Link]",
        "500.000",
        "placeholder",
    ]

    for pattern in fake_patterns:
        if pattern in answer:
            answer = (
                "Dạ hiện tại mình chưa tìm thấy mẫu bánh phù hợp trong dữ liệu ạ. "
                "Bạn có thể hỏi mình về EVENT CAKE, SET MINI hoặc bánh vị chocolate/matcha nhé."
            )
            break

    product_cards = build_product_cards_from_context(source_information)

    return {
        "answer": answer,
        "products": product_cards,
    }


def handle_order_query(session_id, query):

    query = query.strip()
    query_lower = query.lower()

    if session_id not in order_sessions:
        order_sessions[session_id] = {
            "items": [],
            "name": None,
            "phone": None,
            "address": None,
            "receive_time": None,
            "completed": False,
        }

    order = order_sessions[session_id]

    if order.get("completed"):
        return (
            "Dạ đơn hàng của bạn đã được ghi nhận rồi ạ! "
            "Shop sẽ liên hệ xác nhận trước khi giao nhé."
        )

    if len(order["items"]) == 0:
        order_parts = re.split(r"\s+và\s+|,|;", query_lower)

        for part in order_parts:
            part = part.strip()

            if not part:
                continue

            # Case 1: có đơn vị
            item_patterns = re.findall(
                r"(\d+)\s*(hộp|set|cái|bánh|phần)\s*([^\.,\n;]+)",
                part
            )

            if item_patterns:
                for qty, unit, product_name in item_patterns:
                    clean_product = product_name.strip()

                    remove_words = [
                        "vị",
                        "loại",
                        "giúp mình",
                        "nhé",
                        "nha",
                        "ạ",
                        "shop",
                    ]

                    for word in remove_words:
                        clean_product = clean_product.replace(word, "")

                    clean_product = clean_product.strip()

                    if clean_product:
                        order["items"].append(
                            {
                                "product": clean_product.title(),
                                "quantity": f"{qty} {unit}",
                            }
                        )

            else:
                # Case 2: không có đơn vị
                no_unit_match = re.search(
                    r"(\d+)\s+(.+)",
                    part
                )

                if no_unit_match:
                    qty = no_unit_match.group(1)
                    product_name = no_unit_match.group(2).strip()

                    if product_name:
                        order["items"].append(
                            {
                                "product": product_name.title(),
                                "quantity": f"{qty} phần",
                            }
                        )

        if len(order["items"]) == 0:
            clean_product = query_lower

            remove_words = [
                "cho mình",
                "mình",
                "đặt",
                "order",
                "mua",
                "lấy",
                "giúp mình",
                "nhé",
                "nha",
                "ạ",
                "shop",
            ]

            for word in remove_words:
                clean_product = clean_product.replace(word, "")

            clean_product = clean_product.strip()

            if clean_product == "":
                clean_product = "Bánh Chewy Chewy"

            order["items"].append(
                {
                    "product": clean_product.title(),
                    "quantity": None,
                }
            )

            return "Dạ bạn muốn đặt số lượng bao nhiêu hộp/set ạ?"

        return "Dạ bạn cho mình xin tên người nhận nhé."

    if any(item["quantity"] is None for item in order["items"]):
        quantity_match = re.search(
            r"(\d+)\s*(hộp|set|cái|bánh|phần)",
            query_lower
        )

        if quantity_match:
            for item in order["items"]:
                if item["quantity"] is None:
                    item["quantity"] = quantity_match.group(0)
                    break

            return "Dạ bạn cho mình xin tên người nhận nhé."

        return "Dạ bạn muốn đặt số lượng bao nhiêu hộp/set ạ?"

    if order["name"] is None:
        order["name"] = query
        return "Bạn cho mình xin số điện thoại để shop liên hệ xác nhận đơn nha."

    if order["phone"] is None:
        phone_match = re.search(r"(0|\+84)[0-9\s.-]{8,12}", query)

        if phone_match:
            order["phone"] = phone_match.group(0)
            return "Bạn gửi giúp mình địa chỉ nhận bánh nhé."

        return "Số điện thoại chưa đúng định dạng ạ. Bạn nhập lại giúp mình nhé."

    if order["address"] is None:
        order["address"] = query
        return "Bạn muốn nhận bánh vào thời gian nào ạ?"

    if order["receive_time"] is None:
        order["receive_time"] = query
        order["completed"] = True
        saved_order = save_order_to_json(session_id, order)

        items_text = ""

        total_price, missing_price_items = calculate_order_total(order["items"])

        total_text = f"{total_price:,}đ".replace(",", ".")

        for idx, item in enumerate(order["items"], start=1):
            items_text += f"{idx}. {item['product']} - {item['quantity']}\n"

        return (
            "Dạ mình xác nhận thông tin đơn hàng của bạn:\n\n"
            f"• Sản phẩm:\n{items_text}\n"
            f"• Người nhận: {order['name']}\n"
            f"• Số điện thoại: {order['phone']}\n"
            f"• Địa chỉ: {order['address']}\n"
            f"• Thời gian nhận: {order['receive_time']}\n"
            f"• Tổng tạm tính: {total_text}\n\n"
            f"• Mã đơn: {saved_order['order_id']}\n"
            "Shop sẽ liên hệ xác nhận đơn trước khi giao nhé!"
        )

    return "Dạ đơn hàng của bạn đã được ghi nhận nhé!"

def save_order_to_json(session_id, order):
    os.makedirs("orders", exist_ok=True)

    order_id = "CC" + datetime.now().strftime("%Y%m%d%H%M%S")

    order_data = {
        "order_id": order_id,
        "session_id": session_id,
        "items": order["items"],
        "name": order["name"],
        "phone": order["phone"],
        "address": order["address"],
        "receive_time": order["receive_time"],
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "status": "new",
    }

    order_path = "orders/orders.json"

    if os.path.exists(order_path):
        with open(order_path, "r", encoding="utf-8") as f:
            orders = json.load(f)
    else:
        orders = []

    orders.append(order_data)

    with open(order_path, "w", encoding="utf-8") as f:
        json.dump(orders, f, ensure_ascii=False, indent=2)

    return order_data


def format_store(store):
    name = store.get("name") or "Chewy Chewy"
    city = store.get("city") or ""
    address = store.get("address") or "Đang cập nhật"
    opening_hours = store.get("opening_hours") or "Đang cập nhật"
    hotline = store.get("hotline") or ""
    notes = store.get("note") or []

    response = (
        f" {name}\n"
        f" {address}\n"
        f" {city}\n"
        f" {opening_hours}\n"
    )

    if hotline:
        response += f" {hotline}\n"

    if notes:
        clean_notes = [note for note in notes if note.strip()]
        if clean_notes:
            response += " Ghi chú: " + " | ".join(clean_notes[:2]) + "\n"

    return response

def format_price(price):
    if not price:
        return "Đang cập nhật"

    return str(price).replace(" VND", "đ")

def parse_price_to_number(price):
    if not price:
        return None

    price_text = str(price).lower()
    price_text = price_text.replace("vnd", "")
    price_text = price_text.replace("đ", "")
    price_text = price_text.replace(".", "")
    price_text = price_text.replace(",", "")
    price_text = price_text.strip()

    if price_text.isdigit():
        return int(price_text)

    return None

def find_product_price_by_name(order_product_name):
    order_name_norm = normalize_vietnamese(order_product_name)

    best_product = None
    best_score = 0

    for product in PRODUCTS_DATA:
        product_title = product.get("title", "")
        product_title_norm = normalize_vietnamese(product_title)

        score = 0

        for word in order_name_norm.split():
            if word in product_title_norm:
                score += 1

        if score > best_score:
            best_score = score
            best_product = product

    if best_product and best_score > 0:
        price = parse_price_to_number(best_product.get("price"))
        return price

    return None


def calculate_order_total(items):
    total = 0
    missing_price_items = []

    for item in items:
        price = find_product_price_by_name(item["product"])

        quantity_text = item["quantity"]
        quantity_match = re.search(r"\d+", quantity_text)

        quantity = int(quantity_match.group(0)) if quantity_match else 1

        if price is None:
            missing_price_items.append(item["product"])
            continue

        total += price * quantity

    return total, missing_price_items

def extract_price_limit(query):
    query_norm = normalize_vietnamese(query)

    match = re.search(r"(duoi|dưới)\s*(\d+)", query_norm)

    if match:
        number = int(match.group(2))

        if number < 1000:
            number = number * 1000

        return number

    return None

def handle_price_filter_query(query, session_id=None):
    limit_price = extract_price_limit(query)

    if not limit_price:
        return None

    query_norm = normalize_vietnamese(query)

    category_filter = None

    if "set mini" in query_norm or "mini" in query_norm:
        category_filter = "set mini"

    elif (
        "event cake" in query_norm
        or "banh event" in query_norm
        or "sinh nhat" in query_norm
        or query_norm.startswith("event")
        or " event " in query_norm
    ):
        category_filter = "event cake"

    elif "banh su" in query_norm or "medium" in query_norm:
        category_filter = "medium"

    matched_products = []

    for product in PRODUCTS_DATA:
        if category_filter and product.get("category_tag") != category_filter:
            continue

        price_number = parse_price_to_number(product.get("price"))

        query_norm = normalize_vietnamese(query)

        need_low_sweet = (
            "it ngot" in query_norm
            or "ngot nhe" in query_norm
            or "khong qua ngot" in query_norm
        )

        if price_number and price_number <= limit_price:

            if need_low_sweet and product.get("sweetness") != "low":
                continue

            matched_products.append(product)

    if not matched_products:
        return {
            "answer": f"Dạ hiện tại mình chưa thấy mẫu nào dưới {limit_price:,}đ trong dòng bạn đang xem ạ.",
            "products": []
        }

    if need_low_sweet:
        answer = f"Dạ các mẫu ít ngọt dưới {limit_price:,}đ bên mình có:\n\n"
    else:
        answer = f"Dạ các mẫu dưới {limit_price:,}đ bên mình có:\n\n"

    for product in matched_products[:10]:
        answer += format_product_line(product) + "\n"

    answer += "\nBạn muốn mình lọc tiếp theo vị bánh không ạ?"

    image_urls = [
        product.get("image_url")
        for product in matched_products[:10]
        if product.get("image_url")
    ]

    return {
        "answer": answer,
        "products": image_urls
    }

def handle_cheapest_query(query):
    query_norm = normalize_vietnamese(query)

    if "re nhat" not in query_norm:
        return None

    category_filter = None

    if "banh su" in query_norm or "medium" in query_norm:
        category_filter = "medium"
    elif "set mini" in query_norm or "mini" in query_norm:
        category_filter = "set mini"
    elif "event" in query_norm or "sinh nhat" in query_norm:
        category_filter = "event cake"

    matched_products = []

    for product in PRODUCTS_DATA:
        if category_filter and product.get("category_tag") != category_filter:
            continue

        price_number = parse_price_to_number(product.get("price"))

        if price_number:
            matched_products.append((price_number, product))

    if not matched_products:
        return None

    matched_products.sort(key=lambda x: x[0])

    cheapest_price, cheapest_product = matched_products[0]

    answer = (
        "Dạ mẫu rẻ nhất mình tìm thấy là:\n\n"
        f"{format_product_line(cheapest_product)}\n\n"
        "Bạn muốn mình gợi ý thêm vài mẫu cùng dòng này không ạ?"
    )

    image_urls = []
    if cheapest_product.get("image_url"):
        image_urls.append(cheapest_product.get("image_url"))

    return {
        "answer": answer,
        "products": image_urls
    }

def handle_flavor_existence_query(query, session_id=None):
    query_norm = normalize_vietnamese(query)

    flavor_map = {
        "matcha": ["matcha", "tra xanh"],
        "vanilla": ["vanilla", "vani"],
        "chocolate": ["chocolate", "socola"],
        "strawberry": ["strawberry", "dau"],
        "mango": ["mango", "xoai"],
        "orange": ["orange", "cam"],
        "yogurt": ["yogurt", "sua chua"],
        "cheese": ["cheese", "pho mai"],
        "oreo": ["oreo"],
    }

    detected_flavor = None

    for flavor, keywords in flavor_map.items():
        if any(keyword in query_norm for keyword in keywords):
            detected_flavor = flavor
            break

    if not detected_flavor:
        return None

    if "set mini" in query_norm or "mini" in query_norm:
        category = "set mini"
        category_name = "Set Mini"

    elif "event cake" in query_norm or "banh event" in query_norm:
        category = "event cake"
        category_name = "Event Cake"

    elif "banh su" in query_norm or "medium" in query_norm:
        category = "medium"
        category_name = "Bánh su Medium"

    else:
        category = None
        category_name = "Chewy Chewy"

    matched_products = []

    for product in PRODUCTS_DATA:
        if category and product.get("category_tag") != category:
            continue

        if detected_flavor in product.get("flavors", []):
            matched_products.append(product)

    if not matched_products:
        return {
            "answer": f"Dạ hiện tại mình chưa thấy dòng {category_name} có vị {detected_flavor.title()} ạ.",
            "products": []
        }

    answer = f"Dạ có ạ. Dòng {category_name} có vị {detected_flavor.title()} như:\n\n"

    for product in matched_products[:8]:
        answer += format_product_line(product) + "\n"

    answer += "\nBạn muốn mình lọc thêm theo giá hoặc độ ngọt không ạ?"

    image_urls = [
        product.get("image_url")
        for product in matched_products[:8]
        if product.get("image_url")
    ]

    return {
        "answer": answer,
        "products": image_urls
    }

def get_products_by_category(category_keyword):
    category_keyword = normalize_vietnamese(category_keyword)

    results = []

    for product in PRODUCTS_DATA:
        category = normalize_vietnamese(product.get("category", ""))
        title = normalize_vietnamese(product.get("title", ""))

        if category_keyword in category or category_keyword in title:
            results.append(product)

    return results

def extract_preferences(query):

    query_norm = normalize_vietnamese(query)

    prefs = {
        "flavors": [],
        "sweetness": None,
    }

    flavor_map = {
        "vanilla": ["vanilla", "vani"],
        "matcha": ["matcha", "tra xanh"],
        "chocolate": ["socola", "chocolate"],
        "strawberry": ["dau", "strawberry"],
        "fruit": ["trai cay", "xoai", "cam", "berry"],
    }

    for flavor, keywords in flavor_map.items():

        if any(k in query_norm for k in keywords):
            prefs["flavors"].append(flavor)

    low_sweet_keywords = [
        "it ngot",
        "ngot nhe",
        "healthy",
    ]

    if any(k in query_norm for k in low_sweet_keywords):
        prefs["sweetness"] = "low"

    return prefs

def format_product_line(product):
    title = product.get("title", "Sản phẩm")
    price = format_price(product.get("price", ""))
    return f"• {title} - {price}"


def handle_menu_query(query):
    query_norm = normalize_vietnamese(query)

    # FLAVOR QUERY
    flavor_keywords = [
        "huong vi",
        "nhung vi",
        "cac vi",
        "co vi gi",
        "co nhung vi nao",
    ]

    if any(keyword in query_norm for keyword in flavor_keywords):

        matched_products = []

        if "event cake" in query_norm:
            matched_products = get_products_by_category(
                "banh event sinh nhat"
            )

        elif "set mini" in query_norm:
            matched_products = get_products_by_category(
                "set banh mini chewy"
            )

        else:
            matched_products = PRODUCTS_DATA

        flavor_set = set()

        possible_flavors = [
            "chocolate",
            "socola",
            "matcha",
            "vanilla",
            "strawberry",
            "dau",
            "xoai",
            "mango",
            "oreo",
            "cheese",
            "pho mai",
            "yogurt",
            "sua chua",
            "red velvet",
            "tiramisu",
            "almond",
            "hanh nhan",
        ]

        for product in matched_products:

            searchable_text = normalize_vietnamese(
                product.get("title", "")
                + " "
                + product.get("description", "")
            )

            for flavor in possible_flavors:
                if flavor in searchable_text:
                    flavor_set.add(flavor.title())

        if flavor_set:

            flavor_list = sorted(list(flavor_set))

            response = "Dạ hiện dòng bánh này bên mình có các vị như:\n\n"

            for flavor in flavor_list:
                response += f"• {flavor}\n"

            response += (
                "\nBạn thích vị nào để mình gợi ý mẫu bánh phù hợp nha 💖"
            )

            return response

    if not PRODUCTS_DATA:
        return (
            "Dạ hiện tại mình chưa tải được dữ liệu sản phẩm. "
            "Bạn thử lại sau giúp mình nhé."
        )

    if "event cake" in query_norm or "banh event" in query_norm or "sinh nhat" in query_norm:
        products = get_products_by_category("banh event sinh nhat")

        response = "Dạ dòng Bánh Event/Sinh nhật bên mình hiện có các mẫu như:\n\n"

        for product in products[:20]:
            response += format_product_line(product) + "\n"

        response += "\nBạn muốn mình tư vấn mẫu Event Cake theo ngân sách hoặc số người ăn không ạ?"
        return response

    if "set mini" in query_norm or "mini" in query_norm:
        products = get_products_by_category("set banh mini chewy")

        response = "Dạ dòng Set bánh mini Chewy hiện có các loại như:\n\n"

        for product in products[:20]:
            response += format_product_line(product) + "\n"

        response += "\nBạn thích vị chocolate, vanilla, matcha hay trái cây để mình gợi ý set phù hợp hơn ạ?"
        return response

    if (
        "medium" in query_norm
        or "banh su" in query_norm
        or "banh su medium" in query_norm
    ):
        products = get_products_by_category("banh su medium")

        response = "Dạ dòng Bánh su Medium bên mình hiện có các loại như:\n\n"

        for product in products[:20]:
            response += format_product_line(product) + "\n"

        response += "\nBạn muốn vị ít ngọt, chocolate, trái cây hay phô mai ạ?"
        return response

    categories = {}

    for product in PRODUCTS_DATA:
        category = product.get("category", "Khác")

        if category not in categories:
            categories[category] = []

        categories[category].append(product)

    response = "Dạ Chewy Chewy hiện có các dòng bánh chính:\n\n"

    for category, products in categories.items():
        response += f"🍰 {category}\n"

        for product in products[:5]:
            response += format_product_line(product) + "\n"

        if len(products) > 5:
            response += f"  ... và {len(products) - 5} mẫu khác\n"

        response += "\n"

    response += (
        "Bạn muốn xem chi tiết dòng nào ạ? "
        "Ví dụ: Event Cake, Set Mini hoặc Bánh su Medium."
    )

    return response
def product_exists_in_data(query):
    query_norm = normalize_vietnamese(query)

    weak_words = [
        "shop", "co", "có", "ban", "bán", "banh", "bánh",
        "khong", "không", "loai", "loại", "nao", "nào",
        "gi", "gì", "khong?", "không?"
    ]

    query_words = [
        word for word in query_norm.split()
        if word not in weak_words and len(word) >= 2
    ]

    if not query_words:
        return True

    for product in PRODUCTS_DATA:
        searchable_text = normalize_vietnamese(
            product.get("title", "") + " " + product.get("description", "")
        )

        if all(word in searchable_text for word in query_words):
            return True

    return False

def handle_recommend_query(query, session_id=None):
    prefs = extract_preferences(query)
    query_norm = normalize_vietnamese(query)

    last_category = None

    if session_id and session_id in user_contexts:
        last_category = user_contexts[session_id].get("last_category")

    # FLAVOR PREFERENCE RECOMMENDATION

    if any(
        kw in query_norm
        for kw in [
            "it ngot",
            "ngot nhe",
            "trai cay",
            "fruit",
            "nen chon vi nao",
            "vi nao ngon",
        ]
    ):

        recommended = []

        for product in PRODUCTS_DATA:

            flavors = product.get("flavors", [])
            sweetness = product.get("sweetness", "")

            score = 0
            if last_category and product.get("category_tag") != last_category:
                continue

            # Ít ngọt
            if "it ngot" in query_norm or "ngot nhe" in query_norm:

                if sweetness == "low":
                    score += 3

            # Trái cây
            if "trai cay" in query_norm or "fruit" in query_norm:

                fruit_flavors = [
                    "strawberry",
                    "mango",
                    "orange",
                    "blueberry",
                ]

                if any(f in flavors for f in fruit_flavors):
                    score += 3

            if score > 0:
                recommended.append((score, product))

        recommended.sort(key=lambda x: x[0], reverse=True)

        if recommended:

            response = "Dạ mình gợi ý vài mẫu phù hợp với khẩu vị bạn nha:\n\n"

            shown = set()

            count = 0

            for _, product in recommended:

                title = product.get("title", "Sản phẩm")

                if title in shown:
                    continue

                shown.add(title)

                price = format_price(product.get("price", ""))

                response += f"• {title} - {price}\n"

                count += 1

                if count >= 6:
                    break

            response += "\nBạn thích dòng Event Cake hay Set Mini hơn để mình gợi ý tiếp nha!"

            return {
                "answer": response,
                "products": []
            }
    # GROUP SIZE RECOMMENDATION

    group_patterns = [
        ("20", 20),
        ("15", 15),
        ("10", 10),
        ("8", 8),
        ("6", 6),
    ]

    detected_people = None

    for text_num, people in group_patterns:

        if text_num in query_norm:
            detected_people = people
            break
    if not PRODUCTS_DATA:
        return {
            "answer": "Dạ hiện tại mình chưa tải được dữ liệu sản phẩm ạ.",
            "products": []
        }

    filtered_products = []
    
    if detected_people:

        for product in PRODUCTS_DATA:

            category = product.get("category_tag", "")

            score = 0

            # EVENT CAKE ưu tiên cho đông người
            if detected_people >= 8:

                if category == "event cake":
                    score += 5

            # SET MINI cho ít người
            elif detected_people <= 4:

                if category == "set mini":
                    score += 5

            if score > 0:
                filtered_products.append((score, product))

    for product in PRODUCTS_DATA:
        score = 0

        if last_category and product.get("category_tag") != last_category:
            continue

        for flavor in prefs["flavors"]:

            if flavor == "fruit":

                fruit_flavors = [
                    "strawberry",
                    "mango",
                    "orange",
                    "blueberry",
                    "apple",
                ]

                if any(
                    fruit in product.get("flavors", [])
                    for fruit in fruit_flavors
                ):
                    score += 3

            elif flavor in product.get("flavors", []):
                score += 3

        if prefs["sweetness"] == "low":
            if product.get("sweetness") == "low":
                score += 2

        if "sinh nhat" in query_norm or "event cake" in query_norm or "banh event" in query_norm:
            if product.get("category_tag") == "event cake":
                score += 4

        if score > 0:
            filtered_products.append((score, product))

    filtered_products.sort(
        reverse=True,
        key=lambda x: x[0]
    )

    products = [
        item[1]
        for item in filtered_products[:6]
    ]

    if not products:
        products = PRODUCTS_DATA[:6]

    answer = "Dạ mình gợi ý một số mẫu bánh phù hợp của Chewy Chewy:\n\n"

    for product in products:
        answer += format_product_line(product) + "\n"

    answer += "\nBạn muốn mình tư vấn tiếp theo vị bánh, ngân sách hay dịp sử dụng ạ?"

    image_urls = [
        product.get("image_url")
        for product in products
        if product.get("image_url")
    ]

    return {
        "answer": answer,
        "products": image_urls
    }

def handle_delivery_query(query):
    return (
        "Dạ Chewy Chewy có hỗ trợ giao hàng ạ. "
        "Phí ship và thời gian giao sẽ tùy theo khu vực. "
        "Bạn gửi giúp mình quận/huyện hoặc địa chỉ nhận bánh để shop kiểm tra phí ship chính xác nhé."
    )


def handle_store_query(query):
    query_norm = normalize_vietnamese(query)

    if not STORES_DATA:
        return (
            "Dạ hiện tại mình chưa tải được dữ liệu chi nhánh. "
            "Bạn thử lại sau hoặc liên hệ fanpage Chewy Chewy giúp mình nhé."
        )

    matched_stores = []

    # CASE 1: User hỏi quận số, ví dụ quận 7, q7, q.7
    district_match = re.search(r"(quan|q)\.?\s*(\d+)", query_norm)

    if district_match:
        district_number = district_match.group(2)

        for store in STORES_DATA:
            address_norm = normalize_vietnamese(store.get("address", ""))

            patterns = [
                rf"\bq\.?\s*{district_number}\b",
                rf"\bquan\s+{district_number}\b",
            ]

            if any(re.search(pattern, address_norm) for pattern in patterns):
                matched_stores.append(store)

    # CASE 2: User hỏi khu vực bằng chữ
    else:
        area_keywords = [
            "tan binh",
            "thu duc",
            "go vap",
            "binh thanh",
            "phu nhuan",
            "ha noi",
            "da nang",
            "can tho",
            "bien hoa",
            "ba ria",
            "tra vinh",
        ]

        detected_area = None

        for area in area_keywords:
            if area in query_norm:
                detected_area = area
                break

        if detected_area:
            for store in STORES_DATA:
                searchable_text = normalize_vietnamese(
                    " ".join([
                        store.get("city", ""),
                        store.get("address", ""),
                        store.get("name", ""),
                    ])
                )

                if detected_area in searchable_text:
                    matched_stores.append(store)

    if matched_stores:
        response = "Dạ mình tìm thấy chi nhánh phù hợp với khu vực bạn hỏi:\n\n"

        for store in matched_stores:
            response += format_store(store) + "\n"

        response += "Bạn có thể chọn chi nhánh thuận tiện nhất để ghé mua trực tiếp nhé."
        return response

    response = (
        "Dạ hiện tại Chewy Chewy chưa có chi nhánh ở khu vực bạn hỏi ạ.\n\n"
        "Bạn có thể tham khảo một số chi nhánh hiện có và chọn cửa hàng thuận tiện nhất để ghé nhé:\n\n"
    )

    for store in STORES_DATA[:8]:
        response += format_store(store) + "\n"

    response += (
        "Bạn có thể chọn chi nhánh gần hoặc tiện đường nhất, "
        "hoặc gửi lại khu vực khác để mình kiểm tra giúp bạn nha."
    )

    return response


def handle_storage_query(query):
    return (
        "Dạ bánh nên dùng trong ngày để ngon nhất ạ. "
        "Nếu chưa dùng ngay, bạn nên bảo quản lạnh (dùng được trong 2-3 ngày) và tránh để bánh ở nơi nóng. "
        "Khi ăn có thể lấy bánh ra trước một chút để bánh mềm ngon hơn nhé."
    )


def handle_support_query(query):
    return (
        "Dạ mình rất tiếc về trải nghiệm này ạ. "
        "Bạn gửi giúp mình số điện thoại đặt hàng, mã đơn nếu có, và vấn đề bạn gặp phải "
        "để shop kiểm tra và hỗ trợ nhanh nhất nhé."
    )


def handle_chitchat_query(session_id, query):
    query_lower = query.lower().strip()

    greeting_words = ["xin chào", "hello", "hi", "hey", "chào", "shop ơi", "alo"]

    if any(word in query_lower for word in greeting_words):
        return (
            "Xin chào bạn. "
            "Mình là trợ lý tư vấn của Chewy Chewy. "
            "Bạn muốn xem menu, hỏi giá, được tư vấn bánh hay đặt hàng ạ?"
        )

    thanks_words = ["cảm ơn", "thanks", "thank you"]

    if any(word in query_lower for word in thanks_words):
        return (
            "Dạ không có gì ạ. "
            "Bạn cần mình gợi ý thêm mẫu bánh nào không?"
        )

    bye_words = ["bye", "tạm biệt", "hẹn gặp lại"]

    if any(word in query_lower for word in bye_words):
        return (
            "Dạ cảm ơn bạn đã ghé Chewy Chewy. "
            "Chúc bạn một ngày thật ngọt ngào nhé!"
        )

    chitchat_prompt = f"""
Mình là nhân viên tư vấn bánh của Chewy Chewy.

Khách hàng nói:
{query}

Hãy trả lời:
- ngắn gọn
- tự nhiên
- thân thiện
- giống nhân viên thật
- xưng "mình" và "bạn"

Không được:
- nói về AI
- nói về hệ thống
- nói về RAG
- nói về database

Nếu phù hợp, hãy nhẹ nhàng gợi ý khách xem menu, hỏi giá, được tư vấn bánh hoặc đặt hàng.
""".strip()

    try:
        return reflection.chat(
            session_id=session_id,
            enhanced_message=chitchat_prompt,
            original_message=query,
            cache_response=False,
        )

    except Exception:
        return "Mình có thể hỗ trợ bạn tư vấn bánh của Chewy Chewy ạ."


def handle_fallback_query():
    return (
        "Dạ hiện tại mình chưa hiểu rõ ý bạn ạ. "
        "Bạn có thể hỏi mình về menu, giá bánh, tư vấn bánh, đặt hàng, giao hàng, "
        "bảo quản bánh hoặc địa chỉ cửa hàng nhé."
    )


def build_product_prompt(query, source_information):
    return f"""
Bạn là nhân viên tư vấn bánh của Chewy Chewy.

NHIỆM VỤ:
- Chỉ tư vấn bằng dữ liệu thật trong SOURCE INFORMATION.
- Không được tự bịa sản phẩm.
- Không được tự bịa giá.
- Không được dùng placeholder như:
  [Tên bánh]
  [Giá]
  [Link]
- Không được nói lan man.
- Không được nói về AI, database, RAG hay hệ thống.

PHONG CÁCH:
- Thân thiện
- Tự nhiên
- Ngắn gọn
- Giống nhân viên bán bánh thật
- Xưng "mình" và "bạn"

SOURCE INFORMATION:
{source_information}

KHÁCH HỎI:
{query}

QUY TẮC TRẢ LỜI:

1. Nếu hỏi menu:
- Liệt kê đúng tên bánh có trong SOURCE INFORMATION.
- Có thể nhóm theo dòng bánh.

2. Nếu hỏi giá:
- Chỉ trả lời giá có trong dữ liệu.

3. Nếu hỏi tư vấn:
- Chỉ gợi ý sản phẩm thật trong dữ liệu.

4. Nếu khách muốn mua:
- Gợi ý đặt hàng nhẹ nhàng.

5. Nếu không có dữ liệu phù hợp:
Trả lời:
"Dạ hiện tại mình chưa tìm thấy mẫu bánh phù hợp trong dữ liệu ạ."

6. KHÔNG được:
- tự thêm giá
- tự thêm sản phẩm
- tự thêm chi nhánh
- tự thêm khuyến mãi
- tự thêm thông tin không có trong SOURCE INFORMATION

Hãy trả lời ngắn gọn, đúng dữ liệu.
""".strip()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=True)