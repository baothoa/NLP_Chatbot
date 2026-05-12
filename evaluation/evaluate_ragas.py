"""
╔══════════════════════════════════════════════════════════════════════╗
║          RAGAS Evaluation — 100% Ollama, không OpenAI               ║
║                                                                      ║
║  Metrics tự implement:                                               ║
║   • faithfulness        – LLM judge: answer có nằm trong context?   ║
║   • answer_relevancy    – cosine sim(embed(answer), embed(question)) ║
║   • context_precision   – cosine sim(embed(context), embed(question))║
║   • context_recall      – cosine sim(embed(context), embed(ground))  ║
║                                                                      ║
║  Yêu cầu:                                                            ║
║   1. Ollama đang chạy:  ollama serve                                 ║
║   2. Đã pull model:     ollama pull nomic-embed-text                 ║
║                         ollama pull llama3                           ║
║   3. pip install ollama pandas matplotlib requests                   ║
╚══════════════════════════════════════════════════════════════════════╝
"""

# ─── Imports ──────────────────────────────────────────────────────────────────
import ast
import json
import math
import re
import sys
import time
import textwrap
from typing import List

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import requests

# ─── Cấu hình ─────────────────────────────────────────────────────────────────
import os, pathlib

# ── Tự tìm file CSV ở nhiều vị trí phổ biến ──────────────────────────────────
_CSV_CANDIDATES = [
    "ragas_questions_v3.csv",
    "evaluation/ragas_questions_v3.csv",
    "NLP/evaluation/ragas_question_v3.csv",
]

def _find_csv() -> str:
    # 1. Thử từng candidate
    for p in _CSV_CANDIDATES:
        if pathlib.Path(p).exists():
            return p
    # 2. Tìm đệ quy từ thư mục hiện tại (glob)
    for p in pathlib.Path(".").rglob("ragas_*.csv"):
        return str(p)
    # 3. Không tìm thấy → báo lỗi rõ ràng
    sys.exit(
        "\n❌  Không tìm thấy file CSV!\n"
        "    Hãy đặt file vào cùng thư mục với script và đặt tên:\n"
        "      ragas_questions.csv  HOẶC  ragas_test_data.csv\n"
        "    Hoặc sửa biến INPUT_CSV ở đầu file.\n"
    )

INPUT_CSV        = _find_csv()
OUTPUT_CSV       = "ragas_result.csv"
CHART_PNG        = "ragas_chart.png"
OLLAMA_BASE_URL = "http://localhost:11434"
EMBED_MODEL      = "nomic-embed-text:latest"      # model embedding

# ── Tự chọn LLM judge từ các model đã pull ───────────────────────────────────
# Ưu tiên theo thứ tự: llama3 → mistral → phi3 → gemma → bất kỳ model nào có
_LLM_PREFER = ["llama3.2:latest", "qwen2.5:0.5b"]
LLM_MODEL   = "qwen2.5:0.5b"  # sẽ được resolve ở check_ollama_models()

# ─── Tiện ích Ollama ──────────────────────────────────────────────────────────

def _post(endpoint: str, payload: dict, timeout: int = 120) -> dict:
    """Gọi Ollama REST API, raise lỗi rõ ràng."""
    url = f"{OLLAMA_BASE_URL}{endpoint}"
    try:
        r = requests.post(url, json=payload, timeout=timeout)
        r.raise_for_status()
        return r.json()
    except requests.exceptions.ConnectionError:
        sys.exit(
            "\n  Không kết nối được Ollama!\n"
            "    Hãy chạy:  ollama serve\n"
            "    rồi thử lại script."
        )
    except requests.exceptions.HTTPError as e:
        sys.exit(f"\n  Ollama HTTP error: {e}\n    Response: {r.text}")


def embed(text: str) -> List[float]:
    """Trả về vector embedding của một đoạn văn bản."""
    data = _post("/api/embeddings", {"model": EMBED_MODEL, "prompt": text})
    return data["embedding"]


