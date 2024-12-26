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
- Two-step process:
  1. Fetch and store raw emails
  2. Process stored emails to extract flight information
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

The tool now supports a two-step process for better control and debugging:

### 1. Fetch Emails

To fetch emails and store them locally:

```bash
python src/main.py --year 2024 --days 365 --fetch-only
```

This will:
- Fetch flight-related emails from Gmail
- Store them in `data/raw_emails/emails_YYYY_TIMESTAMP.json`
- Not process the emails yet

### 2. Process Stored Emails

To process previously stored emails:

```bash
python src/main.py --year 2024 --process-only
```

This will:
- Load emails from storage
- Extract flight information
- Save results to `data/processed/flights_YYYY.json`
- Display formatted results

### Combined Operation

To fetch and process in one go (default behavior):

```bash
python src/main.py --year 2024 --days 365
```

### Command Line Options

- `--year`: Year to search for flights (default: current year)
- `--days`: Number of days to look forward from start of year (default: 365)
- `--use-sample`: Use sample data instead of Gmail API
- `--fetch-only`: Only fetch and store emails, do not process them
- `--process-only`: Only process stored emails, do not fetch new ones

## First Run

On the first run, the script will:
1. Open your default web browser
2. Ask you to log in to your Google account
3. Request permission to read your Gmail messages
4. Save the authorization token for future use

The token will be stored in `credentials/token.pickle` and will be reused for subsequent runs.

## Sample Data

The repository includes sample email data in the `data/sample` directory for testing purposes. Use the `--use-sample` flag to process these instead of fetching from Gmail.

## Project Structure

```
gmail-flight-tracker/
├── data/
│   ├── raw_emails/     # Stored raw emails
│   ├── processed/      # Processed flight information
│   └── sample/         # Sample email data
├── src/
│   ├── gmail_client.py # Gmail API client
│   ├── main.py        # Main entry point
│   ├── process_emails.py # Email processing script
│   ├── storage/       # Email storage module
│   └── parsers/       # Email parsers
└── README.md
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.
