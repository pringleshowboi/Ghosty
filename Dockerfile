FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
WORKDIR /app
RUN pip install --no-cache-dir streamlit pandas scikit-learn plotly networkx requests ollama
RUN pip install --no-cache-dir feedparser
COPY app.py /app/app.py
COPY supply_chain /app/supply_chain
EXPOSE 8501
CMD ["streamlit","run","/app/app.py","--server.port","8501","--server.headless","true","--browser.gatherUsageStats","false"]
