# Barcode & QR Code Reader - Workflow Documentation

## 1. Functional Specification

### Project Objective
A Python-based GUI application that detects and decodes barcodes and QR codes from images. Users can load images via click, drag & drop, or clipboard paste. The app identifies each barcode/QR code, highlights it with a green rectangle, and displays the decoded text in a results panel.

### Feature List
- Load images via file dialog (click)
- Load images via clipboard paste (Ctrl+V)
- Load images via drag and drop
- QR code detection using OpenCV
- Barcode detection using pyzbar library
- Multi-scale detection for small barcodes
- Visual highlighting with green rectangles
- Indexed labels on detected codes
- Results panel showing all decoded text
- Responsive GUI with background processing

### Tools & Libraries
- **Tkinter** - GUI framework
- **OpenCV (cv2)** - QR code detection
- **pyzbar** - Barcode detection
- **Pillow (PIL)** - Image handling and display
- **NumPy** - Matrix/array operations
- **tkinterdnd2** - Drag and drop support

---

## 2. Theoretical Background

### Algorithm: QR Code Detection (OpenCV)
OpenCV's QRCodeDetector uses pattern recognition algorithms to detect QR codes in images. The detector returns:
- Decoded string data
- Corner points of the QR code bounding box

### Algorithm: Barcode Detection (pyzbar)
pyzbar uses the zbar library for barcode scanning. It supports multiple barcode formats (EAN-13, EAN-8, UPC, Code128, Code39, QR).

### Multi-Scale Detection
pyzbar has minimum size requirements for reliable detection. Small barcodes (~100px wide) may not be detected at original scale.
- Detection works at scales 3.0-4.0x for small barcodes
- Complexity: O(k × n²) where k is number of scales tried

---

## 3. System Architecture

### Class Structure
```
BarcodeReaderApp
├── UI Components
│   ├── drop_frame - Input area
│   ├── result_frame - Output area
│   └── results_panel - Decoded text list
└── Methods
    ├── select_image() - File dialog
    ├── on_paste() - Clipboard
    ├── on_drop() - Drag & drop
    ├── process_image() - Load from file
    ├── process_pil_image() - Load from PIL
    └── scan_and_display() - Detection
```

### Data Flow
1. User selects image (file/paste/drop)
2. Image loaded as NumPy array
3. Converted to grayscale for detection
4. QR codes detected via OpenCV
5. Barcodes detected via pyzbar (multi-scale)
6. Coordinates converted back to original scale
7. Results drawn on image
8. Decoded text shown in panel
9. Image displayed in GUI

---

## 4. Results & Test Cases

### Test Cases

| Test Case | Input Type | Expected Result | Status |
|----------|----------|--------------|--------|
| Load JPG | .jpg file | Display & detect | ✓ Works |
| Load PNG | .png file | Display & detect | ✓ Works |
| Load PNG with QR | .png with QR | Display, detect QR | ✓ Works |
| Load PNG with barcode | .png with barcode | Display, detect barcode | ✓ Works |
| Paste from clipboard | Image in clipboard | Display & detect | ✓ Works |
| Drag and drop | Image file | Display & detect | ✓ Works |
| No codes in image | Image without codes | Show "0 codes" | ✓ Works |
| Large image | 4K image | Scale to fit window | ✓ Works |
| Small barcode | ~100px barcode | Multi-scale detect | ✓ Works |

### Edge Cases
- No QR codes found - OpenCV returns tuple with boolean (False, None, None)
- No barcodes found - Empty list
- Large images - Scaled down to fit window
- pyzbar objects - Cannot add custom attributes (use dict wrapper)

---

## 5. Summary of Challenges

### Challenge 1: Barcode Not Detected
**Problem**: Small barcodes not detected at original scale
**Solution**: Multi-scale detection - resize image at 2.0x to 4.0x before detection

### Challenge 2: Coordinate Mapping
**Problem**: Coordinates from scaled image, drew on original
**Solution**: Divide coordinates by scale before drawing: `pts = (pts / scale).astype(int)`

### Challenge 3: Duplicate Detection
**Problem**: Same barcode detected at multiple scales
**Solution**: Check for duplicates before adding: `if not any(sb.data == b.data for b in barcodes)`

### Challenge 4: Immutable Objects
**Problem**: pyzbar Decoded objects don't allow custom attributes
**Solution**: Use dict wrapper: `{'barcode': sb, 'scale': scale}`

---

## Architecture

### 1. Image Input

The user can input an image in three ways:

#### Click to Upload
```python
def select_image(self):
    file_path = filedialog.askopenfilename(
        filetypes=[("Images", "*.png *.jpg *.jpeg *.bmp")]
    )
    if file_path:
        self.process_image(file_path)
```

#### Ctrl+V Paste
```python
def on_paste(self, event=None):
    try:
        from PIL import ImageGrab
        img = ImageGrab.grabclipboard()  # Get image from clipboard
        if img:
            self.process_pil_image(img)
    except:
        pass
```

#### Drag and Drop
```python
def on_drop(self, event):
    files = event.data
    for path in files.split():
        path = path.strip().strip('{}')
        if os.path.exists(path):
            self.process_image(path)
            break
```

### 2. Processing (Background Thread)

Both input methods call processing in a separate thread to keep the GUI responsive:

```python
def process_image(self, file_path):
    self.lbl_status.config(text="Analyzing...")
    # Run in background thread
    import threading
    thread = threading.Thread(target=self._process_async, args=(file_path,))
    thread.start()

def _process_async(self, file_path):
    image = cv2.imread(file_path)
    self.scan_and_display(image)
```

### 3. Detection Algorithm

This is the core detection logic:

