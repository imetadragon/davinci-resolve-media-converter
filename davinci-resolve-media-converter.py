#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DaVinci Resolve Medya Dönüştürücü (PyQt6 GUI - macOS Dark Theme)
Linux/Cross-platform DaVinci Resolve Uyumlu Medya Dönüştürücü.
"""

import sys
import os
import subprocess
import time
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QSettings, QLocale
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QListWidget, QListWidgetItem, QPushButton, QProgressBar,
    QFileDialog, QMessageBox, QFrame, QComboBox, QCheckBox
)
from PyQt6.QtGui import QDragEnterEvent, QDropEvent

# Dil sözlükleri (Türkçe ve İngilizce)
TRANSLATIONS = {
    "tr": {
        "window_title": "DaVinci Resolve Medya Dönüştürücü",
        "drop_text": "Pencerenin Herhangi Bir Yerine Dosyaları Sürükleyin\nveya Tıklayıp Seçin",
        "select_files": "Video Dosyaları Seç",
        "mode_video": "Mod: Video ve Ses Yeniden Kodlanıyor (MPEG-4)",
        "mode_audio": "Varsayılan Mod: Sadece Ses (AAC to PCM)",
        "clear_list": "Listeyi Temizle",
        "video_checkbox": "Videoyu da Yeniden Kodla",
        "codec_mpeg4": "MPEG-4 (Varsayılan)",
        "codec_dnxhr_lb": "DNxHR LB (Profesyonel - Az Alan Kaplar)",
        "codec_dnxhr_hq": "DNxHR HQ (Profesyonel - Yüksek Kalite)",
        "convert_btn": "Dönüştürmeyi Başlat",
        "stop_btn": "Dönüştürmeyi Durdur",
        "desktop_tooltip": "Menü Kısayolu Oluştur",
        "lang_tooltip": "İngilizce'ye Geç",
        "waiting": "Bekliyor",
        "converting": "Dönüştürülüyor...",
        "completed": "Tamamlandı ✅",
        "skipped": "Atlandı (Çıktı Zaten Var)",
        "cancelled": "İptal Edildi 🛑",
        "error_ffmpeg": "FFmpeg Hatası",
        "error_prefix": "Hata: ",
        "warning": "Uyarı",
        "info": "Bilgi",
        "success": "Başarılı",
        "clear_running_warning": "İşlem devam ederken liste temizlenemez.",
        "add_files_prompt": "Lütfen önce en az bir medya dosyası ekleyin.",
        "output_exists_msg": "adet çıktı dosyası ./output/ dizinlerinde zaten mevcut:\n\nVar olan dosyaların üzerine yazmak istiyor musunuz?",
        "output_exists_title": "Çıktı Dosyaları Mevcut",
        "desktop_success": "Uygulama menü kısayolu başarıyla oluşturuldu:\n{}",
        "desktop_error": "Masaüstü kısayolu oluşturulurken hata oluştu:\n{}",
        "remove_tooltip": "Bu dosyayı listeden kaldır",
    },
    "en": {
        "window_title": "DaVinci Resolve Media Converter",
        "drop_text": "Drag and Drop Files Anywhere Here\nor Click to Select",
        "select_files": "Select Video Files",
        "mode_video": "Mode: Video and Audio Re-encoded (MPEG-4)",
        "mode_audio": "Default Mode: Audio Only (AAC to PCM)",
        "clear_list": "Clear List",
        "video_checkbox": "Re-encode Video",
        "codec_mpeg4": "MPEG-4 (Default)",
        "codec_dnxhr_lb": "DNxHR LB (Professional - Low Size)",
        "codec_dnxhr_hq": "DNxHR HQ (Professional - High Quality)",
        "convert_btn": "Start Conversion",
        "stop_btn": "Stop Conversion",
        "desktop_tooltip": "Create Menu Shortcut",
        "lang_tooltip": "Switch to Turkish",
        "waiting": "Waiting",
        "converting": "Converting...",
        "completed": "Completed ✅",
        "skipped": "Skipped (Output Exists)",
        "cancelled": "Cancelled 🛑",
        "error_ffmpeg": "FFmpeg Error",
        "error_prefix": "Error: ",
        "warning": "Warning",
        "info": "Information",
        "success": "Success",
        "clear_running_warning": "Cannot clear the list while conversion is in progress.",
        "add_files_prompt": "Please add at least one media file first.",
        "output_exists_msg": "output files already exist in ./output/ directories:\n\nDo you want to overwrite existing files?",
        "output_exists_title": "Output Files Exist",
        "desktop_success": "Menu shortcut successfully created:\n{}",
        "desktop_error": "Error occurred while creating desktop shortcut:\n{}",
        "remove_tooltip": "Remove this file from list",
    }
}


class ConversionWorker(QThread):
    progress_signal = pyqtSignal(int, str, str)
    finished_signal = pyqtSignal()

    def __init__(self, file_queue, convert_video=True, video_codec="mpeg4", overwrite=False, lang="tr"):
        super().__init__()
        self.file_queue = file_queue
        self.convert_video = convert_video
        self.video_codec = video_codec
        self.overwrite = overwrite
        self.lang = lang
        self.t = TRANSLATIONS[lang]
        self.is_cancelled = False
        self.process = None

    def run(self):
        for idx, file_path in self.file_queue:
            if self.is_cancelled:
                break

            folder, filename = os.path.split(file_path)
            name, _ = os.path.splitext(filename)

            output_dir = os.path.join(folder, "output")
            os.makedirs(output_dir, exist_ok=True)

            ext = ".mp4" if self.video_codec == "mpeg4" else ".mov"
            output_path = os.path.join(output_dir, f"{name}{ext}")

            if os.path.exists(output_path) and os.path.getsize(output_path) > 0 and not self.overwrite:
                self.progress_signal.emit(idx, file_path, self.t["skipped"])
                continue

            self.progress_signal.emit(idx, file_path, self.t["converting"])

            cmd = ["ffmpeg", "-y", "-i", file_path]

            if self.convert_video:
                if self.video_codec == "mpeg4":
                    cmd.extend(["-c:v", "mpeg4", "-q:v", "2", "-pix_fmt", "yuv420p"])
                elif self.video_codec == "dnxhr_hq":
                    cmd.extend(["-c:v", "dnxhd", "-profile:v", "dnxhr_hq", "-pix_fmt", "yuv422p"])
                elif self.video_codec == "dnxhr_lb":
                    cmd.extend(["-c:v", "dnxhd", "-profile:v", "dnxhr_lb", "-pix_fmt", "yuv422p"])

                # Tüm video modlarında ses artık pcm_s16le olarak kodlanıyor
                cmd.extend(["-c:a", "pcm_s16le", "-f", "mp4" if self.video_codec == "mpeg4" else "mov"])
            else:
                cmd.extend(["-c:v", "copy", "-c:a", "pcm_s16le", "-f", "mov"])

            cmd.append(output_path)

            try:
                self.process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )

                while self.process.poll() is None:
                    if self.is_cancelled:
                        self.process.terminate()
                        self.process.wait()
                        if os.path.exists(output_path):
                            try:
                                os.remove(output_path)
                            except Exception:
                                pass
                        self.progress_signal.emit(idx, file_path, self.t["cancelled"])
                        self.finished_signal.emit()
                        return
                    time.sleep(0.1)

                if self.process.returncode == 0 and os.path.exists(output_path) and os.path.getsize(output_path) > 0:
                    self.progress_signal.emit(idx, file_path, self.t["completed"])
                else:
                    if os.path.exists(output_path):
                        os.remove(output_path)
                    _, stderr_data = self.process.communicate()
                    err_msg = stderr_data.splitlines()[-1] if stderr_data else self.t["error_ffmpeg"]
                    self.progress_signal.emit(idx, file_path, f"{self.t['error_prefix']}{err_msg[:35]}")
            except Exception as e:
                if os.path.exists(output_path):
                    os.remove(output_path)
                self.progress_signal.emit(idx, file_path, f"{self.t['error_prefix']}{str(e)[:35]}")

        self.finished_signal.emit()

    def cancel(self):
        self.is_cancelled = True


class FileItemWidget(QWidget):
    remove_requested = pyqtSignal(str)

    def __init__(self, file_path, lang="tr"):
        super().__init__()
        self.file_path = file_path
        self.lang = lang
        self.t = TRANSLATIONS[lang]
        filename = os.path.basename(file_path)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(6, 2, 6, 2)
        layout.setSpacing(8)

        self.label_info = QLabel(f"⏳ {filename} — {self.t['waiting']}")
        self.label_info.setStyleSheet("color: #F5F5F7; font-size: 12px;")

        self.remove_btn = QPushButton("✕")
        self.remove_btn.setFixedSize(22, 22)
        self.remove_btn.setToolTip(self.t["remove_tooltip"])
        self.remove_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #8E8E93;
                border: none;
                font-weight: bold;
                font-size: 13px;
                border-radius: 11px;
                padding: 0px;
            }
            QPushButton:hover {
                background-color: #FF453A;
                color: #FFFFFF;
            }
        """)
        self.remove_btn.clicked.connect(lambda: self.remove_requested.emit(self.file_path))

        layout.addWidget(self.label_info, stretch=1)
        layout.addWidget(self.remove_btn, stretch=0)

    def set_status(self, status_text):
        filename = os.path.basename(self.file_path)
        self.label_info.setText(f"{filename} — {status_text}")

    def set_remove_enabled(self, enabled):
        self.remove_btn.setEnabled(enabled)


