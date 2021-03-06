#
# Copyright (C) 2017 Ericsson India Global Services Pvt Ltd.
#
#  Licensed under the Apache License, Version 2.0 (the "License"); you may
#  not use this file except in compliance with the License. You may obtain
#  a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#  WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#  License for the specific language governing permissions and limitations
#  under the License.
#

from oslo_config import cfg
from oslo_log import helpers as log_helpers
from oslo_log import log as logging

from networking_bgpvpn.neutron.extensions import bgpvpn as bgpvpn_ext
from networking_bgpvpn.neutron.services.service_drivers import driver_api
from networking_odl.common import constants as odl_const
from networking_odl.common import postcommit
from networking_odl.journal import journal


cfg.CONF.import_group('ml2_odl', 'networking_odl.common.config')

LOG = logging.getLogger(__name__)


@postcommit.add_postcommit('bgpvpn', 'net_assoc', 'router_assoc')
class OpenDaylightBgpvpnDriver(driver_api.BGPVPNDriver):

    """OpenDaylight BGPVPN Driver

    This code is the backend implementation for the OpenDaylight BGPVPN
    driver for Openstack Neutron.
    """

    @log_helpers.log_method_call
    def __init__(self, service_plugin):
        LOG.info("Initializing OpenDaylight BGPVPN v2 driver")
        super(OpenDaylightBgpvpnDriver, self).__init__(service_plugin)
        self.journal = journal.OpenDaylightJournalThread()

    @log_helpers.log_method_call
    def create_bgpvpn_precommit(self, context, bgpvpn):
        journal.record(context, odl_const.ODL_BGPVPN,
                       bgpvpn['id'], odl_const.ODL_CREATE, bgpvpn)

    @log_helpers.log_method_call
    def update_bgpvpn_precommit(self, context, bgpvpn):
        journal.record(context, odl_const.ODL_BGPVPN,
                       bgpvpn['id'], odl_const.ODL_UPDATE, bgpvpn)

    @log_helpers.log_method_call
    def delete_bgpvpn_precommit(self, context, bgpvpn):
        journal.record(context, odl_const.ODL_BGPVPN,
                       bgpvpn['id'], odl_const.ODL_DELETE, [])

    @log_helpers.log_method_call
    def create_net_assoc_precommit(self, context, net_assoc):
        our_bgpvpn = None
        bgpvpns = self.get_bgpvpns(context)
        for bgpvpn in bgpvpns:
            # ODL only allows a network to be associated with one BGPVPN
            if bgpvpn['id'] == net_assoc['bgpvpn_id']:
                our_bgpvpn = bgpvpn
            else:
                if bgpvpn['networks'] and (net_assoc['network_id'] in
                                           bgpvpn['networks']):
                    raise bgpvpn_ext.BGPVPNNetworkAssocExistsAnotherBgpvpn(
                        driver="OpenDaylight V2",
                        network=net_assoc['network_id'],
                        bgpvpn=bgpvpn['id'])
        journal.record(context, odl_const.ODL_BGPVPN,
                       our_bgpvpn['id'], odl_const.ODL_UPDATE, our_bgpvpn)

    @log_helpers.log_method_call
    def delete_net_assoc_precommit(self, context, net_assoc):
        bgpvpn = self.get_bgpvpn(context, net_assoc['bgpvpn_id'])
        journal.record(context, odl_const.ODL_BGPVPN,
                       bgpvpn['id'], odl_const.ODL_UPDATE, bgpvpn)

    @log_helpers.log_method_call
    def create_router_assoc_precommit(self, context, router_assoc):
        associated_routers = self.get_router_assocs(context,
                                                    router_assoc['bgpvpn_id'])
        for assoc_router in associated_routers:
            if(router_assoc["router_id"] != assoc_router["router_id"]):
                raise bgpvpn_ext.BGPVPNMultipleRouterAssocNotSupported(
                    driver="OpenDaylight V2")
        bgpvpn = self.get_bgpvpn(context, router_assoc['bgpvpn_id'])
        journal.record(context, odl_const.ODL_BGPVPN,
                       bgpvpn['id'], odl_const.ODL_UPDATE, bgpvpn)

    @log_helpers.log_method_call
    def delete_router_assoc_precommit(self, context, router_assoc):
        bgpvpn = self.get_bgpvpn(context, router_assoc['bgpvpn_id'])
        journal.record(context, odl_const.ODL_BGPVPN,
                       bgpvpn['id'], odl_const.ODL_UPDATE, bgpvpn)
