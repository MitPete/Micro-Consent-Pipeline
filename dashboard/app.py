# dashboard/app.py
# Purpose: Interactive dashboard for consent analysis results

"""
Module: app.py
Purpose: Interactive dashboard for consent analysis results with API integration.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
from io import StringIO
from datetime import datetime, timedelta
from typing import List, Dict, Any
import requests
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# API Configuration
API_BASE = os.getenv("API_BASE", "https://micro-consent-pipeline.onrender.com")
API_KEY = os.getenv("API_KEY", "")


def main():
    """
    Main Streamlit dashboard application.
    """
    st.set_page_config(
        page_title="Micro-Consent Pipeline Dashboard",
        page_icon="🔒",
        layout="wide"
    )

    st.title("🔒 Micro-Consent Pipeline Dashboard")
    st.markdown("Analyze consent-related content from websites and documents")

    # Create tabs
    tab1, tab2 = st.tabs(["🔍 Analyze", "📚 History"])

    with tab1:
        analyze_tab()

    with tab2:
        history_tab()


def analyze_tab():
    """
    Content analysis tab.
    """
    # Sidebar configuration
    st.sidebar.header("Configuration")

    api_base = st.sidebar.text_input(
        "API Base URL",
        value=API_BASE,
        help="Base URL for the consent analysis API"
    )

    min_confidence = st.sidebar.slider(
        "Minimum Confidence",
        min_value=0.0,
        max_value=1.0,
        value=0.5,
        step=0.1
    )

    api_key = st.sidebar.text_input(
        "API Key (optional)",
        value=API_KEY,
        type="password",
        help="API key for authentication if required"
    )

    # Main content area
    col1, col2 = st.columns([2, 1])

    with col1:
        st.header("Input Content")

        # Input method selection
        input_method = st.radio(
            "Choose input method:",
            options=["Text Input", "URL"]
        )

        source_content = None

        if input_method == "Text Input":
            source_content = st.text_area(
                "Enter HTML content:",
                height=200,
                placeholder="<html><body><button>Accept Cookies</button></body></html>"
            )

        elif input_method == "URL":
            url = st.text_input(
                "Enter URL:",
                placeholder="https://example.com"
            )
            if url:
                source_content = url

    with col2:
        st.header("Settings")
        st.write(f"API Base: {api_base}")
        st.write(f"Min Confidence: {min_confidence}")
        st.write(f"API Key: {'Set' if api_key else 'Not set'}")

        if st.button("🚀 Analyze", type="primary", use_container_width=True):
            if source_content:
                analyze_content(source_content, min_confidence, api_base, api_key)
            else:
                st.error("Please provide content to analyze")


def history_tab():
    """
    Information about analysis history (API-based).
    """
    st.header("📚 Analysis History")
    st.markdown("Analysis history is stored on the server. Access via API endpoints:")

    st.code("""
# Get recent analyses
curl https://api.microconsent.dev/history

# Get specific analysis
curl https://api.microconsent.dev/history/{id}
    """)

    st.info("💡 History functionality requires server-side database access. Results from this dashboard are processed in real-time via API calls.")


def analyze_content(source: str, min_confidence: float, api_base: str, api_key: str = ""):
    """
    Analyze the provided content via API and display results.

    Args:
        source: Source content to analyze
        min_confidence: Minimum confidence threshold
        api_base: Base URL for the API
        api_key: API key for authentication
    """
    try:
        with st.spinner("Analyzing content via API..."):
            # Prepare API request
            headers = {"Content-Type": "application/json"}
            if api_key:
                headers["X-API-Key"] = api_key

            payload = {
                "source": source,
                "output_format": "json",
                "min_confidence": min_confidence
            }

            # Make API call
            response = requests.post(
                f"{api_base}/analyze",
                json=payload,
                headers=headers,
                timeout=30
            )

            response.raise_for_status()
            results = response.json()

        if not results or not isinstance(results, list):
            st.warning("No consent elements found in the content.")
            return

        st.success(f"Analysis completed! Found {len(results)} consent elements.")

        # Convert to DataFrame for display
        df = pd.DataFrame(results)

        # Results table
        st.header("📊 Analysis Results")

        # Filter by confidence
        filtered_df = df[df['confidence'] >= min_confidence]

        if filtered_df.empty:
            st.warning(f"No results meet the minimum confidence threshold of {min_confidence}")
        else:
            st.dataframe(
                filtered_df[['text', 'category', 'confidence', 'type']],
                use_container_width=True
            )

        # Category distribution chart
        st.header("📈 Category Distribution")

        if not filtered_df.empty:
            category_counts = filtered_df['category'].value_counts()

            col1, col2 = st.columns(2)

            with col1:
                fig_pie = px.pie(
                    values=category_counts.values,
                    names=category_counts.index,
                    title="Distribution by Category"
                )
                st.plotly_chart(fig_pie, use_container_width=True)

            with col2:
                fig_bar = px.bar(
                    x=category_counts.index,
                    y=category_counts.values,
                    title="Count by Category",
                    labels={'x': 'Category', 'y': 'Count'}
                )
                st.plotly_chart(fig_bar, use_container_width=True)

        # Summary statistics
        st.header("📋 Summary")

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("Total Items", len(results))

        with col2:
            st.metric("Above Threshold", len(filtered_df))

        with col3:
            avg_confidence = filtered_df['confidence'].mean() if not filtered_df.empty else 0
            st.metric("Avg Confidence", f"{avg_confidence:.2f}")

        with col4:
            unique_categories = filtered_df['category'].nunique() if not filtered_df.empty else 0
            st.metric("Categories Found", unique_categories)

        # Detailed results (expandable)
        with st.expander("View Detailed Results"):
            st.json(results)

    except requests.exceptions.RequestException as e:
        st.error(f"API request failed: {str(e)}")
        if "401" in str(e):
            st.error("Authentication failed. Please check your API key.")
        elif "403" in str(e):
            st.error("Access forbidden. Please check CORS settings.")
        elif "500" in str(e):
            st.error("Server error. Please try again later.")
    except Exception as e:
        st.error(f"Analysis failed: {str(e)}")


if __name__ == "__main__":
    main()