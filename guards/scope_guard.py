BAKERY_KEYWORDS = [
    "bánh", "chewy", "cake", "event cake", "set mini",
    "matcha", "socola", "chocolate", "vanilla",
    "dâu", "xoài", "kem", "ngọt", "ít ngọt",
    "sinh nhật", "quà", "người yêu", "tiệc", "trẻ em",
    "mua", "đặt", "order", "ship", "giao hàng",
    "giá", "mô tả", "hình ảnh", "link", "sản phẩm"
]

UNSUPPORTED_INFO_KEYWORDS = [
    "khuyến mãi", "mã giảm giá", "freeship", "ưu đãi",
    "đổi trả", "hoàn tiền", "khiếu nại",
    "chi nhánh", "giờ mở cửa", "chỉ đường", "còn hàng"
]

# Các câu chitchat nhẹ được phép
SAFE_CHITCHAT = [
    "xin chào",
    "hello",
    "hi",
    "hey",
    "cảm ơn",
    "thanks",
    "thank you",
    "ok",
    "oke",
    "haha",
    "👍"
]

def is_safe_chitchat(query: str) -> bool:
    query = query.lower().strip()

    return any(chat in query for chat in SAFE_CHITCHAT)

def is_related_to_bakery(query: str) -> bool:
    query = query.lower().strip()

    # cho phép chitchat nhẹ
    if is_safe_chitchat(query):
        return True

    bakery_keywords = BAKERY_KEYWORDS + UNSUPPORTED_INFO_KEYWORDS

    # có keyword bakery rõ ràng
    if any(keyword in query for keyword in bakery_keywords):
        return True

    # có từ liên quan sản phẩm / đồ ăn / mua hàng
    food_patterns = [
        "bánh",
        "cake",
        "tiramisu",
        "matcha",
        "chocolate",
        "socola",
        "vanilla",
        "dessert",
        "ngọt",
        "kem",
        "cookie",
        "brownie",
        "mousse"
    ]

    return any(word in query for word in food_patterns)

def detect_unsupported_info(query: str):
    query = query.lower().strip()

    for keyword in UNSUPPORTED_INFO_KEYWORDS:
        if keyword in query:
            return keyword

    return None

def out_of_scope_response():
    return (
        "Dạ xin lỗi, mình chỉ hỗ trợ tư vấn bánh và sản phẩm của Chewy Chewy thôi ạ. "
        "Bạn có thể hỏi mình về bánh sinh nhật, bánh chocolate, bánh ít ngọt "
        "hoặc các mẫu bánh làm quà tặng nhé."
    )

def unsupported_info_response(keyword: str):
    return (
        f"Dạ hiện tại mình chưa có thông tin về {keyword} trong dữ liệu Chewy Chewy ạ. "
        "Mình có thể hỗ trợ bạn xem các mẫu bánh, giá, mô tả và hình ảnh sản phẩm hiện có nhé."
    )