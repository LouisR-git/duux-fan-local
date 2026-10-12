# Duux Bora Smart (Dehumidifier)

Local control specifications and supported features for the **Duux Bora Smart** dehumidifier.

## Supported Features

| Feature | Key | Command Payload | Value / Range |
|---|---|---|---|
| **Power** | `power` | `tune set power X` | `0`: off, `1`: on |
| **Mode** | `mode` | `tune set mode X` | `0`: auto, `1`: continuous |
| **Current Humidity** | `hum` | N/A (sensor) | `0` to `100` (%) |
| **Set Target Humidity** | `sp` | `tune set sp X` | `35` to `80` (%, step 5) |
| **Water Tank Full** | `err` | N/A (binary sensor) | `0`: normal, `8`: tank full |
| **Fan Speed** | `fan` | `tune set fan X` | `1`: Level 1, `0`: Level 2 |
| **Night Mode** | `sleep` | `tune set sleep X` | `0`: off, `1`: on |
| **Child Lock** | `lock` | `tune set lock X` | `0`: off, `1`: on |

## Home Assistant Entities

- **Humidifier**: Power on/off, target humidity setpoint (30% to 80%, step 5), current humidity reading.
- **Select**: Mode (`Auto`, `Continuous`), Fan Speed (`Level 1`, `Level 2`).
- **Switch**: Night Mode, Child Lock.
- **Sensor**: Current Humidity (%).
- **Binary Sensor**: Water Tank Full (problem sensor).
