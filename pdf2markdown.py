
import base64
import requests
import pathlib
import sys
import os

# 服务URL
API_URL = "http://localhost:18080/layout-parsing"

def main():
    # 获取PDF文件路径，默认为 test.pdf
    if len(sys.argv) > 1:
        pdf_path = sys.argv[1]
    else:
        pdf_path = "GB 55034-2022 建筑与市政施工现场安全卫生与职业健康通用规范.pdf"

    if not os.path.exists(pdf_path):
        print(f"Error: File '{pdf_path}' not found.")
        print("Usage: python pdf2markdown.py <path_to_pdf>")
        return

    print(f"Processing file: {pdf_path}")

    # 对本地PDF进行Base64编码
    with open(pdf_path, "rb") as file:
        file_bytes = file.read()
        file_data = base64.b64encode(file_bytes).decode("ascii")

    payload = {
        "file": file_data, # Base64编码的文件内容
        "fileType": 0,     # 文件类型，0表示PDF文件
        "prettifyMarkdown": True, # 是否输出美化后的 Markdown 文本
        "visualize": False # 是否返回可视化结果图
    }

    try:
        # 调用API
        print("Sending request to API...")
        response = requests.post(API_URL, json=payload)
        
        # 检查响应状态
        if response.status_code != 200:
            print(f"Error: API request failed with status code {response.status_code}")
            print(response.text)
            return

        resp_json = response.json()
        
        if resp_json.get("errorCode") != 0:
            print(f"Error: API returned error code {resp_json.get('errorCode')}")
            print(f"Error Message: {resp_json.get('errorMsg')}")
            return

        result = resp_json["result"]
        
        # 创建输出目录
        input_filename = pathlib.Path(pdf_path).stem
        output_base_dir = pathlib.Path(f"output_{input_filename}")
        output_base_dir.mkdir(exist_ok=True)

        print(f"Saving results to {output_base_dir}...")

        all_markdown_texts = []

        # 处理每一页的结果
        for i, res in enumerate(result["layoutParsingResults"]):
            page_num = i + 1
            print(f"Processing page {page_num}...")
            
            markdown_content = res["markdown"]["text"]
            all_markdown_texts.append(markdown_content)
            
            # 处理图片
            images = res["markdown"].get("images", {})
            for img_rel_path, img_b64 in images.items():
                # img_rel_path 通常是相对路径，如 "images/img_0.jpg"
                # 我们需要将其保存到本地，并确保 markdown 中的引用是正确的
                
                img_save_path = output_base_dir / img_rel_path
                img_save_path.parent.mkdir(parents=True, exist_ok=True)
                
                with open(img_save_path, "wb") as f:
                    f.write(base64.b64decode(img_b64))
            
            # 如果有可视化结果 (visualize=True时)
            if "outputImages" in res and res["outputImages"]:
                 for img_name, img_b64 in res["outputImages"].items():
                    vis_img_path = output_base_dir / f"vis_{img_name}_page_{page_num}.jpg"
                    with open(vis_img_path, "wb") as f:
                        f.write(base64.b64decode(img_b64))
                    print(f"Saved visualization to {vis_img_path}")

        # 合并所有页面的Markdown
        merged_markdown = "\n\n".join(all_markdown_texts)
        merged_md_path = output_base_dir / f"{input_filename}.md"
        
        with open(merged_md_path, "w", encoding="utf-8") as f:
            f.write(merged_markdown)
            
        print(f"Saved merged markdown to {merged_md_path}")

        print("Done.")

    except requests.exceptions.RequestException as e:
        print(f"Error connecting to API: {e}")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()
