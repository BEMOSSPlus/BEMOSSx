# -*- coding: utf-8 -*-
'''
#Copyright © 2014 by Virginia Polytechnic Institute and State University
#All rights reserved

#Virginia Polytechnic Institute and State University (Virginia Tech) owns the copyright for the BEMOSS software and its
#associated documentation (“Software”) and retains rights to grant research rights under patents related to
#the BEMOSS software to other academic institutions or non-profit research institutions.
#You should carefully read the following terms and conditions before using this software.
#Your use of this Software indicates your acceptance of this license agreement and all terms and conditions.

#You are hereby licensed to use the Software for Non-Commercial Purpose only.  Non-Commercial Purpose means the
#use of the Software solely for research.  Non-Commercial Purpose excludes, without limitation, any use of
#the Software, as part of, or in any way in connection with a product or service which is sold, offered for sale,
#licensed, leased, loaned, or rented.  Permission to use, copy, modify, and distribute this compilation
#for Non-Commercial Purpose to other academic institutions or non-profit research institutions is hereby granted
#without fee, subject to the following terms of this license.

#Commercial Use If you desire to use the software for profit-making or commercial purposes,
#you agree to negotiate in good faith a license with Virginia Tech prior to such profit-making or commercial use.
#Virginia Tech shall have no obligation to grant such license to you, and may grant exclusive or non-exclusive
#licenses to others. You may contact the following by email to discuss commercial use: vtippatents@vtip.org

#Limitation of Liability IN NO EVENT WILL VIRGINIA TECH, OR ANY OTHER PARTY WHO MAY MODIFY AND/OR REDISTRIBUTE
#THE PROGRAM AS PERMITTED ABOVE, BE LIABLE TO YOU FOR DAMAGES, INCLUDING ANY GENERAL, SPECIAL, INCIDENTAL OR
#CONSEQUENTIAL DAMAGES ARISING OUT OF THE USE OR INABILITY TO USE THE PROGRAM (INCLUDING BUT NOT LIMITED TO
#LOSS OF DATA OR DATA BEING RENDERED INACCURATE OR LOSSES SUSTAINED BY YOU OR THIRD PARTIES OR A FAILURE
#OF THE PROGRAM TO OPERATE WITH ANY OTHER PROGRAMS), EVEN IF VIRGINIA TECH OR OTHER PARTY HAS BEEN ADVISED
#OF THE POSSIBILITY OF SUCH DAMAGES.

#For full terms and conditions, please visit https://bitbucket.org/bemoss/bemoss_os.

#Address all correspondence regarding this license to Virginia Tech’s electronic mail address: vtippatents@vtip.org

#__author__ = "Avijit Saha"
#__credits__ = ""
#__version__ = "2.0"
#__maintainer__ = "Avijit Saha"
#__email__ = "avijit@vt.edu"
#__website__ = "www.bemoss.org"
#__status__ = "Prototype"
#__created__ = "2015-05-19"
#__lastUpdated__ = "2015-05-21"
'''

import importlib
import sys
import json
import logging
import os
import re
from volttron.platform.agent import BaseAgent, PublishMixin, periodic
from volttron.platform.agent import utils, matching
from volttron.platform.messaging import headers as headers_mod
import settings

utils.setup_logging()  # setup logger for debugging
_log = logging.getLogger(__name__)

