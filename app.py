# app.py
import streamlit as st
import requests
import json
import PyPDF2
import io
import re
import pandas as pd
import yfinance as yf
import plotly.graph_objs as go
import plotly.express as px
from datetime import datetime, timedelta
from thefuzz import fuzz
import matplotlib.pyplot as plt
from wordcloud import WordCloud
import numpy as np
from PIL import Image
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure page
st.set_page_config(layout="wide", page_title="Ethical Stock Screener", page_icon="📈")

# Custom CSS for styling
st.markdown("""
<style>
    :root {
        --primary: #1f77b4;
        --secondary: #2ca02c;
        --success: #28a745;
        --warning: #ffc107;
        --danger: #dc3545;
        --info: #17a2b8;
        --dark: #343a40;
        --light: #f8f9fa;
    }
    
    .header {
        font-size: 36px !important;
        font-weight: bold !important;
        color: var(--primary) !important;
        text-align: center;
        margin-bottom: 25px;
        text-shadow: 1px 1px 3px rgba(0,0,0,0.1);
    }
    .subheader {
        font-size: 24px !important;
        font-weight: bold !important;
        color: var(--secondary) !important;
        border-bottom: 3px solid var(--secondary);
        padding-bottom: 10px;
        margin-top: 20px;
        background: linear-gradient(90deg, rgba(44,160,44,0.1) 0%, rgba(255,255,255,0) 100%);
        padding: 10px 15px;
        border-radius: 5px;
    }
    .card {
        background-color: #f8f9fa;
        border-radius: 10px;
        padding: 20px;
        margin-bottom: 20px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        transition: transform 0.3s ease, box-shadow 0.3s ease;
    }
    .card:hover {
        transform: translateY(-5px);
        box-shadow: 0 8px 15px rgba(0,0,0,0.1);
    }
    .success-card {
        background-color: #d4edda;
        border-left: 5px solid var(--success);
    }
    .warning-card {
        background-color: #fff3cd;
        border-left: 5px solid var(--warning);
    }
    .error-card {
        background-color: #f8d7da;
        border-left: 5px solid var(--danger);
    }
    .info-card {
        background-color: #d1ecf1;
        border-left: 5px solid var(--info);
    }
    .sdg-card {
        background-color: #e8f4f8;
        border-radius: 10px;
        padding: 15px;
        margin: 10px 0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        transition: all 0.3s ease;
    }
    .sdg-card:hover {
        box-shadow: 0 5px 15px rgba(0,0,0,0.1);
    }
    .metric-card {
        background: linear-gradient(135deg, #6a11cb 0%, #2575fc 100%);
        color: white;
        border-radius: 10px;
        padding: 15px;
        text-align: center;
        margin: 10px 0;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .metric-value {
        font-size: 28px;
        font-weight: bold;
        margin: 10px 0;
    }
    .metric-label {
        font-size: 14px;
        opacity: 0.9;
    }
    .stButton>button {
        background: linear-gradient(135deg, #6a11cb 0%, #2575fc 100%);
        color: white;
        border: none;
        border-radius: 5px;
        padding: 10px 20px;
        font-weight: bold;
        transition: all 0.3s ease;
    }
    .stButton>button:hover {
        background: linear-gradient(135deg, #2575fc 0%, #6a11cb 100%);
        color: white;
        transform: scale(1.05);
    }
    .comparison-container {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 20px;
        margin-bottom: 30px;
    }
    .comparison-card {
        background: white;
        border-radius: 10px;
        padding: 20px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .halal-radial {
        width: 150px;
        height: 150px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        margin: 0 auto;
        position: relative;
    }
    .radial-value {
        font-size: 24px;
        font-weight: bold;
        color: var(--dark);
    }
    .detailed-analysis {
        background: white;
        border-radius: 10px;
        padding: 20px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        margin-top: 20px;
    }
    .progress-container {
        height: 10px;
        background: #e9ecef;
        border-radius: 5px;
        margin: 10px 0;
        overflow: hidden;
    }
    .progress-bar {
        height: 100%;
        border-radius: 5px;
    }
    .controversy-tag {
        display: inline-block;
        background-color: #f8d7da;
        color: #721c24;
        padding: 3px 8px;
        border-radius: 20px;
        font-size: 12px;
        margin: 3px;
    }
    .table-container {
        overflow-x: auto;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        margin: 20px 0;
    }
    .stDataFrame {
        border-radius: 10px;
    }
    .sdg-badge {
        display: inline-block;
        width: 30px;
        height: 30px;
        border-radius: 50%;
        text-align: center;
        line-height: 30px;
        font-weight: bold;
        color: white;
        margin-right: 5px;
    }
    .keyword-badge {
        display: inline-block;
        background-color: #e9ecef;
        padding: 3px 10px;
        border-radius: 20px;
        font-size: 12px;
        margin: 3px;
    }
    .sdg-grid {
        display: grid;
        grid-template-columns: repeat(6, 1fr);
        gap: 10px;
        margin-top: 15px;
    }
    .sdg-grid-item {
        text-align: center;
        padding: 10px;
        border-radius: 8px;
        color: white;
        font-weight: bold;
        font-size: 12px;
    }
</style>
""", unsafe_allow_html=True)

# SDG Titles and Descriptions
SDG_TITLES = {
    1: "No Poverty",
    2: "Zero Hunger",
    3: "Good Health and Well-being",
    4: "Quality Education",
    5: "Gender Equality",
    6: "Clean Water and Sanitation",
    7: "Affordable and Clean Energy",
    8: "Decent Work and Economic Growth",
    9: "Industry, Innovation and Infrastructure",
    10: "Reduced Inequalities",
    11: "Sustainable Cities and Communities",
    12: "Responsible Consumption and Production",
    13: "Climate Action",
    14: "Life Below Water",
    15: "Life on Land",
    16: "Peace, Justice and Strong Institutions",
    17: "Partnerships for the Goals"
}

SDG_COLORS = {
    1: "#e5243b",
    2: "#dda63a",
    3: "#4c9f38",
    4: "#c5192d",
    5: "#ff3a21",
    6: "#26bde2",
    7: "#fcc30b",
    8: "#a21942",
    9: "#fd6925",
    10: "#dd1367",
    11: "#fd9d24",
    12: "#bf8b2e",
    13: "#3f7e44",
    14: "#0a97d9",
    15: "#56c02b",
    16: "#00689d",
    17: "#19486a"
}

SDG_DESCRIPTIONS = {
    1: "End poverty in all its forms everywhere",
    2: "End hunger, achieve food security and improved nutrition and promote sustainable agriculture",
    3: "Ensure healthy lives and promote well-being for all at all ages",
    4: "Ensure inclusive and equitable quality education and promote lifelong learning opportunities for all",
    5: "Achieve gender equality and empower all women and girls",
    6: "Ensure availability and sustainable management of water and sanitation for all",
    7: "Ensure access to affordable, reliable, sustainable and modern energy for all",
    8: "Promote sustained, inclusive and sustainable economic growth, full and productive employment and decent work for all",
    9: "Build resilient infrastructure, promote inclusive and sustainable industrialization and foster innovation",
    10: "Reduce inequality within and among countries",
    11: "Make cities and human settlements inclusive, safe, resilient and sustainable",
    12: "Ensure sustainable consumption and production patterns",
    13: "Take urgent action to combat climate change and its impacts",
    14: "Conserve and sustainably use the oceans, seas and marine resources for sustainable development",
    15: "Protect, restore and promote sustainable use of terrestrial ecosystems, sustainably manage forests, combat desertification, and halt and reverse land degradation and halt biodiversity loss",
    16: "Promote peaceful and inclusive societies for sustainable development, provide access to justice for all and build effective, accountable and inclusive institutions at all levels",
    17: "Strengthen the means of implementation and revitalize the Global Partnership for Sustainable Development"
}

