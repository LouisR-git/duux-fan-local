# Duux Whisper Flex 2 (Fan)

Local control specifications and supported features for the **Duux Whisper Flex 2** fan.

## Supported Features

| Feature | Key | Command Payload | Value / Range |
|---|---|---|---|
| **Power** | `power` | `tune set power X` | `0`: off, `1`: on |
| **Mode** | `mode` | `tune set mode X` | `0`: fan mode, `1`: natural wind |
| **Speed** | `speed` | `tune set speed X` | `1` to `30` |
| **Timer** | `timer` | `tune set timer X` | `0` to `12` hours |
| **Horizontal Oscillation** | `horosc` | `tune set horosc X` | `0`: off, `1`: 30°, `2`: 60°, `3`: 90° |
| **Vertical Oscillation** | `verosc` | `tune set verosc X` | `0`: off, `1`: 45°, `2`: 100° |
| **Night Mode** | `night` | `tune set night X` | `0`: off, `1`: on |
| **Child Lock** | `lock` | `tune set lock X` | `0`: off, `1`: on |
| **Battery Level** | `batlvl` | N/A (sensor) | `0` to `10` (mapped to 0–100%) |
| **Charging Status** | `batcha` | N/A (binary sensor) | `0`: not charging, `1`: charging |

## Home Assistant Entities

- **Fan**: Power on/off, speed (1–30), preset modes (`Fan`, `Natural`).
- **Select**: Horizontal oscillation (`Off`, `30°`, `60°`, `90°`), Vertical oscillation (`Off`, `45°`, `100°`).
- **Switch**: Night Mode, Child Lock.
- **Sensor**: Battery Level (%).
- **Binary Sensor**: Battery Charging Status.
- **Number**: Timer (`0` to `12` hours), Speed (`1` to `30`).

### Known Limitations

- **Charging Status** does not update automatically when the battery is fully charged. The device only refreshes this attribute when the Power state changes (firmware limitation).