def cosine_sim(a: List[float], b: List[float]) -> float:
    """Tính cosine similarity giữa 2 vector."""
    dot   = sum(x * y for x, y in zip(a, b))
    mag_a = math.sqrt(sum(x * x for x in a))
    mag_b = math.sqrt(sum(x * x for x in b))
    if mag_a == 0 or mag_b == 0:
        return 0.0
    return max(0.0, min(1.0, dot / (mag_a * mag_b)))


def llm_judge(prompt: str) -> str:
    """Gọi LLM và trả về text response (non-streaming)."""
    data = _post(
        "/api/generate",
        {"model": LLM_MODEL, "prompt": prompt, "stream": False},
        timeout=180,
    )
    return data.get("response", "").strip()

# ─── Helpers ──────────────────────────────────────────────────────────────────

def parse_contexts(val) -> List[str]:
    """Chuyển cột contexts (chuỗi hoặc list) → list[str]."""
    if isinstance(val, list):
        return val
    val = str(val).strip()
    if val.startswith("["):
        try:
            parsed = ast.literal_eval(val)
            if isinstance(parsed, list):
                return [str(x) for x in parsed]
        except Exception:
            pass
    return [val]


def avg_pool(vectors: List[List[float]]) -> List[float]:
    """Trung bình cộng nhiều vector → 1 vector."""
    if len(vectors) == 1:
        return vectors[0]
    length = len(vectors[0])
    result = [0.0] * length
    for v in vectors:
        for i, x in enumerate(v):
            result[i] += x
    n = len(vectors)
    return [x / n for x in result]


def progress(current: int, total: int, label: str = "") -> None:
    pct   = int(current / total * 40)
    bar   = "█" * pct + "░" * (40 - pct)
    print(f"\r  [{bar}] {current}/{total}  {label:<35}", end="", flush=True)

# ─── 4 Metrics ────────────────────────────────────────────────────────────────

def score_faithfulness(answer: str, contexts: List[str]) -> float:
    """
    LLM judge: yêu cầu model xác nhận mỗi câu trong answer
    có được hỗ trợ bởi context hay không.
    Trả về tỉ lệ số câu được hỗ trợ / tổng số câu.
    """
    context_text = "\n".join(f"- {c}" for c in contexts)
    prompt = textwrap.dedent(f"""
        You are a factual checker. Below is a CONTEXT and an ANSWER.
        For each sentence in the ANSWER, decide if it is supported by the CONTEXT.
        Reply ONLY with a JSON array of true/false values, one per sentence.
        Example: [true, false, true]

        CONTEXT:
        {context_text}

        ANSWER:
        {answer}

        JSON array:
    """).strip()

    raw = llm_judge(prompt)

    # Trích xuất JSON array từ response
    match = re.search(r"\[.*?\]", raw, re.DOTALL)
    if not match:
        # Fallback: đếm true/false trong text
        trues  = raw.lower().count("true")
        falses = raw.lower().count("false")
        total  = trues + falses
        return trues / total if total > 0 else 0.5

    try:
        verdicts = json.loads(match.group())
        if not verdicts:
            return 0.5
        return sum(1 for v in verdicts if v is True) / len(verdicts)
    except Exception:
        return 0.5


def score_answer_relevancy(question: str, answer: str) -> float:
    """cosine_sim(embed(answer), embed(question))"""
    eq = embed(question)
    ea = embed(answer)
    return cosine_sim(eq, ea)


def score_context_precision(question: str, contexts: List[str]) -> float:
    """
    Average cosine_sim(embed(context_i), embed(question))
    → context nào liên quan đến question?
    """
    eq = embed(question)
    sims = [cosine_sim(embed(c), eq) for c in contexts]
    return sum(sims) / len(sims)


def score_context_recall(contexts: List[str], ground_truth: str) -> float:
    """
    cosine_sim(avg_pool(embed(contexts)), embed(ground_truth))
    → context có bao phủ được ground truth không?
    """
    eg      = embed(ground_truth)
    ec_vecs = [embed(c) for c in contexts]
    ec_avg  = avg_pool(ec_vecs)
    return cosine_sim(ec_avg, eg)

# ─── Pipeline chính ───────────────────────────────────────────────────────────

