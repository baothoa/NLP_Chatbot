def build_product_cards_from_context(
    source_information: str,
    max_items: int = 3
):
    products = []
    current = {}

    if not source_information:
        return []

    for line in source_information.splitlines():
        line = line.strip()

        if not line:
            continue

        # ===== TÊN BÁNH =====
        if line.startswith("Tên bánh:"):

            # push product cũ nếu hợp lệ
            if current.get("name"):
                products.append(current)

            current = {
                "name": line.replace("Tên bánh:", "").strip(),
                "price": "",
                "category": "",
                "description": "",
                "image_url": "",
                "link": "",
            }

        # ===== GIÁ =====
        elif line.startswith("Giá:"):
            current["price"] = (
                line.replace("Giá:", "").strip()
            )

        # ===== DANH MỤC =====
        elif line.startswith("Danh mục:"):
            current["category"] = (
                line.replace("Danh mục:", "").strip()
            )

        # ===== MÔ TẢ =====
        elif line.startswith("Mô tả:"):
            current["description"] = (
                line.replace("Mô tả:", "").strip()
            )

        # ===== HÌNH ẢNH =====
        elif line.startswith("Hình ảnh:"):
            current["image_url"] = (
                line.replace("Hình ảnh:", "").strip()
            )

        # ===== LINK =====
        elif line.startswith("Link:"):
            current["link"] = (
                line.replace("Link:", "").strip()
            )

    # push product cuối
    if current.get("name"):
        products.append(current)

    # ===== FILTER PRODUCT RÁC =====
    cleaned_products = []

    for product in products:

        # phải có tên
        if not product["name"]:
            continue

        # ít nhất có ảnh hoặc link
        if not product["image_url"] and not product["link"]:
            continue

        cleaned_products.append(product)

    return cleaned_products[:max_items]