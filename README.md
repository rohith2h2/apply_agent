# Job Application Agent

## Overview
An AI-powered personal agent system that automates job applications by learning from your application patterns. This project consists of two main components:

1. **Web Application & API**: A Flask-based web application with a backend API that manages user profiles, learning data, and application tracking.
2. **Chrome Extension**: A browser extension that captures your form submissions and learns your application patterns.

## Key Features

### Web Application
- **User Profile Management**: Store and manage your personal and professional information
- **Learning Data Analysis**: View and analyze the data collected during learning sessions
- **Application Tracking**: Track your job applications and their statuses

### Chrome Extension
- **Learning Mode**: Observes how you fill out job application forms
- **Form Field Detection**: Automatically detects and categorizes form fields
- **Secure Data Storage**: Stores your data locally in the browser with optional sync to backend
- **Visual Indicators**: Provides visual feedback when recording is active

## Project Structure

### Web Application (`/apply_agent`)
- `app.py`: Main application entry point
- `config.json`: Configuration settings
- `/src`: Core application logic
  - `/utils`: Helper functions
  - `/data_collection`: Data processing components
  - `/ai_model`: Machine learning components
- `/ui`: User interface
  - `app.py`: Flask routes and API endpoints
  - `/templates`: HTML templates
  - `/static`: CSS, JavaScript and other static files

### Chrome Extension (`/apply_agent_extension`)
- `manifest.json`: Extension configuration
- `/background`: Background service worker
  - `background.js`: Manages state and communication
- `/content`: Content scripts
  - `observer.js`: Form field detection and recording
- `/popup`: Extension popup UI
  - `popup.html`: Popup interface
  - `popup.js`: Popup interaction logic
  - `popup.css`: Styling for the popup

## Installation

### Web Application

1. Clone this repository
```bash
git clone https://github.com/yourusername/job-application-agent.git
cd job-application-agent
```

2. Create a virtual environment and install dependencies
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

3. Configure the application
```bash
# Edit config.json with your settings
```

4. Run the application
```bash
python app.py
```
The web application will be available at http://127.0.0.1:5000

### Chrome Extension

1. Open Chrome and navigate to `chrome://extensions/`
2. Enable "Developer mode" (toggle in top right)
3. Click "Load unpacked" and select the `apply_agent_extension` directory
4. The extension icon should appear in your browser toolbar

## Usage

### Learning Mode

1. Click the extension icon in your browser toolbar
2. Click "Start Learning Mode" 
3. Fill out a job application form as you normally would
4. The extension will collect information about the fields and your inputs
5. Click "Stop Learning" when you're done
6. Repeat for 2-3 applications for best results

### Viewing Collected Data

1. Open the web application at http://127.0.0.1:5000
2. Navigate to the "Learning" section to see your collected data
3. You can also export data directly from the extension by clicking "Export Collected Data"

## Development

### API Endpoints

The web application provides the following API endpoints for the Chrome extension:

- `POST /api/start-learning`: Begin a learning session
- `POST /api/finish-learning`: Complete a learning session
- `GET /api/learning-sessions`: Get all learning sessions
- `GET /api/learning-status`: Get current learning status
- `GET /api/active-learning-session`: Get details of active session
- `POST /api/analyze-learning`: Analyze collected learning data

### Extension Communication

The extension uses Chrome's messaging system for internal communication:
- Content script to background script: Send form field data
- Background script to popup: Send status updates
- Popup to content script: Control recording

## Security Considerations

- Personal data is primarily stored in the browser's local storage
- Communication with the backend is optional
- No passwords or sensitive authentication data is collected
- Data can be exported and deleted at any time

## Future Enhancements

- Implement the autofill functionality
- Add user authentication
- Improve field detection accuracy
- Add support for more complex form types
- Implement AI-driven response customization

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details. 