# Bookspire

This repository contains the backend for Bookspire Platform, a  FastAPI application designed to help users improve their language skills through interactive, AI-driven conversations.

## Key Features

- **Multi-Modal Interaction**: Engages users through both text-based chat and real-time voice conversations.
- **Diverse Learning Modes**:
  - **Story Mode**: Interactive, narrative-driven conversations with distinct AI characters.
  - **Sandbox Mode**: Open-ended, real-time voice chat for practicing conversational flow.
  - **Journey Mode**: A structured question-and-answer curriculum to assess and score user responses.
  - **Penpal Mode**: An asynchronous letter-writing feature for long-form practice.
- **Dynamic AI Personas**: Character personalities, behaviors, and even language tutoring styles are defined and controlled by external prompt files, allowing for rapid iteration and character creation without code changes.
- **Real-time Feedback**: Provides instant grammar correction and content moderation during conversations using a parallel processing architecture.
- **Robust Infrastructure**:
  - **Containerized**: Fully containerized with Docker for consistent development and production environments.
  - **Infrastructure as Code (IaC)**: Production infrastructure is declaratively managed via a DigitalOcean App Platform spec (`.do/app.yaml`).
  - **Database Migrations**: Uses Alembic for safe, version-controlled database schema management.

## Tech Stack

- **Backend**: FastAPI, Python 3.11
- **Database**: PostgreSQL
- **Caching**: Redis
- **Real-time Communication**: WebSockets, WebRTC
- **AI/LLM**: OpenAI (GPT-4o)
- **Containerization**: Docker, Docker Compose
- **Deployment**: DigitalOcean App Platform
- **Database Migrations**: Alembic
- **Dependency Management**: Pydantic

---

## Getting Started

### Prerequisites

- Docker and Docker Compose
- An environment file (`.env`) in the project root.

### 1. Create the Environment File

Create a `.env` file in the project root. The application will not start without it. Populate it with your development secrets and configuration:

```env
# Example .env file

# Security (generate these with `openssl rand -hex 32`)
SECRET_KEY=your_super_secret_key_for_general_app_security
JWT_SECRET_KEY=your_super_secret_key_for_jwt_tokens

# OpenAI API Key
OPENAI_API_KEY=sk-your_openai_api_key

# Development Settings (optional, will use defaults from docker-compose.yml)
MODEL_NAME=gpt-4o-mini
```

### 2. Build and Run the Application
Running in local without Docker : uvicorn src.main:app --reload


The entire development environment, including the FastAPI application, PostgreSQL database, and Redis cache, is managed by Docker Compose.

```bash
docker-compose up --build
```

- The FastAPI application will be available at `http://localhost:8000`.
- The PostgreSQL database will be exposed on port `5432`.
- The Redis cache will be exposed on port `6379`.

The application uses hot-reloading. Any changes you make to the source code on your local machine will trigger an automatic restart of the Uvicorn server inside the container.

### 3. API Documentation

Once the application is running, the interactive API documentation (powered by Swagger UI) is available at:

[**http://localhost:8000/docs**](http://localhost:8000/docs)

This provides a complete, self-documenting reference for all API endpoints, schemas, and request/response formats.

---

## Project Architecture

This project follows a clean, feature-based architecture designed for scalability and separation of concerns.

- **`src/core/`**: Contains the application's core logic, which is shared across all features. This includes database connections, security and authentication utilities, configuration management, and application-wide event handlers.

- **`src/shared/`**: Houses reusable components that are not part of the core application framework but are leveraged by multiple features. This promotes code reuse and a single source of truth for common functionalities.
  - **`llm/`**: A robust, high-performance client for interacting with Large Language Models. It includes built-in support for rate limiting, caching, and resilient retry mechanisms.
  - **`message_processing/`**: A dedicated service for asynchronous content analysis. It provides grammar correction and content moderation as a pluggable utility for any chat feature.
  - **`realtime/`**: Encapsulates the logic for communicating with OpenAI's Realtime API to generate the ephemeral tokens required for client-side WebRTC sessions.
  - **`websockets/`**: Contains the centralized `WebSocketManager`, providing a single, consistent interface for managing all WebSocket connections and messaging across the application.
  - **`services.py`**: Defines the `BaseChatService`, an inheritable base class that provides common business logic for session and message management, used by `StoryService` and `SandboxService`.
  - **`schemas.py`**: Contains shared Pydantic schemas (`BaseSessionResponse`, `BaseMessageResponse`) that enforce a consistent data contract across different feature APIs.
  - **`dependencies.py`**: Provides shared FastAPI dependency injectors, such as the provider for the singleton `MessageProcessingService`.

- **`src/features/`**: This is where the primary business logic lives. Each subdirectory represents a distinct feature of the application (e.g., `story_mode`, `sandbox`, `auth`). This modular design allows features to be developed and maintained independently.
  - **`auth/`**: Manages user registration, login, and password management, providing the core authentication and authorization for the application.
  - **`journey/`**: Implements a structured, curriculum-based learning path where users answer a series of questions and receive AI-generated scores and feedback.
  - **`sandbox/`**: Provides an open-ended, real-time voice conversation environment using WebRTC, complete with AI-generated hints based on user speech.
  - **`story_mode/`**: An interactive, text-based chat where users engage in a narrative conversation with dynamic AI characters who provide contextual hints.
  - **`penpal/`**: An asynchronous communication feature allowing users to write letters to AI characters and receive thoughtful, AI-generated responses at a later time.

- **`src/prompts/`**: Contains the raw prompt files that define the behavior of the AI characters. This "prompts-as-code" approach allows for easy iteration and tuning of AI personas without requiring code changes.
  - **Modular Structure**: Prompts are organized by feature (`/journey`) and by content (`/books`), ensuring a clean separation of concerns.
  - **Dynamic Loading**: The application dynamically loads prompts at runtime based on the character ID and the user's language level. This allows for highly tailored and level-appropriate interactions.
  - **Advanced Prompting Techniques**: The system uses separate, specialized prompts for different tasks:
    - **System Prompts** (`{character_id}_{level}.txt`): Define the core personality, voice, and rules for an AI character.
    - **Hint Prompts** (`{character_id}_{level}_hint.txt`): A sophisticated "meta-prompt" that instructs the AI on how to act as a language tutor, providing contextually relevant hints based on the conversation.

- **`scripts/`**: A dedicated directory for standalone administrative and maintenance scripts, keeping them organized and separate from the main application source code.

- **`migrations/`**: Contains the Alembic database migration scripts, providing a version-controlled history of the database schema.

## Administrative Scripts

The `scripts/` directory contains useful command-line tools for managing the application. To run them, you can `exec` into the running application container.

1.  Find your application's container ID:
    ```bash
    docker ps
    ```
2.  Execute a script inside the container:
    ```bash
    # Example: Create a new user interactively
    docker exec -it <your_container_id> python scripts/create_local_user.py

    # Example: List all users in the database
    docker exec -it <your_container_id> python scripts/check_users.py
    ```

---
