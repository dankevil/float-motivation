# Float Motivation

A motivational widget application that helps keep you inspired and focused. This application provides motivational quotes and productivity tools to help you stay motivated throughout your day.

## Features

- Motivational quotes displayed in a floating widget
- Customizable quote intervals
- Minimal floating icon mode for distraction-free work
- Simple and clean interface
- Quote management for adding personal quotes
- Persistent configuration

## Requirements

- Python 3.6+
- PySide6 (Qt for Python)

## Installation

1. Clone the repository:
```bash
git clone https://github.com/dankevil/float-motivation.git
cd float-motivation
```

2. Install dependencies:
```bash
pip install PySide6
```

## Usage

Run the application from the command line:

```bash
python main.py
```

### Functionality

- **Floating Icon Mode**: Hover over the icon to display the quote widget
- **Quote Display**: Automatically cycles through quotes at a configurable interval
- **Settings**: Configure quote source, display interval, and appearance
- **Quote Management**: Add, edit, or remove quotes from your collection

## Building an Executable

To create a standalone executable that doesn't require Python to be installed:

1. Install PyInstaller:
```bash
pip install pyinstaller
```

2. Build the executable:
```bash
# For Windows
pyinstaller --name="Float-Motivation" --windowed --icon=assets/buddha.png --add-data="assets;assets" --add-data="quotes.csv;." main.py

# For macOS
pyinstaller --name="Float-Motivation" --windowed --icon=assets/buddha.png --add-data="assets:assets" --add-data="quotes.csv:." main.py

# For Linux
pyinstaller --name="Float-Motivation" --windowed --icon=assets/buddha.png --add-data="assets:assets" --add-data="quotes.csv:." main.py
```

3. The executable will be created in the `dist/Float-Motivation` directory.

## Configuration

The application stores its configuration in the user's home directory. You can modify settings through the application's interface.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is open source and available under the [MIT License](LICENSE). 