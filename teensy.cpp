#include <Audio.h>
#include <Wire.h>
#include <SPI.h>
#include <SD.h>
#include <SerialFlash.h>

#define GRANULAR_MEMORY_SIZE 12800
#define SERIAL_BUFFER_SIZE 256

// Audio objects
AudioInputI2S       micInput;
AudioEffectGranular granular;
AudioEffectFreeverb reverb;
AudioRecordQueue    audioQueue;
AudioMixer4         mixer;  
AudioOutputI2S      audioOutput;

// Connections
AudioConnection patchCord1(micInput, 0, granular, 0);
AudioConnection patchCord2(granular, 0, reverb, 0);
AudioConnection patchCord3(granular, 0, mixer, 0);  // Dry signal to mixer
AudioConnection patchCord4(reverb, 0, mixer, 1);    // Wet signal to mixer
AudioConnection patchCord5(mixer, 0, audioQueue, 0);
AudioConnection patchCord6(mixer, 0, audioOutput, 0);
AudioConnection patchCord7(mixer, 0, audioOutput, 1);

AudioControlSGTL5000 audioShield;
int16_t granularMemory[GRANULAR_MEMORY_SIZE];

// Parameters
float pitchFactor = 1.0;
float reverbMix = 0.0; // 0 = Dry, 1 = Full Reverb
const int audioBlockSize = 128;

void setup() {
    Serial.begin(921600);
    AudioMemory(150);  

    audioShield.enable();
    audioShield.inputSelect(AUDIO_INPUT_MIC);
    audioShield.micGain(30);
    audioShield.volume(0.5);

    granular.begin(granularMemory, GRANULAR_MEMORY_SIZE);
    granular.beginPitchShift(50.0);
    granular.setSpeed(1.0);

    // Configure reverb
    reverb.roomsize(0.6);  // 0.0 (small) to 1.0 (large hall)
    reverb.damping(0.5);

    // Mixer setup: Default to only dry signal
    mixer.gain(0, 1.0);  // Dry signal (original)
    mixer.gain(1, 0.0);  // Wet signal (reverb)

    audioQueue.begin();
}

void loop() {
    if (audioQueue.available() >= 1) {
        int16_t *buffer = audioQueue.readBuffer();
        Serial.write((uint8_t*)buffer, audioBlockSize * sizeof(int16_t));
        audioQueue.freeBuffer();
    }

    if (Serial.available()) {
        String cmd = Serial.readStringUntil('\n');
        handleCommand(cmd);
    }
}

void handleCommand(String cmd) {
    if (cmd.startsWith("PITCH")) {
        pitchFactor = cmd.substring(6).toFloat();
        granular.setSpeed(pitchFactor); 
    }
    else if (cmd.startsWith("REVERB")) {
        reverbMix = cmd.substring(7).toFloat();
        reverbMix = constrain(reverbMix, 0.0, 1.0);  // Keep in range

        // Adjust mixer for dry/wet balance
        mixer.gain(0, 1.0 - reverbMix);  // Dry signal
        mixer.gain(1, reverbMix);        // Wet signal
    }
    else if (cmd == "RESET") {
        pitchFactor = 1.0;
        reverbMix = 0.0;
        granular.setSpeed(1.0);
        granular.beginPitchShift(50.0);
        reverb.roomsize(0.6);
        x
        // Reset mixer to dry signal only
        mixer.gain(0, 1.0);
        mixer.gain(1, 0.0);
    }
}
