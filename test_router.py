from semantic_router.samples import routes
from semantic_router import SemanticRouter


def test_router():
    router = SemanticRouter(
        routes=routes,
        threshold=0.45,
    )

    tests = [
        ("Shop có bánh gì?", "menu"),
        ("Giá bánh bao nhiêu?", "price"),
        ("Bánh nào ít ngọt?", "recommend"),
        ("Cho mình đặt 2 hộp socola", "order"),
        ("Mình muốn mua 1 set mini", "order"),
        ("Có ship quận 7 không?", "delivery"),
        ("Phí ship bao nhiêu?", "delivery"),
        ("Cửa hàng ở đâu?", "store"),
        ("Shop có bán trực tiếp không?", "store"),
        ("Bánh để được bao lâu?", "storage"),
        ("Có cần để tủ lạnh không?", "storage"),
        ("Mình chưa nhận được bánh", "support"),
        ("Đơn hàng bị giao sai", "support"),
        ("Xin chào shop", "chitchat"),
        ("Cảm ơn shop", "chitchat"),
        ("Shop có bán laptop không?", "fallback"),
    ]

    print("\n        TEST SEMANTIC ROUTER       \n")

    passed = 0
    failed = 0

    for text, expected_intent in tests:
        score, predicted_intent = router.guide(text)

        status = "PASS" if predicted_intent == expected_intent else "FAIL"

        if status == "PASS":
            passed += 1
        else:
            failed += 1

        print(f"Câu hỏi: {text}")
        print(f"Expected: {expected_intent}")
        print(f"Predicted: {predicted_intent}")
        print(f"Score: {score:.4f}")
        print(f"Status: {status}")
        print("-" * 50)

    print("\n        SUMMARY        ")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    print("                         \n")


if __name__ == "__main__":
    test_router()