# Gmail Flight Tracker

A Python tool to automatically extract and aggregate flight information from Gmail, creating a consolidated travel history with minimal manual input.

## Features

- Automatically fetches flight-related emails from Gmail
- Supports multiple email formats (VietJet Air, Trip.com, Booking.com)
- Extracts key flight information:
  - Flight numbers
  - Departure/arrival airports
  - Times and dates
  - Airlines
  - Duration
- Deduplicates flight entries
- Provides clean, formatted output

## Setup

1. Clone the repository:
```bash
git clone https://github.com/yourusername/gmail-flight-tracker.git
cd gmail-flight-tracker
```

2. Create and activate a virtual environment:
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up Google Cloud Project and Gmail API:

   a. Go to the [Google Cloud Console](https://console.cloud.google.com/)
   
   b. Create a new project or select an existing one
   
   c. Enable the Gmail API:
      - Go to "APIs & Services" > "Library"
      - Search for "Gmail API"
      - Click "Enable"
   
   d. Create credentials:
      - Go to "APIs & Services" > "Credentials"
      - Click "Create Credentials" > "OAuth client ID"
      - Choose "Desktop app" as the application type
      - Download the credentials file
   
   e. Place the downloaded credentials file in the `credentials` directory:
      ```bash
      mkdir -p credentials
      mv path/to/downloaded/credentials.json credentials/
      ```

## Usage

Run the script with the following options:

```bash
# Search for flights in the current year
python src/main.py

# Search for flights in a specific year
python src/main.py --year 2024

# Search for flights in a specific period
python src/main.py --year 2024 --days 90

# Use sample data instead of Gmail API
python src/main.py --use-sample
```

### Command-line Arguments

- `--year`: Year to search for flights (default: current year)
- `--days`: Number of days to look forward from start of year (default: 365)
- `--use-sample`: Use sample data instead of Gmail API

## First Run

On the first run, the script will:
1. Open your default web browser
2. Ask you to log in to your Google account
3. Request permission to read your Gmail messages
4. Save the authorization token for future use

The token will be stored in `credentials/token.pickle` and will be reused for subsequent runs.

## Sample Data

The repository includes sample email data in the `data/sample` directory for testing purposes. Use the `--use-sample` flag to process these instead of fetching from Gmail.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.
