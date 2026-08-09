# My Naturewatch Camera — fork notes

This is a fork of the [Community Development Edition](https://github.com/interactionresearchstudio/NaturewatchCameraServer-CommunityDevelopmentEdition),
modified so the image **builds and runs on a current Raspberry Pi OS Bookworm base**,
on a **Raspberry Pi Zero v1.3 with a USB WiFi dongle and a Camera Module 3**.

The changes fall into two groups: general fixes (proposed back upstream) and
personal customizations (specific to my setup — not for upstream).

## General fixes (submitted upstream as a PR)

These make the image build and run correctly on Bookworm for anyone, regardless
of region or hardware preference.

### 1. Image build no longer hangs — `install.sh`, `os/config`
On the pinned base image, the full `apt-get upgrade` hits an interactive dpkg
prompt and then hangs indefinitely regenerating the arm64 (v8) initramfs under
32‑bit armhf QEMU emulation. Fix: skip the full upgrade
(`ADMIN_TOOLKIT_UPDATE_PACKAGES=no`; removed the `apt-get upgrade` /
`dist-upgrade` calls) and make apt non-interactive. The base kernel runs the
camera fine and every needed package is installed explicitly.

### 2. USB WiFi dongle support — `helpers/cfgsetup.py`
The hotspot script assumed the wireless interface always exists and is named
`wlan0`. A USB dongle enumerates a few seconds later and can get a different
name, so the hotspot never started. Fix: wait for a wireless interface to appear
and auto-detect its name.

### 3. Hotspot joinable by modern phones/laptops — `helpers/cfgsetup.py`
NetworkManager 1.42 brings the hotspot up in WPA2/WPA3 "transition mode"
(`key_mgmt "WPA-PSK WPA-PSK-SHA256 SAE"`). Many USB WiFi drivers can't do
WPA3/PMF in AP mode, so the network is invisible on some phones and fails the
handshake on others (shown as a wrong password). Fix: force plain **WPA2-PSK**
and **disable PMF** (`wifi-sec.pmf 1`).

### 4. Camera actually detected on Bookworm — `install.sh`
The bundled CustomPiOS `raspicam` module sets the **legacy** camera stack
(`start_x=1`, `camera_auto_detect=0`), but this image uses picamera2/libcamera,
so the camera was never detected. The base image can also ship a `libcamera0.3`
that mismatches `libpisp`, crashing rpicam/picamera2 with an undefined-symbol
error (`compute_optimal_stride`). Fix: switch to libcamera auto-detection
(`start_x=0`, `camera_auto_detect=1`) and sync the libcamera libraries to
matching versions.

## Personal customizations (this fork's `main` only — not upstream)

These reflect my location and preferences and are intentionally kept out of the
upstream PR.

### WiFi region set to US — `helpers/cfgsetup.py`
Upstream uses `iw reg set GB` (it's a UK project). Changed to `iw reg set US` so
the hotspot uses US-legal channels.

### Hotspot locked to channel 6 — `helpers/cfgsetup.py`
`nmcli connection modify Hotspot 802-11-wireless.band bg 802-11-wireless.channel 6`.
Channel 6 is legal everywhere and visible to every device, which avoids the
UK-only high channels (12/13) that US phones won't display.

### Activity LED as a heartbeat — `install.sh`
Upstream disables the green activity LED (`act_led_trigger=none`). Changed to
`act_led_trigger=heartbeat` so a running Pi visibly double-blinks — a handy
"it's alive" signal for a headless board. Set it back to `none` for a discreet
field camera.

### (Optional) `rt2800usb.nohwcrypt=1` in `cmdline.txt`
Added during debugging to force software WiFi encryption. It was **not** the
actual fix (the PMF change was) and is harmless to remove.

## Hardware notes (Pi Zero v1.3)

- The **Pi Zero v1.3 has no onboard WiFi**, so it needs a **USB WiFi dongle**
  plus a **micro-USB (male) → USB-A (female) OTG adapter** on the Zero's inner
  data port.
- The dongle **must support AP (access point) mode with an in-kernel driver**.
  A **Ralink RT5370/RT5372** (e.g. **Panda PAU05**, driver `rt2800usb`) works.
- Camera: **Raspberry Pi Camera Module 3** (`imx708`), via the narrow **Pi Zero
  camera cable**.

## Shopping list
- Pi Zero: https://www.pishop.us/product/raspberry-pi-zero/?src=raspberrypi
- Heat Sink: https://www.pishop.us/product/aluminum-heatsink-for-raspberry-pi-zero/?searchid=0&search_query=pi+zero+heatsink
- Camera Module 3: https://www.canakit.com/raspberry-pi-camera-module-3.html?defpid=4836
- Camera cable: https://www.canakit.com/raspberry-pi-zero-camera-cable.html
- MicroSD card: https://tinyurl.com/2w6fjwmf
- USB-A to Micro-B Cable (x2): https://tinyurl.com/589drvpc
- Plastic container: https://tinyurl.com/5e82759e
- Battery: https://tinyurl.com/35abfy8x
- Panda PAU05 WiFi adapter: https://tinyurl.com/y2z498ny


## Using the camera

1. Power on. After ~1–2 minutes the Pi broadcasts a WiFi hotspot named
   **`MyNaturewatch-XXXXXXXX`**.
2. Join it with password **`badgersandfoxes`**.
3. Open **`http://10.42.0.1`** (or `http://mynaturewatchcamera.local/`) for the
   camera interface.

Default OS login (e.g. over SSH): user **`pi`**, password **`badgersandfoxes`** —
change this if the camera will be on a network you don't control.

## Files changed

| File | Change |
| --- | --- |
| `os/config` | `ADMIN_TOOLKIT_UPDATE_PACKAGES=no` |
| `install.sh` | skip full upgrade; non-interactive apt; camera config fix (`start_x=0`, `camera_auto_detect=1`); libcamera version sync; heartbeat LED *(personal)* |
| `helpers/cfgsetup.py` | wait-for + auto-detect wireless interface; WPA2 + PMF-disable; US region *(personal)*; channel 6 *(personal)* |
| `cmdline.txt` | *(personal, optional)* `rt2800usb.nohwcrypt=1` |
