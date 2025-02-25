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
        -`AudioEffectGranula` object to perform granular synthesis, which involves breaking up an audio signal into small "grains" (tiny segments of audio), and then manipulating those grains in various ways, such as altering their pitch, speed, and position.
        -`granular.setSpeed(pitchFactor)`function allows you to modify the playback speed of the granular grains. The pitchFactor variable controls this speed, and thus the pitch. When pitchFactor is greater than 1.0, the grains play faster (raising the pitch), and when pitchFactor is less than 1.0, the grains play slower (lowering the pitch). This is the main mechanism for pitch modulation.
        -`granular.beginPitchShift(grainSize` function is used in the "ROBOT" command section of the code. This function allows the pitch shift to be simulated by adjusting the size of the grains. By manipulating the robotAmount (which is a parameter controlled via a GUI), the grain size is changed, affecting the texture of the sound and adding a "robotic" effect. A smaller grain size typically results in a more robotic, jittery sound.
        -`handleCommand()` function listens for specific commands ("PITCH", "ROBOT", "RESET") sent from the GUI. When the "PITCH" command is received, it updates the pitchFactor and adjusts the speed of the granular effect, effectively modulating the pitch. When the "ROBOT" command is received, the grain size is adjusted to simulate a robotic sound by modifying the pitch shift behavior. 


## Graphical Interface Explained 

