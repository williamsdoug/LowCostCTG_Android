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



#### LowCostCTG_Client

- Minimal Client-only version.  Primarily UI and data management
- Does not include any code associated with served operations 
- Functions not yet moved to server implementation:
  - TocoPatch processing
  - Selective functions used when importing data
  - Rules engine and related code 
     

#### libAudioServer

- Exposes audio_recorder object from libAudio.py (also libAudioEmulate.py when in emulation mode)
  - pub/sub used for callbacks
- Exposes combineExtractionResults from libUltrasound.py
- Note: Some refactoring of original code in wrapLibAudioServer.py to avoid back-to-back calls during callback functions


#### libDecelServer

- Exposes summarizeDecels and extractAllDecels from libDecel.py as RPC
- libDecelServer/main.py includes ZeroMQ RPC management and gasket
  

#### LowCostCTG_Development

- Integrated version including LowCostCTG_Client, libAudioServer and libDecelServer
- Can selectively enables which functions utilize RPC and which operations are performed locally
  - Selected in CONFIG
- See documentation for LowCostCTG_Client, libAudioServer and libDecelServer for other CONFIG.py copnfiguration options
