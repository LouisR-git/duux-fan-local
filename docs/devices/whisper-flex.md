# Duux Whisper Flex (Fan)

Local control specifications and supported features for the **Duux Whisper Flex** fan.

## Supported Features

| Feature | Key | Command Payload | Value / Range |
|---|---|---|---|
| **Power** | `power` | `tune set power X` | `0`: off, `1`: on |
| **Mode** | `mode` | `tune set mode X` | `0`: fan mode, `1`: natural wind, `2`: night mode |
| **Speed** | `speed` | `tune set speed X` | `1` to `26` |
| **Timer** | `timer` | `tune set timer X` | `0` to `12` hours |
| **Horizontal Oscillation** | `swing` | `tune set swing X` | `0`: off, `1`: on |
| **Vertical Oscillation** | `tilt` | `tune set tilt X` | `0`: off, `1`: on |

## Home Assistant Entities

- **Fan**: Power on/off, speed (1-26), preset modes (`Fan`, `Natural`, `Night`), oscillation.
- **Number**: Timer (`0` to `12` hours).
