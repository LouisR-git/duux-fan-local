---
name: New device support request
about: Request the addition of a new Duux device (Fan, Purifier, Heater...) to the integration
labels: 'enhancement, new-device'
---

## Device Information
- **Exact Model Name**: (e.g. Duux Whisper Flex Ultimate, Duux Threesixty 2)
- **Device Type**: (e.g. Fan, Heater, Humidifier, Air Purifier)

## 📡 MQTT Payload Capture
To add support for your device, we need to know how it communicates.
Please connect to your local MQTT broker using a tool like [MQTT Explorer](http://mqtt-explorer.com/) and subscribe to the `#` topic.

## Supported Commands
Using the official Duux app (while sniffing MQTT traffic), change the state of your device (turn it on, change speed, change mode, etc.) and record the commands sent to the `sensor/<device_id>/command` topic.

List the commands you found below:

| Feature being changed | Command Payload observed | Value meaning     |
|-----------------------|--------------------------|-------------------|
| Power                 | `tune set power 1`       | `0`: off, `1`: on |
| Example: Speed        | `tune set speed 5`       | `1` to `30`       |
| ...                   | ...                      | ...               |

## Testing Check
- [ ] I have successfully routed my device's DNS to my local MQTT broker.
- [ ] I can see my device connecting to my local broker.
- [ ] I have verified that publishing the commands listed above actually controls the device.

## Additional context
Add any other details, screenshots, logs, or quirks about this device.
