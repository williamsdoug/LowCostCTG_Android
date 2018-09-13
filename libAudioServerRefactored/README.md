# libAudioServer

### Exposed Endpoint (libAudio):

- Exposes audio_recorder object from libAudio.py (also libAudioEmulate.py when in emulation mode)
  - RPC:  
    - audio_recorder() => 'audio_recorder__init'
    - audio_recorder.stop() => 'audio_recorder__stop'
    - audio_recorder.wait() => 'audio_recorder__wait'
    - audio_recorder.get_start_time() => 'audio_recorder__get_start_time'
  - pub/sub used for callbacks:
   - self.update_callback => 'update' message
   - self.completion_callback = 'completion' message
- Indirectly exposes combineExtractionResults from libUltrasound.py
  - Currently exposed only as part of update and completion callbacks

- Note: Some refactoring of original code in wrapLibAudioServer.py to avoid back-to-back calls during callback functions


### Operaton
- cd libAudioServer
- python main.py


### Configuration (CONFG.py)

#### Network configuration
- Update CONFIG.py to reflect correct port addresses, as needed
- Currently requires assignment of two port addresses
  - port for RPC
  - port for PUB (used for pub/sub operations as part of implementation of callbacks)

#### Audio configuration:
- Supports two modes of operation:
  - Realtime audio capture
  - Recording emulation using existing recording (sample.wav)
- Realtime audio capture (using libAudio.py):
  - set USE_LIB_AUDIO_EMULATE = True
  - set ENABLE_EMULATE = False
- Emulation (using libAudio.py or LibAudioEmulate.py):
  - Select library
    - USE_LIB_AUDIO_EMULATE = True selects libAudioEmulate
    - USE_LIB_AUDIO_EMULATE = False selects libAudio
      - must also set ENABLE_EMULATE = True
  - Playback speed
     - EMULATION_SPEEDUP controls wait time between 1 seconbds worth of data
     - set EMULATION_SPEEDUP = 1.0 for full speed recording
     - set EMULATION_SPEEDUP = n for increased recording speed
       - For example, setting n=4 will speed-up playback 4x
     