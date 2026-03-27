FROM python:3.9-slim
WORKDIR /app

# Copy the requirements file first to leverage Docker caching
COPY requirements.txt .

# Install all packages listed in requirements.txt (including cryptography)
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

EXPOSE 81
CMD ["python", "app.py"]