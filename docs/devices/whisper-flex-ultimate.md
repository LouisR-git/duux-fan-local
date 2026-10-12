# Duux Whisper Flex Ultimate (Fan)

Local control specifications and supported features for the **Duux Whisper Flex Ultimate** fan.

## Supported Features

| Feature | Key | Command Payload | Value / Range |
|---|---|---|---|
| **Power** | `power` | `tune set power X` | `0`: off, `1`: on |
| **Mode** | `mode` | `tune set mode X` | `0`: regular, `1`: natural, `2`: night |
| **Speed** | `speed` | `tune set speed X` | `1` to `30` |
| **Timer** | `timer` | `tune set timer X` | `0` to `12` hours |
| **Horizontal Oscillation** | `swing` | `tune set swing X` | `0`: off, `1`: 30°, `2`: 60°, `3`: 90° |
| **Vertical Oscillation** | `tilt` | `tune set tilt X` | `0`: off, `1`: 90°, `2`: 105° |
| **Setpoint Temperature** | `sp` | `tune set sp X` | `17` to `28` °C |

## Home Assistant Entities

- **Fan**: Power on/off, speed (1-30).
- **Select**: Fan Mode (`Regular`, `Natural`, `Night`), Swing (`Off`, `30°`, `60°`, `90°`), Tilt (`Off`, `90°`, `105°`).
- **Number**: Speed (`1` to `30`), Timer (`0` to `12` hours), Setpoint Temperature (`17` to `28` °C).
