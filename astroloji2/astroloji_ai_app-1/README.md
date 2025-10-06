# Astrology AI Application

This project is an Astrology AI application built using FastAPI. It provides horoscope predictions based on user input, utilizing astrological calculations and a retrieval-augmented generation (RAG) service for commentary.

## Project Structure

```
astroloji_ai_app
├── src
│   ├── astroloji_ai
│   │   ├── api
│   │   │   └── main.py          # Entry point of the FastAPI application
│   │   ├── config
│   │   │   └── settings.py      # Configuration settings for the application
│   │   ├── core
│   │   │   ├── astrology.py      # Astrology calculations
│   │   │   └── ephemeris.py      # Ephemeris service for astrological positions
│   │   ├── monitoring
│   │   │   └── metrics.py        # Application performance metrics
│   │   ├── rag
│   │   │   └── client.py         # RAG client for querying astrological commentary
│   │   ├── schemas
│   │   │   └── horoscope.py      # Pydantic models for horoscope requests and responses
│   │   └── utils
│   │       └── logging.py        # Logging utility functions
│   └── __init__.py               # Marks the directory as a Python package
├── requirements.txt               # Project dependencies
├── README.md                      # Project documentation
└── .gitignore                     # Files and directories to ignore in version control
```

## Setup Instructions

1. Clone the repository:
   ```
   git clone <repository-url>
   cd astroloji_ai_app
   ```

2. Create a virtual environment:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   ```

3. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

4. Run the application:
   ```
   uvicorn src.astroloji_ai.api.main:app --host 0.0.0.0 --port 8000 --reload
   ```

## Usage

Once the application is running, you can access the API at `http://localhost:8000`. The following endpoints are available:

- **GET /health**: Check the health status of the application.
- **POST /horoscope**: Submit a horoscope request with user details and receive a horoscope prediction.

## Contributing

Contributions are welcome! Please open an issue or submit a pull request for any enhancements or bug fixes.

## License

This project is licensed under the MIT License. See the LICENSE file for more details.