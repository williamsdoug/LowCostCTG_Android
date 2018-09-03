# LowCostCTG_Client

- Minimal Client-only version.  Primarily UI and data management
- Does not include any code associated with served operations 
  
  
### Configuration (CONFIG.py)

#### Network Configuration
- ZMQ_CLIENT_ADDRESS_SPEC : specified IP address and port by service endpoint
  - For services with callbacks, 2 ports are required (REQ/REP and PUB/SUB )

### To Do:

- Functions not yet moved to server implementation:
  - TocoPatch processing
  - Selective functions used when importing data
  - Rules engine and related code 