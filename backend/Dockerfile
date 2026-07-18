FROM eclipse-temurin:25-jre AS jre

FROM python:3.12-slim

WORKDIR /app

COPY --from=jre /opt/java/openjdk /opt/java/openjdk

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV JAVA_HOME=/opt/java/openjdk
ENV PATH=/opt/java/openjdk/bin:$PATH
ENV PYTHONPATH=/app

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
