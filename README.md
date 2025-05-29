# Bot Help Application

## Overview
This project is a Python-based application designed to assist users by providing contextual search results from a text file (`kte.txt`) based on selected text. The application uses `tkinter` for GUI elements and integrates with `pynput` for mouse and keyboard event handling.

## Features
- **Text Search**: Automatically searches for selected text in the `kte.txt` file and displays relevant results.
- **Popup Display**: Shows search results in a popup window with navigation support.
- **Accessibility Permissions**: Checks and guides users to enable accessibility permissions on macOS.
- **Logging**: Detailed logging for debugging and error tracking.

## Requirements
- Python 3.13 or higher
- macOS (for accessibility permission checks)

### Python Libraries
The following Python libraries are required:
- `tkinter`
- `pyperclip`
- `pynput`
- `logging`

## Installation
1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd bot_help
   ```
2. Set up a virtual environment:
   ```bash
   python3 -m venv env
   source env/bin/activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage
1. Run the application:
   ```bash
   python main.py
   ```
2. Select text using your mouse. The application will automatically search for the selected text in `kte.txt` and display results in a popup window.

## File Structure
- `main.py`: Main application logic.
- `kte.txt`: Text file used for searching.
- `requirements.txt`: List of dependencies.
- `env/`: Virtual environment folder.

## Accessibility Permissions (macOS)
If you encounter permission issues, follow these steps:
1. Open **System Preferences** > **Security & Privacy** > **Privacy** > **Accessibility**.
2. Click the lock icon to make changes.
3. Add and enable **Terminal** or **Python** in the list.
4. Restart the application.

## Logging
Logs are saved to `debug.log` and also displayed in the console. This includes:
- Application start and stop events.
- Errors and exceptions.
- User interactions.

## Limitations
- The application is designed for macOS and may not work on other operating systems.
- The search functionality is limited to the `kte.txt` file.

## License
This project is licensed under the MIT License.

## Contributing
Feel free to submit issues or pull requests to improve the application.

## Contact
For questions or support, contact [your-email@example.com].
