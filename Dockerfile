# Base image
FROM python:3.11-slim

# Set workdir
WORKDIR /app

# Copy and install dependencies
COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt


# Copy the app
COPY app/ ./app

# Set the permission to allow writing to the app directory
RUN chmod -R o+w app/

#(TESTAR DEPOIS) Cria um usuário não-root e dá permissão adequada
#RUN adduser --disabled-password --gecos '' dermasyncuser && \
#    chown -R dermasyncuser /app/app

#USER dermasyncuser


# Expose port
EXPOSE 8080

# Command to run the app
#uvicorn app.main:app --host 0.0.0.0 --port 8080 --reload
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080", "--reload"]
