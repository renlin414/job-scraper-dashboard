import requests
import pandas as pd
from openai import OpenAI
import json
import os

import os
# 改为从系统的环境变量中读取 API Key
API_KEY = os.environ.get("DEEPSEEK_API_KEY")

# ==========================================
# 🎯 数据源配置
# ==========================================
# 这里填写你找到的真实 GitHub 秋招/校招汇总仓库的 Raw 链接。
# 如何获取：在 GitHub 找到对应仓库的 README.md 文件，点击右上角的 "Raw" 按钮，复制浏览器里的网址。
# （此处为一个示例结构链接，你需要替换为你自己在 GitHub 上搜到的真实链接）
TARGET_URL = "https://raw.githubusercontent.com/namewyf/Campus2026/refs/heads/main/README.md"

def fetch_real_data(url):
    """从指定的 URL 抓取网页文本数据"""
    try:
        # 添加 User-Agent 伪装成浏览器，防止被直接拦截
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status() # 检查请求是否成功
        
        full_text = response.text
        print(f"✅ 成功获取网页数据，总长度：{len(full_text)} 字符。")
        
        # ⚠️ 核心保护机制：防止文本过长导致大模型 API 报错 (Token 超限)
        # 第一版我们先截取前 4000 个字符（通常是最新的更新记录）。
        # 等你跑通后，如果需要处理全文，可以研究“分块处理 (Chunking)”技术。
        return full_text[:4000] 
        
    except Exception as e:
        print(f"❌ 抓取网页失败，请检查网络或链接是否正确：{e}")
        return ""

def parse_with_ai(text):
    client = OpenAI(api_key=API_KEY, base_url="https://api.deepseek.com") 
    
    prompt = f"""
    你是一个全能的秋招情报分析官。请提取招聘信息，严格输出为 JSON 数组，不包含 markdown 标记。
    
    【字段提取与生成规则】
    1. priority: 属于"出海/数据分析/商业分析/用户获取(UA)/增长(Growth)"或"新能源/消费电子/美妆/互联网"，标为 "High"，否则 "Normal"。
    2. company_type: "央国企"、"外企"、"民企" 之一。
    3. start_date (开始时间): 提取明确的开始日期。若无，填 "未知"。
    4. end_date (截止时间): 提取明确的截止日期。若无，填 "招满即止"。
    5. link: 提取真实链接。若无，生成快捷搜索链接：https://www.baidu.com/s?wd={{公司名}}+校园招聘+招聘官网
    
    JSON 格式要求：
    [{{ "company": "公司名", "company_type": "央国企/外企/民企", "role": "岗位名称", "industry": "所属行业", "start_date": "开始时间", "end_date": "截止时间", "priority": "High/Normal", "link": "投递链接" }}]
    
    待解析文本：
    {text}
    """
    
    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=[
            {"role": "system", "content": "你只输出严格符合格式的 JSON 数组，绝不允许捏造虚假 URL。"},
            {"role": "user", "content": prompt}
        ]
    )
    
    result_str = response.choices[0].message.content.strip()
    if result_str.startswith("```json"):
        result_str = result_str[7:]
    if result_str.endswith("```"):
        result_str = result_str[:-3]
        
    return json.loads(result_str.strip())

if __name__ == "__main__":
    print("正在连接真实开源数据源...")
    raw_text = fetch_real_data(TARGET_URL)
    
    if raw_text:
        print("正在呼叫 DeepSeek 智能清洗并结构化数据...")
        try:
            jobs_data = parse_with_ai(raw_text)
            df = pd.DataFrame(jobs_data)
            
            # 调整列顺序
            cols = ['company', 'company_type', 'role', 'industry', 'start_date', 'end_date', 'priority', 'link']
            cols = [c for c in cols if c in df.columns] 
            df = df[cols]
            
            # 这里的模式改为了覆盖写入。如果要做增量更新，后续可以改为读取旧 CSV 并去重合并
            df.to_csv("jobs_daily.csv", index=False, encoding="utf-8-sig")
            print(f"✅ 成功解析出 {len(df)} 条真实岗位情报！已更新到 jobs_daily.csv！")
        except Exception as e:
            print(f"❌ 数据解析阶段出错：{e}")
    else:
        print("⚠️ 未获取到有效文本，跳过 AI 解析。")