This script is used to update VM-FEX for VMs from 3.5 version to 3.6.
Following is an example how to run the script:

    python vmfex-upgrade-3.5-to-3.6.py -u admin -url http://host/ovirt-engine/api -dc test-dc -dest-net destination-network -vms vm1,vm2,vm3 -c new_cluster

Where:
dc: the datacenter where the VM is running
dest-net: the destination network whetre thte vnic profile is defined
c: destination cluster (where RHEL7 hosts are created) to move the VM to

Before running the script, please make sure that:
1. The VM is down
2. The user must create vnic profiles for each UCS-M profile used, and the name of the vnic profile must match the name of the UCSM profile

Plese note that the old vmfex custom property is removed after running the script.
