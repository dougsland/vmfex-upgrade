This script is used to update VM-FEX for VMs from 3.6 version to 4.0.
Following is an example how to run the script:

    python vmfex-upgrade-3.6-to-4.0.py -u admin -url http://host/ovirt-engine/api -vms vm1,vm2,vm3 -c new_cluster

Before running the script, please make sure that:
1. The VM is down
2. UCS-M profile used in the vmfex are created

After running the script, the VM is moved to the provided cluster.
