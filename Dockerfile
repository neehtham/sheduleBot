# Use official Python image
FROM python:3.11-slim

# Set work directory
WORKDIR /app

# Copy project files
COPY . /app

# Install dependencies
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Set environment variables (optional, for .env support)
ENV PYTHONUNBUFFERED=1

# Expose port if needed (not required for Telegram bots)
# EXPOSE 8080

# Run the bot
CMD ["python", "Bot.py"]