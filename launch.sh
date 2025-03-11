
#!/bin/bash

# Default values
STOP_ON_ERROR=false
INSTALL_SPACY=false
PORT=8501
CLEAN_PYTEST_CACHE=true

# Parse command line arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    --stop-on-error)
      STOP_ON_ERROR=true
      shift
      ;;
    --port)
      PORT="$2"
      shift
      shift
      ;;
    --install-spacy)
      INSTALL_SPACY=true
      shift
      ;;
    --clean-pytest-cache)
      CLEAN_PYTEST_CACHE=true
      shift
      ;;
    *)
      echo "Unknown option: $1"
      exit 1
      ;;
  esac
done

echo "Running tests..."
if [ "$STOP_ON_ERROR" = true ]; then
  # Run tests with immediate failure on error
  python -m pytest tests/ -v || exit 1
else
  # Run all tests regardless of failures
  python -m pytest tests/ -v
fi

if [ "$INSTALL_SPACY" = true ]; then
  echo "Downloading spaCy model..."
  python -m spacy download en_core_web_sm
fi

if [ "$CLEAN_PYTEST_CACHE" = true ]; then
  echo "Cleaning pytest cache..."
  rm -rf .pytest_cache
fi

echo "Starting Streamlit app on port $PORT..."
PYTHONUNBUFFERED=1 streamlit run demo/streamlit_app.py \
  --server.port=$PORT \
  --server.address=0.0.0.0 \
  --server.enableCORS=false \
  --server.enableXsrfProtection=false \
  --logger.level=debug \
  --server.baseUrlPath=''
