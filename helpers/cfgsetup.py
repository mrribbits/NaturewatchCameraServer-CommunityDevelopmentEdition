# -*- coding: utf-8 -*-
"""Bring up the MyNaturewatch WiFi hotspot.

Hardened for USB WiFi dongles:
  * waits for a wireless interface to actually appear (USB dongles enumerate
    slower than onboard WiFi, so the original fire-once approach could miss it);
  * auto-detects the interface name (a USB dongle is often NOT called wlan0);
  * writes a diagnostic log to /boot/firmware/wifi-setup.log, which is readable
    from a Mac/PC by popping the SD card in, for headless debugging.
"""
import glob
import os
import subprocess
import time

LOG = "/boot/firmware/wifi-setup.log"


def log(msg):
    try:
        with open(LOG, "a", encoding="utf-8") as f:
            f.write(str(msg) + "\n")
    except Exception:
        pass
    print(msg)


def run(cmd):
    """Run a shell command, log it and its output, return exit code."""
    log("$ " + cmd)
    try:
        out = subprocess.run(
            cmd, shell=True, capture_output=True, text=True, timeout=60
        )
        if out.stdout.strip():
            log(out.stdout.rstrip())
        if out.stderr.strip():
            log("[stderr] " + out.stderr.rstrip())
        return out.returncode
    except Exception as e:
        log("[error] " + str(e))
        return 1


def find_wifi_iface(timeout=90):
    """Return the first wireless interface name, waiting up to timeout seconds."""
    for i in range(timeout):
        for marker in ("/sys/class/net/*/wireless", "/sys/class/net/*/phy80211"):
            hits = glob.glob(marker)
            if hits:
                return hits[0].split("/")[-2]
        if i in (0, 10, 30, 60):
            log("Waiting for a wireless interface to appear... (%ds)" % i)
        time.sleep(1)
    return None


log("\n==================== wifisetup run ====================")
run("uptime")
run("lsusb")
run("dmesg | grep -iE 'rt2|ralink|rt5370|firmware|usb ' | tail -40")

iface = find_wifi_iface(90)
log("Detected wireless interface: %r" % iface)

if not iface:
    log("NO WIRELESS INTERFACE FOUND. The dongle is not being recognized "
        "(missing driver/firmware, or not enumerating). See lsusb/dmesg above.")
    raise SystemExit(1)

# Report the interface's capabilities (does it support AP mode?)
run("iw dev")
run("iw list | grep -A10 'Supported interface modes'")

# Generate a unique SSID based on the Pi's serial number
try:
    unique_id = subprocess.check_output(
        r"sed -n 's/^Serial\s*: 0*//p' /proc/cpuinfo", shell=True
    )
    suffix = unique_id.strip().decode("utf-8")[-8:]
except Exception:
    suffix = "00000000"
unique_ssid = "MyNaturewatch-" + suffix
log("SSID: " + unique_ssid)

# Build the hotspot on the detected interface.
# Region US + a fixed 2.4GHz channel so the hotspot is visible and joinable on
# all US devices. The original GB region could park it on channel 12/13, which
# US phones won't display and Macs often can't associate with (shows up as a
# misleading "incorrect password").
run("iw reg set US")
run("nmcli r wifi on")
run("nmcli con delete id Hotspot")
run("nmcli con delete id hotspot")
rc = run(
    "nmcli device wifi hotspot ssid %s password badgersandfoxes ifname %s"
    % (unique_ssid, iface)
)
log("=> nmcli hotspot create exit code: %d" % rc)
run("nmcli connection modify Hotspot connection.autoconnect yes")
# Lock to 2.4GHz band + channel 6 (legal everywhere, visible to every device)
run("nmcli connection modify Hotspot 802-11-wireless.band bg 802-11-wireless.channel 6")
# Force plain WPA2 (RSN / CCMP-AES) only. NetworkManager's default hotspot can
# advertise legacy WPA/TKIP, which recent Apple devices refuse to show or join
# (network is invisible on iPhone, "wrong password" on Mac). WPA2-AES works
# on every modern client.
run("nmcli connection modify Hotspot "
    "wifi-sec.key-mgmt wpa-psk wifi-sec.proto rsn "
    "wifi-sec.pairwise ccmp wifi-sec.group ccmp")
run("systemctl restart NetworkManager")
time.sleep(5)
run("nmcli con up Hotspot")

# Final state, for the log
run("nmcli -t device")
run("ip -o addr show %s" % iface)
run("nmcli -s -f 802-11-wireless-security connection show Hotspot")
run("iw dev %s info" % iface)
log("==================== end wifisetup run ====================")
