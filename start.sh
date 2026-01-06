#!/bin/bash
# =============================================================================
# Budget Tracker - Startup Script
# =============================================================================
# Run this script to start the budget tracker app
#
# Usage:
#   ./start.sh          # Normal start
#   ./start.sh --bg     # Start in background
#
# =============================================================================

cd "$(dirname "$0")"

echo "🚀 Starting Family Budget Tracker..."
echo ""

# Check if streamlit is installed
if ! command -v streamlit &> /dev/null && ! python3 -m streamlit --version &> /dev/null; then
    echo "❌ Streamlit not found. Installing dependencies..."
    python3 -m pip install -r requirements.txt
fi

# Check for background flag
if [ "$1" == "--bg" ]; then
    echo "📍 Running in background..."
    python3 -m streamlit run app.py --server.headless true &
    echo ""
    echo "✅ App started in background!"
    echo "   Open: http://localhost:8501"
    echo ""
    echo "   To stop: pkill -f 'streamlit run app.py'"
else
    echo "📍 Open your browser to: http://localhost:8501"
    echo "   Press Ctrl+C to stop"
    echo ""
    python3 -m streamlit run app.py
fi


