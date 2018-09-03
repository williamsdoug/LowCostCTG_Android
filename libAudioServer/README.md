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


### Network configuration
- Update main.py to reflect correct port addresses, as needed
- Currently requires assignment of two port addresses
  - port for RPC
  - port for PUB (used for pub/sub operations as part of implementation of callbacks)

### Configuration Options:
- Supports two modes of operation:
  - Recording emulation using existing recording (sample.wav)
  - Realtime audio capture
- Emulation:
  - To enable emulation either:
    - import libAudioEmulate in  wrapLibAudioServer.py
    - or import libAudio in wrapLibAudioServer.py AND set ENABLE_EMULATE = True (near line 10)
  - Playback speed
     - EMULATION_DELAY controls wait time for each 1K (0.125 seconds) worth of data
     - set EMULATION_DELAY = 1.0/8 for full speed recording
     - set EMULATION_DELAY = 1.0/8/n for increased recording speed
       - For example, setting n=4 will speed-up oplayback 4x
- Realtime audio capture:
  - import libAudio in wrapLibAudioServer.py
  - set ENABLE_EMULATE = False (near line 10)
     