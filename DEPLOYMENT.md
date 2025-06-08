# Deployment Guide

This guide provides instructions on how to build the Docker image for this project and run it as a container.

## Prerequisites

- **Docker**: You must have Docker installed and running on your system. You can download it from the [official Docker website](https://www.docker.com/get-started).
- **Environment File**: You need a `.env` file in the root of the project directory. This file contains the necessary API keys for the services to run. It should look like this:

```plaintext
# .env file
DEEPSEEK_API_KEY="your_deepseek_api_key_here"
FMP_API_KEY="your_fmp_api_key_here"
```

Replace the placeholder values with your actual API keys.

## 1. Building the Docker Image

The `Dockerfile` in the project root contains all the instructions to create a container image with the application and all its dependencies.

To build the image, navigate to the project's root directory in your terminal and run the following command:

```bash
docker build -t project-alpha .
```

- `docker build`: The command to build an image from a Dockerfile.
- `-t project-alpha`: This tags the image with the name `project-alpha`. You can choose a different name if you prefer.
- `.`: This specifies that the build context (the set of files to be sent to the Docker daemon) is the current directory.

The build process might take some time, especially the first time you run it, as it needs to download the Python base image, install system dependencies, install Python packages, and download the Playwright browsers.

## 2. Running the Docker Container

Once the image is built successfully, you can run the application as a container.

Execute the following command in your terminal:

```bash
docker run --rm -p 8000:8000 --env-file .env project-alpha
```

Let's break down this command:
- `docker run`: The command to run a new container from an image.
- `--rm`: This flag automatically removes the container when it exits. This is useful for keeping your system clean during development and testing.
- `-p 8000:8000`: This maps port `8000` of the host machine to port `8000` of the container. The application inside the container runs on port `8000`, and this mapping makes it accessible from your host machine's browser at `http://localhost:8000`.
- `--env-file .env`: This is a crucial step. It reads the environment variables from your `.env` file and passes them securely to the container. The application needs these variables to access the APIs.
- `project-alpha`: The name of the image you want to run.

## Accessing the Application

After running the command above, the server should be running. You can open your web browser and navigate to:

[http://localhost:8000](http://localhost:8000)

You should see the web interface, where you can enter a stock ticker to generate a technical analysis report. The backend service running inside the Docker container will handle the request and generate the report image. 