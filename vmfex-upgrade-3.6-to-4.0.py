#!/usr/bin/env python
# -*- coding: utf-8 -*-

#
# Copyright (c) 2017 Red Hat, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

import argparse
import ast
import getpass
import logging
import sys

from ovirtsdk.api import API
from ovirtsdk.xml import params

logging.basicConfig(level=logging.DEBUG, filename='vmfex-upgrade.log')

def get_vmfex(vm):
    if vm.custom_properties:
        for custom_property in vm.custom_properties.custom_property:
            if custom_property.name == "vmfex":
                return custom_property.value
    return None

def get_profiles(vmfex):
    vmfex_dict = ast.literal_eval(vmfex)
    profile_name_to_id = {}
    for profile in api.vnicprofiles.list():
        if profile.name in vmfex_dict.values():
            profile_name_to_id[profile.name] = profile.id

    return profile_name_to_id

def add_profiles(vm, vmfex):
    for (profile_name, profile_id) in get_profiles(vmfex).items():
        try:
            print("Adding profile name: '{0}'to VM: '{1}'").format(profile_name, vm.name)
            logging.info("Adding profile name: %s, id: %s to VM: %s", profile_name, profile_id, vm.name)
            vm.nics.add(
                params.NIC(
                    name=profile_name,
                    description='',
                    vnic_profile=params.VnicProfile(
                        id=profile_id,
                    )
                )
            )
        except Exception as e:
            # probably adding an existing vnic. Ignore this exception
            logging.exception(e)

def move_vm_to_cluster(vm, cluster):
    print("Moving vm: '{0}' to cluster: '{1}'").format(vm.name, cluster)
    logging.info("Moving VM: %s to cluster: %s", vm.name, cluster)
    vm.cluster = params.Cluster(name=cluster)
    try:
        vm.update()
    except Exception as e:
        # getting exception that VM cannot be updated if some of the specified
        # custom properties are not configured by the system. Ignoring this exception.
        logging.exception(e)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("-u", "--username", help="username")
    parser.add_argument("-url", "--url", help="API URL")
    parser.add_argument("-vms", "--vmsname", help="VMS name")
    parser.add_argument("-c", "--cluster", help="Cluster name")
    if len(sys.argv) != 9:
        parser.print_help()
        exit()

    args = parser.parse_args()
    password = getpass.getpass(prompt='Please enter RHV Manager admin password: ')

    api = API(url=args.url, username=args.username, password=password)

    for vmname in args.vmsname.split(','):
        print("Upgrading vmfex for vm: '{0}'").format(vmname)
        logging.info("Upgrading vmfex for vm: %s", vmname)
        vm = api.vms.get(vmname)
        if not vm:
            print("VM: {0} doesn't exist. Please mske sure you provided correct VM name").format(vmname)
            continue

        if vm.status.state != 'down':
            print("VM: '{0}' is not down").format(vmname)
            logging.info("VM: %s is not down", vmname)
            continue

        vmfex = get_vmfex(vm)
        if vmfex == None:
            print("No vmfex property found for vm: '{0}'").format(vmname)
            logging.info("No vmfex property found for vm: %s", vmname)
            continue

        print("vmfex for VM: '{0}' is: '{1}'").format(vm.name, vmfex)
        logging.info("vmfex value: %s", vmfex)

        add_profiles(vm, vmfex)

        move_vm_to_cluster(vm, args.cluster)
        print("Upgrading vmfex for vm: '{0}' completed").format(vmname)
