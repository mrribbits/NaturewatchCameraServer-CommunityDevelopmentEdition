# My Naturewatch Camera — fork notes

This is a fork of the [Community Development Edition](https://github.com/interactionresearchstudio/NaturewatchCameraServer-CommunityDevelopmentEdition),
modified so the image **builds and runs on a current Raspberry Pi OS Bookworm base**.
It was first set up on a **Raspberry Pi Zero v1.3** (which has no WiFi, so it uses a
USB WiFi dongle) with a **Camera Module 3**, and it also runs on Pi models that have
**onboard WiFi** — any "W" Zero or a full‑size Pi — where **no dongle is needed**
(see [Hardware notes](#hardware-notes)).

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
and auto-detect its name. (This also means the same script works unchanged on
boards with onboard WiFi — it just finds the built-in `wlan0`.)

### 3. Hotspot joinable by modern phones/laptops — `helpers/cfgsetup.py`
NetworkManager 1.42 brings the hotspot up in WPA2/WPA3 "transition mode"
(`key_mgmt "WPA-PSK WPA-PSK-SHA256 SAE"`). Many WiFi drivers can't do
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

### Model-aware CPU under-clock — `install.sh`
Upstream always sets `arm_freq=600` (a WiFi-stability fix specific to the Pi
Zero / Zero W). That needlessly slows faster boards, so it's now wrapped in a
`config.txt` board-model filter:

```
[pi0]
arm_freq=600
[all]
```

The firmware applies the 600 MHz under-clock **only** on a Pi Zero / Zero W;
every other model (Pi 3, Zero 2 W, …) ignores it and runs at full speed. One
image adapts to whatever board it's flashed into — no hand-editing after
flashing. (Reasonable candidate for upstreaming.)

### Activity LED as a heartbeat — `install.sh`
Upstream disables the green activity LED (`act_led_trigger=none`). Changed to
`act_led_trigger=heartbeat` so a running Pi visibly double-blinks — a handy
"it's alive" signal for a headless board. Set it back to `none` for a discreet
field camera.

### (Optional) `rt2800usb.nohwcrypt=1` in `cmdline.txt`
Added during debugging to force software WiFi encryption on the Ralink USB
dongle. It was **not** the actual fix (the PMF change was), is a no-op on boards
that don't use that dongle, and is harmless to remove.

## Hardware notes

### WiFi: onboard vs. USB dongle
- **Boards with onboard WiFi need no adapter.** Any "W" Zero (**Pi Zero W**,
  **Pi Zero 2 W**) or a full-size Pi (**Pi 3 A+/B+**, **Pi 4**, …) has built-in
  WiFi. Leave the dongle and OTG adapter out entirely — the hotspot runs on the
  onboard radio, and `cfgsetup.py` auto-detects its `wlan0`.
- **The original Pi Zero (v1.3) has no WiFi**, so it needs a **USB WiFi dongle**
  plus a **micro-USB (male) → USB-A (female) OTG adapter** on the Zero's inner
  data port. The dongle **must support AP (access point) mode with an in-kernel
  driver** — a **Ralink RT5370/RT5372** (e.g. **Panda PAU05**, driver
  `rt2800usb`) works. Avoid Realtek **RTL8188** dongles (station/monitor only —
  no AP mode).

### Camera
- **Camera Module 3** (`imx708`).
- The cable depends on the board: the **narrow Pi Zero camera cable** for
  Zero-family boards, or the **standard (wider) Raspberry Pi camera cable** for
  full-size boards (Pi 3 A+/B+, Pi 4). Camera Module 3 ships with the standard
  cable; the narrow one is a separate Zero-specific part.

### Power
- A Pi Zero sips power. Full-size boards (Pi 3, etc.) draw noticeably more — use
  a solid **5V / 2.5A** supply and expect shorter battery life if running from a
  pack.

## Shopping list

> The WiFi adapter and OTG adapter below are **only for the original Pi Zero
> (v1.3)**. On a Zero W, Zero 2 W, or full-size Pi, skip them — WiFi is built in.
> Full-size boards also use the **standard** camera cable, not the Zero one.

- Pi Zero: https://www.pishop.us/product/raspberry-pi-zero/?src=raspberrypi
- Heat Sink: https://www.pishop.us/product/aluminum-heatsink-for-raspberry-pi-zero/?searchid=0&search_query=pi+zero+heatsink
- Camera Module 3: https://www.canakit.com/raspberry-pi-camera-module-3.html?defpid=4836
- Camera cable (Zero): https://www.canakit.com/raspberry-pi-zero-camera-cable.html
- MicroSD card: https://tinyurl.com/2w6fjwmf
- USB-A to Micro-B Cable (x2): https://tinyurl.com/589drvpc
- Plastic container: https://tinyurl.com/5e82759e
- Battery: https://tinyurl.com/35abfy8x
- Panda PAU05 WiFi adapter *(original Pi Zero only)*: https://tinyurl.com/y2z498ny

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
| `install.sh` | skip full upgrade; non-interactive apt; camera config fix (`start_x=0`, `camera_auto_detect=1`); libcamera version sync; model-aware `arm_freq=600` under a `[pi0]` filter *(personal)*; heartbeat LED *(personal)* |
| `helpers/cfgsetup.py` | wait-for + auto-detect wireless interface; WPA2 + PMF-disable; US region *(personal)*; channel 6 *(personal)* |
| `cmdline.txt` | *(personal, optional)* `rt2800usb.nohwcrypt=1` |