def check_ollama_models() -> None:
    """Kiểm tra model đã pull và tự chọn LLM judge phù hợp."""
    global LLM_MODEL

    try:
        r = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=10)
        r.raise_for_status()
        tags  = r.json()
        avail = [m["name"] for m in tags.get("models", [])]
    except requests.exceptions.ConnectionError:
        sys.exit(
            "\n  Không kết nối được Ollama!\n"
            "    Hãy chạy:  ollama serve\n"
            "    rồi thử lại script.\n"
        )
    except Exception as e:
        print(f"  Không thể kiểm tra model: {e}. Dùng mặc định llama3.\n")
        LLM_MODEL = "qwen2.5:0.5b"
        return

    # Tự chọn LLM judge từ danh sách ưu tiên
    for preferred in _LLM_PREFER:
        if preferred in avail:
            LLM_MODEL = preferred
            break

    if LLM_MODEL is None:
        # Không có model nào trong danh sách ưu tiên → dùng bất kỳ model nào không phải embed
        others = [m for m in avail if "embed" not in m and "nomic" not in m]
        if others:
            LLM_MODEL = others[0]
        else:
            sys.exit(
                "\n  Không tìm thấy LLM model nào trong Ollama!\n"
                "    Chạy một trong các lệnh sau để cài:\n"
                "      ollama pull llama3      (khuyên dùng, ~4.7GB)\n"
                "      ollama pull mistral     (~4.1GB)\n"
                "      ollama pull phi3        (~2.3GB, máy yếu)\n"
                "      ollama pull gemma:2b    (~1.7GB, máy rất yếu)\n"
            )

    # Kiểm tra embed model
    if EMBED_MODEL not in avail:
        sys.exit(
            f"\n  Chưa pull embedding model '{EMBED_MODEL}'!\n"
            f"    Chạy:  ollama pull {EMBED_MODEL}\n"
        )

    print(f"  Embedding model : {EMBED_MODEL}")
    print(f"  LLM judge       : {LLM_MODEL}  (tự chọn từ danh sách đã pull)\n")


