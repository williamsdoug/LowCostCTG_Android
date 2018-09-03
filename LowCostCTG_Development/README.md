# LowCostCTG_Development

- Integrated version including LowCostCTG_Client, libAudioServer and libDecelServer
- Can selectively enables which functions utilize RPC and which operations are performed locally

#### Configuration (CONFIG.py)

#### Network Configuration
- ZMQ_CLIENT_ADDRESS_SPEC : specified IP address and port by service endpoint
  - For services with callbacks, 2 ports are required (REQ/REP and PUB/SUB )

#### RPC/Local function 
- LIBAUDIO_USE_REMOTE : Determines whether libAudio functions peformed locally or remote
  - if local, see libAudioServer documentation for CONFIG.py settings
- LIBDECEL_USE_REMOTE : Determines whether libDecel functions peformed locally or remote

