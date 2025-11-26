#!/bin/bash

echo "🚀 Boardy QA Analyzer - Conversation Quality Analysis"
echo "===================================================="

echo "🔧 Checking API server..."
python3 start_api_server.py

echo ""
echo "🌐 Opening Boardy QA Analyzer..."
echo ""
echo "✨ Features:"
echo "   • 🔍 Detailed violation explanations"
echo "   • ⚠️ Impact on user experience"
echo "   • 💡 Actionable solutions"
echo "   • 📝 Before/after examples"
echo "   • 📊 Comprehensive statistics"
echo ""
echo "📋 Analysis Includes:"
echo "   • Style violations with natural language guidance"
echo "   • Question responsiveness checks"
echo "   • Length optimization recommendations"
echo "   • Conversation health monitoring"
echo "   • Turn-taking analysis"
echo ""
echo "🧪 Quick Start:"
echo "   1. Click '📋 Load Sample'"
echo "   2. Click '🔍 Analyze Conversation'"
echo "   3. Review detailed explanations for each violation"
echo ""
echo "🎯 What You'll See:"
echo "   • What's Wrong: Clear problem descriptions"
echo "   • Why It Matters: User experience impact"
echo "   • How to Fix: Actionable solutions"
echo "   • Examples: Real before/after comparisons"

open analyzer.html
