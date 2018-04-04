# -*- coding: utf-8 -*- {{{
# vim: set fenc=utf-8 ft=python sw=4 ts=4 sts=4 et:
#
# Copyright (c) 2013, Battelle Memorial Institute
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# 1. Redistributions of source code must retain the above copyright notice, this
#    list of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright notice,
#    this list of conditions and the following disclaimer in the documentation
#    and/or other materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR
# ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
# ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#
# The views and conclusions contained in the software and documentation are those
# of the authors and should not be interpreted as representing official policies,
# either expressed or implied, of the FreeBSD Project.
#

# This material was prepared as an account of work sponsored by an
# agency of the United States Government.  Neither the United States
# Government nor the United States Department of Energy, nor Battelle,
# nor any of their employees, nor any jurisdiction or organization
# that has cooperated in the development of these materials, makes
# any warranty, express or implied, or assumes any legal liability
# or responsibility for the accuracy, completeness, or usefulness or
# any information, apparatus, product, software, or process disclosed,
# or represents that its use would not infringe privately owned rights.
#
# Reference herein to any specific commercial product, process, or
# service by trade name, trademark, manufacturer, or otherwise does
# not necessarily constitute or imply its endorsement, recommendation,
# r favoring by the United States Government or any agency thereof,
# or Battelle Memorial Institute. The views and opinions of authors
# expressed herein do not necessarily state or reflect those of the
# United States Government or any agency thereof.
#
# PACIFIC NORTHWEST NATIONAL LABORATORY
# operated by BATTELLE for the UNITED STATES DEPARTMENT OF ENERGY
# under Contract DE-AC05-76RL01830

#}}}


from datetime import datetime
import logging
import sys
from random import randint
from volttron.platform.vip.agent import Agent, Core, PubSub
from volttron.platform.agent import utils
from volttron.platform.messaging import headers as headers_mod

import settings

utils.setup_logging()
_log = logging.getLogger(__name__)

class PublisherAgent(Agent):

    def __init__(self, config_path, **kwargs):
        super(PublisherAgent, self).__init__(**kwargs)
        self.config = utils.load_config(config_path)

    def setup(self):
        # Demonstrate accessing a value from the config file
        _log.info(self.config['message'])
        self._agent_id = self.config['agentid']

    # Demonstrate periodic decorator and settings access
    @Core.periodic(settings.HEARTBEAT_PERIOD)
    def publish_heartbeat(self):
        # For lighting test
        # _data = dict()
        # _data['brightness'] = datetime.now().second
        # _data['status'] = 'ON'
        # _data['color'] = '(255,255,255)'
        # _data['device_info'] = '999/lighting/2HUE001788262e88'
        #
        # headers = {}

        # self.vip.pubsub.publish(
        #     'pubsub', 'to/2HUE001788262e88/update', headers, _data)


        # For vav test
        _data = {"heat_setpoint": 67, "cool_setpoint": 75, "flap_override": "ON", "flap_position": 81,
         "device_info": "999/vav/1VAV30168D000262"}

        headers = {}

        self.vip.pubsub.publish(
            'pubsub', 'to/1VAV30168D000262/update', headers, _data)
        print 'VAV set'

        # _data = dict()
        # cnt = randint(0,1)
        # if cnt == 0:
        #     status = 'OFF'
        # else:
        #     status = 'ON'
        # _data['status']=status
        # _data['device_info'] = '999/plugload/3WSP221609K0102348'
        # headers = {}
        # self.vip.pubsub.publish(
        #     'pubsub', 'to/3WSP221609K0102348/update', headers, _data)
        # print 'changing status to ' + status
        # now = datetime.utcnow().isoformat(' ') + 'Z'
        # headers = {
        #     'AgentID': self._agent_id,
        #     headers_mod.CONTENT_TYPE: headers_mod.CONTENT_TYPE.PLAIN_TEXT,
        #     headers_mod.DATE: now,
        # }
        # self.publish('/ui/agent/misc/bemoss/discovery_request', headers, now)
        # print "published message"

def main(argv=sys.argv):
    '''Main method called by the eggsecutable.'''
    try:
        utils.vip_main(PublisherAgent)
    except Exception as e:
        _log.exception('unhandled exception')

if __name__ == '__main__':
    # Entry point for script
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        pass