# Step1: Agent Initialization
def TestDRAgent(config_path, **kwargs):
    config = utils.load_config(config_path)  # load the config_path from approvalhelperagent.launch.json
    def get_config(name):
        try:
            value = kwargs.pop(name)  # from the **kwargs when call this function
        except KeyError:
            return config.get(name, '')

    # 1. @params agent
    agent_id = get_config('agent_id')
    headers = {headers_mod.FROM: agent_id}
    publish_address = 'ipc:///tmp/volttron-lite-agent-publish'
    subscribe_address = 'ipc:///tmp/volttron-lite-agent-subscribe'
    topic_delim = '/'  # topic delimiter

    # @paths
    PROJECT_DIR = settings.PROJECT_DIR
    # Loaded_Agents_DIR = settings.Loaded_Agents_DIR
    # Autostart_Agents_DIR = settings.Autostart_Agents_DIR
    #Applications_Launch_DIR = settings.Applications_Launch_DIR
    Agents_Launch_DIR = settings.Agents_Launch_DIR

    class Agent(PublishMixin, BaseAgent):

        def __init__(self, **kwargs):
            super(Agent, self).__init__(**kwargs)
            self.status = False
            sys.path.append(PROJECT_DIR)

        def setup(self):
            super(Agent, self).setup()


        @matching.match_exact('openadr/status')
        def agentLaunchBehavior(self, topic, headers, message, match):
            print "TestDRAgent got\nTopic: {topic}".format(topic=topic)
            print "Headers: {headers}".format(headers=headers)
            print "Message: {message}\n".format(message=message)

            messagejson = json.loads(message[0])

            flag = 0
            if messagejson['active'] == False and self.status == True:
                self.status = False
                _data_therm = {"thermostat_mode":"COOL","cool_setpoint":72,"fan_mode":"ON"}
                _data_light = {'brightness':100}
                flag = 1
            elif messagejson['active'] == True and self.status == False:
                self.status = True
                _data_therm = {"thermostat_mode":"COOL","cool_setpoint":78,"fan_mode":"ON"}
                _data_light = {'brightness':60}
                flag = 1
                

            # if messagejson['status'] == 'cancelled':
            #     _data = {"thermostat_mode":"COOL","cool_setpoint":72,"fan_mode":"ON"}
            # elif messagejson['status'] == 'active':
            #     _data = {"thermostat_mode":"COOL","cool_setpoint":78,"fan_mode":"ON"}

            if flag == 1:
                #Change Thermostat Set-point
                topic = '/ui/agent/bemoss/999/thermostat/1NST18b43017e76a/update' #1THE88308a2231de
                headers = {
                    'AgentID': agent_id,
                    headers_mod.CONTENT_TYPE: headers_mod.CONTENT_TYPE.JSON,
                    # headers_mod.DATE: now,
                    headers_mod.FROM: agent_id,
                    headers_mod.TO: '1NST18b43017e76a'
                }

                message = json.dumps(_data_therm)
                message = message.encode(encoding='utf_8')

                self.publish(topic, headers, message)

                #Change Lighting Brightness
                topic = '/ui/agent/bemoss/999/lighting/2WSL830568i469810079n1/update'
                headers = {
                    'AgentID': agent_id,
                    headers_mod.CONTENT_TYPE: headers_mod.CONTENT_TYPE.JSON,
                    # headers_mod.DATE: now,
                    headers_mod.FROM: agent_id,
                    headers_mod.TO: '2WSL830568i469810079n1'
                }

                message = json.dumps(_data_light)
                message = message.encode(encoding='utf_8')

                self.publish(topic, headers, message)


        def publish_subtopic(self, publish_item, topic_prefix):
            #TODO: Update to use the new topic templates
            if type(publish_item) is dict:
                # Publish an "all" property, converting item to json

                headers[headers_mod.CONTENT_TYPE] = headers_mod.CONTENT_TYPE.JSON
                self.publish_json(topic_prefix + topic_delim + "all", headers, json.dumps(publish_item))
                print "WiFiTherAgent got"+str(type(publish_item))
                os.system("date");
                # Loop over contents, call publish_subtopic on each
                for topic in publish_item.keys():
                    self.publish_subtopic(publish_item[topic], topic_prefix + topic_delim + topic)

            else:
                # Item is a scalar type, publish it as is
                headers[headers_mod.CONTENT_TYPE] = headers_mod.CONTENT_TYPE.PLAIN_TEXT
                self.publish(topic_prefix, headers, str(publish_item))
                print "Topic:{topic}={message}".format(topic=topic_prefix,message=str(publish_item))

    Agent.__name__ = 'TestDRAgent'
    return Agent(**kwargs)

def main(argv=sys.argv):
    '''Main method called by the eggsecutable.'''
    utils.default_main(TestDRAgent, description='Test DR agent', argv=argv)

if __name__ == '__main__':
    # Entry point for script
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        pass
