import requests
import pandas as pd
from openai import OpenAI
import json
import os

# 1. 这里是从环境变量安全读取 API Key
API_KEY = os.environ.get("DEEPSEEK_API_KEY")

# 2. 这里是我们的目标数据源链接
TARGET_URL = "https://raw.githubusercontent.com/namewyf/Campus2026/main/README.md"

def fetch_and_filter_data(url):
    """
    抓取 GitHub 原始文本，并利用“脱水算法”只保留真正的表格行，
    过滤掉前言、贡献指南等废话，防止 Token 超限。
    """
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        lines = response.text.split('\n')
        # 🎯 核心黑科技：只保留含有 Markdown 表格符号 '|' 的行
        table_lines = [line for line in lines if '|' in line]
        
        # 限制前 150 行投递，既有海量数据又不会撑爆 Token（你也可以根据需要调大）
        filtered_text = '\n'.join(table_lines[:150])
        print(f"✅ 成功提取并脱水 GitHub 表格数据，保留了 {len(table_lines[:150])} 行精华数据。")
        return filtered_text
    except Exception as e:
        print(f"❌ 抓取或过滤失败：{e}")
        return ""

def parse_with_ai(text):
    client = OpenAI(api_key=API_KEY, base_url="https://api.deepseek.com") 
    
    prompt = f"""
    你是一个全能的秋招情报分析官。请从以下脱水表格文本中提取有效的招聘信息，严格输出为 JSON 数组，不包含 markdown 标记。
    
    【字段提取与生成规则】
    1. priority: 岗位涉及"出海/数据分析/商业分析/需求分析/解决方案/技术支持/产品经理/UA/Growth"或"新能源/消费电子/美妆/互联网"，标为 "High"，否则 "Normal"。
    2. company_type: "央国企"、"外企"、"民企" 之一（根据公司名智能盲猜）。
    3. start_date / end_date: 有就提取，无则填 "未知" / "招满即止"。
    4. link: 提取真实链接。若无，生成：https://www.baidu.com/s?wd={{公司名}}+校园招聘+官网
    
    JSON 格式要求：
    [{{ "company": "公司名", "company_type": "央国企/外企/民企", "role": "岗位名称", "industry": "行业", "start_date": "开始时间", "end_date": "截止时间", "priority": "High/Normal", "link": "投递链接" }}]
    
    待解析文本：
    {text}
    """
    
    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=[
            {"role": "system", "content": "你只输出严格符合格式的 JSON 数组。"},
            {"role": "user", "content": prompt}
        ]
    )
    
    result_str = response.choices[0].message.content.strip()
    
    # 清理可能带有的 markdown json 符号
    if result_str.startswith("```json"): 
        result_str = result_str[7:]
    if result_str.endswith("```"): 
        result_str = result_str[:-3]
        
    return json.loads(result_str.strip())

if __name__ == "__main__":
    print("正在连接开源仓库并注入‘脱水算法’...")
    raw_text = fetch_and_filter_data(TARGET_URL)
    
    if raw_text:
        print("正在呼叫 DeepSeek 榨干表格内容...")
        try:
            jobs_data = parse_with_ai(raw_text)
            df = pd.DataFrame(jobs_data)
            
            # 确保列的顺序一致，且容错处理（防止 AI 漏掉某些列）
            cols = ['company', 'company_type', 'role', 'industry', 'start_date', 'end_date', 'priority', 'link']
            df = df[[c for c in cols if c in df.columns]]
            
            # 保存到本地 CSV
            df.to_csv("jobs_daily.csv", index=False, encoding="utf-8-sig")
            print(f"✅ 完美逆袭！成功提炼出 {len(df)} 条真实名企岗位！")
            
        except Exception as e:
            print(f"❌ 解析失败：{e}")