# Controversy keywords for PDF analysis
CONTROVERSY_KEYWORDS = [
    "controvers", "scandal", "lawsuit", "violation", "protest", "fine", "penalty",
    "ethical concern", "human rights", "exploitation", "pollution", "discrimination",
    "corruption", "bribery", "fraud", "investigation", "settlement", "conflict"
]


# Load data from Excel files
def load_data():
    try:
        # Create data directory if it doesn't exist
        os.makedirs('data', exist_ok=True)
        
        # Check if Halal file exists, create if not
        halal_path = 'data/halal_checker.xlsx'
        if not os.path.exists(halal_path):
            pd.DataFrame(columns=['Ticker', 'Company Name', 'Sector', 'Final Halal Status', 'Reason']).to_excel(halal_path, index=False)
        
        # Check if SDG file exists, create if not
        sdg_path = 'data/sdg_checker.xlsx'
        if not os.path.exists(sdg_path):
            pd.DataFrame(columns=['Ticker', 'Company Name', 'SDG GOAL NO.', 'keywords']).to_excel(sdg_path, index=False)
        
        # Load Halal data
        halal_df = pd.read_excel(halal_path, sheet_name=0, engine='openpyxl')
        # Normalize column names
        halal_df.columns = halal_df.columns.str.strip()

        # Check for required columns
        required_columns = ['Ticker', 'Company Name', 'Sector', 'Final Halal Status', 'Reason']
        for col in required_columns:
            if col not in halal_df.columns:
                st.error(f"Missing column in Halal data: {col}")
                return pd.DataFrame(), pd.DataFrame()

        halal_df = halal_df[required_columns]
        halal_df = halal_df.rename(columns={
            'Final Halal Status': 'Halal Status',
            'Reason': 'Halal Reason'
        })
        halal_df = halal_df[halal_df['Halal Status'].notna() &
                            (halal_df['Halal Status'] != '')]

        # Load SDG data
        sdg_df = pd.read_excel(sdg_path, sheet_name=0, engine='openpyxl')
        # Normalize column names
        sdg_df.columns = sdg_df.columns.str.strip()

        # Check for required columns
        required_columns = ['Ticker', 'Company Name', 'SDG GOAL NO.', 'keywords']
        for col in required_columns:
            if col not in sdg_df.columns:
                st.error(f"Missing column in SDG data: {col}")
                return pd.DataFrame(), pd.DataFrame()

        sdg_df = sdg_df[required_columns]
        sdg_df = sdg_df.rename(columns={
            'SDG GOAL NO.': 'Primary SDG',
            'keywords': 'SDG Keywords'
        })
        sdg_df = sdg_df[sdg_df['Primary SDG'].notna() &
                        (sdg_df['Primary SDG'] != '')]

        return halal_df, sdg_df

    except Exception as e:
        st.error(f"Error loading data files: {str(e)}")
        return pd.DataFrame(), pd.DataFrame()


def create_ticker_mapping(halal_df):
    if halal_df.empty:
        return {}
    return dict(zip(halal_df['Company Name'], halal_df['Ticker']))


def get_stock_data(ticker):
    try:
        stock = yf.Ticker(ticker)
        hist = stock.history(period="1y")

        if hist.empty:
            return None

        current_price = hist['Close'].iloc[-1]
        week52_high = hist['High'].max()
        week52_low = hist['Low'].min()

        # Calculate additional metrics
        moving_avg_50 = hist['Close'].tail(50).mean()
        moving_avg_200 = hist['Close'].tail(200).mean()
        daily_returns = hist['Close'].pct_change().dropna()
        volatility = daily_returns.std() * np.sqrt(252)  # Annualized volatility

        return {
            'current_price': current_price,
            '52_week_high': week52_high,
            '52_week_low': week52_low,
            'moving_avg_50': moving_avg_50,
            'moving_avg_200': moving_avg_200,
            'volatility': volatility
        }
    except:
        return None


def plot_stock_history(ticker):
    try:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=365)

        stock = yf.Ticker(ticker)
        hist = stock.history(start=start_date, end=end_date)

        if hist.empty:
            return None

        # Calculate moving averages
        hist['MA50'] = hist['Close'].rolling(window=50).mean()
        hist['MA200'] = hist['Close'].rolling(window=200).mean()

        fig = go.Figure()
        fig.add_trace(
            go.Scatter(x=hist.index, y=hist['Close'], mode='lines', name='Close Price', line=dict(color='#1f77b4')))
        fig.add_trace(go.Scatter(x=hist.index, y=hist['MA50'], mode='lines', name='50-Day MA',
                                 line=dict(color='#ff7f0e', dash='dash')))
        fig.add_trace(go.Scatter(x=hist.index, y=hist['MA200'], mode='lines', name='200-Day MA',
                                 line=dict(color='#2ca02c', dash='dash')))

        fig.update_layout(
            title=f'{ticker} Stock Price (1 Year)',
            xaxis_title='Date',
            yaxis_title='Price ($)',
            template='plotly_white',
            height=400,
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )

        return fig
    except:
        return None