class DropArea(QFrame):
    files_dropped = pyqtSignal(list)

    def __init__(self, lang="tr"):
        super().__init__()
        self.lang = lang
        self.t = TRANSLATIONS[lang]
        self.setMinimumHeight(110)

        self.setStyleSheet("""
            DropArea {
                border: 1px dashed #3A3A3C;
                border-radius: 10px;
                background-color: #252528;
            }
            DropArea:hover {
                border: 1.5px solid #0A84FF;
                background-color: #2C2C30;
            }
            QLabel {
                border: none;
                background: transparent;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.label_icon = QLabel("🎬")
        self.label_icon.setStyleSheet("font-size: 26px;")
        self.label_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.label_text = QLabel(self.t["drop_text"])
        self.label_text.setStyleSheet("font-size: 13px; color: #8E8E93; font-weight: 500;")
        self.label_text.setAlignment(Qt.AlignmentFlag.AlignCenter)

        layout.addWidget(self.label_icon)
        layout.addWidget(self.label_text)

    def update_language(self, lang):
        self.lang = lang
        self.t = TRANSLATIONS[lang]
        self.label_text.setText(self.t["drop_text"])

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            files, _ = QFileDialog.getOpenFileNames(
                self, self.t["select_files"], "", "Video Files (*.mp4 *.mov *.mkv);;All Files (*.*)"
            )
            if files:
                self.files_dropped.emit(files)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.settings = QSettings("DaVinciResolve", "MediaConverter")

        system_locale = QLocale.system().name().lower()
        default_lang = "tr" if system_locale.startswith("tr") else "en"
        self.lang = self.settings.value("language", default_lang, type=str)
        self.t = TRANSLATIONS[self.lang]

        self.setWindowTitle(self.t["window_title"])
        self.resize(680, 600)
        self.setAcceptDrops(True)

        self.files_list = []
        self.widget_map = {}
        self.worker = None

        self.init_ui()
        self.load_settings()

    def init_ui(self):
        self.setStyleSheet("""
            QMainWindow {
                background-color: #1E1E1E;
            }
            QLabel {
                color: #F5F5F7;
                border: none;
            }
            QListWidget {
                background-color: #252528;
                border: 1px solid #3A3A3C;
                border-radius: 10px;
                color: #F5F5F7;
                padding: 4px;
                outline: none;
            }
            QListWidget::item {
                border-bottom: 1px solid #323235;
                padding: 2px 0px;
            }
            QPushButton {
                background-color: #0A84FF;
                color: #FFFFFF;
                border: none;
                border-radius: 8px;
                padding: 9px 16px;
                font-weight: 600;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #0071E3;
            }
            QPushButton:disabled {
                background-color: #3A3A3C;
                color: #7D7D82;
            }
            QPushButton#clear_btn {
                background-color: #3A3A3C;
                color: #F5F5F7;
            }
            QPushButton#clear_btn:hover {
                background-color: #48484A;
            }
            QPushButton#stop_btn {
                background-color: #FF453A;
                color: #FFFFFF;
            }
            QPushButton#stop_btn:hover {
                background-color: #FF3B30;
            }
            QPushButton#stop_btn:disabled {
                background-color: #3A3A3C;
                color: #7D7D82;
            }
            QPushButton.icon_btn {
                background-color: #2C2C2E;
                color: #F5F5F7;
                border: 1px solid #3A3A3C;
                border-radius: 8px;
                font-size: 16px;
                padding: 0px;
            }
            QPushButton.icon_btn:hover {
                background-color: #3A3A3C;
                border: 1px solid #0A84FF;
            }
            QComboBox {
                background-color: #2C2C2E;
                color: #F5F5F7;
                border: 1px solid #3A3A3C;
                border-radius: 6px;
                padding: 6px 10px;
            }
            QComboBox:disabled {
                color: #7D7D82;
                background-color: #1E1E1E;
            }
            QComboBox QAbstractItemView {
                background-color: #2C2C2E;
                color: #F5F5F7;
                selection-background-color: #0A84FF;
                border: 1px solid #3A3A3C;
            }
            QCheckBox {
                color: #F5F5F7;
                font-weight: 500;
                spacing: 8px;
            }
            QProgressBar {
                background-color: #252528;
                border: 1px solid #3A3A3C;
                border-radius: 6px;
                text-align: center;
                color: #FFFFFF;
                font-weight: bold;
            }
            QProgressBar::chunk {
                background-color: #30D158;
                border-radius: 5px;
            }
        """)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(12)
        main_layout.setContentsMargins(16, 16, 16, 16)

        # Üst Başlık ve Sağ Üst Emojili 1:1 Butonlar
        top_layout = QHBoxLayout()
        self.title_label = QLabel(self.t["window_title"])
        self.title_label.setStyleSheet("font-size: 17px; font-weight: 600; color: #F5F5F7;")
        top_layout.addWidget(self.title_label)
        top_layout.addStretch()

        # Menü Kısayol Butonu (🔗 1:1)
        self.desktop_btn = QPushButton("🔗")
        self.desktop_btn.setProperty("class", "icon_btn")
        self.desktop_btn.setFixedSize(36, 36)
        self.desktop_btn.setToolTip(self.t["desktop_tooltip"])
        self.desktop_btn.clicked.connect(self.create_desktop_file)
        top_layout.addWidget(self.desktop_btn)

        # Dil Değiştirme Butonu (Bayrak 1:1)
        flag_emoji = "🇬🇧" if self.lang == "tr" else "🇹🇷"
        self.lang_btn = QPushButton(flag_emoji)
        self.lang_btn.setProperty("class", "icon_btn")
        self.lang_btn.setFixedSize(36, 36)
        self.lang_btn.setToolTip(self.t["lang_tooltip"])
        self.lang_btn.clicked.connect(self.toggle_language)
        top_layout.addWidget(self.lang_btn)

        main_layout.addLayout(top_layout)

        self.drop_area = DropArea(lang=self.lang)
        self.drop_area.files_dropped.connect(self.add_files)
        main_layout.addWidget(self.drop_area)

        ctrl_layout1 = QHBoxLayout()
        self.mode_info_label = QLabel(self.t["mode_video"])
        self.mode_info_label.setStyleSheet("color: #FF9F0A; font-size: 12px; font-weight: 500;")

        self.clear_btn = QPushButton(self.t["clear_list"])
        self.clear_btn.setObjectName("clear_btn")
        self.clear_btn.clicked.connect(self.clear_list)

        ctrl_layout1.addWidget(self.mode_info_label)
        ctrl_layout1.addStretch()
        ctrl_layout1.addWidget(self.clear_btn)
        main_layout.addLayout(ctrl_layout1)

        ctrl_layout2 = QHBoxLayout()
        self.video_checkbox = QCheckBox(self.t["video_checkbox"])
        self.video_checkbox.setChecked(True)
        self.video_checkbox.toggled.connect(self.toggle_video_options)
        self.video_checkbox.toggled.connect(self.save_settings)

        self.video_codec_combo = QComboBox()
        self.video_codec_combo.addItem(self.t["codec_mpeg4"], "mpeg4")
        self.video_codec_combo.addItem(self.t["codec_dnxhr_lb"], "dnxhr_lb")
        self.video_codec_combo.addItem(self.t["codec_dnxhr_hq"], "dnxhr_hq")
        self.video_codec_combo.setEnabled(True)
        self.video_codec_combo.currentIndexChanged.connect(self.save_settings)

        ctrl_layout2.addWidget(self.video_checkbox)
        ctrl_layout2.addWidget(self.video_codec_combo)
        ctrl_layout2.addStretch()
        main_layout.addLayout(ctrl_layout2)

        self.list_widget = QListWidget()
        main_layout.addWidget(self.list_widget)

        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        main_layout.addWidget(self.progress_bar)

        # En alt alan: Yalnızca dönüştürme butonları
        btn_layout = QHBoxLayout()

        self.convert_btn = QPushButton(self.t["convert_btn"])
        self.convert_btn.clicked.connect(self.start_conversion)

        self.stop_btn = QPushButton(self.t["stop_btn"])
        self.stop_btn.setObjectName("stop_btn")
        self.stop_btn.setEnabled(False)
        self.stop_btn.clicked.connect(self.stop_conversion)

        btn_layout.addWidget(self.convert_btn, stretch=2)
        btn_layout.addWidget(self.stop_btn, stretch=1)
        main_layout.addLayout(btn_layout)

    def load_settings(self):
        convert_video = self.settings.value("convert_video", True, type=bool)
        codec_data = self.settings.value("video_codec", "mpeg4", type=str)

        self.video_checkbox.setChecked(convert_video)
        index = self.video_codec_combo.findData(codec_data)
        if index != -1:
            self.video_codec_combo.setCurrentIndex(index)
        self.toggle_video_options(convert_video)

    def save_settings(self):
        self.settings.setValue("convert_video", self.video_checkbox.isChecked())
        self.settings.setValue("video_codec", self.video_codec_combo.currentData())
        self.settings.setValue("language", self.lang)

    def toggle_language(self):
        self.lang = "en" if self.lang == "tr" else "tr"
        self.t = TRANSLATIONS[self.lang]
        self.save_settings()
        self.retranslate_ui()

    def retranslate_ui(self):
        self.setWindowTitle(self.t["window_title"])
        self.title_label.setText(self.t["window_title"])
        self.desktop_btn.setToolTip(self.t["desktop_tooltip"])
        self.lang_btn.setText("🇬🇧" if self.lang == "tr" else "🇹🇷")
        self.lang_btn.setToolTip(self.t["lang_tooltip"])

        self.drop_area.update_language(self.lang)
        self.clear_btn.setText(self.t["clear_list"])
        self.video_checkbox.setText(self.t["video_checkbox"])

        current_data = self.video_codec_combo.currentData()
        self.video_codec_combo.clear()
        self.video_codec_combo.addItem(self.t["codec_mpeg4"], "mpeg4")
        self.video_codec_combo.addItem(self.t["codec_dnxhr_lb"], "dnxhr_lb")
        self.video_codec_combo.addItem(self.t["codec_dnxhr_hq"], "dnxhr_hq")
        idx = self.video_codec_combo.findData(current_data)
        if idx != -1:
            self.video_codec_combo.setCurrentIndex(idx)

        self.toggle_video_options(self.video_checkbox.isChecked())
        self.convert_btn.setText(self.t["convert_btn"])
        self.stop_btn.setText(self.t["stop_btn"])

    def create_desktop_file(self):
        try:
            home_dir = os.path.expanduser("~")
            apps_dir = os.path.join(home_dir, ".local", "share", "applications")
            os.makedirs(apps_dir, exist_ok=True)

            script_path = os.path.abspath(__file__)
            script_dir = os.path.dirname(script_path)

            desktop_content = f"""[Desktop Entry]
