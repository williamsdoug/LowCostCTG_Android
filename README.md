# LowCostCTG_Android

Porting of LowCostCTG / Combined Recorder to a client (UI) and a set of services for running on Android

### Porting Evolution

1. Restructure Scipy and Android dependent code into standalone services
     1. Currently uses ZeroMQ for RPC
1. Modify android-specific code (primarily android audio processing)
    1. Includes libAudiDetect code for discovery of bluetooth audio input and audio output devices
1. Add service lifecycle management code
1. Update data persistence code (patient and recording objects)
1. (optional) Replace ZMQ with native Android IPC mechanisms
4. Rewrite client code IO code to use native GUI elements


### Overall Structure

#### SplitRecorder

- Based on Combined Recorder
- Configurable to operate standalone or by making IPC/RPC calls to standalone services
- wrapLibAudioCommon.py responsible for basic IPC/RPC plumbing and callback handling
  - CONTAINS IP ADDRESS AND PORTS for served functions.  Update as appropriate
  - callbacks handled using pub/sub
- library specific wrappers control inclusion of selected remote services
  - wrapLibAudioClient.py - Basic audio processing and realtime FHR extraction
    - use import dummmy_extractAllDecels and dummy_summarizeDecels in recorder_ui.py for local (non-served) configuration
  - wrapLibDecel.py - FHR pattern detection code
    - use import dummmy_audio_recorder in recorder_ui.py for local (non-served) configuration
 - When configued for client/server operation, the following libraries can be demoved from client-side build:
   - libAudio.py, libAudioEmulate.py, libUltrasound.py, libQuality.py, wrapLibAudioServer.py
     - Also remove dummy functions and related imports from wrapLibAudioClient.py
   - libDecel.py, libSignalProcessing
     - Also remove dummy functions from wrapLibDecel.py
     

#### libAudioServer

- Exposes audio_recorder object from libAudio.py (also libAudioEmulate.py when in emulation mode)
  - pub/sub used for callbacks
- Exposes combineExtractionResults from libUltrasound.py
- Note: Some refactoring of original code in wrapLibAudioServer.py to avoid back-to-back calls during callback functions


#### libDecelServer

- Exposes summarizeDecels and extractAllDecels from libDecel.py as RPC
- libDecelServer/main.py includes ZeroMQ RPC management and gasket
  
