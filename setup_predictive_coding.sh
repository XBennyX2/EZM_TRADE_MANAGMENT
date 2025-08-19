#!/bin/bash

# Setup script for Predictive Coding Neural Network

echo "Setting up Predictive Coding Neural Network Environment"
echo "======================================================="

# Check if Python 3 is available
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is not installed. Please install Python 3 first."
    exit 1
fi

echo "Python 3 found: $(python3 --version)"

# Try to create virtual environment
echo "Creating virtual environment..."
if python3 -m venv predictive_coding_env 2>/dev/null; then
    echo "Virtual environment created successfully."
    
    # Activate virtual environment
    source predictive_coding_env/bin/activate
    
    # Upgrade pip
    echo "Upgrading pip..."
    pip install --upgrade pip
    
    # Install requirements
    echo "Installing requirements..."
    if [ -f "requirements_predictive_coding.txt" ]; then
        pip install -r requirements_predictive_coding.txt
        echo "Requirements installed successfully."
    else
        echo "Installing individual packages..."
        pip install torch numpy matplotlib scipy jupyter seaborn tqdm scikit-learn
    fi
    
    echo "Setup completed successfully!"
    echo "To activate the environment, run: source predictive_coding_env/bin/activate"
    echo "To test the installation, run: python predictive_coding_network.py"
    
else
    echo "Could not create virtual environment. This might be due to missing python3-venv package."
    echo "On Ubuntu/Debian systems, try: sudo apt install python3-venv"
    echo ""
    echo "Alternative: Running simple test without dependencies..."
    python3 simple_predictive_coding_test.py
    echo ""
    echo "For full functionality, please install PyTorch and other dependencies manually."
fi