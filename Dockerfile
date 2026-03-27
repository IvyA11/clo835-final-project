FROM python:3.9-slim
WORKDIR /app
RUN pip install flask boto3 pymysql
COPY . .
EXPOSE 81
CMD ["python", "app.py"]