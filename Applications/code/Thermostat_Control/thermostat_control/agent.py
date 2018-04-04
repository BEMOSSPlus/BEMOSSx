

import sys
import json
import logging
from volttron.platform.vip.agent import Agent, Core
from volttron.platform.agent import utils
import datetime
from bemoss_lib.utils import db_helper
import psycopg2
import numpy as np
from sklearn.linear_model import LinearRegression

utils.setup_logging()
_log = logging.getLogger(__name__)
from bemoss_lib.utils.BEMOSSAgent import BEMOSSAgent
from bemoss_lib.utils.BEMOSS_ONTOLOGY import BEMOSS_ONTOLOGY
from bemoss_lib.databases.cassandraAPI import cassandraDB
from bemoss_lib.utils import date_converter
import settings
from scipy import stats
import uuid
TEMP = BEMOSS_ONTOLOGY.TEMPERATURE.NAME

class ThermostatControlAgent(BEMOSSAgent):

    #1. agent initialization
    def __init__(self, config_path, **kwargs):
        super(ThermostatControlAgent, self).__init__(**kwargs)
        #1. initialize all agent variables
        config = utils.load_config(config_path)
        self.agent_id = config.get('agent_id','faultdetectionagent')
        self.data = {'thermostat': 'RTH8_1169269', 'sensor': '', 'sensor_weight':0.5,
                     'cool_setpoint':70,'heat_setpoint':80,'mode':'AUTO','deadband':0.5}


    @Core.receiver('onsetup')
    def setup(self, sender, **kwargs):
        self.curcon = db_helper.db_connection()
        self.core.periodic(60, self.periodicProcess)
        self.vip.pubsub.subscribe(peer='pubsub', prefix='to/'+self.agent_id+'/update/', callback=self.appUpdate)
        self.updateAppData()
        self.get_nicknames()

    def appUpdate(self, peer, sender, bus, topic, headers, message):
        self.updateAppData()

    def updateAppData(self):
        self.curcon.execute("select app_data from application_running where app_agent_id=%s", (self.agent_id,))
        if self.curcon.rowcount:
            data = self.curcon.fetchone()[0]
            for key, value in data.items():
                self.data[key] = value

    def get_nicknames(self):
        try:
            self.curcon.execute("select nickname from device_info where agent_id=%s",(self.data['thermostat'],))
            if self.curcon.rowcount:
                self.thermostat_nickname = self.curcon.fetchone()[0]

            self.curcon.execute("select nickname from device_info where agent_id=%s", (self.data['sensor'],))
            if self.curcon.rowcount:
                self.sensor_nickname = self.curcon.fetchone()[0]
            else:
                self.sensor_nickname = "Sensor not selected"
        except psycopg2.IntegrityError as er: #Database trouble
            #reconnect first
            self.curcon.database_connect()

    def make_thermostat(self,thermo_data,action):
        control_message = dict()
        control_message['user'] = 'thermostat_control_app'
        control_message['hold'] = BEMOSS_ONTOLOGY.HOLD.POSSIBLE_VALUES.PERMANENT

        if action == 'COOL':
            if thermo_data['thermostat_mode'] != 'COOL' or thermo_data[TEMP] < thermo_data['cool_setpoint'] + 2:
                control_message['thermostat_mode'] = 'COOL'
                control_message['cool_setpoint'] = thermo_data[TEMP] - 5
                self.bemoss_publish('update',self.data['thermostat'],control_message)
                print "Thermostat cooled to: " + str(control_message)

        if action == 'NOCOOL':
            if thermo_data['thermostat_mode'] != 'COOL' or thermo_data[TEMP] > thermo_data['cool_setpoint'] - 2:
                control_message['thermostat_mode'] = 'COOL'
                control_message['cool_setpoint'] = thermo_data[TEMP] + 5
                self.bemoss_publish('update',self.data['thermostat'],control_message)
                print "Thermostat nocooled to: " + str(control_message)

        if action == 'HEAT':
            if thermo_data['thermostat_mode'] != 'HEAT' or thermo_data[TEMP] > thermo_data['heat_setpoint'] - 2:
                control_message['thermostat_mode'] = 'HEAT'
                control_message['heat_setpoint'] = thermo_data[TEMP] + 5
                self.bemoss_publish('update',self.data['thermostat'],control_message)
                print "Thermostat heated to: " + str(control_message)

        if action == 'NOHEAT':
            if thermo_data['thermostat_mode'] != 'HEAT' or thermo_data[TEMP] < thermo_data['heat_setpoint'] + 2:
                control_message['thermostat_mode'] = 'HEAT'
                control_message['heat_setpoint'] = thermo_data[TEMP] - 5
                self.bemoss_publish('update',self.data['thermostat'],control_message)
                print "Thermostat noheated to: " + str(control_message)


    def periodicProcess(self):

        self.updateAppData()
        self.curcon.execute("select data from devicedata where agent_id=%s",(self.data['thermostat'],))
        if self.curcon.rowcount:
            thermo_data = self.curcon.fetchone()[0]
        else:
            return
        self.curcon.execute("select data from devicedata where agent_id=%s", (self.data['sensor'],))
        if self.curcon.rowcount:
            sensor_data = self.curcon.fetchone()[0]
        else:
            return

        s_weight = self.data['sensor_weight']
        avg_temperature = thermo_data[TEMP] * (1 - s_weight) + sensor_data[TEMP] * s_weight
        if self.data['mode'] in ['COOL','AUTO']:
            if avg_temperature > self.data['cool_setpoint'] + self.data['deadband']:
                self.make_thermostat(thermo_data,'COOL')
            elif avg_temperature < self.data['cool_setpoint'] - self.data['deadband']:
                self.make_thermostat(thermo_data,'NOCOOL')

        if self.data['mode'] in ['HEAT','AUTO']:
            if avg_temperature < self.data['heat_setpoint'] - self.data['deadband']:
                self.make_thermostat(thermo_data,'HEAT')
            elif avg_temperature > self.data['cool_setpoint'] + self.data['deadband']:
                self.make_thermostat(thermo_data,'NOHEAT')

        self.data['avg_temperature'] = avg_temperature
        self.curcon.execute("UPDATE application_running SET app_data=%s, status=%s WHERE app_agent_id=%s",
                            (json.dumps(self.data), "running", self.agent_id))
        self.curcon.commit()
        print avg_temperature


def main(argv=sys.argv):
    '''Main method called by the eggsecutable.'''
    try:
        utils.vip_main(ThermostatControlAgent)
    except Exception as e:
        _log.exception('unhandled exception')

if __name__ == '__main__':
    # Entry point for script
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        pass