#### Step 3.1: QR Code Detection (Using OpenCV)
```python
def scan_and_display(self, image):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    h, w = gray.shape

    detector = cv2.QRCodeDetector()
    qrcodes = detector.detect(gray)

    results = []
    idx = 1

    # OpenCV QR detector returns: (decoded_strings, points_array)
    if qrcodes is not None and qrcodes[0] is not None:
        for i, qr in enumerate(qrcodes[0]):
            points = qrcodes[1][i]
            if points is not None:
                pts = np.int32(points.reshape(-1, 2))
                
                # Draw rectangle with padding
                x_min = max(0, pts[:, 0].min() - 5)
                x_max = min(w, pts[:, 0].max() + 5)
                y_min = max(0, pts[:, 1].min() - 5)
                y_max = min(h, pts[:, 1].max() + 5)
                
                cv2.rectangle(image, (x_min, y_min), (x_max, y_max), (0, 255, 0), 3)
                cv2.putText(image, str(idx), (x_min + 5, y_min + 20), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                
                result = {"index": idx, "text": str(qr), "type": "QR"}
                results.append(result)
                idx += 1
```

#### Step 3.2: Barcode Detection (Using pyzbar)

Single-scale detection often fails for small barcodes. We use multi-scale detection:

```python
# Try multiple scales (barcodes may be too small at original scale)
h_orig, w_orig = gray.shape
for scale in [2.0, 2.5, 3.0, 3.5, 4.0]:
    new_w = int(w_orig * scale)
    new_h = int(h_orig * scale)
    if new_w > 2000 or new_h > 2000:
        continue
    
    # Resize and detect on larger image
    scaled = cv2.resize(image, (new_w, new_h))
    scaled_barcodes = decode(scaled)
    
    # Add unique barcodes (avoid duplicates)
    for sb in scaled_barcodes:
        if not any(sb.data == b.data for b in barcodes):
            barcodes.append({
                'barcode': sb,
                'scale': scale
            })

# Later when drawing, convert coordinates back:
for b in barcodes:
    if isinstance(b, dict):
        barcode = b['barcode']
        scale = b['scale']  # e.g., 3.0 means detected at 3x size
    else:
        barcode = b
        scale = 1.0
    
    pts = np.array([[p.x, p.y] for p in barcode.polygon], np.int32)
    
    # Convert from scaled coordinates to original
    if scale > 1.0:
        pts = (pts / scale).astype(int)
    
    # Now draw...
```

**Why Multi-Scale?**
- pyzbar needs barcodes to be large enough to detect
- Small barcodes (~100px wide) are detected at scales 3.0-4.0x
- This is why we resize the image before detection

### 4. Display Results

#### Draw on Image
```python
cv2.rectangle(image, (x_min, y_min), (x_max, y_max), (0, 255, 0), 3)
cv2.putText(image, str(idx), (x_min + 5, y_min + 20), 
           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
```

#### Show in Panel (Hybrid Approach)

For small images, labels might not fit. We show them in a panel:

```python
def show_results_panel(self, results):
    for widget in self.results_frame_inner.winfo_children():
        widget.destroy()
    
    for r in results:
        frame = tk.Frame(self.results_frame_inner, bg="#e0e0e0")
        frame.pack(side=tk.LEFT, padx=5)
        
        tk.Label(frame, text=f"[{r['index']}]", 
                font=("Arial", 10, "bold"),
                fg="green").pack(side=tk.LEFT)
        
        tk.Label(frame, text=r['text'],
                font=("Arial", 10),
                width=25).pack(side=tk.LEFT)
```

#### Resize Image to Fit Window

```python
def display_image(self, image):
    image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    h, w, _ = image_rgb.shape
    
    max_w, max_h = 1260, 580
    
    # Scale down if needed (never scale up)
    scale = min(max_w / w, max_h / h, 1.0)
    image_resized = cv2.resize(image_rgb, 
                              (int(w * scale), int(h * scale)))
    
    photo = ImageTk.PhotoImage(Image.fromarray(image_resized))
    self.lbl_image.config(image=photo)
```

---

## Key Variables Explained

| Variable | Type | Description |
|---------|------|------------|
| image | ndarray | Original BGR image |
| gray | ndarray | Grayscale version |
| qrcodes | tuple | OpenCV QR results |
| barcodes | list | pyzbar results |
| scale | float | Multi-scale factor (1.0-4.0) |
| results | list | Dict with index, text, type |
| pts | ndarray | Corner points of detected code |

---

## Dependencies

Install all dependencies using:
```
pip install -r requirements.txt
```

**Required packages:**
- `numpy==2.4.4` - Array operations
- `opencv-python==4.13.0.92` - Image processing & QR detection
- `pillow==12.2.0` - Image display
- `pyzbar==0.1.9` - Barcode detection
- `tkinterdnd2==0.4.3` - Drag and drop support

---

## Common Issues & Solutions

### Issue 1: Barcode Not Detected
**Cause**: Barcode too small
**Solution**: Multi-scale detection (try scales 2.0-4.0x)

### Issue 2: Wrong Coordinates
**Cause**: Coordinates from scaled image, drawing on original
**Solution**: Divide coordinates by scale before drawing
```python
pts = (pts / scale).astype(int)
```

### Issue 3: Duplicate Barcodes
**Cause**: Same barcode detected at multiple scales
**Solution**: Check for duplicates before adding
```python
if not any(sb.data == b.data for b in barcodes):
    barcodes.append(sb)
```

### Issue 4: pyzbar Objects Can't Store Custom Attributes
**Cause**: Decoded objects are immutable
**Solution**: Use a dict wrapper
```python
barcodes.append({
    'barcode': sb,
    'scale': scale
})
```