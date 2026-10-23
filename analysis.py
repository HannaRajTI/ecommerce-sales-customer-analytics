import pandas as pd
import numpy as np
import datetime as dt

def load_and_clean_data(file_path):
    # Load data
    df = pd.read_csv(file_path, encoding='ISO-8859-1')
    
    # Standardize column names
    df.columns = [col.strip().lower().replace(' ', '_').replace('-', '_') for col in df.columns]
    
    # Map common column aliases to standard names
    column_mapping = {
        'invoice_no': 'invoice',
        'invoiceno': 'invoice',
        'invoice_date': 'invoicedate',
        'unit_price': 'unitprice',
        'customer_id': 'customerid',
        'cust_id': 'customerid',
        'qty': 'quantity',
        'price': 'unitprice'
    }
    
    df.rename(columns=column_mapping, inplace=True)
            
    # Check if critical columns exist
    required_cols = ['customerid', 'invoicedate', 'quantity', 'unitprice']
    for col in required_cols:
        if col not in df.columns:
            raise ValueError(f"Missing required column '{col}'. Available columns: {list(df.columns)}")

    # Clean missing/invalid data
    df = df.dropna(subset=['customerid', 'invoicedate'])
    df['customerid'] = df['customerid'].astype(str).str.split('.').str[0]
    
    # Parse dates
    df['invoicedate'] = pd.to_datetime(df['invoicedate'], errors='coerce')
    df = df.dropna(subset=['invoicedate'])
    
    # Ensure numeric types
    df['quantity'] = pd.to_numeric(df['quantity'], errors='coerce').fillna(0)
    df['unitprice'] = pd.to_numeric(df['unitprice'], errors='coerce').fillna(0.0)
    
    # Filter out returns/cancellations
    df = df[(df['quantity'] > 0) & (df['unitprice'] > 0)]
    
    # Calculate Total Spending
    df['total_price'] = df['quantity'] * df['unitprice']
    
    # Invoice column fallback
    if 'invoice' not in df.columns:
        df['invoice'] = range(len(df))

    return df

def calculate_rfm(df):
    snapshot_date = df['invoicedate'].max() + dt.timedelta(days=1)
    
    rfm = df.groupby('customerid').agg({
        'invoicedate': lambda x: (snapshot_date - x.max()).days,
        'invoice': 'nunique',
        'total_price': 'sum'
    }).reset_index()
    
    rfm.columns = ['customerid', 'recency', 'frequency', 'monetary']
    
    r_labels = [4, 3, 2, 1]
    f_labels = [1, 2, 3, 4]
    m_labels = [1, 2, 3, 4]
    
    rfm['R'] = pd.qcut(rfm['recency'], q=4, labels=r_labels, duplicates='drop')
    rfm['F'] = pd.qcut(rfm['frequency'].rank(method='first'), q=4, labels=f_labels, duplicates='drop')
    rfm['M'] = pd.qcut(rfm['monetary'], q=4, labels=m_labels, duplicates='drop')
    
    rfm['score_num'] = rfm[['R', 'F', 'M']].astype(int).sum(axis=1)
    
    def segment_customer(score):
        if score >= 10:
            return 'VIP / Champions'
        elif score >= 7:
            return 'Loyal Customers'
        elif score >= 5:
            return 'At-Risk / Potential'
        else:
            return 'Lost / Inactive'
            
    rfm['customer_segment'] = rfm['score_num'].apply(segment_customer)
    return rfm