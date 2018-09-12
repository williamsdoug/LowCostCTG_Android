# TocopatchServer

### Exposed Endpoint (libTocopatch):

- Exposes TocoListener object from wrapTocopatchServer.py (combined libTocopatchDevice.py and libTocopatchSignal.py)
  - RPC:  
    - TocoListener() => 'libTocopatch__init'
    - TocoListener.go() => 'libTocopatch__go'
    - TocoListener.stop() => 'libTocopatch__stop'
    - TocoListener.wait() => 'libTocopatch__wait'
    - TocoListener.get_start_time() => 'libTocopatch__get_start_time'
    - TocoListener.get_sample_rate() => 'libTocopatch__ get_sample_rate'
    - TocoListener.getData() => 'libTocopatch__getData'
    - TocoListener.update_skew() => 'libTocopatch__update_skew'
    - TocoListener.teardown() => 'libTocopatch__teardown'
    
  - pub/sub used for callbacks:
   - self.connection_callback => 'connection' message
   - self.update_callback => 'update' message
   - self.completion_callback = 'completion' message

- Note: Some refactoring of original code in wrapTocopatchServer.py to avoid back-to-back calls during callback functions


### Operaton
- cd libTocopatchServer
- python main.py


### Configuration (CONFG.py)

#### Network configuration
- Update CONFIG.py to reflect correct port addresses, as needed
- Currently requires assignment of two port addresses
  - port for RPC
  - port for PUB (used for pub/sub operations as part of implementation of callbacks)

#### Tocopatch configuration:
- Supports two modes of operation:
  - Realtime tocopatch capture
  - Recording emulation using existing recording (sample.wav)
- Emulation (using HeartyPatch_Listener or HeartyPatch_Emulator):
  - Select library
    - TOCO_ENABLE_EMULATE = True selects HeartyPatch_Emulator
    - TOCO_ENABLE_EMULATE = False selects HeartyPatch_Listener
  - Playback speed
     - EMULATION_SPEEDUP controls wait time between 1 seconbds worth of data
     - set EMULATION_SPEEDUP = 1.0 for full speed recording
     - set EMULATION_SPEEDUP = n for increased recording speed
       - For example, setting n=4 will speed-up playback 4x
     