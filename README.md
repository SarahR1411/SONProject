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