# Grok API integration
def get_grok_analysis(company_name, ticker):
    """Get ethical analysis from Grok API for companies not in the dataset"""
    try:
        # Get API key with proper error handling
        api_key = None
        
        # First try environment variables
        if os.getenv("GROK_API_KEY"):
            api_key = os.getenv("GROK_API_KEY")
            st.toast("Using API key from environment variables", icon="🔑")
        
        # Then try Streamlit secrets
        elif hasattr(st, "secrets"):
            try:
                if "GROK_API_KEY" in st.secrets:
                    api_key = st.secrets["GROK_API_KEY"]
                    st.toast("Using API key from Streamlit secrets", icon="🔒")
                # Check for nested secrets (common in Streamlit)
                elif "grok" in st.secrets and "api_key" in st.secrets.grok:
                    api_key = st.secrets.grok["api_key"]
                    st.toast("Using API key from nested secrets", icon="🔒")
            except Exception as secrets_error:
                st.error(f"Secrets access error: {str(secrets_error)}")
                return None
        
        if not api_key:
            st.error("GROK_API_KEY not found in environment variables or Streamlit secrets")
            st.info("Please ensure your key is set in Streamlit's secrets under 'GROK_API_KEY'")
            return None

        # API endpoint and headers
        api_endpoint = "https://api.groq.com/openai/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

        # Create the prompt with enhanced detail request
        prompt = f"""
        You are an expert in Islamic finance and sustainable development goals (SDGs). 
        Please analyze the company {company_name} ({ticker}) and provide:

        1. Halal status: [Halal or Not Halal]
        2. Detailed reason for Halal status: [3-5 sentences explaining business activities, financial ratios, and compliance with Islamic principles]
        3. Business activities breakdown: [detailed description of core business activities]
        4. Financial compliance analysis: [analysis of debt, interest-based income, and other financial factors]
        5. Primary SDG goal: [number between 1 and 17, or 0 if none]
        6. Secondary SDG goals: [comma separated list of additional relevant SDGs]
        7. SDG keywords: [comma separated keywords]
        8. Sector: [sector of the company]
        9. SDG impact analysis: [detailed explanation of the company's impact on primary SDG]
        10. Controversies: [any known ethical or environmental controversies]

        Output in JSON format only:
        {{
            "halal_status": "Halal",
            "detailed_reason": "The company operates in the technology sector...",
            "business_activities": "Detailed description of business activities...",
            "financial_analysis": "Analysis of financial compliance...",
            "sdg_goal": 9,
            "secondary_sdgs": "4,5,8",
            "sdg_keywords": "innovation, technology, digital transformation",
            "sector": "Technology",
            "sdg_impact": "The company contributes to SDG 9 through...",
            "controversies": "None known"
        }}
        """

        # Create the payload with UPDATED MODEL
        payload = {
            "model": "llama3-70b-8192",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.3,
            "max_tokens": 1000
        }

        # Make the API request
        response = requests.post(api_endpoint, headers=headers, json=payload, timeout=45)

        if response.status_code == 200:
            # Extract the JSON content from the response
            response_data = response.json()
            content = response_data['choices'][0]['message']['content']
            
            # FIX: Improved JSON parsing logic
            try:
                # First try to parse the entire content as JSON
                return json.loads(content)
            except json.JSONDecodeError:
                # If that fails, look for the JSON object within the content
                try:
                    # Find the first { and last } to extract the JSON
                    start_index = content.find('{')
                    end_index = content.rfind('}') + 1
                    
                    if start_index == -1 or end_index == -1:
                        st.error("No JSON object found in Grok response")
                        return None
                        
                    json_str = content[start_index:end_index]
                    return json.loads(json_str)
                except Exception as e:
                    st.error(f"Error parsing Grok response: {str(e)}")
                    st.error(f"Response content: {content}")
                    return None
        else:
            st.error(f"Grok API error: {response.status_code} - {response.text}")
            return None

    except Exception as e:
        st.error(f"Error accessing Grok API: {str(e)}")
        return None


def save_to_halal_excel(company_name, ticker, grok_data):
    """Save AI-generated data to Halal Excel file"""
    try:
        file_path = 'data/halal_checker.xlsx'

        # Create new row data
        new_row = {
            'Ticker': ticker,
            'Company Name': company_name,
            'Sector': grok_data.get('sector', ''),
            'Final Halal Status': grok_data.get('halal_status', ''),
            'Reason': grok_data.get('detailed_reason', '')
        }

        # Create new DataFrame for the row
        new_df = pd.DataFrame([new_row])

        # Append to Excel
        if os.path.exists(file_path):
            # Read existing data
            halal_df = pd.read_excel(file_path, sheet_name=0, engine='openpyxl')

            # Append new row
            halal_df = pd.concat([halal_df, new_df], ignore_index=True)
        else:
            halal_df = new_df

        # Save back to Excel
        halal_df.to_excel(file_path, index=False)
        return True
    except Exception as e:
        st.error(f"Error saving to Halal Excel: {str(e)}")
        return False


def save_to_sdg_excel(company_name, ticker, grok_data):
    """Save AI-generated data to SDG Excel file"""
    try:
        file_path = 'data/sdg_checker.xlsx'

        # Create new row data
        new_row = {
            'Ticker': ticker,
            'Company Name': company_name,
            'SDG GOAL NO.': grok_data.get('sdg_goal', 0),
            'keywords': grok_data.get('sdg_keywords', '')
        }

        # Create new DataFrame for the row
        new_df = pd.DataFrame([new_row])

        # Append to Excel
        if os.path.exists(file_path):
            # Read existing data
            sdg_df = pd.read_excel(file_path, sheet_name=0, engine='openpyxl')

            # Append new row
            sdg_df = pd.concat([sdg_df, new_df], ignore_index=True)
        else:
            sdg_df = new_df

        # Save back to Excel
        sdg_df.to_excel(file_path, index=False)
        return True
    except Exception as e:
        st.error(f"Error saving to SDG Excel: {str(e)}")
        return False


def find_company(halal_df, company_name, ticker_symbol):
    """Find company in dataset with error handling"""
    company_match = None

    # Normalize inputs
    company_name_norm = company_name.strip().lower() if company_name else None
    ticker_norm = ticker_symbol.strip().upper() if ticker_symbol else None

    # Check if we have data to search
    if halal_df.empty:
        return None

    if company_name_norm:
        # Normalize company names in dataframe
        halal_df_normalized = halal_df.copy()
        halal_df_normalized['Company Name Normalized'] = halal_df_normalized['Company Name'].str.strip().str.lower()

        # Find exact match
        exact_matches = halal_df_normalized[halal_df_normalized['Company Name Normalized'] == company_name_norm]
        if not exact_matches.empty:
            company_match = exact_matches.iloc[0]
        else:
            # Try fuzzy matching as fallback
            matches = halal_df_normalized['Company Name Normalized'].apply(
                lambda x: fuzz.ratio(x, company_name_norm))
            best_match = matches.idxmax()
            if matches[best_match] > 80:  # Only accept good matches
                company_match = halal_df_normalized.iloc[best_match]

    if company_match is None and ticker_norm:
        # Normalize tickers in dataframe
        halal_df_normalized = halal_df.copy()
        halal_df_normalized['Ticker Normalized'] = halal_df_normalized['Ticker'].str.strip().str.upper()

        # Find exact match
        matches = halal_df_normalized[halal_df_normalized['Ticker Normalized'] == ticker_norm]
        if not matches.empty:
            company_match = matches.iloc[0]

    return company_match


# PDF Analysis Functions
def extract_text_from_pdf(uploaded_file):
    """Extract text from PDF file"""
    pdf_reader = PyPDF2.PdfReader(io.BytesIO(uploaded_file.read()))
    text = ""
    for page in pdf_reader.pages:
        text += page.extract_text() + "\n"
    return text


