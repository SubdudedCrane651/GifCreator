import sys
import os
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QListWidget, QFileDialog, QSpinBox, QMessageBox
)
from PyQt6.QtGui import QPixmap
from PyQt6.QtCore import Qt
from PIL import Image


class GifCreator(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Animated GIF Creator (PyQt6)")
        self.frames = []  # list of (filepath, duration_ms)

        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)

        # Frame list + preview
        list_preview_layout = QHBoxLayout()
        main_layout.addLayout(list_preview_layout)

        self.list_widget = QListWidget()
        self.list_widget.currentRowChanged.connect(self.update_preview)
        list_preview_layout.addWidget(self.list_widget, 1)

        self.preview_label = QLabel("Preview")
        self.preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview_label.setMinimumSize(300, 200)
        list_preview_layout.addWidget(self.preview_label, 2)

        # Controls
        controls_layout = QHBoxLayout()
        main_layout.addLayout(controls_layout)

        self.add_button = QPushButton("Add Frame(s)")
        self.add_button.clicked.connect(self.add_frames)
        controls_layout.addWidget(self.add_button)

        self.remove_button = QPushButton("Remove Selected")
        self.remove_button.clicked.connect(self.remove_selected)
        controls_layout.addWidget(self.remove_button)

        self.duration_label = QLabel("Frame duration (ms):")
        controls_layout.addWidget(self.duration_label)

        self.duration_spin = QSpinBox()
        self.duration_spin.setRange(10, 10000)
        self.duration_spin.setValue(100)
        controls_layout.addWidget(self.duration_spin)

        self.save_button = QPushButton("Save GIF")
        self.save_button.clicked.connect(self.save_gif)
        main_layout.addWidget(self.save_button)

    def add_frames(self):
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "Select frame images",
            "",
            "Images (*.png *.jpg *.jpeg *.bmp *.gif);;All Files (*)"
        )
        if not files:
            return

        duration = self.duration_spin.value()
        for f in files:
            self.frames.append((f, duration))
            self.list_widget.addItem(f)

        if self.list_widget.count() == 1:
            self.list_widget.setCurrentRow(0)

    def remove_selected(self):
        row = self.list_widget.currentRow()
        if row < 0:
            return
        self.list_widget.takeItem(row)
        self.frames.pop(row)
        self.update_preview(self.list_widget.currentRow())

    def update_preview(self, row):
        if row < 0 or row >= len(self.frames):
            self.preview_label.setPixmap(QPixmap())
            self.preview_label.setText("Preview")
            return

        path, _ = self.frames[row]
        pix = QPixmap(path)
        if not pix.isNull():
            scaled = pix.scaled(
                self.preview_label.size(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            self.preview_label.setPixmap(scaled)
        else:
            self.preview_label.setText("Cannot load image")

    def save_gif(self):
        if not self.frames:
            QMessageBox.warning(self, "No frames", "Add at least one frame first.")
            return

        save_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save GIF",
            "animation.gif",
            "GIF Files (*.gif);;All Files (*)"
        )
        if not save_path:
            return

        images = []
        durations = []
        for path, duration in self.frames:
            img = Image.open(path).convert("RGBA")
            images.append(img)
            durations.append(duration)

        first = images[0]
        extra = images[1:] if len(images) > 1 else []

        try:
            first.save(
                save_path,
                save_all=True,
                append_images=extra,
                loop=0,
                duration=durations
            )
            QMessageBox.information(self, "Saved", f"GIF saved to:\n{save_path}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save GIF:\n{e}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = GifCreator()
    win.resize(800, 500)
    win.show()
    sys.exit(app.exec())