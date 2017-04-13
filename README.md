This script is used to update VM-FEX for VMs from 3.6 version to 4.0.
In order to run the script, the user must provide engine API URL,
username, user password, VM name and cluser. For example:

    python vmfex-upgrade-3.6-to-4.0.py -u admin -url http://host/ovirt-engine/api -vm MyVm -c newClstr

In order to run the script:
1. The VM must be down
2. The use must create vnic profiles for each UCS-M profile used

After running the script, the VM is moved to the provided cluster.
