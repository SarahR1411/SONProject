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
AudioRecordQueue    audioQueue;
AudioOutputI2S      audioOutput;

// Connections
AudioConnection patchCord1(micInput, 0, granular, 0);
AudioConnection patchCord2(granular, 0, audioQueue, 0);
AudioConnection patchCord3(granular, 0, audioOutput, 0);
AudioConnection patchCord4(granular, 0, audioOutput, 1);

AudioControlSGTL5000 audioShield;
int16_t granularMemory[GRANULAR_MEMORY_SIZE];

// Parameters
float pitchFactor = 1.0;
float robotAmount = 0.0;
const int audioBlockSize = 128;

void setup() {
    Serial.begin(921600);
    AudioMemory(120);
    
    audioShield.enable();
    audioShield.inputSelect(AUDIO_INPUT_MIC);
    audioShield.micGain(30);
    audioShield.volume(0.5);
    
    granular.begin(granularMemory, GRANULAR_MEMORY_SIZE);
    granular.beginPitchShift(1.0);
    audioQueue.begin();
}

void loop() {
    // Send audio data to GUI
    if (audioQueue.available() >= 1) {
        int16_t *buffer = audioQueue.readBuffer();
        Serial.write((uint8_t*)buffer, audioBlockSize * sizeof(int16_t));
        audioQueue.freeBuffer();
    }

    // Receive commands from GUI
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
    else if (cmd.startsWith("ROBOT")) {
        robotAmount = cmd.substring(6).toFloat();
        
        // Simulate robotization using pitch shift with grain size
        float grainSize = 50 + (robotAmount * 50);  
        granular.beginPitchShift(grainSize);
    }
    else if (cmd == "RESET") {
        pitchFactor = 1.0;
        robotAmount = 0.0;
        granular.setSpeed(1.0);
        granular.stop();  // Stop granular processing to reset
    }
}
