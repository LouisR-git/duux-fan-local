# Option B — Mosquitto (Anonymous TLS)

Quickest local control for testing/labs. 

## 1. Install Mosquitto

Any Linux host will work. Below is an example using a **Proxmox LXC container**.

You can use this helper script (optional but easy):
👉 https://community-scripts.github.io/ProxmoxVE/scripts?id=mqtt

> ✅ No need for a privileged container.

## 2. Create self-signed certificates

```bash
mkdir -p /etc/mosquitto/certs/
openssl req -x509 -nodes -newkey rsa:2048 \
  -keyout /etc/mosquitto/certs/collector3.cloudgarden.nl.key \
  -out /etc/mosquitto/certs/collector3.cloudgarden.nl.crt \
  -days 3650 \
  -subj "/CN=collector3.cloudgarden.nl" \
  -addext "subjectAltName=DNS:collector3.cloudgarden.nl"
```

Then set ownership and permissions :

```bash
chown -R mosquitto:mosquitto /etc/mosquitto/certs/
chmod 640 /etc/mosquitto/certs/collector3.cloudgarden.nl.key
chmod 644 /etc/mosquitto/certs/collector3.cloudgarden.nl.crt
```

## 3. Mosquitto configuration

Edit `/etc/mosquitto/mosquitto.conf`:

```ini
user root  # Required to bind to port 443
```

> ⚠️ **Warning:** Running Mosquitto as `root` is not recommended. Use this approach only in isolated or controlled environments. Alternatively, you can use `iptables`/`nftables` to forward connections to a non-root MQTT listener port or set up `port forwarding (DNAT)` on your router to redirect traffic ...

Then remove the default config:

```bash
rm /etc/mosquitto/conf.d/default.conf
```

Create a custom config at `/etc/mosquitto/conf.d/duux-fan.conf`:

```ini
listener 443
allow_anonymous true

# TLS settings
certfile /etc/mosquitto/certs/collector3.cloudgarden.nl.crt
keyfile /etc/mosquitto/certs/collector3.cloudgarden.nl.key
require_certificate false
tls_version tlsv1.2
```

## 4. Restart the broker

```bash
service mosquitto restart
```
