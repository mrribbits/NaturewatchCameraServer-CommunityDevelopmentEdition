# -*- coding: utf-8 -*-
"""Automatically generate a unique SSID for the MyNaturewatch WiFi hotspot,
based on the Pi's serial number, and bring the hotspot up.

Works with both the onboard WiFi and USB WiFi dongles: it waits for a wireless
interface to appear (USB adapters enumerate a few seconds later than onboard
WiFi) and auto-detects its name instead of assuming it is called 'wlan0'.
"""
import glob
import os
import subprocess
import time


def find_wifi_interface(timeout=90):
    """Return the name of the first wireless interface, waiting up to `timeout`
    seconds for one to appear (a USB dongle can take a few seconds to come up)."""
    for _ in range(timeout):
        for marker in ("/sys/class/net/*/wireless", "/sys/class/net/*/phy80211"):
            found = glob.glob(marker)
            if found:
                return found[0].split("/")[-2]
        time.sleep(1)
    return None


# Wait for and detect the wireless interface (onboard WiFi or a USB dongle)
iface = find_wifi_interface()
if iface is None:
    print("No wireless interface found; cannot start the hotspot.")
    raise SystemExit(1)
print("Using wireless interface: " + iface)

# Generate a unique SSID based on the Pi's serial number
unique_id = subprocess.check_output(
    r"sed -n 's/^Serial\s*: 0*//p' /proc/cpuinfo", shell=True
)
unique_ssid = f"MyNaturewatch-{unique_id.strip().decode('utf-8')[-8:]}"

print("Updating hotspot")

os.system("sudo iw reg set GB")
os.system("sudo nmcli r wifi on")
os.system("sudo nmcli con delete id Hotspot")
os.system("sudo nmcli con add type wifi con-name hotspot")
os.system("sudo nmcli device wifi hotspot ssid " + unique_ssid + " password badgersandfoxes ifname " + iface)
os.system("sudo nmcli connection modify Hotspot connection.autoconnect yes")
os.system("sudo systemctl restart NetworkManager")
time.sleep(5)
os.system("sudo nmcli con up Hotspot")
