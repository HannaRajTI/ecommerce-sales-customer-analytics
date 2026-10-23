import streamlit as st
import pandas as pd
import plotly.express as px
from analysis import load_and_clean_data, calculate_rfm

st.set_page_config(page_title="E-Commerce Analytics & RFM Dashboard", layout="wide")

st.title("📊 E-Commerce Sales & Customer Segmentation Dashboard")

# Upload CSV File or use default
uploaded_file = st.sidebar.file_uploader("Upload dataset CSV", type=["csv"])

if uploaded_file is not None:
    df = load_and_clean_data(uploaded_file)
else:
    st.info("Please upload a CSV file to begin analysis.")
    st.stop()

rfm = calculate_rfm(df)

# Key Metrics Row
col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Revenue", f"${df['total_price'].sum():,.2f}")
col2.metric("Total Orders", f"{df['invoice'].nunique():,}")
col3.metric("Total Customers", f"{rfm['customerid'].nunique():,}")
col4.metric("Avg Order Value", f"${df['total_price'].sum() / df['invoice'].nunique():,.2f}")

st.markdown("---")

# Visualizations Layout
tab1, tab2 = st.tabs(["📈 Sales Performance", "🎯 Customer Segments (RFM)"])

with tab1:
    st.subheader("Monthly Sales Trend")
    df['year_month'] = df['invoicedate'].dt.to_period('M').astype(str)
    monthly_sales = df.groupby('year_month')['total_price'].sum().reset_index()
    
    fig_sales = px.line(monthly_sales, x='year_month', y='total_price', labels={'total_price': 'Revenue ($)', 'year_month': 'Month'}, title="Monthly Revenue Trend")
    st.plotly_chart(fig_sales, use_container_width=True)

    col_left, col_right = st.columns(2)
    with col_left:
        st.subheader("Top 10 Products by Revenue")
        top_products = df.groupby('description')['total_price'].sum().nlargest(10).reset_index()
        fig_prod = px.bar(top_products, x='total_price', y='description', orientation='h', labels={'total_price': 'Revenue ($)', 'description': 'Product'})
        st.plotly_chart(fig_prod, use_container_width=True)
        
    with col_right:
        st.subheader("Top Countries by Revenue")
        top_countries = df.groupby('country')['total_price'].sum().nlargest(10).reset_index()
        fig_country = px.bar(top_countries, x='country', y='total_price', labels={'total_price': 'Revenue ($)', 'country': 'Country'})
        st.plotly_chart(fig_country, use_container_width=True)

with tab2:
    st.subheader("Customer Distribution across Segments")
    segment_counts = rfm['customer_segment'].value_counts().reset_index()
    segment_counts.columns = ['Segment', 'Count']
    
    fig_pie = px.pie(segment_counts, names='Segment', values='Count', hole=0.4, title="Customer Segments Breakdown")
    st.plotly_chart(fig_pie, use_container_width=True)
    
    st.subheader("RFM Summary Table")
    st.dataframe(rfm[['customerid', 'recency', 'frequency', 'monetary', 'customer_segment']].head(20))