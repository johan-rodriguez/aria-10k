#!/bin/bash
# .agents/harness/init.sh — Initialize aria-10k agent development environment
# SEC 10-K Autonomous Risk Analyzer: LangChain + LangGraph + LangSmith + Streamlit

set -e

echo "=== Initializing aria-10k Agent Harness ==="

# Step 1: Ensure Python 3.10+ is available
echo "Checking Python version..."
python3 --version

# Step 2: Create virtual environment if it doesn't exist
if [ ! -d ".venv" ]; then
  echo "Creating virtual environment..."
  python3 -m venv .venv
fi

# Step 3: Activate virtual environment
echo "Activating virtual environment..."
source .venv/bin/activate

# Step 4: Install dependencies
if [ -f "requirements.txt" ]; then
  echo "Installing dependencies from requirements.txt..."
  pip install --quiet -r requirements.txt
else
  echo "WARNING: requirements.txt not found. Skipping dependency install."
  echo "Please create requirements.txt (see .env.example for required packages)."
fi

# Step 5: Validate environment variables
if [ -f ".env" ]; then
  echo "Loading environment variables from .env..."
  set -a
  source .env
  set +a
else
  echo "WARNING: .env file not found."
  echo "Copy .env.example to .env and configure your API keys before running the pipeline."
fi

# Step 6: Run tests if src/ has any test files
if find src/ -name "test_*.py" -o -name "*_test.py" 2>/dev/null | grep -q .; then
  echo "Running tests..."
  python -m pytest src/ -v
else
  echo "No test files found in src/. Skipping test run."
fi

# Step 7: Save PID marker
echo $$ > .agents/harness/dev_server.pid

echo ""
echo "=== aria-10k Harness initialization complete ==="
echo "Virtual environment: .venv (activate with: source .venv/bin/activate)"
echo "To run the Streamlit app: streamlit run app.py"
echo "To check agent status: cat .agents/harness/aria-10k-progress.md"
