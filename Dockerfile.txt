FROM python:3.11-slim

# ติดตั้ง ffmpeg
RUN apt-get update && apt-get install -y ffmpeg

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 10000

CMD streamlit run app.py --server.port=10000 --server.address=0.0.0.0
