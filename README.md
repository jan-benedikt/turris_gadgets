# Turris Gadgets for Home Assistant

Modern Home Assistant integration for the Turris Gadgets USB dongle developed
by CZ.NIC and Jablotron.

> [!NOTE]
> The integration has been verified with real Turris Gadgets hardware,
> including receiving peripheral messages and controlling transmitter outputs.

## Current functionality

- UI setup with a serial-port connection test
- local push communication at 57,600 baud
- automatic loading of all 32 dongle slots
- admin-only sidebar panel for adding and removing peripherals in dongle memory
- dynamic entity creation and removal without reloading the integration
- JSON backup and restore of all dongle registration slots
- manual model override for unknown or incorrectly inferred peripherals
- camera/barcode-assisted entry of the 8-digit peripheral identifier
- real-time WebSocket monitor of radio messages forwarded by the dongle
- transparent product images for recognized peripherals in Home Assistant and
  the management panel
- automatic reconnect after a USB disconnect
- a Home Assistant Repairs notification after repeated connection failures
- optional raw RX/TX protocol logging, configurable from the integration UI
- serial-port reconfiguration and privacy-safe downloadable diagnostics
- parsing of both current and legacy `ID:...` firmware messages
- binary sensors for contacts, motion, vibration, smoke, tamper, battery,
  blackout and AC-88 relay state
- current and target temperature sensors for TP-82N
- event entities for RC-86K and JA-80L
- PGX and PGY switches
- loud-alarm and slow/fast chime sirens
- optional receiver-enrollment button
- Czech and English UI strings

## Installation

Copy `custom_components/turris_gadgets` into the Home Assistant configuration
directory and restart Home Assistant. Add **Turris Gadgets** under
**Settings → Devices & services**.

Prefer a stable Linux path such as `/dev/serial/by-id/...` to `/dev/ttyUSB0`.
The Home Assistant process or container must have permission to open the serial
device.

Raw protocol logging can be enabled during setup or later with **Configure** on
the integration page. It records device identifiers and can produce many log
entries, so leave it disabled during normal operation.

## Managing peripherals

Administrators can open **Turris Gadgets** in the Home Assistant sidebar to see
all 32 registration slots, add a peripheral to a free slot, remove a peripheral,
change an incorrectly detected model, create or restore a JSON slot backup, or
monitor received radio messages in real time. Recognized models include a
product image in the slot list, RF monitor, and their Home Assistant entities.
A new peripheral can be entered manually or by scanning the code on its label
with a supported browser camera. Entities are added and removed immediately;
the integration no longer needs to reload after every slot change.

The serial port can be changed with **Reconfigure** on the integration page.
The same page offers a diagnostics download that excludes serial paths, raw RF
messages, and peripheral identifiers.

Before restoring a slot backup, the panel lists every slot that would change
and asks for confirmation. Because the dongle protocol has no atomic bulk-write
command, keep the dongle connected until the restore finishes.

The original dongle firmware only forwards radio messages from peripherals that
are already registered. The live RF monitor therefore cannot discover an
unregistered sensor over the air; use the last 8 digits printed on its label.
Camera access may require HTTPS and browser support for the Barcode Detection
API. Manual entry is always available.

## Historical sources

This project is a clean rewrite of the 2015 MIT-licensed integration:

- <https://gitlab.nic.cz/turris/home-assistant-turris-gadgets>

The old integration is not compatible with current Home Assistant releases.

## Documentation

The [project wiki](https://github.com/jan-benedikt/turris_gadgets/wiki) contains
installation and configuration instructions for the current integration, a
device/entity reference, troubleshooting, and a Czech backup of the original
Turris Gadgets documentation:

- [Current integration](https://github.com/jan-benedikt/turris_gadgets/wiki)
- [Installation and setup](https://github.com/jan-benedikt/turris_gadgets/wiki/Instalace-a-nastaveni)
- [Peripheral management](https://github.com/jan-benedikt/turris_gadgets/wiki/Sprava-periferii)
- [Devices and entities](https://github.com/jan-benedikt/turris_gadgets/wiki/Podporovana-zarizeni-a-entity)
- [Original protocol reference](https://github.com/jan-benedikt/turris_gadgets/wiki/Referencni-manual)
