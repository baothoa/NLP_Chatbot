# Vietnamese Product Consultant Chatbot using RAG and Semantic Router

## 1. Giới thiệu
Đây là đồ án môn NLP xây dựng chatbot tư vấn sản phẩm bánh ngọt cho cửa hàng Chewy Chewy. Hệ thống sử dụng RAG để truy xuất thông tin sản phẩm và LLM local thông qua Ollama để sinh câu trả lời tự nhiên bằng tiếng Việt.

## 2. Mục tiêu
- Phân loại ý định người dùng: hỏi sản phẩm hoặc trò chuyện thông thường.
- Truy xuất sản phẩm phù hợp từ vector database.
- Sinh câu trả lời ngắn gọn, thân thiện, không bịa thông tin.
- Hỗ trợ hội thoại nhiều lượt thông qua session_id.

## 3. Kiến trúc hệ thống

User Query
→ Semantic Router
→ Product Route / Chitchat Route
→ RAG Retrieval
→ Prompt Construction
→ Ollama LLM
→ Response

## 4. Công nghệ sử dụng
- Python
- Flask
- ChromaDB
- SentenceTransformer
- keepitreal/vietnamese-sbert
- Ollama llama3.2
- HTML/CSS/JavaScript

## 5. Cách cài đặt

```bash
git clone https://github.com/baothoa/NLP_Chatbot.git
cd NLP_Chatbot
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
