import tkinter as tk
from tkinter import filedialog
from PIL import Image, ImageTk
import cv2
import numpy as np
from pyzbar.pyzbar import decode as decode_barcode
import os


class BarcodeReaderApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Barcode & QR Code Reader")
        self.root.geometry("1280x720")
        self.root.configure(bg="#2d2d2d")

        # Main container using pack
        self.main_frame = tk.Frame(root, bg="#2d2d2d")
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        # Drop frame - pack in center
        self.drop_frame = tk.Frame(
            self.main_frame,
            bg="#3d3d3d"
        )
        self.drop_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        # Instruction label
        self.lbl_drop = tk.Label(
            self.drop_frame,
            text="Click to upload  •  Drag & drop  •  Ctrl+V to paste",
            font=("Segoe UI", 16),
            bg="#3d3d3d",
            fg="#888888"
        )
        self.lbl_drop.place(relx=0.5, rely=0.4, anchor="center")

        self.drop_frame.bind("<Button-1>", lambda e: self.select_image())
        self.lbl_drop.bind("<Button-1>", lambda e: self.select_image())

        self.root.bind("<Control-v>", self.on_paste)

        # Result frame - initially hidden
        self.result_frame = tk.Frame(self.main_frame, bg="#2d2d2d")

        # Image label
        self.lbl_image = tk.Label(self.result_frame, bg="#1a1a1a")
        self.lbl_image.pack(pady=(10, 5))

        # Results panel
        self.results_panel = tk.Frame(self.result_frame, bg="#2d2d2d", height=150)
        self.results_panel.pack(fill=tk.X, padx=15, pady=5)
        self.results_panel.pack_propagate(False)

        # Status label
        self.lbl_status = tk.Label(
            self.results_panel,
            text="",
            font=("Segoe UI", 12),
            bg="#2d2d2d",
            fg="#888888",
            anchor="w"
        )
        self.lbl_status.pack(fill=tk.X, pady=(0, 5))

        # Results list (vertical scroll)
        self.results_canvas = tk.Canvas(
            self.results_panel,
            bg="#3d3d3d",
            highlightthickness=0
        )
        self.results_scrollbar = tk.Scrollbar(
            self.results_panel,
            orient="vertical",
            command=self.results_canvas.yview
        )
        self.results_canvas.configure(yscrollcommand=self.results_scrollbar.set)

        self.results_canvas.pack(side="left", fill="both", expand=True)
        self.results_scrollbar.pack(side="right", fill="y")

        self.results_inner = tk.Frame(self.results_canvas, bg="#3d3d3d")
        self.results_canvas.create_window((0, 0), window=self.results_inner, anchor="nw")
        self.results_inner.bind("<Configure>",
            lambda e: self.results_canvas.configure(scrollregion=self.results_canvas.bbox("all")))

        # Back button
        self.btn_back = tk.Button(
            self.result_frame,
            text="Process Another Image",
            command=self.show_drop_frame,
            font=("Segoe UI", 12),
            bg="#4a4a4a",
            fg="#ffffff",
            relief="flat",
            padx=20,
            pady=8,
            cursor="hand2"
        )
        self.btn_back.pack(pady=10)

        # Setup drag and drop
        self.root.after(200, self.setup_dnd)
        self.current_results = []

    def setup_dnd(self):
        try:
            from tkinterdnd2 import DND_FILES
            self.root.drop_target_register(DND_FILES)
            self.root.dnd_bind("<<Drop>>", self.on_drop)
        except:
            pass

    def show_drop_frame(self):
        self.result_frame.pack_forget()
        self.drop_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        self.lbl_status.config(text="")

    def show_result_frame(self):
        self.drop_frame.pack_forget()
        self.result_frame.pack(fill=tk.BOTH, expand=True)

    def select_image(self):
        file_path = filedialog.askopenfilename(
            filetypes=[("Images", "*.png *.jpg *.jpeg *.bmp")]
        )
        if file_path:
            self.process_image(file_path)

    def on_paste(self, event=None):
        try:
            from PIL import ImageGrab
            img = ImageGrab.grabclipboard()
            if img:
                self.process_pil_image(img)
        except:
            pass

    def on_drop(self, event):
        files = event.data
        if files:
            for path in files.split():
                path = path.strip().strip("{}")
                if os.path.exists(path) and path.lower().endswith((".png", ".jpg", ".jpeg", ".bmp")):
                    self.process_image(path)
                    break

    def process_pil_image(self, pil_img):
        self.lbl_status.config(text="Analyzing...")
        import threading
        thread = threading.Thread(target=self.scan_and_display, args=(np.array(pil_img),))
        thread.start()

    def process_image(self, file_path):
        self.lbl_status.config(text="Analyzing...")
        import threading
        thread = threading.Thread(target=self._process_async, args=(file_path,))
        thread.start()

    def _process_async(self, file_path):
        image = cv2.imread(file_path)
        self.scan_and_display(image)

    def scan_and_display(self, image):
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        h, w = gray.shape

        detector = cv2.QRCodeDetector()
        qrcodes = detector.detect(gray)

        results = []
        idx = 1

        # QR codes
        if qrcodes is not None and qrcodes[0] is not None and not isinstance(qrcodes[0], bool):
            for i, qr in enumerate(qrcodes[0]):
                points = qrcodes[1][i]
                if points is not None and len(points) > 0:
                    pts = np.int32(points.reshape(-1, 2))
                    
                    x_min = max(0, pts[:, 0].min() - 5)
                    x_max = min(w, pts[:, 0].max() + 5)
                    y_min = max(0, pts[:, 1].min() - 5)
                    y_max = min(h, pts[:, 1].max() + 5)
                    
                    cv2.rectangle(image, (x_min, y_min), (x_max, y_max), (0, 255, 0), 3)
                    cv2.putText(image, str(idx), (x_min + 5, y_min + 20), 
                               cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                    
                    results.append({"index": idx, "text": str(qr), "type": "QR"})
                    idx += 1

        # Barcodes - always try multi-scale
        barcodes = decode_barcode(gray)
        
        h_orig, w_orig = gray.shape
        for scale in [2.0, 2.5, 3.0, 3.5, 4.0]:
            new_w = int(w_orig * scale)
            new_h = int(h_orig * scale)
            if new_w > 2000 or new_h > 2000:
                continue
            scaled = cv2.resize(image, (new_w, new_h))
            scaled_barcodes = decode_barcode(scaled)
            for sb in scaled_barcodes:
                found = False
                for existing in barcodes:
                    existing_barcode = existing['barcode'] if isinstance(existing, dict) else existing
                    if sb.data == existing_barcode.data:
                        found = True
                        break
                if not found:
                    barcodes.append({'barcode': sb, 'scale': scale})

        img_h, img_w = image.shape[:2]

        for b in barcodes:
            if isinstance(b, dict):
                barcode = b['barcode']
                scale = b['scale']
            else:
                barcode = b
                scale = 1.0
            
            points = barcode.polygon
            pts = np.array([[p.x, p.y] for p in points], np.int32)
            
            if scale > 1.0:
                pts = (pts / scale).astype(int)
            
            x_min = max(0, pts[:, 0].min() - 5)
            x_max = min(img_w, pts[:, 0].max() + 5)
            y_min = max(0, pts[:, 1].min() - 5)
            y_max = min(img_h, pts[:, 1].max() + 5)
            
            cv2.rectangle(image, (x_min, y_min), (x_max, y_max), (0, 255, 0), 3)
            cv2.putText(image, str(idx), (x_min + 5, y_min + 20), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            
            results.append({
                "index": idx,
                "text": barcode.data.decode('utf-8'),
                "type": barcode.type
            })
            idx += 1

        # OpenCV barcode detector fallback
        try:
            idx = self.scan_barcodes_opencv(image, results, idx)
        except:
            pass

        self.root.after(0, lambda: self._display_result(image, results))

    def scan_barcodes_opencv(self, image, results, idx):
        detector = cv2.barcode_BarcodeDetector()
        try:
            decoded, points, straight = detector.detectAndDecode(image)
            if decoded:
                for i, (barcode_data, barcode_points) in enumerate(zip(decoded, points)):
                    if barcode_data and len(barcode_data) > 0:
                        pts = np.int32(barcode_points.reshape(-1, 2))
                        x_min = max(0, pts[:, 0].min() - 5)
                        x_max = min(image.shape[1], pts[:, 0].max() + 5)
                        y_min = max(0, pts[:, 1].min() - 5)
                        y_max = min(image.shape[0], pts[:, 1].max() + 5)
                        
                        cv2.rectangle(image, (x_min, y_min), (x_max, y_max), (0, 255, 0), 3)
                        cv2.putText(image, str(idx), (x_min + 5, y_min + 20), 
                                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                        
                        results.append({"index": idx, "text": barcode_data, "type": "Barcode"})
                        idx += 1
        except:
            pass
        return idx

    def _display_result(self, image, results):
        self.display_image(image)
        count = len(results)
        self.lbl_status.config(text=f"Found {count} code{'s' if count != 1 else ''}")
        self.show_results_panel(results)
        self.show_result_frame()
        self.current_results = results

    def show_results_panel(self, results):
        for widget in self.results_inner.winfo_children():
            widget.destroy()

        for r in results:
            row = tk.Frame(self.results_inner, bg="#4a4a4a")
            row.pack(fill=tk.X, pady=2, padx=2)

            tk.Label(row, text=f"[{r['index']}]", font=("Consolas", 11, "bold"),
                    bg="#4a4a4a", fg="#00ff00", width=4).pack(side="left", padx=(8, 4))
            
            tk.Label(row, text=r['type'], font=("Segoe UI", 10),
                   bg="#3a3a3a", fg="#888888", width=10, anchor="w").pack(side="left", padx=(0, 8))
            
            tk.Label(row, text=r['text'], font=("Consolas", 11),
                   bg="#4a4a4a", fg="#ffffff", anchor="w").pack(side="left", fill=tk.X, expand=True, padx=(0, 8))

    def display_image(self, image):
        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        h, w, _ = image_rgb.shape
        
        max_w, max_h = 1150, 500
        
        scale = min(max_w / w, max_h / h, 1.0)
        new_w, new_h = int(w * scale), int(h * scale)
        
        image_resized = cv2.resize(image_rgb, (new_w, new_h))

        photo = ImageTk.PhotoImage(Image.fromarray(image_resized))
        self.lbl_image.config(image=photo)
        self.lbl_image.image = photo


if __name__ == "__main__":
    root = tk.Tk()
    app = BarcodeReaderApp(root)
    root.mainloop()