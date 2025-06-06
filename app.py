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
from dotenv import load_dotenv  # Added for environment variables

# Load environment variables
load_dotenv()

# Configure page
st.set_page_config(layout="wide", page_title="Ethical Stock Screener", page_icon="📈")

# Custom CSS for styling
st.markdown("""
<style>
    .header {
        font-size: 36px !important;
        font-weight: bold !important;
        color: #1f77b4 !important;
        text-align: center;
        margin-bottom: 25px;
    }
    .subheader {
        font-size: 24px !important;
        font-weight: bold !important;
        color: #2ca02c !important;
        border-bottom: 2px solid #2ca02c;
        padding-bottom: 10px;
        margin-top: 20px;
    }
    .card {
        background-color: #f8f9fa;
        border-radius: 10px;
        padding: 20px;
        margin-bottom: 20px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .success-card {
        background-color: #d4edda;
        border-left: 5px solid #28a745;
    }
    .warning-card {
        background-color: #fff3cd;
        border-left: 5px solid #ffc107;
    }
    .error-card {
        background-color: #f8d7da;
        border-left: 5px solid #dc3545;
    }
    .info-card {
        background-color: #d1ecf1;
        border-left: 5px solid #17a2b8;
    }
    .sdg-card {
        background-color: #e8f4f8;
        border-radius: 10px;
        padding: 15px;
        margin: 10px 0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
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
    }
    .stButton>button:hover {
        background: linear-gradient(135deg, #2575fc 0%, #6a11cb 100%);
        color: white;
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


# Load data from Excel files
def load_data():
    try:
        # Load Halal data
        halal_df = pd.read_excel('data/halal_checker.xlsx', sheet_name=0, engine='openpyxl')
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
        sdg_df = pd.read_excel('data/sdg_checker.xlsx', sheet_name=0, engine='openpyxl')
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
        # Get API key from environment variables
        api_key = os.getenv("GROK_API_KEY")
        if not api_key:
            st.error("GROK_API_KEY environment variable not set")
            return None

        # API endpoint and headers
        api_endpoint = "https://api.groq.com/openai/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

        # Create the prompt
        prompt = f"""
        You are an expert in Islamic finance and sustainable development goals (SDGs). 
        Please analyze the company {company_name} ({ticker}) and provide:

        1. Halal status: [Halal or Not Halal]
        2. Reason for Halal status: [brief reason]
        3. Primary SDG goal: [number between 1 and 17, or 0 if none]
        4. SDG keywords: [comma separated keywords]
        5. Sector: [sector of the company]

        Output in JSON format only:
        {{
            "halal_status": "Halal",
            "reason": "The company operates in the technology sector...",
            "sdg_goal": 9,
            "sdg_keywords": "innovation, technology, digital transformation",
            "sector": "Technology"
        }}
        """

        # Create the payload with UPDATED MODEL
        payload = {
            "model": "llama3-70b-8192",  # CORRECTED MODEL NAME
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.3,
            "max_tokens": 500
        }

        # Make the API request
        response = requests.post(api_endpoint, headers=headers, json=payload, timeout=30)

        if response.status_code == 200:
            # Extract the JSON content from the response
            response_data = response.json()
            content = response_data['choices'][0]['message']['content']

            # Extract JSON from the response string
            try:
                # Find JSON part in the response
                json_start = content.find('{')
                json_end = content.rfind('}') + 1
                json_str = content[json_start:json_end]

                # Parse the JSON
                return json.loads(json_str)
            except json.JSONDecodeError:
                st.error("Error parsing Grok response")
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
            'Reason': grok_data.get('reason', '')
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
        if sdg_counts[sdg] > 0:
            relevant_sdgs.append({
                "sdg": sdg,
                "count": sdg_counts[sdg],
                "keywords": ", ".join(set(sdg_keywords_found[sdg]))  # Deduplicate keywords
            })

    # Sort by relevance (keyword count descending)
    relevant_sdgs.sort(key=lambda x: x["count"], reverse=True)

    return relevant_sdgs, sdg_counts


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

        # Create bar chart
        fig = go.Figure(go.Bar(
            x=sdg_numbers,
            y=counts,
            text=counts,
            textposition='auto',
            marker_color=colors
        ))

        fig.update_layout(
            title="SDG Keyword Frequency",
            xaxis_title="Sustainable Development Goal",
            yaxis_title="Keyword Count",
            xaxis=dict(
                tickmode='array',
                tickvals=sdg_numbers,
                ticktext=labels
            ),
            height=500,
            template='plotly_white'
        )
        return fig
    except:
        return None


def display_sdg_grok_results(company, ticker, grok_data):
    """Display SDG-specific results from Grok API"""
    st.subheader(f"{company} ({ticker})" if ticker else company)

    with st.container():
        st.markdown('<div class="warning-card">', unsafe_allow_html=True)
        st.warning("This SDG analysis is AI-generated and may not be 100% accurate")
        st.markdown('</div>', unsafe_allow_html=True)

    # SDG Analysis
    sdg_goal = grok_data.get('sdg_goal', 0)
    sdg_keywords = grok_data.get('sdg_keywords', '')

    if sdg_goal and sdg_goal != 0:
        st.markdown(f"**Primary SDG: {sdg_goal} - {SDG_TITLES.get(sdg_goal, '')}**")

        with st.container():
            st.markdown(f'<div class="sdg-card" style="border-left: 5px solid {SDG_COLORS.get(sdg_goal, "#1f77b4")};">',
                        unsafe_allow_html=True)
            st.markdown(f"**Description:** {SDG_DESCRIPTIONS.get(sdg_goal, '')}")
            if sdg_keywords:
                st.markdown("**Related Keywords:**")
                st.info(f"{sdg_keywords}")
            st.markdown('</div>', unsafe_allow_html=True)
    else:
        with st.container():
            st.markdown('<div class="warning-card">', unsafe_allow_html=True)
            st.warning("No SDG analysis available for this company")
            st.markdown('</div>', unsafe_allow_html=True)

    # Disclaimer
    st.markdown("---")
    st.caption("ℹ️ This analysis was generated using AI and may contain inaccuracies.")


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

            if company_match is None:
                if not company_name and ticker_symbol:
                    company_name = ticker_symbol

                with st.container():
                    st.markdown('<div class="info-card">', unsafe_allow_html=True)
                    st.warning("Company not found in database. Using AI analysis...")
                    st.markdown('</div>', unsafe_allow_html=True)

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
            else:
                # Show SDG data for found company
                company = company_match['Company Name']
                ticker = company_match['Ticker']

                st.subheader(f"{company} ({ticker})")

                # Get SDG data
                sdg_data = sdg_df[sdg_df['Company Name'].str.strip().str.lower() == company.strip().lower()]
                if not sdg_data.empty:
                    goal = sdg_data['Primary SDG'].iloc[0]
                    keywords = sdg_data['SDG Keywords'].iloc[0]

                    col1, col2 = st.columns([1, 3])
                    with col1:
                        st.markdown(f"**Primary SDG**")
                        with st.container():
                            st.markdown(
                                f'<div class="sdg-card" style="border-left: 5px solid {SDG_COLORS.get(goal, "#1f77b4")};">',
                                unsafe_allow_html=True)
                            st.markdown(f"<h3>SDG {goal}</h3>", unsafe_allow_html=True)
                            st.markdown(f"<p><strong>{SDG_TITLES[goal]}</strong></p>", unsafe_allow_html=True)
                            st.markdown(f"<p><small>{SDG_DESCRIPTIONS[goal]}</small></p>", unsafe_allow_html=True)
                            st.markdown('</div>', unsafe_allow_html=True)

                    with col2:
                        st.markdown("**Keywords**")
                        with st.container():
                            st.markdown(f'<div class="sdg-card">', unsafe_allow_html=True)
                            st.markdown(f"{keywords}")
                            st.markdown('</div>', unsafe_allow_html=True)
                else:
                    with st.container():
                        st.markdown('<div class="warning-card">', unsafe_allow_html=True)
                        st.warning("No SDG data available for this company")
                        st.markdown('</div>', unsafe_allow_html=True)

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
            relevant_sdgs, sdg_counts = analyze_text_for_sdg(text)

        if relevant_sdgs:
            st.success(f"Identified {len(relevant_sdgs)} relevant SDGs in the document")

            # Display all relevant SDGs
            for sdg_info in relevant_sdgs:
                sdg = sdg_info["sdg"]
                keywords = sdg_info["keywords"]

                with st.container():
                    st.markdown(
                        f'<div class="sdg-card" style="border-left: 5px solid {SDG_COLORS.get(sdg, "#1f77b4")};">',
                        unsafe_allow_html=True)
                    st.markdown(f"### SDG {sdg}: {SDG_TITLES[sdg]}")
                    st.markdown(f"**Description:** {SDG_DESCRIPTIONS[sdg]}")
                    st.markdown(f"**Keyword Count:** {sdg_info['count']}")
                    st.markdown(f"**Keywords Found:** {keywords}")
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
            with st.container():
                st.markdown('<div class="warning-card">', unsafe_allow_html=True)
                st.warning("No SDG alignment detected in the document")
                st.markdown('</div>', unsafe_allow_html=True)


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
                    f'<div class="sdg-card" style="border-left: 5px solid {SDG_COLORS.get(goal, "#1f77b4")};">'
                    f'<h4>SDG {goal}: {SDG_TITLES[goal]}</h4>'
                    f'<p><small>{SDG_DESCRIPTIONS[goal]}</small></p>'
                    f'</div>', unsafe_allow_html=True)

            # Show companies associated with this SDG
            with st.expander(f"Companies Focused on SDG {goal}"):
                for company in companies:
                    st.markdown(f"- {company}")

    # Database Insights
    st.subheader("Database Insights")

    col1, col2 = st.columns(2)

    with col1:
        # SDG Distribution - only if column exists and data is available
        if not sdg_df.empty and 'Primary SDG' in sdg_df.columns:
            st.markdown("**SDG Distribution**")
            sdg_counts = sdg_df['Primary SDG'].value_counts().reset_index()
            sdg_counts.columns = ['SDG', 'Count']
            sdg_counts['Color'] = sdg_counts['SDG'].apply(lambda x: SDG_COLORS.get(x, '#1f77b4'))

            fig = px.bar(sdg_counts, x='SDG', y='Count', color='SDG',
                         color_discrete_map=SDG_COLORS,
                         labels={'SDG': 'Sustainable Development Goal', 'Count': 'Number of Companies'})
            fig.update_layout(showlegend=False, height=400)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No SDG data available")

    with col2:
        # Halal Status Distribution
        if not halal_df.empty and 'Halal Status' in halal_df.columns:
            st.markdown("**Halal Status Distribution**")
            halal_counts = halal_df['Halal Status'].value_counts().reset_index()
            halal_counts.columns = ['Status', 'Count']

            fig = px.pie(halal_counts, values='Count', names='Status',
                         color='Status',
                         color_discrete_map={'Halal': '#28a745', 'Not Halal': '#dc3545'},
                         hole=0.3)
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No Halal data available")


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

    # Handle company not found in dataset
    if company_match is None:
        if not company_name and ticker_symbol:
            company_name = ticker_symbol  # Use ticker as company name if none provided

        with st.container():
            st.markdown('<div class="info-card">', unsafe_allow_html=True)
            st.warning("Company not found in our database. Using AI analysis...")
            st.markdown('</div>', unsafe_allow_html=True)

        # Get analysis from Grok API
        with st.spinner("Analyzing company with AI..."):
            grok_data = get_grok_analysis(company_name, ticker_symbol)

        if grok_data:
            display_grok_results(company_name, ticker_symbol, grok_data)

            # Save to Excel
            if ticker_symbol:
                if save_to_halal_excel(company_name, ticker_symbol, grok_data) and \
                        save_to_sdg_excel(company_name, ticker_symbol, grok_data):
                    st.success("Company data saved to database for future reference")
        else:
            st.error("Failed to get AI analysis. Please try a different company.")
        return

    # Extract data from the match
    company = company_match['Company Name']
    ticker = company_match['Ticker']
    status = company_match['Halal Status']
    reason = company_match['Halal Reason']
    sector = company_match['Sector']

    try:
        # Fetch real-time data
        stock_data = get_stock_data(ticker)
        price_chart = plot_stock_history(ticker)

        # Layout
        st.subheader(f"{company} ({ticker})")
        st.caption(f"Sector: {sector}")

        # Status and metrics
        col1, col2, col3 = st.columns([1, 1, 2])
        with col1:
            st.markdown("**Halal Status**")
            status_color = "#28a745" if status == "Halal" else "#dc3545"
            st.markdown(
                f"<div style='background-color:{status_color}; color:white; padding:15px; border-radius:5px; text-align:center; font-size:20px; font-weight:bold;'>"
                f"{status}"
                f"</div>", unsafe_allow_html=True)
            st.caption(reason)

        with col2:
            if isinstance(stock_data, dict):
                # Create metric cards
                cols = st.columns(2)
                with cols[0]:
                    st.markdown('<div class="metric-card">', unsafe_allow_html=True)
                    st.markdown(f'<div class="metric-value">${stock_data["current_price"]:.2f}</div>',
                                unsafe_allow_html=True)
                    st.markdown('<div class="metric-label">Current Price</div>', unsafe_allow_html=True)
                    st.markdown('</div>', unsafe_allow_html=True)

                with cols[1]:
                    st.markdown('<div class="metric-card">', unsafe_allow_html=True)
                    st.markdown(f'<div class="metric-value">${stock_data["52_week_high"]:.2f}</div>',
                                unsafe_allow_html=True)
                    st.markdown('<div class="metric-label">52-Week High</div>', unsafe_allow_html=True)
                    st.markdown('</div>', unsafe_allow_html=True)

                cols = st.columns(2)
                with cols[0]:
                    st.markdown('<div class="metric-card">', unsafe_allow_html=True)
                    st.markdown(f'<div class="metric-value">${stock_data["52_week_low"]:.2f}</div>',
                                unsafe_allow_html=True)
                    st.markdown('<div class="metric-label">52-Week Low</div>', unsafe_allow_html=True)
                    st.markdown('</div>', unsafe_allow_html=True)

                with cols[1]:
                    st.markdown('<div class="metric-card">', unsafe_allow_html=True)
                    st.markdown(f'<div class="metric-value">{stock_data["volatility"] * 100:.2f}%</div>',
                                unsafe_allow_html=True)
                    st.markdown('<div class="metric-label">Volatility</div>', unsafe_allow_html=True)
                    st.markdown('</div>', unsafe_allow_html=True)

        with col3:
            if price_chart:
                st.plotly_chart(price_chart, use_container_width=True)
            else:
                st.warning("Could not load stock chart")

        # SDG Summary
        st.subheader("SDG Analysis")
        if not sdg_df.empty and 'Company Name' in sdg_df.columns and 'Primary SDG' in sdg_df.columns:
            sdg_data = sdg_df[sdg_df['Company Name'].str.strip().str.lower() == company.strip().lower()]
            if not sdg_data.empty:
                goal = sdg_data['Primary SDG'].iloc[0]
                keywords = sdg_data['SDG Keywords'].iloc[0]

                col1, col2 = st.columns([1, 3])
                with col1:
                    st.markdown(f"**Primary SDG**")
                    with st.container():
                        st.markdown(
                            f'<div class="sdg-card" style="border-left: 5px solid {SDG_COLORS.get(goal, "#1f77b4")};">',
                            unsafe_allow_html=True)
                        st.markdown(f"<h3>SDG {goal}</h3>", unsafe_allow_html=True)
                        st.markdown(f"<p><strong>{SDG_TITLES[goal]}</strong></p>", unsafe_allow_html=True)
                        st.markdown(f"<p><small>{SDG_DESCRIPTIONS[goal]}</small></p>", unsafe_allow_html=True)
                        st.markdown('</div>', unsafe_allow_html=True)

                with col2:
                    st.markdown("**Keywords**")
                    with st.container():
                        st.markdown(f'<div class="sdg-card">', unsafe_allow_html=True)
                        st.markdown(f"{keywords}")
                        st.markdown('</div>', unsafe_allow_html=True)
            else:
                with st.container():
                    st.markdown('<div class="warning-card">', unsafe_allow_html=True)
                    st.warning("No SDG data available")
                    st.markdown('</div>', unsafe_allow_html=True)
        else:
            with st.container():
                st.markdown('<div class="warning-card">', unsafe_allow_html=True)
                st.warning("SDG data not available")
                st.markdown('</div>', unsafe_allow_html=True)

    except Exception as e:
        st.error(f"Error loading data: {str(e)}")


def display_grok_results(company, ticker, grok_data):
    """Display results from Grok API analysis"""
    st.subheader(f"{company} ({ticker})" if ticker else company)

    with st.container():
        st.markdown('<div class="warning-card">', unsafe_allow_html=True)
        st.warning("This analysis is AI-generated and may not be 100% accurate")
        st.markdown('</div>', unsafe_allow_html=True)

    # Display sector if available
    sector = grok_data.get('sector', 'Unknown')
    st.caption(f"Sector: {sector}")

    # Layout columns
    col1, col2 = st.columns([1, 2])

    with col1:
        # Halal status
        status = grok_data.get('halal_status', 'Unknown')
        reason = grok_data.get('reason', 'No reason provided')

        st.markdown("**Halal Status**")
        status_color = "#28a745" if status == "Halal" else "#dc3545"
        if status == 'Unknown':
            status_color = "#6c757d"
        st.markdown(
            f"<div style='background-color:{status_color}; color:white; padding:15px; border-radius:5px; text-align:center; font-size:20px; font-weight:bold;'>"
            f"{status}"
            f"</div>", unsafe_allow_html=True)
        st.caption(reason)

        # Try to get stock data if available
        if ticker:
            try:
                stock_data = get_stock_data(ticker)
                if isinstance(stock_data, dict):
                    cols = st.columns(2)
                    with cols[0]:
                        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
                        st.markdown(f'<div class="metric-value">${stock_data["current_price"]:.2f}</div>',
                                    unsafe_allow_html=True)
                        st.markdown('<div class="metric-label">Current Price</div>', unsafe_allow_html=True)
                        st.markdown('</div>', unsafe_allow_html=True)

                    with cols[1]:
                        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
                        st.markdown(f'<div class="metric-value">${stock_data["52_week_high"]:.2f}</div>',
                                    unsafe_allow_html=True)
                        st.markdown('<div class="metric-label">52-Week High</div>', unsafe_allow_html=True)
                        st.markdown('</div>', unsafe_allow_html=True)

                    # Try to show price chart
                    price_chart = plot_stock_history(ticker)
                    if price_chart:
                        st.plotly_chart(price_chart, use_container_width=True)
                    else:
                        st.warning("Could not load stock chart")
                else:
                    st.warning("Could not retrieve stock data")
            except:
                st.warning("Could not retrieve stock data")

    with col2:
        # SDG Analysis
        sdg_goal = grok_data.get('sdg_goal', 0)
        sdg_keywords = grok_data.get('sdg_keywords', '')

        if sdg_goal and sdg_goal != 0:
            st.subheader("SDG Analysis (AI-Generated)")
            with st.container():
                st.markdown(
                    f'<div class="sdg-card" style="border-left: 5px solid {SDG_COLORS.get(sdg_goal, "#1f77b4")};">',
                    unsafe_allow_html=True)
                st.markdown(f"**Primary SDG: {sdg_goal} - {SDG_TITLES.get(sdg_goal, '')}**")
                st.markdown(SDG_DESCRIPTIONS.get(sdg_goal, ''))
                
                if sdg_keywords:
                    st.markdown("**Related Keywords:**")
                    st.info(f"{sdg_keywords}")
                st.markdown('</div>', unsafe_allow_html=True)
        else:
            with st.container():
                st.markdown('<div class="warning-card">', unsafe_allow_html=True)
                st.warning("No SDG analysis available for this company")
                st.markdown('</div>', unsafe_allow_html=True)

    # Disclaimer
    st.markdown("---")
    st.caption("ℹ️ This analysis was generated using AI and may contain inaccuracies. "
               "Always verify with additional sources before making investment decisions.")


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

        source = "Database"
    else:
        # Use Grok API
        with st.spinner(f"Getting AI analysis for {company_query}..."):
            grok_data = get_grok_analysis(company_query, "")

        if grok_data:
            company = company_query
            ticker = ""
            status = grok_data.get('halal_status', 'Unknown')
            reason = grok_data.get('reason', 'No reason provided')
            sector = grok_data.get('sector', 'Unknown')
            sdg_goal = grok_data.get('sdg_goal', 0)
            sdg_keywords = grok_data.get('sdg_keywords', '')
            source = "Grok AI"
        else:
            return None

    return {
        "name": company,
        "ticker": ticker,
        "halal_status": status,
        "reason": reason,
        "sector": sector,
        "sdg_goal": sdg_goal,
        "sdg_keywords": sdg_keywords,
        "source": source
    }


# Display SDG card for a company
def display_company_sdg_card(company_data):
    """Display SDG card for a company"""
    if company_data['ticker']:
        header = f"{company_data['name']} ({company_data['ticker']})"
    else:
        header = company_data['name']
    st.subheader(header)
    st.caption(f"Source: {company_data['source']}")

    if company_data['sdg_goal'] != 0:
        with st.container():
            st.markdown(
                f'<div class="sdg-card" style="border-left: 5px solid {SDG_COLORS.get(company_data["sdg_goal"], "#1f77b4")};">',
                unsafe_allow_html=True)
            st.markdown(f"**SDG {company_data['sdg_goal']}: {SDG_TITLES.get(company_data['sdg_goal'], '')}**")
            st.markdown(f"**Description:** {SDG_DESCRIPTIONS.get(company_data['sdg_goal'], '')}")
            if company_data['sdg_keywords']:
                st.markdown("**Keywords**")
                st.info(company_data['sdg_keywords'])
            st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.warning("No SDG data available")


# Display Halal card for a company
def display_company_halal_card(company_data):
    """Display Halal card for a company"""
    if company_data['ticker']:
        header = f"{company_data['name']} ({company_data['ticker']})"
    else:
        header = company_data['name']
    st.subheader(header)
    st.caption(f"Source: {company_data['source']}")

    # Halal status
    status = company_data['halal_status']
    reason = company_data['reason']

    st.markdown("**Halal Status**")
    status_color = "#28a745" if status == "Halal" else "#dc3545"
    if status == 'Unknown':
        status_color = "#6c757d"
    st.markdown(
        f"<div style='background-color:{status_color}; color:white; padding:15px; border-radius:5px; text-align:center; font-size:20px; font-weight:bold;'>"
        f"{status}"
        f"</div>", unsafe_allow_html=True)
    st.caption(reason)

    # Sector
    st.markdown(f"**Sector:** {company_data['sector']}")


# SDG Comparison Page with Search Boxes
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
            cols = st.columns(2)
            with cols[0]:
                display_company_sdg_card(company1_data)
            with cols[1]:
                display_company_sdg_card(company2_data)

            # Comparison summary
            st.markdown("---")
            st.subheader("Comparison Summary")

            comparison_data = {
                "Company": [company1_data['name'], company2_data['name']],
                "Source": [company1_data['source'], company2_data['source']],
                "Primary SDG": [company1_data['sdg_goal'], company2_data['sdg_goal']],
                "SDG Title": [SDG_TITLES.get(company1_data['sdg_goal'], "N/A"),
                              SDG_TITLES.get(company2_data['sdg_goal'], "N/A")],
                "Keywords": [company1_data['sdg_keywords'], company2_data['sdg_keywords']]
            }

            st.table(pd.DataFrame(comparison_data))


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
            # Get company data
            company1_data = get_company_data(halal_df, sdg_df, company1)
            company2_data = get_company_data(halal_df, sdg_df, company2)

            if not company1_data or not company2_data:
                st.error("Could not get data for one or both companies")
                return

            # Display comparison
            cols = st.columns(2)
            with cols[0]:
                display_company_halal_card(company1_data)
            with cols[1]:
                display_company_halal_card(company2_data)

            # Comparison summary
            st.markdown("---")
            st.subheader("Comparison Summary")

            comparison_data = {
                "Company": [company1_data['name'], company2_data['name']],
                "Source": [company1_data['source'], company2_data['source']],
                "Halal Status": [company1_data['halal_status'], company2_data['halal_status']],
                "Reason": [company1_data['reason'], company2_data['reason']],
                "Sector": [company1_data['sector'], company2_data['sector']]
            }

            st.table(pd.DataFrame(comparison_data))


# Main entry point
if __name__ == "__main__":
    main()