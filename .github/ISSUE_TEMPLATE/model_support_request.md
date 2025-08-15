---
name: New fan support request
about: Request the addition of a new fan model to the integration
---

**Fan model and brand**
Provide the exact model name of the fan (including any version/revision if available).

**Endpoint verification**
- Provide the API/cloud endpoint URL: `mqtts://collector3.cloudgarden.nl:443`
- Confirm the endpoint is reachable: Yes/No
- Attach a sample API or MQTT connection log if possible.

**Local MQTT broker check**
- Connect your fan to a local MQTT broker following the install steps in the README.
- Confirm the device is connected to the local broker: Yes/No
- Provide evidence (e.g., MQTT Explorer screenshot or CLI output).

**MQTT topics**
List all relevant topics used by the fan :

Example table format (replace with your fan’s real topics):

| Feature   | Key      | Command Payload       | Values                               |
|-----------|----------|-----------------------|--------------------------------------|
| Power     | `power`  | `tune set power X`    | `0`: off, `1`: on                    |
| Mode      | `mode`   | `tune set mode X`     | `0`: fan mode, `1`: natural wind     |
| Speed     | `speed`  | `tune set speed X`    | `1` to `30`                          |

**Testing**
- Confirm that publishing to the command topics changes the fan state.
- Confirm that state topics update correctly after commands.

**Additional context**
Add any other details, screenshots, logs, or packet captures that may help in the integration.
