def is_product_found(source_information: str) -> bool:
    if not source_information:
        return False

    source_information = source_information.strip().lower()

    # Context quá ngắn
    if len(source_information) < 30:
        return False

    required_markers = [
        "tên bánh:",
        "giá:",
        "hình ảnh:",
        "link:"
    ]

    # Phải có ít nhất 2 marker mới coi là valid product
    matched_markers = sum(
        marker in source_information
        for marker in required_markers
    )

    return matched_markers >= 2