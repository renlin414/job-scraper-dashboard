import streamlit as st
import pandas as pd
import os

st.set_page_config(page_title="全名企秋招情报看板", layout="wide", initial_sidebar_state="expanded")

st.title("🚀 秋招/校招 追踪看板")
st.markdown("系统每日自动抓取，防失联链接机制已启动。")

data_path = "jobs_daily.csv"
if os.path.exists(data_path):
    df = pd.read_csv(data_path)
    
    # 确保存在 status 列
    if 'status' not in df.columns:
        df.insert(0, 'status', False)
        
    # ==========================
    # 🔍 侧边栏多维筛选区域
    # ==========================
    st.sidebar.header("🎯 核心筛选器")
    
    # 1. 公司性质筛选 (央国企/外企/民企)
    if 'company_type' in df.columns:
        types = df['company_type'].dropna().unique().tolist()
        selected_types = st.sidebar.multiselect("🏢 公司性质", options=types, default=types)
    else:
        selected_types = []

    # 2. 行业领域筛选
    industries = df['industry'].dropna().unique().tolist()
    selected_industries = st.sidebar.multiselect("📊 所属行业", options=industries, default=industries)
    
    # 3. 优先级筛选
    priorities = df['priority'].dropna().unique().tolist()
    selected_priorities = st.sidebar.multiselect("⭐️ 岗位匹配度", options=priorities, default=priorities)
    
    # 4. 投递状态筛选
    show_unapplied_only = st.sidebar.checkbox("✅ 只看未投递岗位")
    
    # 根据用户的选项动态过滤 DataFrame
    filtered_df = df.copy()
    if 'company_type' in df.columns and selected_types:
        filtered_df = filtered_df[filtered_df['company_type'].isin(selected_types)]
    if selected_industries:
        filtered_df = filtered_df[filtered_df['industry'].isin(selected_industries)]
    if selected_priorities:
        filtered_df = filtered_df[filtered_df['priority'].isin(selected_priorities)]
    if show_unapplied_only:
        filtered_df = filtered_df[filtered_df['status'] == False]

    # ==========================
    # 📋 数据展示与修改区域
    # ==========================
    st.subheader(f"当前筛选出 {len(filtered_df)} 个岗位")
    
    # 高亮 High 优先级的整行
    def highlight_high_priority(row):
        return ['background-color: #fff9db' if row['priority'] == 'High' else '' for _ in row]
    
    if not filtered_df.empty:
        # 展示筛选后的表格
        # 展示筛选后的表格，并美化列名
        edited_df = st.data_editor(
            filtered_df.style.apply(highlight_high_priority, axis=1),
            column_config={
                "status": st.column_config.CheckboxColumn("已投递", default=False),
                "company": "公司名称",
                "company_type": "性质",
                "role": "招聘岗位",
                "industry": "行业",
                "start_date": "开始时间",
                "end_date": "截止时间",
                "priority": "优先级",
                "link": st.column_config.LinkColumn("直达链接", display_text="点击前往")
            },
            use_container_width=True,
            hide_index=True,
            key="data_editor"
        )
        
        # 保存按钮逻辑
        if st.button("💾 保存我的投递进度"):
            # 将筛选出来并修改后的数据更新回完整的大表中
            df.update(edited_df)
            df.to_csv(data_path, index=False, encoding="utf-8-sig")
            st.success("进度已成功保存！")
    else:
        st.info("当前筛选条件下没有匹配的岗位，请调整左侧筛选器。")
else:
    st.warning("请先在终端运行 python scraper.py 生成数据！")