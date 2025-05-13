# Cisco SD-WAN Manager (vManage) sample API application
This application re-pushes (re-attaches) device templates to the list of devices.
Specify multiple devices by host name or by system IP. Wildcards accepted (?: any single character, *: any sequence of characters).

**Setup**
1. (optional) create virtual environment: `python3 -m venv repush`
2. (optional) activate virtual environment: `cd repush; source bin/activate`
3. Install "requests" python module: `pip install requests`
4. Edit the "set_env_sample.sh" file to match your environment
5. Set environmental variables: `source set_env_sample.sh`

**Operations**

Run `python vmanage_repush.py` without parameters to see the usage guidelines:
```
#python vmanage_repush.py
Usage: sdwan_repush.py <list of device names/system IPs. * and ? wildcards accepted>
This will re-attach/re-push device template configuration to specified devices

The following environment variables are expected:
MANAGER_ADDR: address/port of vManage
MANAGER_USER: Username
MANAGER_PASS: Password
```
Run `python vmanage_repush.py <device1> <device2> <device3> ...` to re-push configuration to specified devices.
