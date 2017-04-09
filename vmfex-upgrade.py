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

import logging
import getpass
import time

import ovirtsdk4 as sdk
import ovirtsdk4.types as types

api_url = raw_input("Please enter RHV Manager API url: ")
username = raw_input("Please enter RHV Manager admin name: ")
password = getpass.getpass(prompt='Please enter RHV Manager admin password: ')
vm_name = raw_input("Please enter VM name: ")
# cluster_name = raw_input("Please enter destination cluster name: ")

# Create the connection to the server:
connection = sdk.Connection(
    url=api_url,
    # url='http://192.168.122.1:8080/ovirt-engine/api',
    username=username,
    password=password,
    # ca_file='/etc/pki/ovirt-engine/ca.pem',
    debug=True,
    log=logging.getLogger(),
)

# Get the reference to the "vms" service:
vms_service = connection.system_service().vms_service()

# Find the virtual machine:
vm = vms_service.list(search='name='+vm_name)[0]

if vm.status != types.VmStatus.DOWN:
    print "The VM is not down. Exiting ..."
    connection.close()
    exit()

# Locate the service that manages the virtual machine:
vm_service = vms_service.vm_service(vm.id)

custom_properties = vm.custom_properties
vmfex = None
if custom_properties:
    for cp in custom_properties:
        if cp.name == 'vmfex':
            vmfex = cp.value

if vmfex == None:
    print "No vmfex property found. Exiting ..."
    connection.close()
    exit()

profiles_service = connection.system_service().vnic_profiles_service()
profile_id = None
for profile in profiles_service.list():
    if profile.name == vmfex:
        profile_id = profile.id
        break

nics_service = vms_service.vm_service(vm.id).nics_service()
nics_service.add(
    types.Nic(
        name=vmfex,
        description='Network interface card',
        vnic_profile=types.VnicProfile(
            id=profile_id,
        ),
    ),
)

"""
clusters_service = connection.system_service().clusters_service()
cluster = clusters_service.list(search='name='+cluster_name)[0]
vm_service.migrate(cluster=cluster)

vm.Cluster = cluster_name
vm_service.update(vm)
"""

connection.close()
