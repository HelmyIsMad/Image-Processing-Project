# Barcode & QR Code Reader

A Python GUI application for detecting and decoding barcodes and QR codes from images.

## Features

- **Multiple Input Methods**: Load images via click, drag & drop, or Ctrl+V paste
- **QR Code Detection**: Using OpenCV's QRCodeDetector
- **Barcode Detection**: Using pyzbar library with multi-scale detection for small barcodes
- **Visual Highlighting**: Green rectangles around detected codes with index numbers
- **Results Panel**: Scrollable list showing all decoded text

## Installation

```bash
pip install -r requirements.txt
```

## Usage

```bash
python main.py
```

## Requirements

- Python 3.7+
- numpy
- opencv-python
- pillow
- pyzbar
- tkinterdnd2

## Project Structure

```
.
├── main.py              # Main application
├── requirements.txt     # Dependencies
├── workflow.md         # Documentation
└── Samples/            # Test images
```

## License

MIT