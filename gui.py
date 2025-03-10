import sys
import glob
import platform
import numpy as np
import sounddevice as sd
import soundfile as sf
import serial
import time  
from PyQt5 import QtWidgets, QtCore, QtGui
import pyqtgraph as pg
from scipy.signal import spectrogram

# Custom color palette
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
        self.vu_level = 0.0
        self.recorded_audio = []
        self.last_recording = None  # Store last recording
        self.reverb_mix = 0.0
        self.status_bar = self.statusBar()
        self.init_serial()
        self.init_ui()
        self.init_audio_processing()
        self.setup_styles()

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
            QPushButton:pressed {{ border: 2px solid white; }}
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
        # detect the teensy port based on the OS
        port_pattern = {
            'Windows': 'COM*',
            'Darwin': '/dev/tty.usbmodem*',
            'Linux': '/dev/ttyACM*'
        }[platform.system()]
        
        ports = glob.glob(port_pattern) # scan for a matching port
        print(f"Available ports: {ports}")
        
        #try to connect to each port
        for port in ports:
            try:
                self.serial_port = serial.Serial(
                    port, 
                    921600,
                    timeout=0,
                    write_timeout=1
                )
                print(f"Connected to {port}")
                self.status_bar.showMessage(f"Connected to {port}", 5000)
                return
            except serial.SerialException as e:
                print(f"Failed to connect to {port}: {str(e)}")
        
        print("No valid Teensy port found!")
        self.serial_port = None
        self.status_bar.showMessage("No Teensy detected!", 5000)

    def init_ui(self):
        self.setWindowTitle("Teensy Audio Processor")
        self.setGeometry(100, 100, 1000, 800)

        central_widget = QtWidgets.QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QtWidgets.QVBoxLayout(central_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(15)

        # Visualization Section
        vis_group = QtWidgets.QGroupBox("Live Visualizations")
        vis_layout = QtWidgets.QVBoxLayout()
        vis_layout.setContentsMargins(5, 15, 5, 5)
        
        self.waveform_plot = pg.PlotWidget(title="Live Waveform")
        self.waveform_plot.setLabel('left', 'Amplitude')
        self.waveform_plot.setLabel('bottom', 'Time (samples)')
        self.waveform_curve = self.waveform_plot.plot(pen=pg.mkPen(COLORS['waveform'], width=2))
        vis_layout.addWidget(self.waveform_plot)

        self.spectrogram_plot = pg.PlotWidget(title="Live Spectrogram")
        self.spectrogram_plot.setLabel('left', 'Frequency (Hz)')
        self.spectrogram_plot.setLabel('bottom', 'Time (s)')
        self.spectrogram_image = pg.ImageItem() # creates an image object for he spectrogram
        self.spectrogram_plot.addItem(self.spectrogram_image) # attaches the image to the plot
        vis_layout.addWidget(self.spectrogram_plot)
        vis_group.setLayout(vis_layout)
        main_layout.addWidget(vis_group)

        # Control Panel
        control_group = QtWidgets.QGroupBox("Processing Controls")
        control_layout = QtWidgets.QGridLayout()
        control_layout.setVerticalSpacing(15)
        control_layout.setHorizontalSpacing(20)

        # Pitch Control
        pitch_control = QtWidgets.QGroupBox("Pitch Control")
        pitch_layout = QtWidgets.QVBoxLayout()
        self.pitch_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.pitch_slider.setRange(50, 200)
        self.pitch_slider.valueChanged.connect(self.update_pitch)
        self.pitch_display = QtWidgets.QLCDNumber()
        self.pitch_display.setDigitCount(5)
        pitch_layout.addWidget(QtWidgets.QLabel("Pitch Factor (0.5x - 2.0x):"))
        pitch_layout.addWidget(self.pitch_slider)
        pitch_layout.addWidget(self.pitch_display)
        pitch_control.setLayout(pitch_layout)
        control_layout.addWidget(pitch_control, 0, 0, 1, 2)

        # Reverb Control
        reverb_control = QtWidgets.QGroupBox("Reverb Control")
        reverb_layout = QtWidgets.QVBoxLayout()
        self.reverb_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.reverb_slider.setRange(0, 100)
        self.reverb_slider.valueChanged.connect(self.update_reverb)
        self.reverb_display = QtWidgets.QLCDNumber()
        self.reverb_display.setDigitCount(5)
        reverb_layout.addWidget(QtWidgets.QLabel("Reverb Mix (0% - 100%):"))
        reverb_layout.addWidget(self.reverb_slider)
        reverb_layout.addWidget(self.reverb_display)
        reverb_control.setLayout(reverb_layout)
        control_layout.addWidget(reverb_control, 1, 0, 1, 2)

        # Presets
        presets_group = QtWidgets.QGroupBox("Presets")
        presets_layout = QtWidgets.QHBoxLayout()
        self.buttons = {}
        presets = [('Low Voice', '#ff4444'), ('High Voice', '#44ff44'), ('Reset', COLORS['accent'])]
        for text, color in presets:
            btn = QtWidgets.QPushButton(text)
            btn.setStyleSheet(f"background-color: {color}; color: black;")
            btn.clicked.connect(self.handle_preset)
            presets_layout.addWidget(btn)
            self.buttons[text] = btn
        presets_group.setLayout(presets_layout)
        control_layout.addWidget(presets_group, 2, 0, 1, 2)

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
        control_layout.addWidget(rec_group, 3, 0, 1, 2)

        # VU Meter
        control_layout.addWidget(QtWidgets.QLabel("Input Level:"), 4, 0)
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
        control_layout.addWidget(self.vu_meter, 4, 1)

        control_group.setLayout(control_layout)
        main_layout.addWidget(control_group)

        # Timer setup : to update the plots every 50 ms
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.update_plots)
        self.timer.start(50)

        self.configure_plots()
        QtCore.QTimer.singleShot(100, self.read_serial)

 

    def configure_plots(self):
        self.waveform_plot.setBackground(COLORS['plot_bg'])
        self.waveform_plot.getAxis('left').setPen(COLORS['text'])
        self.waveform_plot.getAxis('bottom').setPen(COLORS['text'])
        
        self.spectrogram_plot.setBackground(COLORS['plot_bg'])
        self.spectrogram_image.setLookupTable(self.create_colormap())
        self.spectrogram_plot.getAxis('left').setPen(COLORS['text'])
        self.spectrogram_plot.getAxis('bottom').setPen(COLORS['text'])

    def create_colormap(self):
        # colormap is used to visually differentiate the frequency magnitudes in the spectrogram
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
        self.freqs = np.fft.rfftfreq(1024, 1/44100) # convert time domain signal to frequency domain
        self.t_spec = np.arange(100)

    def update_plots(self):
        try:
            # Update VU meter using peak detection
            current_peak = np.max(np.abs(self.audio_buffer[-1000:])) / 32768.0
            self.vu_meter.setValue(int(current_peak * 100))
            
            # Update waveform: plot last 1000 samples
            self.waveform_curve.setData(self.audio_buffer[-1000:])
            
            # Update spectrogram : computed using FFT
            f, t, Sxx = spectrogram(self.audio_buffer, fs=44100, nperseg=1024) # computes spectrogram from audio buffer
            if Sxx.size > 0:
                db_scale = 10 * np.log10(Sxx[::4, ::2] + 1e-12) # converts power values to dB
                self.spectrogram_image.setImage(db_scale.T, levels=(-40, 40))
        except Exception as e:
            print(f"Plotting error: {str(e)}")

    def update_pitch(self):
        factor = self.pitch_slider.value() / 100.0
        self.pitch_display.display(factor)
        self.send_command(f"PITCH {factor:.2f}")
    
    def update_reverb(self):
        mix = self.reverb_slider.value()/100.0
        self.reverb_display.display(mix)
        self.send_command(f"REVERB {mix:.2f}")

    def handle_preset(self):
        btn = self.sender()
        text = btn.text()
        
        # Visual feedback
        original_color = btn.palette().color(btn.backgroundRole()).name()
        btn.setStyleSheet(f"background-color: white; color: black;")
        QtCore.QTimer.singleShot(200, lambda: btn.setStyleSheet(f"background-color: {original_color}; color: black;"))
        
        if self.serial_port:
            self.serial_port.reset_input_buffer()
            self.serial_port.reset_output_buffer()
            
        if text == 'Low Voice':
            self.send_command("PITCH 0.5")
            self.pitch_slider.setValue(50)
        elif text == 'High Voice':
            self.send_command("PITCH 2.0")
            self.pitch_slider.setValue(200)
        elif text == 'Reset':
            self.send_command("RESET")
            self.pitch_slider.setValue(100)
            self.reverb_slider.setValue(0)

    def toggle_recording(self):
        self.recording = not self.recording
        self.record_btn.setText("⏹ Stop" if self.recording else "⏺ Record")
        if not self.recording and len(self.recorded_audio) > 0:
            full_recording = np.concatenate(self.recorded_audio)
            timestamp = int(time.time())
            filename = f'recording_{timestamp}.wav'
            sf.write(filename, full_recording, 44100)
            self.last_recording = full_recording
            self.recorded_audio = []
            self.status_bar.showMessage(f"Saved as {filename}", 5000)

    def play_recording(self):
        if self.recording:
            self.recording = False
            self.record_btn.setText("⏺ Record")
            
        if self.last_recording is not None:
            sd.play(self.last_recording, 44100)
        else:
            self.status_bar.showMessage("No recording available", 3000)

    def send_command(self, cmd):
        if self.serial_port:
            try:
                self.serial_port.write(f"{cmd}\n".encode()) # send command + newline
                self.serial_port.flush() # immediately transmit data
            except Exception as e:
                print(f"Send error: {str(e)}")
                self.status_bar.showMessage("Connection lost!", 5000)
                self.serial_port = None

    def read_serial(self):
        try:
            if self.serial_port and self.serial_port.in_waiting:
                data = self.serial_port.read(self.serial_port.in_waiting)
                # make sure there's an even number of bytes
                if len(data) % 2 != 0:
                    data = data[:-1]
                if len(data) >= 2:
                    # convert bytes into int16 array
                    audio = np.frombuffer(data, dtype=np.int16)
                    # update the rolling buffer for plots
                    self.audio_buffer = np.roll(self.audio_buffer, -len(audio))
                    self.audio_buffer[-len(audio):] = audio
                    
                    if self.recording:
                        self.recorded_audio.append(audio.copy())
        except Exception as e:
            print(f"Serial error: {str(e)}")

if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    gui = AudioGUI()
    gui.show()
    
    serial_timer = QtCore.QTimer()
    serial_timer.timeout.connect(gui.read_serial)
    serial_timer.start(10)
    sys.exit(app.exec_())