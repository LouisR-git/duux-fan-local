# 🌀 Duux Fan – Local Integration for Home Assistant

**Take back control of your Duux fan - locally, privately, and cloud-free.**

This project allows you to use your **Duux Whisper Flex smart fan** entirely outside of Duux’s cloud ecosystem by redirecting its MQTT communication to a **local broker** , giving you full local control via **Home Assistant**.

No cloud. No account. No lag.  

## 📌 Supported Model

This integration has been tested and validated on the following model:

- **DUUX Whisper Flex 2**

Other models may work but are not officially supported.  
Please contribute your feedback to help improve compatibility.



## 📋 Overview

Duux fans communicate with the cloud using **MQTT over TLS**.  
By **spoofing the cloud hostname** and running your own MQTT broker, you can intercept this traffic and integrate the fan directly into **Home Assistant**.

### 🔁 Architecture Summary

```text
+----------------+         +--------------------------+
|  Duux Fan      |<------->|  Your Local Mosquitto    |
| (MQTT over TLS)|         |  on port 443 (TLS)       |
+----------------+         +-----------+--------------+
                                     |
                                     v
                        Home Assistant MQTT Integration
```


## 🧰 Prerequisites

You’ll need:

- 🧠 **Control over your local DNS resolution** (AdGuard, CoreDNS, dnsmasq…)
- 📡 **A self-hosted MQTT broker**, reachable as `collector3.cloudgarden.nl` on port 443
- 🛠️ Basic Linux CLI knowledge


## ⚙️ Setting Up the Local MQTT Broker

### 🔧 Mosquitto Setup (Port 443 + TLS)

Any Linux host will work. Below is an example using a **Proxmox LXC container**.

#### 1. 🧪 Create the container

You can use this helper script (optional but easy):  
👉 https://community-scripts.github.io/ProxmoxVE/scripts?id=mqtt

> ✅ No need for a privileged container.

#### 2. 🛡️ Mosquitto TLS Configuration

Edit `/etc/mosquitto/mosquitto.conf`:

```ini
user root  # Required to bind to port 443
```

⚠️ **Warning**: Running as root is not recommended. Use it only in isolated environments.

Then remove the default config:

```bash
rm /etc/mosquitto/conf.d/default.conf
```

Create a custom config at `/etc/mosquitto/conf.d/duux-fan.conf`:

```ini
listener 443
allow_anonymous true

# TLS settings
certfile /etc/mosquitto/certs/mosquitto.crt
keyfile /etc/mosquitto/certs/mosquitto.key
require_certificate false
tls_version tlsv1.2
```

#### 3. 🔐 Create Self-Signed Certificates

```bash
mkdir -p /etc/mosquitto/certs/
cd /etc/mosquitto/certs/

openssl genrsa -out mosquitto.key 2048
openssl req -new -key mosquitto.key -out collector3.cloudgarden.csr
```

📌 When prompted, set the **Common Name** (CN) to:
```
collector3.cloudgarden.nl
```

Then sign it:

```bash
openssl x509 -req -in collector3.cloudgarden.csr -signkey mosquitto.key -out mosquitto.crt -days 3650
```

#### 4. 🚀 Restart the broker

```bash
service mosquitto restart
```



## 🌐 Local DNS Spoofing

Redirect the Duux cloud MQTT hostname to your local MQTT server’s IP.

### Example: AdGuard DNS Rewrite

Go to AdGuard → Settings → DNS Rewrites:

```
collector3.cloudgarden.nl → 192.168.x.x  # Your Mosquitto IP
```

Other options: `dnsmasq`, `CoreDNS`, `Unbound`…



## 🔄 Reboot the Fan

To apply changes and reconnect:

- Unplug the fan
- Remove the battery
- Wait 2 seconds
- Replug

It should now connect to your **local MQTT broker on port 443** using TLS.


## 📡 Explanations

The fan uses MQTT topics to report its state and receive commands.

### 🔧 MQTT Broker:
```
mqtts://collector3.cloudgarden.nl:443
```

### 📤 Fan publishes to:

| Topic                         | Example Payload                                                                 |
|-------------------------------|----------------------------------------------------------------------------------|
| `sensor/{device_id}/in`       | `{"sub":{"Tune":[{"uid":"xyz","power":1,"mode":0,"speed":10,"timer": 0,"horosc": 0,"verosc": 0,"lock": 0,"night": 1,"batcha": 0,"batlvl": 10}]}}` |
| `sensor/{device_id}/online`   | `{"online":true,"connectionType":"mqtt"}`                                       |
| `sensor/{device_id}/update`   | `{"pid":"xyz","tune":"DUUX Whisper Flex 2"}`                                    |

### 📥 Fan subscribes to:

| Topic                          | Example Payload             |
|--------------------------------|-----------------------------|
| `sensor/{device_id}/command`   | `tune set speed 10`         |
| `sensor/{device_id}/config`    | _(Unused)_                  |
| `sensor/{device_id}/fw`        | _(Unused)_                  |



## ✅ Result

Your Duux fan is now fully **cloud-free** and controllable through **your local network** and **Home Assistant**.

Enjoy full privacy, instant response times, and true independence from proprietary services.


## 🛑 Disclaimer

This setup **spoofs a cloud domain** and runs services on privileged ports. Use only in **lab environments** or **isolated networks**.  
For educational and interoperability purposes only.


## 🙌 Credits

Based on reverse engineering, packet sniffing, vibe coding ~~and a lot of fan noise~~.  
Contributions welcome! 🛠️
