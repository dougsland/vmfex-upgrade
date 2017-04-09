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

import ast
import getpass
import logging

from ovirtsdk.api import API
from ovirtsdk.xml import params

logging.basicConfig(level=logging.DEBUG, filename='vmfex-upgrade.log')

api_url = raw_input("Please enter RHV Manager API url: ")
username = raw_input("Please enter RHV Manager admin name: ")
password = getpass.getpass(prompt='Please enter RHV Manager admin password: ')
vm_name = raw_input("Please enter VM name: ")
cluster = raw_input("Please enter destination cluster name: ")

api = API(url=api_url, username=username, password=password)

vm = api.vms.get(vm_name)

if vm.status.state != 'down':
    logging.info("The VM is not down. Exiting ...")
    exit()

vmfex = None
if vm.custom_properties:
    for custom_property in vm.custom_properties.custom_property:
        if custom_property.name == "vmfex":
            vmfex = custom_property.value

if vmfex == None:
    logging.info("No vmfex property found. Exiting ...")
    exit()
logging.info("vmfex value: %s", vmfex)

vmfex_dict = ast.literal_eval(vmfex)

profile_name_to_id = {}
for profile in api.vnicprofiles.list():
    if profile.name in vmfex_dict.values():
        profile_name_to_id[profile.name] = profile.id

for (profile_name, profile_id) in profile_name_to_id.items():
    try:
        logging.info("Adding profile name: %s, id: %s", profile_name, profile_id)
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

logging.info("Moving the VM to cluster: %s", cluster)
vm.cluster = params.Cluster(name=cluster)
try:
    vm.update()
except Exception as e:
    # getting exception that VM cannot be updated if some of the specified
    # custom properties are not configured by the system. Ignoring this exception.
    logging.exception(e)
