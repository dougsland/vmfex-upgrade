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
logging.getLogger().addHandler(logging.StreamHandler())

def update_vm_vmfex_support(api, dc, cluster, destnet, vmsname):
    dc = api.datacenters.get(args.datacenter)
    if not dc:
        logging.error("Couldn't find DC: '%s'", args.datacenter)
        exit()

    for vmname in args.vmsname.split(','):
        logging.info("Upgrading VMFEX for VM: '%s'", vmname)
        vm = api.vms.get(vmname)
        if not vm:
            logging.error("VM: '%s' doesn't exist. Please mske sure you provided correct VM name", vmname)
            continue

        if vm.status.state != 'down':
            logging.info("VM: '%s' is not down", vmname)
            continue

        vmfex = get_vmfex(vm)
        logging.info("VMFEX value: '%s'", vmfex)
        if vmfex == None:
            logging.info("No VMFEX property found for VM: '%s'", vmname)
            continue

        try:
            if update_vnics_for_vm(api, dc, destnet, vm, vmfex):
                delete_vmfex_custom_property(vm)
                move_vm_to_cluster(vm, cluster)
        except Exception as e:
            logging.exception("Failed to upgrade VMFEX support for VM: '%s'.", vmname)
            continue

def get_vmfex(vm):
    if vm.get_custom_properties():
        for custom_property in vm.get_custom_properties().get_custom_property():
            if custom_property.get_name() == "vmfex":
                return custom_property.get_value()
    return None

def update_vnics_for_vm(api, dc, dest_net, vm, vmfex):
    network = next(
        (
            net for net in dc.networks.list()
            if net.get_name() == dest_net
        ),
        None
    )
    if not network:
        logging.error("Couldn't find network: '%s' in dc: '%s'", dest_net, dc.get_name())
        return False

    vmfex_dict = ast.literal_eval(vmfex)
    for vnic in vm.nics.list():
        if vnic.mac.address in vmfex_dict:
            profile = next(
                (
                    p for p in api.vnicprofiles.list()
                    if p.get_network().get_id() == network.get_id() and p.get_name() == vmfex_dict[vnic.mac.address]
                ),
                None
            )
            if not profile:
                logging.error("Profile: '%s' is not defined in network: '%s'", vmfex_dict[vnic.mac.address], dest_net)
                return False

            logging.info("Updating vnic: '%s' profile to: '%s'", vnic.name, vmfex_dict[vnic.mac.address])
            vnic.set_vnic_profile(profile)
            vnic.update()

    return True

def delete_vmfex_custom_property(vm):
    logging.info("Removing vmfex custom property of VM: '%s'", vm.name)
    new_properties = []
    if vm.get_custom_properties():
        for custom_property in vm.get_custom_properties().get_custom_property():
            if custom_property.get_name() != "vmfex":
                new_properties.append(custom_property)

    vm.set_custom_properties(
        params.CustomProperties(
            custom_property=new_properties
        )
    )
    vm.update()

def move_vm_to_cluster(vm, cluster):
    logging.info("Moving VM: '%s' to cluster: '%s'", vm.name, cluster)
    vm.cluster = params.Cluster(name=cluster)
    vm.update()

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("-u", "--username", help="username")
    parser.add_argument("-url", "--url", help="API URL")
    parser.add_argument("-dc", "--datacenter", help="Data center name")
    parser.add_argument("-vms", "--vmsname", help="VMS name")
    parser.add_argument("-dest-net", "--destnet", help="Destination network")
    parser.add_argument("-c", "--cluster", help="Cluster name")
    if len(sys.argv) != 13:
        parser.print_help()
        exit()

    args = parser.parse_args()
    password = getpass.getpass(prompt='Please enter RHV Manager admin password: ')

    api = API(url=args.url, username=args.username, password=password, insecure=True)
    try:
        update_vm_vmfex_support(api, args.datacenter, args.cluster, args.destnet, args.vmsname)
    finally:
        api.disconnect()
