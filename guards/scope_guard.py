BAKERY_KEYWORDS = [
    # Brand / sản phẩm
    "chewy",
    "chewy chewy",
    "bánh",
    "cake",
    "event cake",
    "set mini",
    "bánh su",
    "bánh su medium",
    "bánh kem",
    "bánh sinh nhật",
    "bánh event",
    "bánh sự kiện",
    "dessert",

    # Vị bánh / nhân bánh
    "matcha",
    "trà xanh",
    "socola",
    "chocolate",
    "choco",
    "vanilla",
    "vani",
    "dâu",
    "strawberry",
    "xoài",
    "mango",
    "việt quất",
    "blueberry",
    "cam",
    "orange",
    "táo",
    "apple",
    "phô mai",
    "cheese",
    "yogurt",
    "sữa chua",
    "oreo",
    "hạnh nhân",
    "almond",
    "trân châu",
    "black pearl",
    "bơ tỏi",
    "chà bông",
    "pork floss",
    "chicken floss",
    "kem",
    "nhân kem",
    "nhân bánh",
    "ngọt",
    "ít ngọt",
    "ngọt nhẹ",
    "vị",
    "những vị",
    "các vị",
    "vị bánh",
    "hương vị",

    # Dịp sử dụng
    "sinh nhật",
    "birthday",
    "quà",
    "quà tặng",
    "người yêu",
    "bạn gái",
    "bạn trai",
    "gia đình",
    "tiệc",
    "party",
    "trẻ em",
    "cho bé",
    "công ty",
    "sự kiện",
    "event",

    # Bán hàng / tư vấn
    "mua",
    "đặt",
    "order",
    "chốt đơn",
    "lên đơn",
    "lấy",
    "tư vấn",
    "gợi ý",
    "nên mua",
    "nên chọn",
    "best seller",
    "ngon nhất",
    "giá",
    "bao nhiêu",
    "bảng giá",
    "sản phẩm",
    "menu",
    "mô tả",
    "hình ảnh",
    "link",
    "loại bánh",
    "các loại bánh",
    "bánh gì",
    "bán gì",
    "có gì",
    "dưới",
    "trên",
    "tầm",
    "tầm giá",
    "ngân sách",
    "khoảng giá",
    "500",
    "500.000",
    "300.000",
    "200.000",
    "500k",
    "1 triệu",
    "1.000.000",
    "200k"

    # Giao hàng
    "ship",
    "giao hàng",
    "phí ship",
    "giao tới",
    "giao trong ngày",
    "freeship",
    "quận",
    "huyện",
    "phường",
    "địa chỉ",
    "địa chỉ giao",

    # Cửa hàng / chi nhánh
    "chi nhánh",
    "cửa hàng",
    "shop",
    "offline",
    "mua trực tiếp",
    "địa chỉ shop",
    "địa chỉ cửa hàng",
    "giờ mở cửa",
    "mở cửa",
    "đóng cửa",
    "ở đâu",

    # Bảo quản
    "bảo quản",
    "tủ lạnh",
    "để được bao lâu",
    "hạn dùng",
    "để ngoài",
    "qua đêm",
    "giữ lạnh",
    "mau hỏng",
    "dùng trong mấy ngày",

    # Hỗ trợ đơn hàng
    "đơn hàng",
    "mã đơn",
    "kiểm tra đơn",
    "chưa nhận",
    "chưa thấy giao",
    "giao sai",
    "giao thiếu",
    "bị lỗi",
    "bánh lỗi",
    "bánh hư",
    "đổi đơn",
    "hủy đơn",
    "khiếu nại",
    "hoàn tiền",
    "shipper",
]


UNSUPPORTED_INFO_KEYWORDS = [
    # Chỉ chặn những thông tin chatbot chưa có dữ liệu chắc chắn
    "khuyến mãi",
    "mã giảm giá",
    "ưu đãi",
    "voucher",
    "coupon",
    "còn hàng",
    "tồn kho",
]


SAFE_CHITCHAT = [
    "xin chào",
    "hello",
    "hi",
    "hey",
    "chào",
    "shop ơi",
    "alo",
    "bạn ơi",
    "cảm ơn",
    "thanks",
    "thank you",
    "ok",
    "oke",
    "okay",
    "dạ",
    "vâng",
    "ừ",
    "uh",
    "haha",
    "bye",
    "tạm biệt",
    "hẹn gặp lại",
    "bạn là ai",
    "bạn làm gì",
    "👍",
]


OUT_OF_SCOPE_KEYWORDS = [
    "điện thoại",
    "iphone",
    "samsung",
    "laptop",
    "macbook",
    "máy tính",
    "tai nghe",
    "quần áo",
    "giày",
    "mỹ phẩm",
    "son môi",
    "trà sữa",
    "cà phê",
    "xe máy",
    "ô tô",
    "vé máy bay",
    "khách sạn",
    "bóng đá",
    "game",
    "bitcoin",
    "crypto",
    "cổ phiếu",
    "chứng khoán",
    "bất động sản",
    "thuốc",
]


def normalize_query(query: str) -> str:
    if not query:
        return ""

    return query.lower().strip()


def is_safe_chitchat(query: str) -> bool:
    query = normalize_query(query)

    return any(chat in query for chat in SAFE_CHITCHAT)


def is_related_to_bakery(query: str) -> bool:
    query = normalize_query(query)

    if not query:
        return False

    # Cho phép chitchat nhẹ
    if is_safe_chitchat(query):
        return True

    # Chặn rõ ràng chủ đề ngoài phạm vi
    if any(keyword in query for keyword in OUT_OF_SCOPE_KEYWORDS):
        return False

    # Cho phép mọi câu liên quan bánh / Chewy / bán hàng / giao hàng / cửa hàng
    if any(keyword in query for keyword in BAKERY_KEYWORDS):
        return True

    return False


def detect_unsupported_info(query: str):
    query = normalize_query(query)

    for keyword in UNSUPPORTED_INFO_KEYWORDS:
        if keyword in query:
            return keyword

    return None


def out_of_scope_response():
    return (
        "Dạ xin lỗi, mình chỉ hỗ trợ tư vấn bánh và dịch vụ của Chewy Chewy thôi ạ. "
        "Bạn có thể hỏi mình về menu, giá bánh, tư vấn bánh, đặt hàng, giao hàng, "
        "bảo quản bánh hoặc địa chỉ chi nhánh nhé."
    )


def unsupported_info_response(keyword: str):

    promotion_keywords = [
        "khuyến mãi",
        "mã giảm giá",
        "ưu đãi",
        "voucher",
        "coupon",
    ]

    if keyword in promotion_keywords:
        return (
            "Dạ hiện tại shop chưa có chương trình ưu đãi hoặc mã giảm giá ạ. "
            "Bạn có thể tham khảo menu bánh hoặc để mình tư vấn mẫu phù hợp nhé."
        )

    return (
        f"Dạ hiện tại mình chưa có thông tin chính xác về {keyword} ạ. "
        "Bạn có thể hỏi mình về menu, giá bánh, tư vấn bánh, đặt hàng, "
        "giao hàng hoặc địa chỉ chi nhánh nhé."
    )