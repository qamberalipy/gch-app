# Use the official Python image from the Docker Hub
FROM python:3.11-slim
LABEL Lets Move API

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file to the working directory
COPY requirements.txt .

# Install the dependencies specified in the requirements file
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code to the working directory
COPY . .

COPY alembic.ini .
COPY alembic alembic

ENV DATABASE_URL=postgresql://lets-move-be_owner:RIGmuZoJ8S7Q@ep-shrill-dew-a4i504n9.us-east-1.aws.neon.tech/lets-move-be?sslmode=require
ENV JWT_SECRET=e56623570e0a0152989fd38e13da9cd6eb7031e4e039e939ba845167ee59b496

# Verify alembic migrations exist
RUN ls -la alembic/versions

RUN alembic upgrade head

# Specify the port number the container should expose
EXPOSE 8000

# Command to run the FastAPI application using uvicorn, ensuring the .env file is sourced
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
