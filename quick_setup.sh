#!/bin/bash
# Quick setup script for alternative vision models

set -e

echo "=================================================="
echo "Alternative Vision Models - Quick Setup"
echo "=================================================="
echo ""

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Detect Python
if command_exists python3; then
    PYTHON=python3
elif command_exists python; then
    PYTHON=python
else
    echo "❌ Error: Python not found"
    exit 1
fi

echo "Using Python: $PYTHON"
echo ""

# Menu
echo "Choose your setup:"
echo "1. OpenAI GPT-4o-mini (cheapest API, ~\$0.0002/image)"
echo "2. Google Gemini Flash (free tier available)"
echo "3. Ollama (fully local, FREE, no internet needed)"
echo "4. OpenCV only (minimal, basic functionality)"
echo "5. All methods (install everything)"
echo ""
read -p "Enter choice (1-5): " choice

case $choice in
    1)
        echo ""
        echo "📦 Installing OpenAI..."
        $PYTHON -m pip install openai
        echo ""
        echo "✅ OpenAI installed!"
        echo ""
        echo "Next steps:"
        echo "1. Get API key from: https://platform.openai.com/api-keys"
        echo "2. Export key: export OPENAI_API_KEY='sk-...'"
        echo "3. Test: python src/local_vision_reader.py meter.jpg --method openai"
        ;;
    2)
        echo ""
        echo "📦 Installing Google Gemini..."
        $PYTHON -m pip install google-generativeai
        echo ""
        echo "✅ Gemini installed!"
        echo ""
        echo "Next steps:"
        echo "1. Get API key from: https://makersuite.google.com/app/apikey"
        echo "2. Export key: export GOOGLE_API_KEY='...'"
        echo "3. Test: python src/local_vision_reader.py meter.jpg --method gemini"
        ;;
    3)
        echo ""
        echo "📦 Setting up Ollama (local vision)..."

        # Check if ollama is installed
        if command_exists ollama; then
            echo "✅ Ollama already installed"
        else
            echo "Installing Ollama..."
            if [[ "$OSTYPE" == "darwin"* ]]; then
                if command_exists brew; then
                    brew install ollama
                else
                    echo "Download from: https://ollama.ai/download"
                    exit 1
                fi
            elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
                curl -fsSL https://ollama.ai/install.sh | sh
            else
                echo "Please download from: https://ollama.ai/download"
                exit 1
            fi
        fi

        # Install Python client
        echo ""
        echo "📦 Installing Ollama Python client..."
        $PYTHON -m pip install ollama

        # Start ollama in background
        echo ""
        echo "🚀 Starting Ollama service..."
        if ! pgrep -x "ollama" > /dev/null; then
            ollama serve > /dev/null 2>&1 &
            sleep 2
        fi

        # Pull vision model
        echo ""
        echo "📥 Pulling llama3.2-vision model (~7GB, this will take a few minutes)..."
        echo "You can choose a smaller model if needed:"
        echo "  - llama3.2-vision:11b (recommended, best quality)"
        echo "  - llava:7b (smaller, faster)"
        read -p "Which model? (default: llama3.2-vision:11b): " model
        model=${model:-llama3.2-vision:11b}

        ollama pull "$model"

        echo ""
        echo "✅ Ollama setup complete!"
        echo ""
        echo "Test with: python src/local_vision_reader.py meter.jpg --method ollama"
        ;;
    4)
        echo ""
        echo "📦 Installing OpenCV..."
        $PYTHON -m pip install opencv-python numpy
        echo ""
        echo "✅ OpenCV installed!"
        echo ""
        echo "Note: OpenCV only provides basic functionality (needle detection)"
        echo "For digit recognition, use one of the other methods."
        echo ""
        echo "Test with: python src/local_vision_reader.py meter.jpg --method opencv"
        ;;
    5)
        echo ""
        echo "📦 Installing all dependencies..."
        $PYTHON -m pip install -r requirements-local-vision.txt

        echo ""
        echo "📦 Installing Ollama..."
        if ! command_exists ollama; then
            if [[ "$OSTYPE" == "darwin"* ]]; then
                if command_exists brew; then
                    brew install ollama
                else
                    echo "⚠️  Install Ollama from: https://ollama.ai/download"
                fi
            elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
                curl -fsSL https://ollama.ai/install.sh | sh
            else
                echo "⚠️  Install Ollama from: https://ollama.ai/download"
            fi
        fi

        echo ""
        echo "✅ All dependencies installed!"
        echo ""
        echo "Next steps:"
        echo "1. Set API keys (optional):"
        echo "   export OPENAI_API_KEY='sk-...'"
        echo "   export GOOGLE_API_KEY='...'"
        echo ""
        echo "2. For Ollama (local), pull a vision model:"
        echo "   ollama serve  # Start service"
        echo "   ollama pull llama3.2-vision:11b"
        echo ""
        echo "3. Compare all methods:"
        echo "   python src/local_vision_reader.py meter.jpg --method compare"
        ;;
    *)
        echo "Invalid choice"
        exit 1
        ;;
esac

echo ""
echo "=================================================="
echo "Setup complete! 🎉"
echo "=================================================="
echo ""
echo "Read SETUP_ALTERNATIVE_VISION.md for detailed instructions"
