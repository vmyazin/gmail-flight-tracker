# Gmail Flight Tracker

A Python tool to automatically extract and aggregate flight information from Gmail accounts, creating a consolidated travel history.

## Features

- Multi-account support for processing multiple Gmail accounts
- Automatic flight information extraction from email content
- Support for various airline email formats
- Data export in both CSV and JSON formats
- Incremental processing to avoid duplicate entries
- Secure credential management

## Setup

1. Create a Google Cloud Project:
   - Go to [Google Cloud Console](https://console.cloud.google.com)
   - Create a new project
   - Enable the Gmail API
   - Create OAuth 2.0 credentials
   - Download the credentials JSON file

2. Install Dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Configure Accounts:
   - Place your OAuth credentials in the `credentials/` directory
   - Name the file as `{account_id}_credentials.json` (e.g., `primary_credentials.json`)
   - Update `config/accounts.json` with your account information

## Configuration

The `config/accounts.json` file should contain an array of account configurations:

```json
[
    {
        "account_id": "primary",
        "email": "your.email@gmail.com",
        "last_processed_date": null
    }
]
```

## Usage

Run the flight tracker:

```bash
python src/main.py
```

The script will:
1. Process each configured account
2. Extract flight information from emails
3. Save the data to both CSV and JSON formats in the `data/` directory

## Output

The tool generates two types of output files in the `data/` directory:
- `flights_YYYYMMDD_HHMMSS.csv`: CSV format for easy spreadsheet analysis
- `flights_YYYYMMDD_HHMMSS.json`: JSON format for programmatic access

## Directory Structure

```
gmail-flight-tracker/
├── config/
│   └── accounts.json
├── credentials/
│   └── primary_credentials.json
├── data/
│   └── flights_*.{csv,json}
├── logs/
├── src/
│   ├── auth/
│   │   ├── google_auth.py
│   │   └── gmail_client.py
│   ├── parsers/
│   │   └── flight_parser.py
│   └── main.py
├── tests/
├── requirements.txt
└── README.md
```

## Security

- OAuth credentials are stored locally in the `credentials/` directory
- Access tokens are securely cached
- No email content is stored, only extracted flight information
- Credentials can be revoked at any time through Google Account settings

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.
