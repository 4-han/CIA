## CIA (Campus Institue  )
### Ingestion (Data Scraping)

In this script, we use **Selenium** to load PDF links from a website since the `requests` library was unable to handle the JavaScript content that dynamically loads the links. **BeautifulSoup** is used for parsing the HTML to extract the relevant data.

We use **JavaScript-based CSS selectors** to pinpoint the location of the PDF links and dates on the page. Specifically:
1. We locate the elements containing the embedded PDF links (`<a href>`) using BeautifulSoup.
2. We extract the dates associated with these PDF links.
3. We filter and save the links that fall within the provided date range.

The PDF links and associated metadata (date and title) are saved into a `pdf_links.json` file for later use.

### To test the ingestion pipeline, run the following command:

```bash
python ingestion.py --start_date "2025-05-01" --end_date "2025-05-31" --click_workshop False 
```




```bash
pgcli -h localhost -p 5432 -U rag_user -d rag_db ```

-h localhost: Specifies the host is your local machine.
-p 5432: Specifies the port mapped from the container to your host.
-U rag_user: Specifies the database user (replace rag_user with your DB_USER).
-d rag_db: Specifies the database name (replace rag_db with your DB_NAME).


```

# NIT Warangal RAG Telegram Bot

## Project Overview

This project develops a Telegram chatbot designed to act as a RAG (Retrieval-Augmented Generation) assistant, providing information about the National Institute of Technology Warangal (NITW). The bot retrieves information from a curated dataset and uses a Large Language Model (LLM) to generate informative and context-aware responses.

### Key Features:

-   **Conversational Interface:** Interact with the bot directly through Telegram.
-   **RAG Pipeline:** Combines document retrieval with LLM capabilities for enhanced answer generation based on provided context.
-   **Data Indexing:** Utilizes a local search index (Minsearch) built from NITW-specific documents.
-   **LLM Integration:** Leverages a Large Language Model (currently Google Gemini via `google-generativeai`) for generating human-like responses.
-   **Source Citation:** Provides links to the source documents used to generate answers.
-   **Interaction Logging:** Stores user queries, bot responses, and interaction metadata in a PostgreSQL database.
-   **User Feedback:** Allows users to provide "Thumbs Up" or "Thumbs Down" feedback on bot responses via inline keyboard buttons.
-   **Monitoring Dashboard:** Includes a Grafana instance pre-configured to visualize bot activity and feedback metrics from the PostgreSQL database.
-   **Containerized Deployment:** Uses Docker and Docker Compose for easy setup and management of the bot, database, and monitoring services.

### Scope of Capabilities:

The chatbot is designed to answer questions based on the information present in the provided data source (`database.json`). This includes general information about NIT Warangal, potentially covering academics, admissions (if in data), facilities, events, etc. The quality and scope of answers are directly tied to the content and structure of the `database.json` file.

## Project Components

-   **Telegram Bot API (`python-telegram-bot`):** Handles communication with Telegram users.
-   **Configuration Management (`python-dotenv`):** Loads sensitive information (API keys, database credentials) from a `.env` file.
-   **Data Storage (`PostgreSQL`):** A relational database to log bot interactions, user feedback, and associated metadata.
-   **Search Index (`Minsearch`):** A simple, in-memory search engine used for retrieving relevant document chunks based on user queries.
-   **Large Language Model (`google-generativeai`):** Connects to Google's Gemini models (or other supported LLMs) for generating responses based on retrieved context.
-   **Monitoring (`Grafana`):** A visualization tool to create dashboards for monitoring bot usage, feedback, and database activity.
-   **Containerization (`Docker`, `Docker Compose`):** Packages the bot application, database, and Grafana into isolated containers and manages their interaction.

## Getting Started

### Prerequisites

-   Docker and Docker Compose installed on your system.
-   A Telegram Bot Token obtained from @BotFather on Telegram.
-   A Google Cloud Project and a valid Google API Key with access to the Gemini models.

### Setup

1.  **Clone the repository:** (Assuming your project is in a Git repository)
    ```bash
    git clone your_repository_url
    cd your_repository_directory # This should be the CIA/ directory
    ```

2.  **Create and Configure the `.env` file:**
    *   Navigate to the project's root directory (`CIA/`).
    *   Create a file named `.env`.
    *   Copy the following content into `.env` and replace the placeholder values with your actual credentials and desired settings:

    ```dotenv
    # --- Telegram Bot ---
    TELEGRAM_BOT_TOKEN=YOUR_TELEGRAM_BOT_TOKEN

    # --- LLM APIs ---
    # Using Google Gemini via google-generativeai
    GOOGLE_API_KEY=YOUR_GOOGLE_API_KEY
    LLM_MODEL=gemini-1.5-flash-latest # Or your preferred Gemini model name

    # --- PostgreSQL Database ---
    # Connects from bot and grafana containers using the service name 'db'
    DB_HOST=db
    DB_PORT=5432
    DB_NAME=rag_db
    DB_USER=rag_user
    DB_PASSWORD=your_secure_database_password

    # --- Data Source ---
    # Path to your JSON data file *inside the bot container* after volume mounting
    DATA_FILE=/data/database.json

    # --- Grafana Admin Credentials ---
    GRAFANA_ADMIN_USER=admin # Change this for security
    GRAFANA_ADMIN_PASSWORD=admin # Change this for security
    ```
    *   **Important:** Replace `YOUR_TELEGRAM_BOT_TOKEN`, `YOUR_GOOGLE_API_KEY`, and `your_secure_database_password` with your actual credentials. **Change the default Grafana admin credentials to strong, unique values.**

3.  **Place Your Data File:**
    *   Ensure your `database.json` file is located in the `./data/` directory relative to the project root (`CIA/data/database.json`).

### Running the Application with Docker Compose

1.  **Navigate to the project's root directory (`CIA/`)** in your terminal.

2.  **Build and start the Docker containers:**
    ```bash
    docker-compose up --build -d
    ```
    *   `--build`: Builds the Docker images (especially the bot image) before starting. Use this the first time, or after changing code, `requirements.txt`, or `Dockerfile`.
    *   `-d`: Runs the containers in detached mode (in the background).

3.  **Verify containers are running:**
    ```bash
    docker-compose ps
    ```
    You should see `rag_postgres_db`, `rag_telegram_bot`, and `rag_grafana` with status `Up`.

4.  **Check logs for troubleshooting:**
    ```bash
    docker-compose logs bot
    docker-compose logs db
    docker-compose logs grafana
    ```
    These commands are essential for diagnosing startup issues.

5.  **To stop the application:**
    ```bash
    docker-compose down
    ```
    To stop and remove containers, networks, and volumes (for a clean start, **caution: this will delete your database data**):
    ```bash
    docker-compose down --volumes
    ```

## Using the Bot

Once the `rag_telegram_bot` container is `Up`:

1.  Open the Telegram app.
2.  Search for your bot's username (@your\_bot\_username).
3.  Start a chat and send `/start`.
4.  Ask questions about NIT Warangal based on your data source.

## Monitoring with Grafana

Once the `rag_grafana` container is `Up` and you have configured the PostgreSQL data source:

1.  Open your web browser and go to `http://localhost:3000`.
2.  Log in with your Grafana admin credentials (`GRAFANA_ADMIN_USER` / `GRAFANA_ADMIN_PASSWORD` from `.env`, or default `admin`/`admin` if not set).
3.  Create new dashboards and panels. Use your PostgreSQL data source to query the `rag_interactions` table. Example queries are provided in the steps of this project's development history or can be explored using `pgcli`/`psql`.

## Project Structure
image 


## Development History (Brief Summary)

This project was built iteratively, starting with core RAG logic and gradually integrating components:

1.  Initial RAG script and data loading.
2.  Setting up PostgreSQL with Docker Compose.
3.  Building the Telegram bot structure (`python-telegram-bot`).
4.  Integrating RAG into the bot application (`rag_service.py`, `main.py`).
5.  Containerizing the bot with Docker and Docker Compose.
6.  Integrating database logging for interactions and feedback.
7.  Adding feedback buttons in Telegram.
8.  Integrating Grafana for database monitoring and visualization.

## Future Enhancements

*   Expand the data source with more comprehensive information about NIT Warangal.
*   Implement more sophisticated data parsing and chunking.
*   Explore vector embeddings and vector databases for improved retrieval.
*   Add more advanced prompt engineering techniques.
*   Implement more robust error handling and logging.
*   Explore different LLM providers or models.
*   Deploy to a cloud platform for public access.
*   Add more advanced monitoring metrics and Grafana dashboards.