# Option A - EMQX (TLS + Authentication) — Recommended

Secure setup with **username/password** and **TLS**.  

## 1. Install EMQX

Any Linux host will work. Below is an example using a **Proxmox LXC container**.

You can use this helper script (optional but easy):
👉 https://community-scripts.github.io/ProxmoxVE/scripts?id=emqx

> ✅ No need for a privileged container.

## 2. Create self-signed certificates

Connect to your EMQX server, and create self-signed certificates :

```bash
openssl req -x509 -nodes -newkey rsa:2048 \
  -keyout /etc/emqx/certs/collector3.cloudgarden.nl.key \
  -out /etc/emqx/certs/collector3.cloudgarden.nl.crt \
  -days 3650 \
  -subj "/CN=collector3.cloudgarden.nl" \
  -addext "subjectAltName=DNS:collector3.cloudgarden.nl"
```

Then set ownership and permissions :

```bash
chown emqx:emqx /etc/emqx/certs/collector3.cloudgarden.nl.key /etc/emqx/certs/collector3.cloudgarden.nl.crt
chmod 600 /etc/emqx/certs/collector3.cloudgarden.nl.key
chmod 640 /etc/emqx/certs/collector3.cloudgarden.nl.crt
```

## 3. Get fan credentials

Install tool:
```bash
apt install -y socat
```

Run **socat** to listen TLS on **443** 
```bash
socat openssl-listen:443,reuseaddr,cert=/etc/emqx/certs/collector3.cloudgarden.nl.crt,key=/etc/emqx/certs/collector3.cloudgarden.nl.key,verify=0,openssl-min-proto-version=TLS1.2 STDIO > duux_mqtt_capture.log
```

Reboot the fan to force a new CONNECT.  

Stop the capture and look at the file `duux_mqtt_capture.log`, you should see something like :
```
▒MQTT▒[USERNAME_@MAC]sensor/[USERNAME_@MAC]/online{"online":false}[USERNAME_@MAC]@[PASSWORD_64_charsacters]
```

## 4. EMQX configuration
### 4.1. Create an authentication provider in EMQX

Go to EMQX dashboard `https://[EMQX_SERVER_IP]:18083/` (default creds: admin/public) :
- **Access Control** → **Authentication**  
- **Create** provider → **Password-based** → **Built-in Database**  

### 4.2. Add users
- **Access Control → Authentication** → **Users** → **Add**
Create the fan user :
- **[USERNAME_@MAC]** and **[PASSWORD_64_characters]**
Create a reader user :
- **Add user**: a **username** and a **password** (exemple: reader/reader)

### 4.3. Configure user authorizations
- **Access Control** → **Authorization**  
- **File** → **Settings**
- Add this rules at the begining of the file :
```
%% ===============================
%% ACL for user "reader"
%% Can only SUBSCRIBE to the "/sensor" topic
{allow, {user, "reader"}, subscribe, ["/sensor"]}.

%% ===============================
%% ACL for user "[USERNAME_@MAC]"
%% Can PUBLISH and SUBSCRIBE to "/sensor" and all its subtopics
{allow, {user, "[USERNAME_@MAC]"}, subscribe, ["/sensor", "/sensor/#"]}.
{allow, {user, "[USERNAME_@MAC]"}, publish,   ["/sensor", "/sensor/#"]}.
```

## 4.4. Configure EMQX TLS listener on :8883
Connect to your EMQX server and edit the EMQX config file `/etc/emqx/emqx.conf`. Add the SSL listener at the end of the file :
```
listeners.ssl.default {
  bind = 8883
  ssl_options {
    keyfile    = "/etc/emqx/certs/collector3.cloudgarden.nl.key"
    certfile   = "/etc/emqx/certs/collector3.cloudgarden.nl.crt"
    cacertfile = "/etc/emqx/certs/collector3.cloudgarden.nl.crt"
  }
}
```


## 5. Restart the broker

```bash
service emqx restart
```

## 6. Set port 443 redirection

```bash
nft add table ip nat
nft add chain ip nat prerouting { type nat hook prerouting priority 0 \; }
nft add chain ip nat output     { type nat hook output     priority 0 \; }
nft add rule ip nat prerouting  tcp dport 443 redirect to :8883
nft add rule ip nat output      tcp dport 443 redirect to :8883
```
