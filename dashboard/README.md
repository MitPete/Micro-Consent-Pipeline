# Micro-Consent Dashboard

A Streamlit-based interactive dashboard for analyzing consent mechanisms on websites using the Micro-Consent Pipeline API.

## Features

- 🔍 **Real-time Analysis**: Analyze HTML content or URLs via API
- 📊 **Interactive Visualizations**: Charts and tables for consent categories
- ⚙️ **Configurable Settings**: Adjustable confidence thresholds and API endpoints
- 🎨 **Modern UI**: Clean, responsive interface with dark/light themes

## Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Run locally
streamlit run app.py
```

## Environment Variables

Create a `.env` file in the dashboard directory:

```bash
API_BASE=https://your-api-endpoint.com
API_KEY=your-optional-api-key
```

## Streamlit Cloud Deployment

1. Go to [share.streamlit.io](https://share.streamlit.io)
2. Connect your GitHub repository
3. Select `dashboard/app.py` as the main file
4. Set environment variables:
   - `API_BASE`: Your API endpoint URL
   - `API_KEY`: (Optional) API authentication key
5. Deploy!

## API Integration

The dashboard communicates with the FastAPI backend:

- **Endpoint**: `POST /analyze`
- **Payload**: `{"source": "html_or_url", "output_format": "json", "min_confidence": 0.5}`
- **Headers**: `X-API-Key` (if authentication required)

## Usage

1. **Input Content**: Enter HTML content or a URL
2. **Configure Settings**: Adjust confidence threshold and API endpoint
3. **Analyze**: Click the analyze button to process
4. **View Results**: See categorized consent elements with confidence scores
5. **Visualize**: Explore charts showing category distributions

## Requirements

- Python 3.8+
- Streamlit 1.33+
- Plotly
- Requests
- Pandas

## File Structure

```
dashboard/
├── app.py              # Main Streamlit application
├── requirements.txt    # Python dependencies
├── streamlit_app.toml  # Streamlit configuration
└── README.md          # This file
```