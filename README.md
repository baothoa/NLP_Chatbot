# Chewy Chewy AI Chatbot

Đây là đồ án môn Xử lý ngôn ngữ tự nhiên xây dựng chatbot tư vấn bán bánh cho tiệm bánh Chewy Chewy.

## Chức năng chính

- Tư vấn sản phẩm bánh dựa trên dữ liệu Chewy Chewy.
- Phân loại câu hỏi bằng Semantic Router.
- Truy xuất thông tin sản phẩm bằng RAG và ChromaDB.
- Sinh câu trả lời bằng Ollama LLM.
- Có giao diện web HTML để người dùng chat.
- Có fallback để xử lý câu hỏi ngoài phạm vi.

## Công nghệ sử dụng

- Python
- Flask
- ChromaDB
- SentenceTransformers
- Vietnamese SBERT
- Ollama llama3.2
- HTML/CSS/JavaScript

## Kiến trúc hệ thống

User Query → Semantic Router → RAG Retrieval → Prompt → Ollama LLM → Response

Nếu câu hỏi không liên quan đến sản phẩm hoặc hội thoại thông thường, hệ thống trả về fallback response.

## Cách cài đặt

```bash
pip install -r requirements.txt
```

## Cách chạy

Chạy Ollama:

```bash
ollama run llama3.2
```

Chạy Flask:

```bash
python flask_serve.py
```

Mở file:

```txt
chat.html
```

## API

Endpoint:

```txt
POST /api/v1/chewy_chewy
```

Body:

```json
{
  "session_id": "demo_session",
  "query": "Bên mình có bánh sinh nhật không?"
}
```

## Đánh giá Semantic Router

```bash
python evaluation/evaluate_router.py
```

## Điểm nổi bật

Hệ thống không chỉ gọi LLM trực tiếp mà kết hợp Semantic Router, Vietnamese Sentence Embedding, RAG và Fallback Mechanism. Cách tiếp cận này giúp chatbot trả lời có căn cứ trên dữ liệu sản phẩm và giảm hiện tượng hallucination.
