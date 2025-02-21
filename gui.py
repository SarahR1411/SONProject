import sys
import numpy as np
import sounddevice as sd
import serial
from PyQt5 import QtWidgets, QtCore
import pyqtgraph as pg
from scipy.signal import spectrogram

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

    def init_serial(self):
        try:
            self.serial_port = serial.Serial('COM3', 921600, timeout=0)
        except serial.SerialException:
            print("Failed to open serial port")
            
    def init_ui(self):
        self.setWindowTitle("Teensy Pitch Shifter")
        self.setGeometry(100, 100, 800, 600)

        # Main widget and layout
        central_widget = QtWidgets.QWidget()
        self.setCentralWidget(central_widget)
        layout = QtWidgets.QVBoxLayout()

        # Waveform plot
        self.waveform_plot = pg.PlotWidget()
        self.waveform_curve = self.waveform_plot.plot(pen='y')
        layout.addWidget(self.waveform_plot)

        # Spectrogram plot
        self.spectrogram_plot = pg.PlotWidget()
        self.spectrogram_image = pg.ImageItem()
        self.spectrogram_plot.addItem(self.spectrogram_image)
        layout.addWidget(self.spectrogram_plot)

        # Controls
        control_layout = QtWidgets.QHBoxLayout()
        
        # Pitch control
        self.pitch_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.pitch_slider.setRange(50, 200)
        self.pitch_slider.valueChanged.connect(self.update_pitch)
        self.pitch_label = QtWidgets.QLabel("Pitch Factor: 1.00")
        
        # Preset buttons
        presets = ['Low Voice', 'High Voice', 'Robot', 'Reset']
        self.buttons = {}
        for preset in presets:
            btn = QtWidgets.QPushButton(preset)
            btn.clicked.connect(self.handle_preset)
            control_layout.addWidget(btn)
            
        # Recording controls
        self.record_btn = QtWidgets.QPushButton("Record")
        self.play_btn = QtWidgets.QPushButton("Play")
        self.record_btn.clicked.connect(self.toggle_recording)
        self.play_btn.clicked.connect(self.play_recording)
        
        control_layout.addWidget(self.pitch_slider)
        control_layout.addWidget(self.pitch_label)
        control_layout.addWidget(self.record_btn)
        control_layout.addWidget(self.play_btn)
        layout.addLayout(control_layout)

        central_widget.setLayout(layout)

        # Timer for updates
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.update_plots)
        self.timer.start(50)

    def init_audio_processing(self):
        self.spectrogram_data = np.zeros((100, 100))
        self.freqs = np.fft.rfftfreq(1024, 1/44100)
        self.t_spec = np.arange(100)

    def update_plots(self):
        # Update waveform
        self.waveform_curve.setData(self.audio_buffer[-1000:])
        
        # Update spectrogram
        f, t, Sxx = spectrogram(self.audio_buffer, fs=44100, nperseg=1024)
        self.spectrogram_image.setImage(Sxx[::4, ::2], autoLevels=True)

    def update_pitch(self):
        factor = self.pitch_slider.value() / 100.0
        self.pitch_label.setText(f"Pitch Factor: {factor:.2f}")
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
        if self.serial_port and self.serial_port.in_waiting:
            data = self.serial_port.read(self.serial_port.in_waiting)
            audio = np.frombuffer(data, dtype=np.int16)
            self.audio_buffer = np.roll(self.audio_buffer, -len(audio))
            self.audio_buffer[-len(audio):] = audio
            if self.recording:
                self.recorded_audio.append(audio.copy())

if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    gui = AudioGUI()
    gui.show()
    
    # Serial reading timer
    serial_timer = QtCore.QTimer()
    serial_timer.timeout.connect(gui.read_serial)
    serial_timer.start(10)
    
    sys.exit(app.exec_())