def main() -> None:
    print("=" * 62)
    print("    RAGAS Evaluation — Powered by Ollama (no OpenAI)  ")
    print("=" * 62 + "\n")

    # 1. Kiểm tra Ollama & model
    print("[0/5] Kiểm tra kết nối Ollama …")
    check_ollama_models()

    # 2. Đọc CSV
    print(f"[1/5] Đọc dữ liệu '{INPUT_CSV}' …")
    print(f"      Đường dẫn đầy đủ: {pathlib.Path(INPUT_CSV).resolve()}")
    df = pd.read_csv(INPUT_CSV)
    required = {"question", "answer", "contexts", "ground_truth"}
    missing_cols = required - set(df.columns)
    if missing_cols:
        sys.exit(f"  File CSV thiếu cột: {missing_cols}")

    df["contexts_list"] = df["contexts"].apply(parse_contexts)
    n = len(df)
    print(f"      → {n} dòng dữ liệu.\n")

    # 3. Tính metrics
    print(f"[2/5] Chạy đánh giá ({n} dòng × 4 metrics) …\n")
    print("      Model embedding : ", EMBED_MODEL)
    print("      Model LLM judge : ", LLM_MODEL)
    print()

    rows_faith  = []
    rows_ar     = []
    rows_cp     = []
    rows_cr     = []

    for i, row in df.iterrows():
        idx      = i + 1
        q        = str(row["question"])
        a        = str(row["answer"])
        g        = str(row["ground_truth"])
        ctxs     = row["contexts_list"]

        # faithfulness (LLM call — chậm hơn)
        progress(idx, n, f"faithfulness   row {idx}")
        f_score = score_faithfulness(a, ctxs)
        rows_faith.append(f_score)

        progress(idx, n, f"answer_relevancy row {idx}")
        ar_score = score_answer_relevancy(q, a)
        rows_ar.append(ar_score)

        progress(idx, n, f"context_precision row {idx}")
        cp_score = score_context_precision(q, ctxs)
        rows_cp.append(cp_score)

        progress(idx, n, f"context_recall row {idx}")
        cr_score = score_context_recall(ctxs, g)
        rows_cr.append(cr_score)

    print("\n")  # xuống dòng sau progress bar

    # 4. Gắn kết quả vào DataFrame
    df["faithfulness"]      = rows_faith
    df["answer_relevancy"]  = rows_ar
    df["context_precision"] = rows_cp
    df["context_recall"]    = rows_cr

    # 5. In tổng quan
    METRIC_NAMES = ["faithfulness", "answer_relevancy", "context_precision", "context_recall"]
    avgs = {m: df[m].mean() for m in METRIC_NAMES}

    print("[3/5] Kết quả tổng quan:\n")
    print("=" * 58)
    print("    RAGAS — Điểm trung bình toàn dataset")
    print("=" * 58)
    for name, score in avgs.items():
        bar = "█" * int(score * 24) + "░" * (24 - int(score * 24))
        print(f"  {name:<22} {score:.4f}  |{bar}|")
    print("=" * 58)

    print("\n  Chi tiết từng dòng:\n")
    detail_cols = ["question"] + METRIC_NAMES
    print(df[detail_cols].to_string(index=False, float_format=lambda x: f"{x:.3f}"))
    print()

    # 6. Lưu CSV
    print(f"\n[4/5] Lưu kết quả → '{OUTPUT_CSV}' …")
    out_cols = ["question", "answer", "contexts", "ground_truth"] + METRIC_NAMES
    df[out_cols].to_csv(OUTPUT_CSV, index=False, encoding="utf-8-sig")
    print(f"      → Đã lưu {len(df)} dòng.\n")

    # 7. Vẽ biểu đồ
    print(f"[5/5] Vẽ biểu đồ → '{CHART_PNG}' …")
    COLORS = ["#4C9BE8", "#56C596", "#F5A623", "#E8605A"]
    scores = [avgs[m] for m in METRIC_NAMES]

    fig, ax = plt.subplots(figsize=(10, 6))
    bars = ax.bar(METRIC_NAMES, scores, color=COLORS, width=0.5,
                  edgecolor="white", linewidth=1.5)

    # Nhãn số trên cột
    for bar, score in zip(bars, scores):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + 0.018,
            f"{score:.3f}",
            ha="center", va="bottom",
            fontsize=13, fontweight="bold", color="#222222",
        )

    # Đường tham chiếu 0.5 và 0.8
    for ref, ls, lbl in [(0.5, "--", "0.5 baseline"), (0.8, ":", "0.8 target")]:
        ax.axhline(ref, color="#999999", linestyle=ls, linewidth=1,
                   label=lbl, alpha=0.7)

    ax.set_ylim(0, 1.18)
    ax.set_ylabel("Điểm trung bình (0 – 1)", fontsize=12)
    ax.set_xlabel("Metric RAGAS", fontsize=12)
    ax.set_title(
        "📊  RAGAS Evaluation — Điểm trung bình theo Metric\n"
        f"(Embedding: {EMBED_MODEL} | Judge: {LLM_MODEL})",
        fontsize=13, fontweight="bold", pad=14,
    )
    ax.set_xticks(range(len(METRIC_NAMES)))
    ax.set_xticklabels(METRIC_NAMES, fontsize=10)
    ax.yaxis.grid(True, linestyle="--", alpha=0.35, color="#cccccc")
    ax.set_axisbelow(True)
    ax.spines[["top", "right"]].set_visible(False)

    patches = [mpatches.Patch(color=c, label=n) for c, n in zip(COLORS, METRIC_NAMES)]
    ax.legend(handles=patches, loc="upper right", fontsize=9,
              framealpha=0.7, edgecolor="#cccccc")

    plt.tight_layout()
    plt.savefig(CHART_PNG, dpi=150, bbox_inches="tight")
    plt.show()
    print(f"      → Đã lưu biểu đồ.\n")

    print("  Hoàn tất!")
    print(f"   • Kết quả chi tiết : {OUTPUT_CSV}")
    print(f"   • Biểu đồ          : {CHART_PNG}")
    print()


if __name__ == "__main__":
    main()