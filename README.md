
[![hacs_badge](https://img.shields.io/badge/HACS-Default-41BDF5.svg)](https://github.com/hacs/integration)
![HACS Action](https://github.com/MesserschmittX/hacs-nicehash-excavator/actions/workflows/hacs.yml/badge.svg?style=for-the-badge)
![Validate with hassfest](https://github.com/MesserschmittX/hacs-nicehash-excavator/actions/workflows/hassfest.yml/badge.svg)


# Nicehash Excavator Monitor
Home Assistant integration for Nicehash Excavator miner API

<!--Now with accompanying [UI Card](https://github.com/MesserschmittX/lovelace-nicehash-excavator-monitor-card) to better display all sensors.-->

(Excavator API Doku: https://github.com/nicehash/excavator/tree/master/api)


Available Sensors:
------
 - Combined hashrate for every individual mined algorithm
 - Hashrate for every card for all mined algorithms on that card
 - GPU temp for every card
 - Hotspot temp for every card
 - Vram temp for every card
 - CPU & RAM usage
 - Overtemp (true/false) for every card
 - Device information will show the Excavator version and build as well as a list of the installed GPU models


Available Switches:
------
- Switch for two diferent update speeds


Requirements:
------
- Home Assistant core-2021.12.5 or higher
- Excavator needs to be reachable from the network
- Your mining pc needs to be reachable from your Home Assistant instance


Install:
------
  - This integration is available in HACS (Home Assistant Community Store). HACS is a third party community store and is not included in Home Assistant out of the box
  - After downloading the integration you can add it to Home Assistant under Configuration -> Devices & Services
  - Miner name is the name of your mining rig
  - Host address is your_mining_pc_ip_v4
  - Excavator port is the unused_port_of_your_choise
  - The update intervals are between 1 and 3600 seconds (can be changed later in device configuration)
  - Confirm the dialog and your mining rig will be added shortly after testing the connection


Make Excavator available from the network:
------
 - If you are using the Nicehash Quick Miner:
   - Right-click the icon in the icon tray -> Settings -> Edit config file
   - Search "watchDogAPIHost" and set the value to "your_mining_pc_ip_v4"
   - Search "watchDogAPIPort" and remember the value (default is 18000) or change to another unused_port_of_your_choise
   - Save and close the config file
   - Create an inbound firewall rule allowing the previusly used port (watchDogAPIPort) to be accessed
   - You should now be able to access the Excavator API via your network
 - If you are running Excavator directly from the command line:
   - Add the command line arguments -wi your_mining_pc_ip_v4 and -wp unused_port_of_your_choise
     - Doku: https://github.com/nicehash/excavator#-command-line-parameters
   - Create an inbound firewall rule allowing the unused_port_of_your_choise to be accessed
   - You should now be able to access the Excavator API via your network
