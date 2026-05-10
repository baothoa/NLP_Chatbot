import json
import re
import requests
from bs4 import BeautifulSoup

URL = "https://chewychewy.vn/pages/danh-sach-cua-hang"
OUTPUT = "output_files/chewychewy_stores.json"

headers = {"User-Agent": "Mozilla/5.0"}

def clean_text(text):
    return re.sub(r"\s+", " ", text).strip()

def crawl_stores():
    res = requests.get(URL, headers=headers, timeout=15)
    res.raise_for_status()
    soup = BeautifulSoup(res.text, "html.parser")

    text = soup.get_text("\n", strip=True)
    lines = [clean_text(x) for x in text.split("\n") if clean_text(x)]

    stores = []
    current_city = ""
    current_store = None

    for line in lines:
        if line.startswith("TẠI "):
            current_city = line.replace(":", "").strip()
            continue

        # Ví dụ: 1. Chewy Chewy Nguyễn Cư Trinh:
        if re.match(r"^\d+\.\s+", line):
            if current_store:
                stores.append(current_store)

            name = re.sub(r"^\d+\.\s+", "", line).replace(":", "").strip()
            current_store = {
                "city": current_city,
                "name": name,
                "address": "",
                "opening_hours": "",
                "hotline": "",
                "note": [],
                "source_url": URL
            }
            continue

        if not current_store:
            continue

        if line.startswith("-"):
            value = line.lstrip("-").strip()

            if "Giờ" in value or "hoạt động" in value or "hoạt động" in value:
                current_store["opening_hours"] = value
            elif "Hotline" in value:
                current_store["hotline"] = value
            elif not current_store["address"]:
                current_store["address"] = value
            else:
                current_store["note"].append(value)

        elif line.startswith("*"):
            current_store["note"].append(line.lstrip("*").strip())

    if current_store:
        stores.append(current_store)

    return stores

if __name__ == "__main__":
    stores = crawl_stores()

    with open(OUTPUT, "w", encoding="utf-8") as f:
        json.dump(stores, f, ensure_ascii=False, indent=4)

    print(f"Đã crawl {len(stores)} cửa hàng")
    print(f"Lưu tại: {OUTPUT}")