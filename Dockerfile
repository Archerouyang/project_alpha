# 1. Use an official Python runtime as a parent image
# We use a specific version to ensure consistency.
# The 'slim' variant is smaller than the full one.
FROM python:3.11-slim

# 2. Set the working directory in the container
WORKDIR /app

# 3. Set environment variables
# Prevents Python from writing pyc files to disc
ENV PYTHONDONTWRITEBYTECODE 1
# Ensures Python output is sent straight to the terminal without buffering
ENV PYTHONUNBUFFERED 1
# Set the default encoding to UTF-8
ENV PYTHONIOENCODING=UTF-8

# 4. Install system dependencies
# We need to install dependencies for Playwright's browsers.
# -y flag automatically answers yes to prompts.
# --no-install-recommends reduces the image size.
RUN apt-get update && apt-get install -y --no-install-recommends \
    # System deps for browsers
    libnss3 \
    libnspr4 \
    libdbus-1-3 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libxkbcommon0 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxrandr2 \
    libgbm1 \
    libxshmfence1 \
    libatspi2.0-0 \
    # --- ADD FONTS ---
    # Install fonts required for headless browser rendering.
    fonts-liberation \
    fonts-wqy-zenhei \
    # Clean up apt cache to reduce image size
    && rm -rf /var/lib/apt/lists/*

# 5. Install Python dependencies
# First, copy only the requirements file to leverage Docker's layer caching.
# This layer is only rebuilt when requirements.txt changes.
COPY requirements.txt .

# Install uv, a fast Python package installer
RUN pip install uv

# Install dependencies using uv
# Using --system flag to install into the system Python environment
RUN uv pip install --system --no-cache --prerelease=allow -r requirements.txt

# 6. Install Playwright browsers and their dependencies
# We are specifying 'firefox' to see if a different browser engine avoids the rendering bug.
RUN playwright install firefox chromium --with-deps

# 7. Copy the rest of the application code into the container
COPY . .

# 8. Expose the port the app runs on
# This informs Docker that the container listens on the specified network port at runtime.
EXPOSE 8000

# 9. Define the command to run the application
# This will be the command executed when the container starts.
# We use uvicorn to run our FastAPI application.
# --host 0.0.0.0 makes the server accessible from outside the container.
# --port 8000 matches the EXPOSE instruction.
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"] 