Comment=DaVinci Resolve Media Converter
Exec=python3 "{script_path}"
GenericName=AAC to DaVinci Resolve Converter
Icon=accessories-media-converter
Name=DaVinci AAC Converter
NoDisplay=false
Path={script_dir}
PrefersNonDefaultGPU=false
StartupNotify=true
Terminal=false
Type=Application
Categories=AudioVideo;Audio;Video;
"""
            desktop_file_path = os.path.join(apps_dir, "davinci_aac_converter.desktop")
            with open(desktop_file_path, "w", encoding="utf-8") as f:
                f.write(desktop_content)

            os.chmod(desktop_file_path, 0o755)

            QMessageBox.information(
                self,
                self.t["success"],
                self.t["desktop_success"].format(desktop_file_path)
            )
        except Exception as e:
            QMessageBox.critical(
                self,
                self.t["warning"],
                self.t["desktop_error"].format(str(e))
            )

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent):
        valid_exts = (".mp4", ".mov", ".mkv")
        files = []
        for url in event.mimeData().urls():
            path = url.toLocalFile()
            if os.path.isfile(path) and path.lower().endswith(valid_exts):
                files.append(path)
            elif os.path.isdir(path):
                for root, _, filenames in os.walk(path):
                    for f in filenames:
                        if f.lower().endswith(valid_exts):
                            files.append(os.path.join(root, f))
        if files:
            self.add_files(files)

    def toggle_video_options(self, checked):
        self.video_codec_combo.setEnabled(checked)
        if checked:
            self.mode_info_label.setText(self.t["mode_video"])
            self.mode_info_label.setStyleSheet("color: #FF9F0A; font-size: 12px; font-weight: 500;")
        else:
            self.mode_info_label.setText(self.t["mode_audio"])
            self.mode_info_label.setStyleSheet("color: #30D158; font-size: 12px; font-weight: 500;")

    def add_files(self, paths):
        for path in paths:
            if path not in self.files_list:
                self.files_list.append(path)

                item = QListWidgetItem(self.list_widget)
                item_widget = FileItemWidget(path, lang=self.lang)
                item_widget.remove_requested.connect(self.remove_file)

                item.setSizeHint(item_widget.sizeHint())
                self.list_widget.addItem(item)
                self.list_widget.setItemWidget(item, item_widget)

                self.widget_map[path] = (item, item_widget)

    def remove_file(self, file_path):
        if self.worker and self.worker.isRunning():
            return

        if file_path in self.widget_map:
            item, _ = self.widget_map[file_path]
            row = self.list_widget.row(item)
            self.list_widget.takeItem(row)
            del self.widget_map[file_path]
            self.files_list.remove(file_path)

    def clear_list(self):
        if self.worker and self.worker.isRunning():
            QMessageBox.warning(self, self.t["warning"], self.t["clear_running_warning"])
            return
        self.files_list.clear()
        self.widget_map.clear()
        self.list_widget.clear()
        self.progress_bar.setValue(0)

    def start_conversion(self):
        if not self.files_list:
            QMessageBox.information(self, self.t["info"], self.t["add_files_prompt"])
            return

        convert_video = self.video_checkbox.isChecked()
        video_codec = self.video_codec_combo.currentData()
        ext = ".mp4" if video_codec == "mpeg4" else ".mov"

        existing_files = []
        for path in self.files_list:
            folder, filename = os.path.split(path)
            name, _ = os.path.splitext(filename)
            out_p = os.path.join(folder, "output", f"{name}{ext}")
            if os.path.exists(out_p) and os.path.getsize(out_p) > 0:
                existing_files.append(f"./output/{name}{ext}")

        overwrite = False
        if existing_files:
            msg = f"{len(existing_files)} {self.t['output_exists_msg']}\n\n"
            msg += "\n".join(existing_files[:5])
            if len(existing_files) > 5:
                msg += f"\n...ve {len(existing_files) - 5} dosya daha." if self.lang == "tr" else f"\n...and {len(existing_files) - 5} more files."

            reply = QMessageBox.question(
                self,
                self.t["output_exists_title"],
                msg,
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No | QMessageBox.StandardButton.Cancel,
                QMessageBox.StandardButton.No
            )

            if reply == QMessageBox.StandardButton.Yes:
                overwrite = True
            elif reply == QMessageBox.StandardButton.No:
                overwrite = False
            else:
                return

        for _, widget in self.widget_map.values():
            widget.set_remove_enabled(False)

        self.convert_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.clear_btn.setEnabled(False)
        self.desktop_btn.setEnabled(False)
        self.lang_btn.setEnabled(False)
        self.drop_area.setEnabled(False)
        self.progress_bar.setMaximum(len(self.files_list))
        self.progress_bar.setValue(0)

        queue = list(enumerate(self.files_list))
        self.worker = ConversionWorker(
            queue,
            convert_video=convert_video,
            video_codec=video_codec,
            overwrite=overwrite,
            lang=self.lang
        )
        self.worker.progress_signal.connect(self.update_item_status)
        self.worker.finished_signal.connect(self.conversion_finished)
        self.worker.start()

    def stop_conversion(self):
        if self.worker and self.worker.isRunning():
            self.stop_btn.setEnabled(False)
            self.worker.cancel()

    def update_item_status(self, idx, file_path, status):
        if file_path in self.widget_map:
            item, widget = self.widget_map[file_path]
            widget.set_status(status)
            self.list_widget.scrollToItem(item)

        self.progress_bar.setValue(self.progress_bar.value() + 1)

    def conversion_finished(self, *args, **kwargs):
        for _, widget in self.widget_map.values():
            widget.set_remove_enabled(True)

        self.convert_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.clear_btn.setEnabled(True)
        self.desktop_btn.setEnabled(True)
        self.lang_btn.setEnabled(True)
        self.drop_area.setEnabled(True)


def main():
    app = QApplication(sys.argv)
    app.setDesktopFileName("Davinci_AAC_Converter")

    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
