# Turris Gadgets for Home Assistant

Modern Home Assistant integration for the Turris Gadgets USB dongle developed
by CZ.NIC and Jablotron.

> [!IMPORTANT]
> This is an early development version. Reading and controlling real hardware
> still needs to be verified against multiple dongle firmware versions.

## Current functionality

- UI setup with a serial-port connection test
- local push communication at 57,600 baud
- automatic loading of all 32 dongle slots
- automatic reconnect after a USB disconnect
- optional raw RX/TX protocol logging, configurable from the integration UI
- parsing of both current and legacy `ID:...` firmware messages
- binary sensors for contacts, motion, vibration, smoke, tamper, battery,
  blackout and AC-88 relay state
- current and target temperature sensors for TP-82N
- event entities for RC-86K and JA-80L
- PGX and PGY switches
- loud-alarm and slow/fast chime sirens
- optional receiver-enrollment button
- Czech and English UI strings

## Installation for development

Copy `custom_components/turris_gadgets` into the Home Assistant configuration
directory and restart Home Assistant. Add **Turris Gadgets** under
**Settings → Devices & services**.

Prefer a stable Linux path such as `/dev/serial/by-id/...` to `/dev/ttyUSB0`.
The Home Assistant process or container must have permission to open the serial
device.

Raw protocol logging can be enabled during setup or later with **Configure** on
the integration page. It records device identifiers and can produce many log
entries, so leave it disabled during normal operation.

## Historical sources

This project is a clean rewrite of the 2015 MIT-licensed integration:

- <https://gitlab.nic.cz/turris/home-assistant-turris-gadgets>
- <https://web.archive.org/web/20210621000745/https://wiki.turris.cz/gadgets/>

The old integration is not compatible with current Home Assistant releases.