def analyze_text_for_sdg(text):
    """Analyze text to identify multiple SDG alignments"""
    sdg_keywords = {
        1: ["poverty", "poor", "impoverished", "deprived", "economic disadvantage"],
        2: ["hunger", "food", "nutrition", "famine", "malnutrition", "agriculture"],
        3: ["health", "well-being", "disease", "hospital", "medicine", "vaccine"],
        4: ["education", "school", "learning", "literacy", "university", "student"],
        5: ["gender", "women", "girls", "equality", "empowerment", "feminism"],
        6: ["water", "sanitation", "hygiene", "clean water", "wastewater"],
        7: ["energy", "renewable", "solar", "wind", "electricity", "power"],
        8: ["work", "employment", "economic growth", "decent work", "job"],
        9: ["industry", "innovation", "infrastructure", "technology", "research"],
        10: ["inequality", "discrimination", "inclusion", "equity", "marginalized"],
        11: ["city", "urban", "community", "housing", "transportation", "safe"],
        12: ["consumption", "production", "waste", "recycle", "sustainable"],
        13: ["climate", "global warming", "carbon", "emissions", "temperature"],
        14: ["ocean", "sea", "marine", "fish", "coral", "coastal"],
        15: ["land", "forest", "biodiversity", "ecosystem", "desertification"],
        16: ["peace", "justice", "institutions", "corruption", "rights"],
        17: ["partnership", "global", "cooperation", "implementation", "finance"]
    }

    # Count keyword occurrences for ALL SDGs
    sdg_counts = {sdg: 0 for sdg in range(1, 18)}
    sdg_keywords_found = {sdg: [] for sdg in range(1, 18)}  # Track found keywords per SDG

    for sdg, keywords in sdg_keywords.items():
        for keyword in keywords:
            if re.search(rf'\b{keyword}\b', text, re.IGNORECASE):
                sdg_counts[sdg] += 1
                sdg_keywords_found[sdg].append(keyword)  # Add keyword to list

    # Identify ALL SDGs with at least 1 keyword match
    relevant_sdgs = []
    for sdg in range(1, 18):
        if sdg_counts[sdg] > 3:
            relevant_sdgs.append({
                "sdg": sdg,
                "count": sdg_counts[sdg],
                "keywords": ", ".join(set(sdg_keywords_found[sdg]))  # Deduplicate keywords
            })

    # Sort by relevance (keyword count descending)
    relevant_sdgs.sort(key=lambda x: x["count"], reverse=True)

    # Find controversies
    controversies = []
    for keyword in CONTROVERSY_KEYWORDS:
        if re.search(rf'\b{keyword}\b', text, re.IGNORECASE):
            controversies.append(keyword)
            
    return relevant_sdgs, sdg_counts, controversies


def generate_wordcloud(text):
    """Generate word cloud from raw text"""
    try:
        wordcloud = WordCloud(
            width=800,
            height=400,
            background_color='white',
            collocations=False,
            colormap='viridis'
        ).generate(text)

        plt.figure(figsize=(10, 5))
        plt.imshow(wordcloud, interpolation='bilinear')
        plt.axis("off")
        return plt
    except Exception as e:
        st.error(f"Error generating word cloud: {str(e)}")
        return None


def plot_sdg_keyword_counts(sdg_counts):
    """Plot SDG keyword counts"""
    try:
        # Prepare data
        sdg_numbers = list(sdg_counts.keys())
        counts = [sdg_counts[sdg] for sdg in sdg_numbers]
        labels = [f"SDG {sdg}" for sdg in sdg_numbers]
        colors = [SDG_COLORS.get(sdg, '#1f77b4') for sdg in sdg_numbers]

        # Create horizontal bar chart
        fig = go.Figure(go.Bar(
            y=labels,
            x=counts,
            orientation='h',
            marker_color=colors,
            text=counts,
            textposition='auto'
        ))

        fig.update_layout(
            title="SDG Keyword Frequency",
            yaxis_title="Sustainable Development Goal",
            xaxis_title="Keyword Count",
            height=600,
            template='plotly_white'
        )
        return fig
    except:
        return None


