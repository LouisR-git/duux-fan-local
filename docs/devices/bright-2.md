# Duux Bright 2 (Air Purifier)

Local control specifications and supported features for the **Duux Bright 2** air purifier.

## Supported Features

| Feature | Key | Command Payload | Value / Range |
|---|---|---|---|
| **Power** | `power` | `tune set power X` | `0`: off, `1`: on |
| **Night Mode** | `night` | `tune set mode X` | `0`: normal, `1`: night mode |
| **Speed** | `speed` | `tune set speed X` | `0` to `4` (0 is auto) |
| **ION Setting** | `ion` | `tune set ion X` | `0`: off, `1`: on |
| **Filter Life** | `filter` | N/A (sensor) | `0` to `100` (%) |
| **PM 10** | `ppm` | N/A (sensor) | µg/m³ |
| **Air Quality** | `AQ` | N/A (sensor) | AQI value |
| **TVOC** | `TVOC` | N/A (sensor) | µg/m³ |

## Home Assistant Entities

- **Fan**: Power on/off, speed (1-4).
- **Switch**: Night Mode, ION Setting.
- **Sensor**: Filter Life (%), PM10 (µg/m³), Air Quality Index (AQI), TVOC (µg/m³).
- **Number**: Speed (`1` to `4`).
