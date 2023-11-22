# Set up

Add the following to your configuration.yaml:
```yaml
sensor:
  - platform: apsystemsapi_local
    ip_address: [YOUR_IP_ADDRESS]
    name: [SOME_ARBITRARY_NAME]

number:
  - platform: apsystemsapi_local
    ip_address: [YOUR_IP_ADDRESS]
    name: [SOME_ARBITRARY_NAME]

switch:
  - platform: apsystemsapi_local
    ip_address: [YOUR_IP_ADDRESS]
    name: [SOME_ARBITRARY_NAME]
```