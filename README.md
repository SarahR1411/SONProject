# SONProject

## The Science Behind It
In order to modify the pitch we would need to increase the frequency of the audio sample. However, if no treatment is done on the signal, tampering with the frequency would mean modifying the signal's duration. 
/*Our solution*/: Stretching the time then doubling the playback rate in order to lose less info than directly scaling the frequencies. The challenge is to stretch out all the global relationships but keep the local ones the same since they determine the frequencies.
-->  A way to do this is to divide the signal into little windows small enough to represent an instantaneous moment in time and move them apart in the output signal. We need to work with overlapping windows so that when we stretch the signal again, no audible gaps appear (WINDOW FUNCTION comes into play). 

<u>WINDOW FUNCTION</u>
Window function will find the perfect overlapping level in order to eliminate any audible discontinuity. 

If we randomly place the windows however, we will get weird fluttering (because the waves cancel out). To find the optimal window placement, we use autocorrelation (This is called the SOLA or Synchronous Overlap Add method/algorithm). 

<u>SOLA</u>
A time-domain technique, finds the best window placement searching using an error-minimization strategy.
Focuses on maintaining the perceptual quality of the audio during modifications in time and pitch.

Pitch shifting in the time domain isn’t the powerful enough (still get some fluttering) so we use the STFT (short time Fourrier transform often visualized as a log scale spectrogram (we just display the magnitude as the pixel brightness).


## Adapting to Teensy & Cpp Environments 
First we needed to import the Audio.h library as it allows to handle audio signals. We also import the Wire.h library since the mic is wire to the Teensy. 
When implementing this we kept the same trope, however, didn't implement SOLA directly because best window placement searching using an error-minimization strategy (as it is the case with WSOLA/SOLA) is computationally expensive and impractical for real-time execution on Teensy. 

In our teensy.cpp code, pitch modulation is achieved primarily through the use of the granular.setSpeed(pitchFactor) function and the granular.beginPitchShift(grainSize) function, which are part of the granular synthesis process:
1. **Granular Synthesis**:  
   - The audio is processed using granular synthesis, where the signal is broken into small "grains" of audio.  
   - These grains can be manipulated by changing their playback characteristics, such as pitch and speed.

2. **Speed Control for Pitch**:  
   - The `granular.setSpeed(pitchFactor)` function controls the speed of the granular effect.  
   - The `pitchFactor` variable is used to adjust the speed:  
     - A `pitchFactor > 1.0` increases the speed and raises the pitch.  
     - A `pitchFactor < 1.0` decreases the speed and lowers the pitch.  
   - This is the primary method for pitch modulation in the system.

3. **Robot Effect (Pitch Shifting)**:  
   - The `granular.beginPitchShift(grainSize)` function modifies the pitch shifting based on the size of the grains.  
   - When the `robotAmount` variable is changed, the grain size is adjusted:  
     - A smaller grain size results in a more robotic, jittery sound.  
     - The `robotAmount` is controlled through the GUI.

4. **Command Handling for Pitch Modulation**:  
   - The `handleCommand()` function listens for commands from the GUI to adjust pitch modulation:  
     - `"PITCH <value>"`: Updates the `pitchFactor` to modify the speed and pitch.  
     - `"ROBOT <value>"`: Adjusts the `robotAmount` to control the grain size, simulating a robotic sound.
     - `"RESET"`: Resets all parameters, restoring the default pitch (factor = 1.0).


## Graphical Interface Explained 
The Graphical User Interface (GUI) for the Teensy Pitch Shifter is built using PyQt5 and pyqtgraph, providing real-time visualization and interaction for audio manipulation. The interface is divided into several sections for controlling pitch, viewing visualizations, and interacting with recordings. Below is an overview of the GUI components:

### Live Visualizations Section
This section provides real-time graphical feedback of the audio being processed:

Waveform Plot: Displays the audio signal in the time domain. The waveform plot allows users to see the amplitude of the signal over time, offering a visual representation of the audio's structure.
Label: "Live Waveform"
Axis Labels: "Amplitude" (y-axis), "Time (samples)" (x-axis)
Spectrogram Plot: Visualizes the audio's frequency content over time using a spectrogram. This is especially useful for observing how the frequency characteristics of the audio evolve.
Label: "Live Spectrogram"
Axis Labels: "Frequency (Hz)" (y-axis), "Time (s)" (x-axis)
These visualizations update in real-time based on the processed audio data.

### Processing Controls
The control panel section contains various controls for adjusting pitch and applying audio effects.

Pitch Control:
A horizontal slider (range 50 - 200) allows the user to modify the pitch factor of the audio.
The Pitch Factor is displayed in a QLCDNumber widget, showing the current pitch multiplier (e.g., 1.0 for normal pitch, 2.0 for doubling the pitch).
Pitch Slider: Changes the pitch factor.
The GUI sends the updated pitch value to the Teensy when adjusted.
Presets:
A set of buttons that apply predefined pitch shifts for specific effects, such as 'Low Voice', 'High Voice', and 'Reset'.
When pressed, these buttons change the pitch factor and update the display accordingly.
This feature allows for quick switching between preset pitch effects.

### Recording Controls
Record Button: Starts or stops audio recording. The recorded audio is saved as a .wav file when stopped, and the filename is displayed in the status bar.
Play Button: Plays back the most recent recording if available. If no recording exists, a message is displayed indicating so.

### VU Meter (Volume Unit Meter)
The VU Meter is a progress bar that displays the input audio level as a percentage (0-100). The meter is updated in real-time to give visual feedback of the current amplitude.

### Serial Communication and Teensy Integration
The GUI communicates with the Teensy over a serial connection. Commands like "PITCH <value>" or "RESET" are sent to the Teensy via the serial port, which adjusts the pitch of the audio being processed.
The serial port is automatically detected based on the operating system, and the GUI attempts to connect to the correct device.
Custom Styles & User Interface Design
The interface uses a custom color palette to create a sleek, dark-themed design. The buttons and controls are designed to have smooth hover and press effects, offering a polished user experience.
The pitch control section includes a slider with a color change when interacted with, and the presets have a quick feedback feature when clicked.

### Summary of Key Features
 - Real-time waveform and spectrogram visualizations for monitoring the audio signal.
 - Pitch control slider with an LCD display showing the pitch factor.
 - Preset buttons for applying quick pitch modifications.
 - Recording and playback functionality for capturing and reviewing audio.
 - VU Meter to visualize audio levels.
 - Stylish and interactive design for ease of use.
