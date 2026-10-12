# Option C — Home Assistant Mosquitto Broker Add-on (TLS + Authentication)

If you are running Home Assistant OS or Supervised with the official **Mosquitto broker** add-on, you can configure it directly to accept your Duux device without needing a separate VM or container.

---

## 1. Set Up DNS Redirection

In your router or local DNS server (UniFi, AdGuard Home, Pi-hole, etc.), redirect the Duux cloud hostnames to your Home Assistant server IP:

```text
collector3.cloudgarden.nl → <HOME_ASSISTANT_IP>
collector.cloudgarden.nl  → <HOME_ASSISTANT_IP>
```

---

## 2. Generate SSL Certificates

Open the Home Assistant Terminal (via the **Terminal & SSH** or **Advanced SSH & Web Terminal** add-on) and generate the self-signed certificates:

```bash
mkdir -p /ssl/mqtt
openssl req -x509 -nodes -newkey rsa:2048 \
  -keyout /ssl/mqtt/collector3.cloudgarden.nl.key \
  -out /ssl/mqtt/collector3.cloudgarden.nl.crt \
  -days 3650 \
  -subj "/CN=collector3.cloudgarden.nl" \
  -addext "subjectAltName=DNS:collector3.cloudgarden.nl,DNS:collector.cloudgarden.nl"
```

---

## 3. Extract Fan Credentials via `socat`

Duux devices authenticate to MQTT using the device MAC address as the username and a 64-character token as the password.

1. Ensure the Mosquitto add-on is temporarily **stopped** so port `443` is free.
2. Install `socat` in the HA Terminal (if not already installed):
   ```bash
   apk add socat
   ```
3. Run `socat` to proxy and capture credentials during the TLS handshake:
   ```bash
   socat -v TLS-LISTEN:443,fork,cert=/ssl/mqtt/collector3.cloudgarden.nl.crt,key=/ssl/mqtt/collector3.cloudgarden.nl.key,verify=0 TLS:collector3.cloudgarden.nl:443,verify=0
   ```
4. Power-cycle the fan (unplug, wait 5 seconds, reconnect).
5. Look at the terminal output for the username (`[MAC_ADDRESS]`) and password (`[64-character token]`).
6. Press `Ctrl+C` to stop `socat`.

---

## 4. Create the Fan User in Home Assistant

Home Assistant's Mosquitto add-on authenticates against Home Assistant users:

1. Navigate to **Settings > People > Users** in Home Assistant.
2. Click **Add User**.
3. Set the **Username** to the MAC address extracted in step 3.
4. Set the **Password** to the 64-character token extracted in step 3.
5. Set role to standard **User** and save.

---

## 5. Configure & Start Mosquitto Broker Add-on

1. Go to **Settings > Add-ons > Mosquitto broker > Configuration**.
2. Under **Network**, expose port `443/TCP` (or change `8883/TCP` to `443`).
3. Set **Require Client Certificate** to `false`.
4. Add the following to `/share/mosquitto/mosquitto.conf` (or `/ssl/mosquitto.conf` depending on your setup):
   ```ini
   listener 443
   certfile /ssl/mqtt/collector3.cloudgarden.nl.crt
   keyfile /ssl/mqtt/collector3.cloudgarden.nl.key
   ```
5. **Start** (or restart) the Mosquitto broker add-on.
6. Power-cycle the fan and check the Mosquitto logs to confirm the device successfully connected.

---

## 6. Configure Duux Local Integration

1. Go to **Settings > Devices & Services > Add Integration**.
2. Search for **Duux Fan Local**.
3. Enter your Mosquitto host (e.g. `127.0.0.1` or Home Assistant IP), port `443`, and your regular Home Assistant MQTT user credentials.
4. Select your device model and enter the MAC address.
