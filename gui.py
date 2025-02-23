import sys
import glob
import platform
import numpy as np
import sounddevice as sd
import serial
from PyQt5 import QtWidgets, QtCore, QtGui
import pyqtgraph as pg
from scipy.signal import spectrogram

# custom color palette
COLORS = {
    'dark': '#1a1a1a',
    'darker': '#121212',
    'accent': '#00ff88',
    'text': '#ffffff',
    'plot_bg': '#000000',
    'waveform': '#00ff88',
    'spectrogram': '#00ffff'
}

class AudioGUI(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.serial_port = None
        self.audio_buffer = np.zeros(44100, dtype=np.int16)
        self.recording = False
        self.recorded_audio = []
        self.init_serial()
        self.init_ui()
        self.init_audio_processing()
        self.setup_styles()
        self.status_bar = self.statusBar()

    def setup_styles(self):
        self.setStyleSheet(f"""
            QMainWindow {{ background-color: {COLORS['dark']}; }}
            QLabel {{ color: {COLORS['text']}; font: 12pt Arial; }}
            QPushButton {{
                background-color: {COLORS['darker']};
                color: {COLORS['text']};
                border: 2px solid {COLORS['accent']};
                border-radius: 5px;
                padding: 8px;
                font: bold 12pt Arial;
            }}
            QPushButton:hover {{ background-color: {COLORS['accent']}; color: black; }}
            QSlider::groove:horizontal {{
                background: {COLORS['darker']};
                height: 10px;
                border-radius: 5px;
            }}
            QSlider::handle:horizontal {{
                background: {COLORS['accent']};
                width: 20px;
                margin: -5px 0;
                border-radius: 10px;
            }}
            QSlider::sub-page:horizontal {{ background: {COLORS['accent']}; }}
        """)
    def init_serial(self):
            port_pattern = {
                'Windows': 'COM*',
                'Darwin': '/dev/tty.usbmodem*',
                'Linux': '/dev/ttyACM*'
            }[platform.system()]
            
            ports = glob.glob(port_pattern)
            print(f"Available ports: {ports}")
            
            for port in ports:
                try:
                    self.serial_port = serial.Serial(
                        port, 
                        921600,
                        timeout=0,
                        write_timeout=1
                    )
                    print(f"Connected to {port}")
                    return
                except serial.SerialException as e:
                    print(f"Failed to connect to {port}: {str(e)}")
            
            print("No valid Teensy port found!")
            self.serial_port = None

    def init_ui(self):
        self.setWindowTitle("Teensy Pitch Shifter - Audio Processor")
        self.setGeometry(100, 100, 1000, 800)

        # Main widget and layout
        central_widget = QtWidgets.QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QtWidgets.QVBoxLayout(central_widget)

        # Visualization Section
        vis_group = QtWidgets.QGroupBox("Live Visualizations")
        vis_layout = QtWidgets.QVBoxLayout()
        
        # Waveform plot with title
        self.waveform_plot = pg.PlotWidget(title="Live Waveform")
        self.waveform_plot.setLabel('left', 'Amplitude')
        self.waveform_plot.setLabel('bottom', 'Time (samples)')
        self.waveform_curve = self.waveform_plot.plot(pen=pg.mkPen(COLORS['waveform'], width=2))
        vis_layout.addWidget(self.waveform_plot)

        # Spectrogram plot with title
        self.spectrogram_plot = pg.PlotWidget(title="Live Spectrogram")
        self.spectrogram_plot.setLabel('left', 'Frequency (Hz)')
        self.spectrogram_plot.setLabel('bottom', 'Time (s)')
        self.spectrogram_image = pg.ImageItem()
        self.spectrogram_plot.addItem(self.spectrogram_image)
        vis_layout.addWidget(self.spectrogram_plot)
        vis_group.setLayout(vis_layout)
        main_layout.addWidget(vis_group)

        # Control Panel
        control_group = QtWidgets.QGroupBox("Processing Controls")
        control_layout = QtWidgets.QGridLayout()

        # Pitch Control
        pitch_control = QtWidgets.QGroupBox("Pitch Control")
        pitch_layout = QtWidgets.QVBoxLayout()
        
        self.pitch_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.pitch_slider.setRange(50, 200)
        self.pitch_slider.valueChanged.connect(self.update_pitch)
        
        self.pitch_display = QtWidgets.QLCDNumber()
        self.pitch_display.setDigitCount(5)
        self.pitch_display.setSegmentStyle(QtWidgets.QLCDNumber.Filled)
        self.pitch_display.display(1.00)
        
        pitch_layout.addWidget(QtWidgets.QLabel("Pitch Factor (0.5x - 2.0x):"))
        pitch_layout.addWidget(self.pitch_slider)
        pitch_layout.addWidget(self.pitch_display)
        pitch_control.setLayout(pitch_layout)
        control_layout.addWidget(pitch_control, 0, 0, 1, 2)

        # Presets
        presets_group = QtWidgets.QGroupBox("Presets")
        presets_layout = QtWidgets.QHBoxLayout()
        
        self.buttons = {}
        presets = [
            ('Low Voice', '#ff4444'), 
            ('High Voice', '#44ff44'), 
            ('Robot', '#4444ff'), 
            ('Reset', COLORS['accent'])
        ]
        
        for text, color in presets:
            btn = QtWidgets.QPushButton(text)
            btn.setStyleSheet(f"background-color: {color}; color: black;")
            btn.clicked.connect(self.handle_preset)
            presets_layout.addWidget(btn)
            self.buttons[text] = btn
        
        presets_group.setLayout(presets_layout)
        control_layout.addWidget(presets_group, 1, 0, 1, 2)

        # Recording Controls
        rec_group = QtWidgets.QGroupBox("Recording")
        rec_layout = QtWidgets.QHBoxLayout()
        
        self.record_btn = QtWidgets.QPushButton("⏺ Record")
        self.play_btn = QtWidgets.QPushButton("⏵ Play")
        self.record_btn.clicked.connect(self.toggle_recording)
        self.play_btn.clicked.connect(self.play_recording)
        
        rec_layout.addWidget(self.record_btn)
        rec_layout.addWidget(self.play_btn)
        rec_group.setLayout(rec_layout)
        control_layout.addWidget(rec_group, 2, 0, 1, 2)

        # VU Meter
        self.vu_meter = QtWidgets.QProgressBar()
        self.vu_meter.setRange(0, 100)
        self.vu_meter.setTextVisible(False)
        self.vu_meter.setStyleSheet(f"""
            QProgressBar {{
                background: {COLORS['darker']};
                border: 2px solid {COLORS['accent']};
                border-radius: 5px;
                height: 20px;
            }}
            QProgressBar::chunk {{ background-color: {COLORS['accent']}; }}
        """)
        control_layout.addWidget(QtWidgets.QLabel("Input Level:"), 3, 0)
        control_layout.addWidget(self.vu_meter, 3, 1)

        control_group.setLayout(control_layout)
        main_layout.addWidget(control_group)

        # Timer for updates
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.update_plots)
        self.timer.start(50)

        # Configure plot aesthetics
        self.configure_plots()

    def configure_plots(self):
        # Waveform plot styling
        self.waveform_plot.setBackground(COLORS['plot_bg'])
        self.waveform_plot.getAxis('left').setPen(COLORS['text'])
        self.waveform_plot.getAxis('bottom').setPen(COLORS['text'])
        
        # Spectrogram plot styling
        self.spectrogram_plot.setBackground(COLORS['plot_bg'])
        self.spectrogram_image.setLookupTable(self.create_colormap())
        self.spectrogram_plot.getAxis('left').setPen(COLORS['text'])
        self.spectrogram_plot.getAxis('bottom').setPen(COLORS['text'])

    def create_colormap(self):
        colors = [
            (0, 0, 0),
            (0, 0, 255),
            (0, 255, 255),
            (255, 255, 0),
            (255, 0, 0)
        ]
        pos = np.linspace(0, 1, len(colors))
        return pg.ColorMap(pos, colors).getLookupTable()

    def init_audio_processing(self):
        self.spectrogram_data = np.zeros((100, 100))
        self.freqs = np.fft.rfftfreq(1024, 1/44100)
        self.t_spec = np.arange(100)

    def update_plots(self):
        # Update waveform
        self.waveform_curve.setData(self.audio_buffer[-1000:])
        
        # Update spectrogram
        f, t, Sxx = spectrogram(self.audio_buffer, fs=44100, nperseg=1024)
        self.spectrogram_image.setImage(Sxx[::4, ::2], autoLevels=False)
        
        # Update VU meter
        current_level = np.abs(self.audio_buffer[-1000:]).mean() * 2
        self.vu_meter.setValue(int(np.clip(current_level, 0, 100)))

    def update_pitch(self):
        factor = self.pitch_slider.value() / 100.0
        self.pitch_display.display(factor)
        self.send_command(f"PITCH {factor}")

    def handle_preset(self):
        sender = self.sender().text()
        if sender == 'Low Voice':
            self.send_command("PITCH 0.5")
        elif sender == 'High Voice':
            self.send_command("PITCH 2.0")
        elif sender == 'Robot':
            self.send_command("ROBOT 1.0")
        elif sender == 'Reset':
            self.send_command("RESET")

    def toggle_recording(self):
        self.recording = not self.recording
        self.record_btn.setText("Stop" if self.recording else "Record")
        if not self.recording:
            sd.write(np.concatenate(self.recorded_audio), 44100)

    def play_recording(self):
        if len(self.recorded_audio) > 0:
            sd.play(np.concatenate(self.recorded_audio), 44100)

    def send_command(self, cmd):
        if self.serial_port:
            self.serial_port.write(f"{cmd}\n".encode())

    def read_serial(self):
        try:
            if self.serial_port and self.serial_port.in_waiting:
                print(f"Bytes waiting: {self.serial_port.in_waiting}")
                # Read all available bytes
                data = self.serial_port.read(self.serial_port.in_waiting)
                print(f"Received {len(data)} bytes")
                
                # Ensure we have even number of bytes for int16 conversion
                if len(data) % 2 != 0:
                    data = data[:-1]  # Drop last byte if odd count
                    
                if len(data) >= 2:
                    audio = np.frombuffer(data, dtype=np.int16)
                    self.audio_buffer = np.roll(self.audio_buffer, -len(audio))
                    self.audio_buffer[-len(audio):] = audio
                    
                    if self.recording:
                        self.recorded_audio.append(audio.copy())
        except Exception as e:
            print(f"Serial read error: {str(e)}")
        finally:
                pass

if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    app.setWindowIcon(QtGui.QIcon('icon.png'))  # Add your own icon
    gui = AudioGUI()
    gui.show()
    
    # Serial reading timer
    serial_timer = QtCore.QTimer()
    serial_timer.timeout.connect(gui.read_serial)
    serial_timer.start(10)

    sys.exit(app.exec_())