# Enhanced Halal Analysis Display
def display_halal_analysis(company, ticker, status, reason, business_activities, financial_analysis, controversies):
    """Display detailed Halal analysis"""
    st.subheader(f"{company} ({ticker})" if ticker else company)
    
    # Status indicator with radial progress
    col1, col2, col3 = st.columns([1, 2, 3])
    with col1:
        st.markdown("### Halal Status")
        status_color = "#28a745" if status == "Halal" else "#dc3545"
        compliance_level = 85 if status == "Halal" else 25
        
        st.markdown(f"""
        <div class="halal-radial" style="background: conic-gradient({status_color} 0% {compliance_level}%, #e9ecef {compliance_level}% 100%);">
            <div class="radial-value">{compliance_level}%</div>
        </div>
        <div style="text-align:center; margin-top:10px; font-weight:bold; color:{status_color}">
            {status}
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("### Compliance Breakdown")
        st.markdown("**Business Activities**")
        st.markdown(f'<div class="progress-container"><div class="progress-bar" style="width:{compliance_level}%; background-color:{status_color}"></div></div>', unsafe_allow_html=True)
        
        st.markdown("**Financial Compliance**")
        st.markdown(f'<div class="progress-container"><div class="progress-bar" style="width:{compliance_level - 10}%; background-color:{status_color}"></div></div>', unsafe_allow_html=True)
        
        st.markdown("**Ethical Standards**")
        st.markdown(f'<div class="progress-container"><div class="progress-bar" style="width:{compliance_level + 5}%; background-color:{status_color}"></div></div>', unsafe_allow_html=True)
    
    # Detailed analysis
    with st.expander("Detailed Halal Analysis", expanded=True):
        st.markdown("### Business Activities")
        st.info(business_activities)
        
        st.markdown("### Financial Compliance")
        st.info(financial_analysis)
        
        st.markdown("### Compliance Reasoning")
        st.info(reason)
        
        if controversies and controversies.lower() != "none known":
            st.markdown("### Controversies & Concerns")
            with st.container():
                st.markdown('<div class="error-card">', unsafe_allow_html=True)
                st.error(controversies)
                st.markdown('</div>', unsafe_allow_html=True)


# Display SDG results from Grok API
def display_sdg_grok_results(company, ticker, grok_data):
    """Display SDG analysis from Grok API results"""
    st.subheader("SDG Analysis")
    
    if grok_data.get('sdg_goal', 0) != 0:
        goal = grok_data['sdg_goal']
        title = SDG_TITLES.get(goal, f"SDG {goal}")
        description = SDG_DESCRIPTIONS.get(goal, "")
        color = SDG_COLORS.get(goal, "#1f77b4")
        
        with st.container():
            st.markdown(
                f'<div class="sdg-card" style="border-left: 5px solid {color};">',
                unsafe_allow_html=True)
            st.markdown(f"### SDG {goal}: {title}")
            st.markdown(f"**Description:** {description}")
            
            # Impact analysis
            impact = grok_data.get('sdg_impact', '')
            if impact:
                st.markdown("**Impact Analysis:**")
                st.info(impact)
            
            # Keywords
            keywords = grok_data.get('sdg_keywords', '')
            if keywords:
                st.markdown("**Keywords:**")
                keywords_list = keywords.split(",")
                for kw in keywords_list:
                    st.markdown(f'<span class="keyword-badge">{kw.strip()}</span>', unsafe_allow_html=True)
            
            # Secondary SDGs
            secondary_sdgs = grok_data.get('secondary_sdgs', '')
            if secondary_sdgs:
                st.markdown("**Secondary SDGs:**")
                secondary_list = [s.strip() for s in secondary_sdgs.split(",") if s.strip().isdigit()]
                st.markdown('<div class="sdg-grid">', unsafe_allow_html=True)
                for sdg in secondary_list:
                    sdg_num = int(sdg)
                    st.markdown(
                        f'<div class="sdg-grid-item" style="background-color:{SDG_COLORS.get(sdg_num, "#1f77b4")}">'
                        f'SDG {sdg_num}<br>{SDG_TITLES.get(sdg_num, "")}'
                        f'</div>', 
                        unsafe_allow_html=True
                    )
                st.markdown('</div>', unsafe_allow_html=True)
                
            st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.info("No SDG data available")


# In app.py main function
def main():
    halal_df, sdg_df = load_data()
    ticker_map = create_ticker_mapping(halal_df)

    st.sidebar.title("Navigation")
    page = st.sidebar.radio("Go to", ["Home", "Stock Analysis", "SDG Analysis",
                                      "SDG Comparison", "Halal Comparison"])

    if page == "Home":
        show_home(halal_df, sdg_df)
    elif page == "Stock Analysis":
        show_stock_analysis(halal_df, sdg_df)
    elif page == "SDG Analysis":
        show_sdg_analysis(halal_df, sdg_df)
    elif page == "SDG Comparison":
        show_sdg_comparison(halal_df, sdg_df)
    elif page == "Halal Comparison":
        show_halal_comparison(halal_df, sdg_df)


def show_home(halal_df, sdg_df):
    st.markdown('<div class="header">Ethical Stock Screening Platform</div>', unsafe_allow_html=True)
    st.markdown("""
    ### Analyze stocks based on Shariah compliance and UN Sustainable Development Goals
    This platform helps investors evaluate companies based on:
    - **Islamic Finance Principles**: Determine if a company meets Halal investment criteria
    - **Sustainable Development Goals**: Assess alignment with UN sustainability targets
    - **AI-Powered Analysis**: Get insights for companies not in our database
    """)

    # Featured SDG Goals
    st.subheader("Featured SDG Goals")
    featured_sdgs = [13, 7, 9]  # Climate Action, Clean Energy, Innovation

    cols = st.columns(3)
    for idx, goal in enumerate(featured_sdgs):
        with cols[idx]:
            # Check if column exists and DataFrame is not empty
            if not sdg_df.empty and 'Primary SDG' in sdg_df.columns:
                companies = sdg_df[sdg_df['Primary SDG'] == goal]['Company Name'].unique()
            else:
                companies = []

            with st.container():
                st.markdown(
                    f'<div class="sdg-card" style="border-left: 5px solid {SDG_COLORS.get(goal, "#1f77b4")};">',
                    unsafe_allow_html=True)
                st.markdown(f"### SDG {goal}: {SDG_TITLES[goal]}")
                st.markdown(f"<small>{SDG_DESCRIPTIONS[goal]}</small>", unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)

            # Show companies associated with this SDG
            with st.expander(f"Companies Focused on SDG {goal}"):
                if companies:
                    for company in companies:
                        st.markdown(f"- {company}")
                else:
                    st.info("No companies found for this SDG")


def show_stock_analysis(halal_df, sdg_df):
    st.markdown('<div class="header">Stock Analysis</div>', unsafe_allow_html=True)
    st.markdown("### Detailed analysis of individual stocks")

    # Search inputs
    col1, col2 = st.columns([3, 1])
    with col1:
        company_name = st.text_input("Enter Company Name", placeholder="e.g., Apple Inc.")
    with col2:
        ticker_symbol = st.text_input("Ticker Symbol", placeholder="e.g., AAPL").upper()

    # Search logic
    if not company_name and not ticker_symbol:
        st.info("Please enter a company name or ticker symbol to search")
        return

    # Find matching company with error handling
    try:
        company_match = find_company(halal_df, company_name, ticker_symbol)
    except Exception as e:
        st.error(f"Error searching database: {str(e)}")
        company_match = None

    # Handle company found in dataset
    if company_match is not None:
        # Extract data from the match
        company = company_match['Company Name']
        ticker = company_match['Ticker']
        status = company_match['Halal Status']
        reason = company_match['Halal Reason']
        sector = company_match['Sector']

        # Fetch detailed analysis from Grok API even if company is in database
        with st.spinner("Fetching detailed analysis..."):
            grok_data = get_grok_analysis(company, ticker)

        if grok_data:
            # Display enhanced Halal analysis with Grok data
            display_halal_analysis(
                company=company,
                ticker=ticker,
                status=status,
                reason=reason,
                business_activities=grok_data.get('business_activities', 'No information available'),
                financial_analysis=grok_data.get('financial_analysis', 'No information available'),
                controversies=grok_data.get('controversies', 'None known')
            )
            
            # Display enhanced SDG analysis
            st.markdown("---")
            display_sdg_grok_results(company, ticker, grok_data)
            
            # Save to Excel
            if save_to_halal_excel(company, ticker, grok_data) and \
                    save_to_sdg_excel(company, ticker, grok_data):
                st.success("Company data saved to database for future reference")
        else:
            # Display basic Halal analysis from database
            display_halal_analysis(
                company=company,
                ticker=ticker,
                status=status,
                reason=reason,
                business_activities="Business activities information not available",
                financial_analysis="Financial compliance details not available",
                controversies="No known controversies"
            )
            
            # Display SDG data if available
            st.markdown("---")
            st.subheader("SDG Analysis")
            if not sdg_df.empty and 'Company Name' in sdg_df.columns and 'Primary SDG' in sdg_df.columns:
                sdg_data = sdg_df[sdg_df['Company Name'].str.strip().str.lower() == company.strip().lower()]
                if not sdg_data.empty:
                    goal = sdg_data['Primary SDG'].iloc[0]
                    keywords = sdg_data['SDG Keywords'].iloc[0]

                    with st.container():
                        st.markdown(
                            f'<div class="sdg-card" style="border-left: 5px solid {SDG_COLORS.get(goal, "#1f77b4")};">',
                            unsafe_allow_html=True)
                        st.markdown(f"### SDG {goal}: {SDG_TITLES.get(goal, '')}")
                        st.markdown(f"**Description:** {SDG_DESCRIPTIONS.get(goal, '')}")
                        
                        if keywords:
                            st.markdown("**Keywords:**")
                            keywords_list = keywords.split(",")
                            for kw in keywords_list:
                                st.markdown(f'<span class="keyword-badge">{kw.strip()}</span>', unsafe_allow_html=True)
                                
                        st.markdown('</div>', unsafe_allow_html=True)
                else:
                    st.info("No SDG data available")
            else:
                st.info("SDG data not available")

        # Financial metrics and chart
        st.markdown("---")
        st.subheader("Financial Performance")
        
        stock_data = get_stock_data(ticker)
        if isinstance(stock_data, dict):
            col1, col2, col3 = st.columns(3)
            with col1:
                st.markdown('<div class="metric-card">', unsafe_allow_html=True)
                st.markdown(f'<div class="metric-value">${stock_data["current_price"]:.2f}</div>',
                            unsafe_allow_html=True)
                st.markdown('<div class="metric-label">Current Price</div>', unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)
                
            with col2:
                st.markdown('<div class="metric-card">', unsafe_allow_html=True)
                st.markdown(f'<div class="metric-value">${stock_data["52_week_high"]:.2f}</div>',
                            unsafe_allow_html=True)
                st.markdown('<div class="metric-label">52-Week High</div>', unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)
                
            with col3:
                st.markdown('<div class="metric-card">', unsafe_allow_html=True)
                st.markdown(f'<div class="metric-value">${stock_data["52_week_low"]:.2f}</div>',
                            unsafe_allow_html=True)
                st.markdown('<div class="metric-label">52-Week Low</div>', unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)
        else:
            st.warning("Could not retrieve stock data")
            
        price_chart = plot_stock_history(ticker)
        if price_chart:
            st.plotly_chart(price_chart, use_container_width=True)
        else:
            st.warning("Could not load stock chart")

    # Handle company not found in dataset
    else:
        if not company_name and ticker_symbol:
            company_name = ticker_symbol  # Use ticker as company name if none provided

        # Get analysis from Grok API
        with st.spinner("Analyzing company with AI..."):
            grok_data = get_grok_analysis(company_name, ticker_symbol)

        if grok_data:
            # Display enhanced Halal analysis
            display_halal_analysis(
                company=company_name,
                ticker=ticker_symbol,
                status=grok_data.get('halal_status', 'Unknown'),
                reason=grok_data.get('detailed_reason', 'No reason provided'),
                business_activities=grok_data.get('business_activities', 'No information available'),
                financial_analysis=grok_data.get('financial_analysis', 'No information available'),
                controversies=grok_data.get('controversies', 'None known')
            )
            
            # Display enhanced SDG analysis
            st.markdown("---")
            display_sdg_grok_results(company_name, ticker_symbol, grok_data)

            # Save to Excel
            if ticker_symbol:
                if save_to_halal_excel(company_name, ticker_symbol, grok_data) and \
                        save_to_sdg_excel(company_name, ticker_symbol, grok_data):
                    st.success("Company data saved to database for future reference")
        else:
            st.error("Failed to get AI analysis. Please try a different company.")


# SDG Analysis Page with PDF Analysis
def show_sdg_analysis(halal_df, sdg_df):
    st.markdown('<div class="header">SDG Analysis</div>', unsafe_allow_html=True)
    st.markdown("### Analyze company alignment with Sustainable Development Goals")

    # Search inputs
    col1, col2 = st.columns([3, 1])
    with col1:
        company_name = st.text_input("Search Company", placeholder="e.g., Microsoft", key="sdg_search")
    with col2:
        ticker_symbol = st.text_input("Ticker", placeholder="e.g., MSFT", key="sdg_ticker").upper()

    if st.button("Analyze Company", key="sdg_analyze_btn"):
        if not company_name and not ticker_symbol:
            st.info("Please enter a company name or ticker to search")
        else:
            # Find company
            company_match = find_company(halal_df, company_name, ticker_symbol)

            if company_match is not None:
                # Extract data from the match
                company = company_match['Company Name']
                ticker = company_match['Ticker']
                status = company_match['Halal Status']
                reason = company_match['Halal Reason']

                # Fetch detailed analysis from Grok API even if company is in database
                with st.spinner("Fetching detailed analysis..."):
                    grok_data = get_grok_analysis(company, ticker)

                if grok_data:
                    # Display enhanced SDG analysis
                    display_sdg_grok_results(company, ticker, grok_data)
                    
                    # Save to Excel
                    if save_to_halal_excel(company, ticker, grok_data) and \
                            save_to_sdg_excel(company, ticker, grok_data):
                        st.success("Company data saved to database for future reference")
                else:
                    # Show SDG data for found company
                    st.subheader(f"{company} ({ticker})")
                    
                    # Get SDG data
                    if not sdg_df.empty and 'Company Name' in sdg_df.columns and 'Primary SDG' in sdg_df.columns:
                        sdg_data = sdg_df[sdg_df['Company Name'].str.strip().str.lower() == company.strip().lower()]
                        if not sdg_data.empty:
                            goal = sdg_data['Primary SDG'].iloc[0]
                            keywords = sdg_data['SDG Keywords'].iloc[0]

                            with st.container():
                                st.markdown(
                                    f'<div class="sdg-card" style="border-left: 5px solid {SDG_COLORS.get(goal, "#1f77b4")};">',
                                    unsafe_allow_html=True)
                                st.markdown(f"### SDG {goal}: {SDG_TITLES.get(goal, '')}")
                                st.markdown(f"**Description:** {SDG_DESCRIPTIONS.get(goal, '')}")
                                
                                if keywords:
                                    st.markdown("**Keywords:**")
                                    keywords_list = keywords.split(",")
                                    for kw in keywords_list:
                                        st.markdown(f'<span class="keyword-badge">{kw.strip()}</span>', unsafe_allow_html=True)
                                        
                                st.markdown('</div>', unsafe_allow_html=True)
                        else:
                            st.info("No SDG data available for this company")
                    else:
                        st.info("SDG data not available")
            else:
                if not company_name and ticker_symbol:
                    company_name = ticker_symbol

                with st.spinner("Analyzing with AI..."):
                    grok_data = get_grok_analysis(company_name, ticker_symbol)

                if grok_data:
                    display_sdg_grok_results(company_name, ticker_symbol, grok_data)

                    # Save to Excel
                    if ticker_symbol:
                        if save_to_halal_excel(company_name, ticker_symbol, grok_data) and \
                                save_to_sdg_excel(company_name, ticker_symbol, grok_data):
                            st.success("Company data saved to database for future reference")
                else:
                    st.error("AI analysis failed")

    # PDF Analysis Section
    st.markdown("---")
    st.subheader("PDF Document Analysis")
    st.markdown("Upload a PDF document to analyze its alignment with Sustainable Development Goals")

    uploaded_file = st.file_uploader("Choose a PDF file", type="pdf", key="pdf_uploader")

    if uploaded_file is not None:
        # Display file details
        file_details = {"FileName": uploaded_file.name, "FileType": uploaded_file.type, "FileSize": uploaded_file.size}
        st.write(file_details)

        # Extract text
        with st.spinner("Extracting text from PDF..."):
            text = extract_text_from_pdf(uploaded_file)

        # Analyze text in one go
        with st.spinner("Analyzing text for SDG alignment..."):
            relevant_sdgs, sdg_counts, controversies = analyze_text_for_sdg(text)

        if relevant_sdgs:
            st.success(f"Identified {len(relevant_sdgs)} relevant SDGs in the document")
            
            # Display controversies if found
            if controversies:
                st.subheader("Controversies Detected")
                with st.container():
                    st.markdown('<div class="error-card">', unsafe_allow_html=True)
                    st.error("The document contains content related to potential controversies:")
                    for word in controversies:
                        st.markdown(f'<span class="controversy-tag">{word}</span>', unsafe_allow_html=True)
                    st.markdown('</div>', unsafe_allow_html=True)

            # Display all relevant SDGs
            st.subheader("SDG Alignment Analysis")
            for sdg_info in relevant_sdgs:
                sdg = sdg_info["sdg"]
                keywords = sdg_info["keywords"]
                count = sdg_info["count"]

                with st.expander(f"SDG {sdg}: {SDG_TITLES.get(sdg, '')} - {count} keywords found", expanded=True):
                    with st.container():
                        st.markdown(
                            f'<div class="sdg-card" style="border-left: 5px solid {SDG_COLORS.get(sdg, "#1f77b4")};">',
                            unsafe_allow_html=True)
                        st.markdown(f"**Description:** {SDG_DESCRIPTIONS.get(sdg, '')}")
                        st.markdown(f"**Keyword Count:** {count}")
                        st.markdown(f"**Keywords Found:**")
                        keywords_list = keywords.split(", ")
                        for kw in keywords_list:
                            st.markdown(f'<span class="keyword-badge">{kw.strip()}</span>', unsafe_allow_html=True)
                        st.markdown('</div>', unsafe_allow_html=True)

            # Visualizations
            st.markdown("---")
            st.subheader("Document Analysis Visualizations")

            # Word Cloud
            with st.spinner("Generating word cloud..."):
                wordcloud_fig = generate_wordcloud(text)
                if wordcloud_fig:
                    st.pyplot(wordcloud_fig)
                else:
                    st.warning("Could not generate word cloud")

            # SDG Keyword Counts
            with st.spinner("Creating SDG analysis..."):
                sdg_chart = plot_sdg_keyword_counts(sdg_counts)
                if sdg_chart:
                    st.plotly_chart(sdg_chart, use_container_width=True)
                else:
                    st.info("No SDG keywords found to visualize")
        else:
            st.info("No SDG alignment detected in the document")


# Enhanced SDG Comparison Display
def display_sdg_comparison_card(company_data, title):
    """Display SDG comparison card with enhanced visuals"""
    with st.container():
        st.markdown(f"<h3>{title}</h3>", unsafe_allow_html=True)
        st.markdown(f"<h4>{company_data['name']}</h4>", unsafe_allow_html=True)
        
        if company_data['ticker']:
            st.caption(f"Ticker: {company_data['ticker']}")
            
        if company_data['sdg_goal'] != 0:
            # Main SDG card
            with st.container():
                st.markdown(
                    f'<div class="sdg-card" style="border-left: 5px solid {SDG_COLORS.get(company_data["sdg_goal"], "#1f77b4")};">',
                    unsafe_allow_html=True)
                st.markdown(f"### SDG {company_data['sdg_goal']}: {SDG_TITLES.get(company_data['sdg_goal'], '')}")
                st.markdown(f"**Description:** {SDG_DESCRIPTIONS.get(company_data['sdg_goal'], '')}")
                
                if company_data.get('sdg_impact', ''):
                    st.markdown("**Impact Analysis:**")
                    st.info(f"{company_data['sdg_impact']}")
                    
                if company_data.get('sdg_keywords', ''):
                    st.markdown("**Keywords:**")
                    keywords = company_data['sdg_keywords'].split(",")
                    for kw in keywords:
                        st.markdown(f'<span class="keyword-badge">{kw.strip()}</span>', unsafe_allow_html=True)
                        
                st.markdown('</div>', unsafe_allow_html=True)

            # Secondary SDGs grid
            if company_data.get('secondary_sdgs', ''):
                st.subheader("Secondary SDGs")
                secondary_list = [int(s.strip()) for s in company_data['secondary_sdgs'].split(",") if s.strip().isdigit()]
                
                st.markdown('<div class="sdg-grid">', unsafe_allow_html=True)
                for sdg in secondary_list:
                    st.markdown(
                        f'<div class="sdg-grid-item" style="background-color:{SDG_COLORS.get(sdg)}">'
                        f'SDG {sdg}<br>{SDG_TITLES.get(sdg)}'
                        f'</div>', 
                        unsafe_allow_html=True
                    )
                st.markdown('</div>', unsafe_allow_html=True)
                
        else:
            st.info("No SDG data available")
            
        if company_data.get('controversies', '') and company_data['controversies'].lower() != "none known":
            st.markdown("**Controversies:**")
            with st.container():
                st.markdown('<div class="error-card">', unsafe_allow_html=True)
                st.error(company_data['controversies'])
                st.markdown('</div>', unsafe_allow_html=True)


# Enhanced Halal Comparison Display
def display_halal_comparison_card(company_data, title):
    """Display Halal comparison card with enhanced visuals"""
    status = company_data['halal_status']
    status_color = "#28a745" if status == "Halal" else "#dc3545"
    if status == 'Unknown':
        status_color = "#6c757d"
        compliance_level = 50
    else:
        compliance_level = 85 if status == "Halal" else 25

    with st.container():
        st.markdown(f"<h3>{title}</h3>", unsafe_allow_html=True)
        st.markdown(f"<h4>{company_data['name']}</h4>", unsafe_allow_html=True)

        col1, col2 = st.columns([1, 2])
        with col1:
            # Radial chart
            st.markdown(f"""
            <div class="halal-radial" style="background: conic-gradient({status_color} 0% {compliance_level}%, #e9ecef {compliance_level}% 100%);">
                <div class="radial-value">{compliance_level}%</div>
            </div>
            <div style="text-align:center; margin-top:10px; font-weight:bold; color:{status_color}">
                {status}
            </div>
            """, unsafe_allow_html=True)

        with col2:
            st.markdown(f"**Sector:** {company_data.get('sector', 'Unknown')}")
            if company_data['ticker']:
                st.markdown(f"**Ticker:** {company_data['ticker']}")

        # Business Activities
        with st.expander("Business Activities", expanded=False):
            st.info(company_data.get('business_activities', 'No information available'))

        # Financial Compliance
        with st.expander("Financial Compliance", expanded=False):
            st.info(company_data.get('financial_analysis', 'No information available'))
            
        # Compliance Reasoning
        with st.expander("Compliance Reasoning", expanded=False):
            st.info(company_data.get('reason', 'No reason provided'))

        # Controversies
        if company_data.get('controversies', '') and company_data['controversies'].lower() != "none known":
            with st.expander("Controversies", expanded=False):
                with st.container():
                    st.markdown('<div class="error-card">', unsafe_allow_html=True)
                    st.error(company_data['controversies'])
                    st.markdown('</div>', unsafe_allow_html=True)


# Helper function to get company data from DB or Grok
def get_company_data(halal_df, sdg_df, company_query):
    """Get company data from database or Grok API"""
    # First try to find in database
    company_match = find_company(halal_df, company_query, "")

    if company_match is not None:
        # Get data from database
        company = company_match['Company Name']
        ticker = company_match['Ticker']
        status = company_match['Halal Status']
        reason = company_match['Halal Reason']
        sector = company_match['Sector']

        # Get SDG data
        if not sdg_df.empty and 'Company Name' in sdg_df.columns and 'Primary SDG' in sdg_df.columns:
            sdg_data = sdg_df[sdg_df['Company Name'] == company]
            if not sdg_data.empty:
                sdg_goal = sdg_data['Primary SDG'].iloc[0]
                sdg_keywords = sdg_data['SDG Keywords'].iloc[0]
            else:
                sdg_goal = 0
                sdg_keywords = ""
        else:
            sdg_goal = 0
            sdg_keywords = ""

        return {
            "name": company,
            "ticker": ticker,
            "halal_status": status,
            "reason": reason,
            "sector": sector,
            "sdg_goal": sdg_goal,
            "sdg_keywords": sdg_keywords,
            "business_activities": "Not available from database",
            "financial_analysis": "Not available from database",
            "controversies": "",
            "secondary_sdgs": "",
            "sdg_impact": ""
        }
    else:
        # Use Grok API
        with st.spinner(f"Getting AI analysis for {company_query}..."):
            grok_data = get_grok_analysis(company_query, "")

        if grok_data:
            return {
                "name": company_query,
                "ticker": "",
                "halal_status": grok_data.get('halal_status', 'Unknown'),
                "reason": grok_data.get('detailed_reason', 'No reason provided'),
                "sector": grok_data.get('sector', 'Unknown'),
                "sdg_goal": grok_data.get('sdg_goal', 0),
                "secondary_sdgs": grok_data.get('secondary_sdgs', ''),
                "sdg_keywords": grok_data.get('sdg_keywords', ''),
                "business_activities": grok_data.get('business_activities', 'No information available'),
                "financial_analysis": grok_data.get('financial_analysis', 'No information available'),
                "sdg_impact": grok_data.get('sdg_impact', ''),
                "controversies": grok_data.get('controversies', 'None known')
            }
        else:
            return None


# Enhanced Halal Comparison Page
def show_halal_comparison(halal_df, sdg_df):
    st.markdown('<div class="header">Halal Comparison</div>', unsafe_allow_html=True)
    st.markdown("### Compare two companies by their Halal compliance status")

    col1, col2 = st.columns(2)
    with col1:
        company1 = st.text_input("Company 1", placeholder="Enter company name or ticker", key="halal1")
    with col2:
        company2 = st.text_input("Company 2", placeholder="Enter company name or ticker", key="halal2")

    if st.button("Compare Companies", key="halal_compare_btn"):
        if not company1 or not company2:
            st.info("Please enter two companies to compare")
        else:
            # Get company data with AI enhancements
            company1_data = get_company_data(halal_df, sdg_df, company1)
            company2_data = get_company_data(halal_df, sdg_df, company2)

            if not company1_data or not company2_data:
                st.error("Could not get data for one or both companies")
                return

            # For companies in database, get AI details
            def enhance_with_ai(company_data):
                # Skip if already has AI details
                if "Not available from database" not in company_data.get('business_activities', ''):
                    return company_data
                    
                # Get AI analysis
                with st.spinner(f"Getting AI details for {company_data['name']}..."):
                    grok_data = get_grok_analysis(company_data['name'], company_data['ticker'])

                if grok_data:
                    # Merge AI data with existing data
                    return {
                        **company_data,
                        "business_activities": grok_data.get('business_activities', 'No information available'),
                        "financial_analysis": grok_data.get('financial_analysis', 'No information available'),
                        "controversies": grok_data.get('controversies', 'None known'),
                        "sdg_goal": grok_data.get('sdg_goal', 0),
                        "secondary_sdgs": grok_data.get('secondary_sdgs', ''),
                        "sdg_keywords": grok_data.get('sdg_keywords', ''),
                        "sdg_impact": grok_data.get('sdg_impact', '')
                    }
                return company_data

            # Enhance both companies with AI details
            company1_data = enhance_with_ai(company1_data)
            company2_data = enhance_with_ai(company2_data)

            # Display comparison
            st.markdown('<div class="comparison-container">', unsafe_allow_html=True)
            
            col1, col2 = st.columns(2)
            with col1:
                display_halal_comparison_card(company1_data, "Company 1")
            with col2:
                display_halal_comparison_card(company2_data, "Company 2")
                
            st.markdown('</div>', unsafe_allow_html=True)
            
            # Compliance comparison visualization
            st.subheader("Compliance Comparison")
            
            # Prepare data
            compliance_level1 = 85 if company1_data['halal_status'] == "Halal" else 25
            compliance_level2 = 85 if company2_data['halal_status'] == "Halal" else 25
            
            # Create gauge charts
            fig = go.Figure()
            
            fig.add_trace(go.Indicator(
                mode = "gauge+number",
                value = compliance_level1,
                title = {'text': company1_data['name']},
                domain = {'x': [0, 0.45], 'y': [0, 1]},
                gauge = {
                    'axis': {'range': [0, 100]},
                    'bar': {'color': "#1f77b4"},
                    'steps' : [
                        {'range': [0, 33], 'color': "#dc3545"},
                        {'range': [33, 66], 'color': "#ffc107"},
                        {'range': [66, 100], 'color': "#28a745"}
                    ]
                }
            ))
            
            fig.add_trace(go.Indicator(
                mode = "gauge+number",
                value = compliance_level2,
                title = {'text': company2_data['name']},
                domain = {'x': [0.55, 1], 'y': [0, 1]},
                gauge = {
                    'axis': {'range': [0, 100]},
                    'bar': {'color': "#ff7f0e"},
                    'steps' : [
                        {'range': [0, 33], 'color': "#dc3545"},
                        {'range': [33, 66], 'color': "#ffc107"},
                        {'range': [66, 100], 'color': "#28a745"}
                    ]
                }
            ))
            
            fig.update_layout(
                title="Halal Compliance Level",
                height=400
            )
            
            st.plotly_chart(fig, use_container_width=True)


# Enhanced SDG Comparison Page
def show_sdg_comparison(halal_df, sdg_df):
    st.markdown('<div class="header">SDG Comparison</div>', unsafe_allow_html=True)
    st.markdown("### Compare two companies by their Sustainable Development Goals alignment")

    col1, col2 = st.columns(2)
    with col1:
        company1 = st.text_input("Company 1", placeholder="Enter company name or ticker", key="sdg1")
    with col2:
        company2 = st.text_input("Company 2", placeholder="Enter company name or ticker", key="sdg2")

    if st.button("Compare Companies", key="sdg_compare_btn"):
        if not company1 or not company2:
            st.info("Please enter two companies to compare")
        else:
            # Get company data
            company1_data = get_company_data(halal_df, sdg_df, company1)
            company2_data = get_company_data(halal_df, sdg_df, company2)

            if not company1_data or not company2_data:
                st.error("Could not get data for one or both companies")
                return

            # Display comparison
            st.markdown('<div class="comparison-container">', unsafe_allow_html=True)
            
            col1, col2 = st.columns(2)
            with col1:
                display_sdg_comparison_card(company1_data, "Company 1")
            with col2:
                display_sdg_comparison_card(company2_data, "Company 2")
                
            st.markdown('</div>', unsafe_allow_html=True)
            
            # Comparison visualization
            st.subheader("SDG Alignment Comparison")
            
            if company1_data['sdg_goal'] != 0 or company2_data['sdg_goal'] != 0:
                # Prepare data for visualization
                data = {
                    "SDG": [],
                    "Company": [],
                    "Value": []
                }
                
                # Add primary SDG
                if company1_data['sdg_goal'] != 0:
                    data["SDG"].append(f"SDG {company1_data['sdg_goal']}")
                    data["Company"].append(company1_data['name'])
                    data["Value"].append(10)  # Higher value for primary
                    
                if company2_data['sdg_goal'] != 0:
                    data["SDG"].append(f"SDG {company2_data['sdg_goal']}")
                    data["Company"].append(company2_data['name'])
                    data["Value"].append(10)
                    
                # Add secondary SDGs
                if company1_data.get('secondary_sdgs', ''):
                    secondary_list = [int(s.strip()) for s in company1_data['secondary_sdgs'].split(",") if s.strip().isdigit()]
                    for sdg in secondary_list:
                        data["SDG"].append(f"SDG {sdg}")
                        data["Company"].append(company1_data['name'])
                        data["Value"].append(5)  # Lower value for secondary
                        
                if company2_data.get('secondary_sdgs', ''):
                    secondary_list = [int(s.strip()) for s in company2_data['secondary_sdgs'].split(",") if s.strip().isdigit()]
                    for sdg in secondary_list:
                        data["SDG"].append(f"SDG {sdg}")
                        data["Company"].append(company2_data['name'])
                        data["Value"].append(5)
                
                df = pd.DataFrame(data)
                
                if not df.empty:
                    fig = px.bar(
                        df, 
                        x="SDG", 
                        y="Value", 
                        color="Company", 
                        barmode="group",
                        color_discrete_sequence=["#1f77b4", "#ff7f0e"],
                        title="SDG Alignment Comparison"
                    )
                    fig.update_layout(
                        xaxis_title="Sustainable Development Goals",
                        yaxis_title="Alignment Level",
                        template="plotly_white"
                    )
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("No SDG data available for visualization")
            else:
                st.info("No SDG data available for comparison")


# Main entry point
if __name__ == "__main__":
    main()