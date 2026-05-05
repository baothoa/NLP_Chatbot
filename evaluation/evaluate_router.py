import pandas as pd

from semantic_router import Route, SemanticRouter
from semantic_router.samples import chitchatSample, productSample


def main():
    df = pd.read_csv("evaluation/test_queries.csv")

    routes = [
        Route(name="products", samples=productSample),
        Route(name="chitchat", samples=chitchatSample),
    ]

    router = SemanticRouter(routes=routes, threshold=0.45)

    correct = 0

    for _, row in df.iterrows():
        score, predicted_route = router.guide(row["query"])

        if predicted_route == row["expected_route"]:
            correct += 1

        print(
            f"Query: {row['query']} | "
            f"Expected: {row['expected_route']} | "
            f"Predicted: {predicted_route} | "
            f"Score: {score:.4f}"
        )

    accuracy = correct / len(df)
    print(f"\nRouter Accuracy: {accuracy:.2f}")


if __name__ == "__main__":
    main()