#!/bin/bash

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo "Python 3 is not installed. Please install Python 3 and try again."
    exit 1
fi

# Check if pip3 is installed
if ! command -v pip3 &> /dev/null; then
    echo "pip3 is not installed. Please install pip3 and try again."
    exit 1
fi

# Check if venv module is available
python3 -c "import venv" &> /dev/null
if [ $? -ne 0 ]; then
    echo "Python venv module is not available. Installing it now..."
    pip3 install virtualenv
fi

# Create virtual environment if it doesn't exist
if [ ! -d "my-venv" ]; then
    echo "Creating virtual environment 'my-venv'..."
    python3 -m venv my-venv
fi

# Activate virtual environment and install dependencies
echo "Activating virtual environment and installing dependencies..."

# Different activation depending on OS
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
    # Windows
    source my-venv/Scripts/activate
else
    # macOS or Linux
    source my-venv/bin/activate
fi

# Upgrade pip
pip3 install --upgrade pip

# Install required packages
pip3 install requests pillow pystray

echo "Installation complete!"
echo ""
echo "To activate the virtual environment, run:"
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
    echo "source my-venv/Scripts/activate"
else
    echo "source my-venv/bin/activate"
fi
echo ""
echo "To run the application, activate the virtual environment and run:"
echo "python main.py"
