# dashboard/app.py
# Purpose: Interactive dashboard for consent analysis results

"""
Module: app.py
Purpose: Interactive dashboard for consent analysis results with history tracking.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
from io import StringIO
from datetime import datetime, timedelta
from typing import List, Dict, Any

from micro_consent_pipeline.pipeline_runner import PipelineRunner
from micro_consent_pipeline.config.settings import Settings


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
    settings = Settings()

    min_confidence = st.sidebar.slider(
        "Minimum Confidence",
        min_value=0.0,
        max_value=1.0,
        value=settings.min_confidence,
        step=0.1
    )

    language_support = st.sidebar.selectbox(
        "Language Support",
        options=["en", "es", "fr", "de"],
        index=0
    )

    save_to_db = st.sidebar.checkbox(
        "Save results to database",
        value=True,
        help="Store analysis results for future reference"
    )

    # Main content area
    col1, col2 = st.columns([2, 1])

    with col1:
        st.header("Input Content")

        # Input method selection
        input_method = st.radio(
            "Choose input method:",
            options=["Text Input", "File Upload", "URL"]
        )

        source_content = None

        if input_method == "Text Input":
            source_content = st.text_area(
                "Enter HTML content:",
                height=200,
                placeholder="<html><body><button>Accept Cookies</button></body></html>"
            )

        elif input_method == "File Upload":
            uploaded_file = st.file_uploader(
                "Choose an HTML file",
                type=['html', 'htm', 'txt']
            )
            if uploaded_file is not None:
                source_content = StringIO(uploaded_file.getvalue().decode("utf-8")).read()
                st.text_area("File content preview:", source_content[:500] + "...", height=100)

        elif input_method == "URL":
            url = st.text_input(
                "Enter URL:",
                placeholder="https://example.com"
            )
            if url:
                source_content = url

    with col2:
        st.header("Settings")
        st.write(f"Min Confidence: {min_confidence}")
        st.write(f"Language: {language_support}")
        st.write(f"Save to Database: {save_to_db}")

        if st.button("🚀 Analyze", type="primary", use_container_width=True):
            if source_content:
                analyze_content(source_content, min_confidence, save_to_db)
            else:
                st.error("Please provide content to analyze")


def history_tab():
    """
    Analysis history tab showing stored results.
    """
    st.header("📚 Analysis History")
    st.markdown("View and analyze previously stored consent analysis results")

    try:
        # Try to import database modules
        from db.session import get_db_sync
        from db.models import ConsentRecord, ClauseRecord

        # Get database session
        db = get_db_sync()

        try:
            # Query recent analyses
            col1, col2 = st.columns([3, 1])

            with col2:
                st.subheader("Filters")

                # Date range filter
                date_range = st.selectbox(
                    "Time Range",
                    options=["Last 24 hours", "Last 7 days", "Last 30 days", "All time"],
                    index=1
                )

                # Status filter
                status_filter = st.selectbox(
                    "Status",
                    options=["All", "completed", "failed"],
                    index=0
                )

                refresh_button = st.button("🔄 Refresh", use_container_width=True)

            with col1:
                # Calculate date filter
                now = datetime.utcnow()
                if date_range == "Last 24 hours":
                    since_date = now - timedelta(days=1)
                elif date_range == "Last 7 days":
                    since_date = now - timedelta(days=7)
                elif date_range == "Last 30 days":
                    since_date = now - timedelta(days=30)
                else:
                    since_date = None

                # Query records
                query = db.query(ConsentRecord)

                if since_date:
                    query = query.filter(ConsentRecord.created_at >= since_date)

                if status_filter != "All":
                    query = query.filter(ConsentRecord.status == status_filter)

                records = query.order_by(ConsentRecord.created_at.desc()).limit(100).all()

                if not records:
                    st.info("No analysis records found for the selected criteria.")
                else:
                    st.subheader(f"Found {len(records)} analysis records")

                    # Create DataFrame for display
                    records_data = []
                    for record in records:
                        records_data.append({
                            'ID': str(record.id)[:8] + "...",
                            'Source': record.source_url[:50] + "..." if len(record.source_url) > 50 else record.source_url,
                            'Date': record.created_at.strftime("%Y-%m-%d %H:%M"),
                            'Items': record.total_items,
                            'Status': record.status,
                            'Categories': len(record.data.get('categories', {})) if record.data else 0
                        })

                    df = pd.DataFrame(records_data)

                    # Display records table
                    selected_indices = st.dataframe(
                        df,
                        use_container_width=True,
                        on_select="rerun",
                        selection_mode="single-row"
                    )

                    # Show details for selected record
                    if selected_indices and selected_indices['selection']['rows']:
                        selected_idx = selected_indices['selection']['rows'][0]
                        selected_record = records[selected_idx]

                        show_record_details(selected_record, db)

                    # Summary statistics
                    st.subheader("📊 Summary Statistics")

                    col1, col2, col3, col4 = st.columns(4)

                    with col1:
                        total_items = sum(r.total_items for r in records)
                        st.metric("Total Items Found", total_items)

                    with col2:
                        avg_items = total_items / len(records) if records else 0
                        st.metric("Avg Items per Analysis", f"{avg_items:.1f}")

                    with col3:
                        completed_count = sum(1 for r in records if r.status == 'completed')
                        st.metric("Completed Analyses", completed_count)

                    with col4:
                        success_rate = (completed_count / len(records) * 100) if records else 0
                        st.metric("Success Rate", f"{success_rate:.1f}%")

        finally:
            db.close()

    except ImportError:
        st.warning("Database functionality not available. Install database dependencies to view analysis history.")
    except Exception as e:
        st.error(f"Error accessing analysis history: {str(e)}")


def show_record_details(record: 'ConsentRecord', db):
    """
    Show detailed information for a selected record.
    """
    st.subheader(f"📋 Analysis Details - {record.created_at.strftime('%Y-%m-%d %H:%M')}")

    # Basic information
    col1, col2 = st.columns(2)

    with col1:
        st.write(f"**Source:** {record.source_url}")
        st.write(f"**Total Items:** {record.total_items}")
        st.write(f"**Status:** {record.status}")

    with col2:
        st.write(f"**Language:** {record.language or 'Not specified'}")
        st.write(f"**Created:** {record.created_at}")
        if record.processing_time_seconds:
            st.write(f"**Processing Time:** {record.processing_time_seconds:.2f}s")

    # Categories breakdown
    if record.data and record.data.get('categories'):
        st.write("**Categories Found:**")
        categories = record.data['categories']

        # Show as metrics
        category_cols = st.columns(min(len(categories), 4))
        for i, (category, count) in enumerate(categories.items()):
            with category_cols[i % 4]:
                st.metric(category.title(), count)

        # Show as chart
        if len(categories) > 1:
            fig = px.pie(
                values=list(categories.values()),
                names=list(categories.keys()),
                title="Category Distribution"
            )
            st.plotly_chart(fig, use_container_width=True)

    # Detailed clauses
    from db.models import ClauseRecord
    clauses = db.query(ClauseRecord).filter(ClauseRecord.consent_id == record.id).all()

    if clauses:
        st.write(f"**Individual Clauses ({len(clauses)}):**")

        # Create DataFrame for clauses
        clause_data = []
        for clause in clauses:
            clause_data.append({
                'Text': clause.text[:100] + "..." if len(clause.text) > 100 else clause.text,
                'Category': clause.category,
                'Confidence': clause.confidence,
                'Element Type': clause.element_type,
                'Interactive': clause.is_interactive
            })

        clause_df = pd.DataFrame(clause_data)
        st.dataframe(clause_df, use_container_width=True)

        # Option to re-analyze or export
        col1, col2 = st.columns(2)

        with col1:
            if st.button("🔄 Re-analyze Source", key=f"reanalyze_{record.id}"):
                if record.source_url and record.source_url != "HTML_CONTENT":
                    analyze_content(record.source_url, 0.5, True)
                else:
                    st.warning("Cannot re-analyze HTML content - original source not available")

        with col2:
            if st.button("📥 Export Data", key=f"export_{record.id}"):
                export_data = {
                    'record': {
                        'id': str(record.id),
                        'source_url': record.source_url,
                        'created_at': record.created_at.isoformat(),
                        'total_items': record.total_items,
                        'status': record.status
                    },
                    'clauses': clause_data
                }
                st.download_button(
                    label="Download JSON",
                    data=pd.Series(export_data).to_json(),
                    file_name=f"consent_analysis_{record.id}.json",
                    mime="application/json"
                )


def analyze_content(source: str, min_confidence: float, save_to_db: bool = False):
    """
    Analyze the provided content and display results.

    Args:
        source: Source content to analyze
        min_confidence: Minimum confidence threshold
        save_to_db: Whether to save results to database
    """
    try:
        with st.spinner("Analyzing content..."):
            # Configure pipeline with custom settings
            config = {"min_confidence": min_confidence}
            runner = PipelineRunner(config=config)

            # Run analysis with optional database saving
            results = runner.run(source, output_format=None, save_to_db=save_to_db)

        if not results:
            st.warning("No consent elements found in the content.")
            return

        st.success(f"Analysis completed! Found {len(results)} consent elements.")

        if save_to_db:
            st.info("✅ Results have been saved to the database and can be viewed in the History tab.")

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

    except Exception as e:
        st.error(f"Analysis failed: {str(e)}")


def show_record_details(record, db):
    """
    Show detailed information for a selected record.
    """
    st.subheader(f"📋 Analysis Details - {record.created_at.strftime('%Y-%m-%d %H:%M')}")

    # Basic information
    col1, col2 = st.columns(2)

    with col1:
        st.write(f"**Source:** {record.source_url}")
        st.write(f"**Total Items:** {record.total_items}")
        st.write(f"**Status:** {record.status}")

    with col2:
        st.write(f"**Language:** {record.language or 'Not specified'}")
        st.write(f"**Created:** {record.created_at}")
        if record.processing_time_seconds:
            st.write(f"**Processing Time:** {record.processing_time_seconds:.2f}s")

    # Categories breakdown
    if record.data and record.data.get('categories'):
        st.write("**Categories Found:**")
        categories = record.data['categories']

        # Show as metrics
        category_cols = st.columns(min(len(categories), 4))
        for i, (category, count) in enumerate(categories.items()):
            with category_cols[i % 4]:
                st.metric(category.title(), count)

        # Show as chart
        if len(categories) > 1:
            fig = px.pie(
                values=list(categories.values()),
                names=list(categories.keys()),
                title="Category Distribution"
            )
            st.plotly_chart(fig, use_container_width=True)

    # Detailed clauses
    from db.models import ClauseRecord
    clauses = db.query(ClauseRecord).filter(ClauseRecord.consent_id == record.id).all()

    if clauses:
        st.write(f"**Individual Clauses ({len(clauses)}):**")

        # Create DataFrame for clauses
        clause_data = []
        for clause in clauses:
            clause_data.append({
                'Text': clause.text[:100] + "..." if len(clause.text) > 100 else clause.text,
                'Category': clause.category,
                'Confidence': clause.confidence,
                'Element Type': clause.element_type,
                'Interactive': clause.is_interactive
            })

        clause_df = pd.DataFrame(clause_data)
        st.dataframe(clause_df, use_container_width=True)

        # Option to re-analyze or export
        col1, col2 = st.columns(2)

        with col1:
            if st.button("🔄 Re-analyze Source", key=f"reanalyze_{record.id}"):
                if record.source_url and record.source_url != "HTML_CONTENT":
                    analyze_content(record.source_url, 0.5, True)
                else:
                    st.warning("Cannot re-analyze HTML content - original source not available")

        with col2:
            if st.button("📥 Export Data", key=f"export_{record.id}"):
                export_data = {
                    'record': {
                        'id': str(record.id),
                        'source_url': record.source_url,
                        'created_at': record.created_at.isoformat(),
                        'total_items': record.total_items,
                        'status': record.status
                    },
                    'clauses': clause_data
                }
                st.download_button(
                    label="Download JSON",
                    data=pd.Series(export_data).to_json(),
                    file_name=f"consent_analysis_{record.id}.json",
                    mime="application/json"
                )


if __name__ == "__main__":
    main()