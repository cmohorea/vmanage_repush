import time, re, sys
from sdwan_api import sdwan_api

outcomes = {}
total_count = 0

# ================================================================================= #
def add_outcome (device):
    global outcomes

    outcome = device.get("statusId","UNKNOWN")
    if outcome not in outcomes.keys():
        outcomes[outcome] = []
    outcomes[outcome].append (device)

# ================================================================================= #
def it_matches (systemIP, name, pattern_list):
    """
    Returns True if the item matches any pattern in pattern_list.
    Supports wildcards:
        *: any sequence of characters
        ?: any single character
    """
    for pattern in pattern_list:
        pattern_re = re.escape(pattern).replace(r'\*', '.*').replace(r'\?', '.')
        if re.fullmatch(pattern_re, systemIP) or re.fullmatch(pattern_re, name) :
            return True
    return False

# ================================================================================= #
def fetch_wan_edges(sdwan, target_devices):
    global total_count

    result = {}
    skip = []

    data = sdwan.api_GET ("/system/device/vedges")
    data = data.get("data",[])

    for device in data:
        systemIP = device.get('system-ip',None)
        hostname = device.get('host-name',None)
        uuid = device.get('uuid',None)
        template = device.get('template',None)
        templateId = device.get('templateId',None)
        isReachable = device.get('reachability',"")=='reachable'

        if not (systemIP and hostname and uuid):    # unconfigured devices
            continue

        if not it_matches (systemIP, hostname, target_devices): # skip unmatched devices
            continue
        
        total_count += 1

        if not template:
            skip.append({'device':device, 'reason': "Device is not attached to a device template"})
            continue

        if not isReachable:
            skip.append({'device':device, 'reason': "Device is unreachable"})
            continue

        if templateId not in result.keys():
            result[templateId] = {'name': template, 'id': templateId, 'devices': []}
        
        result[templateId]['devices'].append(device)

        # print (f"{systemIP} {hostname} {uuid} {template} {templateId} {isReachable}")

    return ([result,skip])

# ================================================================================= #
def wait_for_task(sdwan, task_id, interval=5, maxtime=60):
    """wait for async task until complete with 1 min timeout"""

    task_url = "/device/action/status/"+task_id
    time_elapsed = 0
    status = "unknown"

    while True:
        if (time_elapsed < maxtime):
            # read task status from vManage
            status_data = sdwan.api_GET(task_url)

            # current status of operation (in progress/success/fail)
            if len(status_data['data']) == 0:
                status = "Validation " + status_data.get("validation","").get("status","unknown error")
            else:
                status = status_data['summary']['status']

            # Stop when done
            if status == "done":
                # for rtr in status_data.get ('data',[]):
                #     add_outcome (rtr)
                break

            # print (f"Operation in progress {time_elapsed}/{maxtime}s, status: {status}")
            time.sleep (interval)
            time_elapsed += interval
        else:
            status = "Timeout"
            break

    for rtr in status_data.get ('data',[]):
        add_outcome (rtr)
    # print (f"Template push completed for {status_data['summary']['count']} devices")
    
    return status

# ================================================================================= #
def push_template (sdwan, targets):

    attach_request = {'deviceTemplateList': []}

    for template in targets.values():

        target_template = template.get ('name',"unknown")
        target_template_id = template.get ('id',"unknown")
        attached_devices = template.get ('devices',[])

        # Prepare "variables_request" data structure to request current variables
        print (f"Processing {len(attached_devices)} devices attached to the '{target_template}' template") #-

        variables_request = {
            'templateId': target_template_id,
            'deviceIds': [rtr['uuid'] for rtr in attached_devices if rtr.get('uuid')],
            'isEdited': False,
            'isMasterEdited': False,
        }

        if variables_request['deviceIds']:
            # Request device variables
            device_variables = sdwan.api_POST("/template/device/config/input", variables_request)['data']

            if device_variables:
                deviceTemplateData = {
                    'templateId': target_template_id,
                    'device': device_variables,
                    'isEdited': False,
                    'isMasterEdited': False
                }

            # Prepare "attach_request" data structure for the template push call
            attach_request['deviceTemplateList'].append (deviceTemplateData) 

    # Template attach - asynchronous call, only returns task ID
    task_id = sdwan.api_POST("/template/device/config/attachfeature", attach_request)['id']

    # Patienly wait for the task to complete
    status = wait_for_task(sdwan, task_id)

    # Report the status
    # print(f"Task execution status: {status}")

# ================================================================================= #
def main():

    target_devices = sys.argv[1:]
    if not target_devices:
        print (f'Usage: {sys.argv[0]} <list of device names/system IPs. * and ? wildcards accepted>')
        print (f'This will re-attach/re-push device template configuration to specified devices')
        print ("\nThe following environment variables are expected:")
        print ("MANAGER_ADDR: address/port of vManage")
        print ("MANAGER_USER: Username")
        print ("MANAGER_PASS: Password")
        exit (0)

    # Initialize API object
    sdwan = sdwan_api()

    # Obtain and organize the list of devices
    targets, skips = fetch_wan_edges (sdwan, target_devices)

    push_template (sdwan, targets)

    print ("\nOutcomes:")
    print (f"Total devices provided: {total_count}")
    for outcome, devices in outcomes.items():
        hostnames = str([device['host-name'] for device in devices]).replace("'","")
        print (f"{outcome.capitalize()}: {len(devices)} {hostnames}")

    if skips:
        print (f"Devices skipped: {len(skips)}")
        for item in skips:
            device = item.get('device',{})
            reason = item.get('reason','unknown')
            print (f" - {device.get('host-name','unknown')} ({device.get('system-ip','unknown')}) [{device.get('uuid','unknown')}] - {reason}") 

    # Close the session and exit
    sdwan.logout()

if __name__ == "__main__":
    main()
