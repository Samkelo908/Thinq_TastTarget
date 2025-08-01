FROM python:3.11-slim-bookworm


# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements files
COPY requirements.txt requirements-frontend.txt ./

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir -r requirements-frontend.txt

# Copy application files
COPY main.py app.py ./
COPY .streamlit .streamlit/

# Create directory for secrets
RUN mkdir -p .streamlit

# Expose ports
EXPOSE 8000 8501

# Create startup script
RUN echo '#!/bin/bash\n\
python main.py &\n\
streamlit run app.py --server.port 8501 --server.address 0.0.0.0\n\
' > /app/start.sh && chmod +x /app/start.sh

# Run the application
CMD ["/app/start.sh"]