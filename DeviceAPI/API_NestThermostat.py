# -*- coding: utf-8 -*-
'''
Copyright (c) 2016, Virginia Tech
All rights reserved.

Redistribution and use in source and binary forms, with or without modification, are permitted provided that the
 following conditions are met:
1. Redistributions of source code must retain the above copyright notice, this list of conditions and the following
disclaimer.
2. Redistributions in binary form must reproduce the above copyright notice, this list of conditions and the following
disclaimer in the documentation and/or other materials provided with the distribution.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES,
INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY,
WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

The views and conclusions contained in the software and documentation are those of the authors and should not be
interpreted as representing official policies, either expressed or implied, of the FreeBSD Project.

This material was prepared as an account of work sponsored by an agency of the United States Government. Neither the
United States Government nor the United States Department of Energy, nor Virginia Tech, nor any of their employees,
nor any jurisdiction or organization that has cooperated in the development of these materials, makes any warranty,
express or implied, or assumes any legal liability or responsibility for the accuracy, completeness, or usefulness or
any information, apparatus, product, software, or process disclosed, or represents that its use would not infringe
privately owned rights.

Reference herein to any specific commercial product, process, or service by trade name, trademark, manufacturer, or
otherwise does not necessarily constitute or imply its endorsement, recommendation, favoring by the United States
Government or any agency thereof, or Virginia Tech - Advanced Research Institute. The views and opinions of authors
expressed herein do not necessarily state or reflect those of the United States Government or any agency thereof.

VIRGINIA TECH – ADVANCED RESEARCH INSTITUTE
under Contract DE-EE0006352

#__author__ = "Mengmeng Cai"
#__credits__ = ""
#__version__ = "3.5"
#__maintainer__ = "BEMOSS Team"
#__email__ = "aribemoss@gmail.com"
#__website__ = "www.bemoss.org"
#__created__ = "2016-10-07"
#__lastUpdated__ = "2016-10-10"
'''

'''This API class is for an agent that want to communicate/monitor/control
devices that compatible with Nest Thermostat'''


import json
from urlparse import urlparse
from DeviceAPI.BaseAPI import baseAPI
from bemoss_lib.utils.BEMOSS_ONTOLOGY import BEMOSS_ONTOLOGY
import requests
import time



class API(baseAPI):

    def __init__(self,**kwargs):
        super(API, self).__init__(**kwargs)
        self.variables = kwargs
        # self.device_supports_auto = False
        # self.set_variable(BEMOSS_ONTOLOGY.THERMOSTAT_MODE.NAME,BEMOSS_ONTOLOGY.THERMOSTAT_MODE.POSSIBLE_VALUES.OFF)
        self._debug = False

        self.serial = None
        self.units = 'F'
        self.index = 0
        self.set_variable('connection_renew_interval', 3600)
        self.set_variable('offline_count', 0)
        if 'username' in self.variables.keys():
            try:
                self.username = self.variables['username']
                self.password = self.variables['password']
                self.login(self.username, self.password)
                self.serial = self.variables['mac_address']
            except:
                print ("ERROR: Couldn't login to Nest website")

    def login(self, username, password):

        try:
            response = requests.post("https://home.nest.com/user/login",
                                     data={"username": username, "password": password},
                                     headers={"user-agent": "Nest/1.1.0.10 CFNetwork/548.0.4"}, timeout=30)

            response.raise_for_status()

            res = response.json()
            # print "Nest response: {}".format(res)
            self.transport_url = res["urls"]["transport_url"]
            self.access_token = res["access_token"]
            self.userid = res["userid"]
        except:
            print "Nest login failed, try again"
            print self.transport_url, self.access_token, self.userid

    def get_status(self):
        try:
            response = requests.get(self.transport_url + "/v2/mobile/user." + self.userid,
                                    headers={"user-agent": "Nest/1.1.0.10 CFNetwork/548.0.4",
                                             "Authorization": "Basic " + self.access_token,
                                             "X-nl-user-id": self.userid,
                                             "X-nl-protocol-version": "1"})

            response.raise_for_status()
            res = response.json()
            self.structure_id = res["structure"].keys()[0]
            self.status = res
        except:
            print "Nest get status failed, try again"

    def temp_in(self, temp):
        if (self.units == "F"):
            return (temp - 32.0) / 1.8
        else:
            return temp

    def temp_out(self, temp):
        if (self.units == "F"):
            return temp * 1.8 + 32.0
        else:
            return temp

    def timeDelay(self, time_iden):  # specify time_iden for how long to delay the process
        t0 = time.time()
        self.seconds = time_iden
        while time.time() - t0 <= time_iden:
            self.seconds = self.seconds - 1
            print("wait: {} sec".format(self.seconds))
            time.sleep(1)

    def API_info(self):
        return [{'device_model' : 'Nest', 'vendor_name' : 'Google', 'communication' : 'WiFi',
                'device_type_id' : 1, 'api_name': 'API_NestThermostat','html_template':'thermostat/thermostat.html',
                'agent_type':'ThermostatAgent','identifiable' : True, 'authorizable': False, 'is_cloud_device' : True,
                'schedule_weekday_period' : 4,'schedule_weekend_period' : 4, 'allow_schedule_period_delete' : True,
                'chart_template': 'charts/charts_thermostat.html'},]

    def dashboard_view(self):
        if self.get_variable(BEMOSS_ONTOLOGY.THERMOSTAT_MODE.NAME) == BEMOSS_ONTOLOGY.THERMOSTAT_MODE.POSSIBLE_VALUES.OFF:
            return {"top": BEMOSS_ONTOLOGY.THERMOSTAT_MODE.NAME, "center": {"type": "number", "value": BEMOSS_ONTOLOGY.TEMPERATURE.NAME},
            "bottom": None}
        else:
            return {"top": BEMOSS_ONTOLOGY.THERMOSTAT_MODE.NAME, "center": {"type": "number", "value": BEMOSS_ONTOLOGY.TEMPERATURE.NAME},
            "bottom": BEMOSS_ONTOLOGY.SETPOINT.NAME}

    def ontology(self):
        return {"target_temperature_type":BEMOSS_ONTOLOGY.THERMOSTAT_MODE,"tstate":BEMOSS_ONTOLOGY.THERMOSTAT_STATE,
                "fan_mode":BEMOSS_ONTOLOGY.FAN_MODE,"fstate":BEMOSS_ONTOLOGY.FAN_STATE,
                "t_cool":BEMOSS_ONTOLOGY.COOL_SETPOINT,"t_heat":BEMOSS_ONTOLOGY.HEAT_SETPOINT,
                'target_temperature':BEMOSS_ONTOLOGY.SETPOINT, "current_temperature":BEMOSS_ONTOLOGY.TEMPERATURE,
                "battery_level":BEMOSS_ONTOLOGY.BATTERY,"anti-tampering":BEMOSS_ONTOLOGY.ANTI_TAMPERING}

    def discover(self, username, password):
        try:
            self.login(username, password)
            self.get_status()
        except:
            print "Nest discovery failed, try again"
        discovered_devices = list()
        for response in self.status["structure"][self.structure_id]["devices"]:
            try:
                mac_address = response.split('.')[1]
                address = self.status['device'][mac_address]['local_ip']
                model_vendor = self.getModelVendor(address)
                discovered_devices.append({'address': address, 'mac': mac_address, 'model': model_vendor['model'],
                                           'vendor': model_vendor['vendor']})
            except:
                pass
        if self._debug:
            print discovered_devices
        return discovered_devices

    def getModelVendor(self,address):
        return {'model': "Nest", 'vendor': "Google"}

    # def getMACAddress(self, address):
    #     pass

    def renewConnection(self, username, password):
        self.login(username, password)

    target_temperature_type_dict = {'off':BEMOSS_ONTOLOGY.THERMOSTAT_MODE.POSSIBLE_VALUES.OFF,
                  'heat':BEMOSS_ONTOLOGY.THERMOSTAT_MODE.POSSIBLE_VALUES.HEAT,
                  'cool':BEMOSS_ONTOLOGY.THERMOSTAT_MODE.POSSIBLE_VALUES.COOL,
                  'range':BEMOSS_ONTOLOGY.THERMOSTAT_MODE.POSSIBLE_VALUES.AUTO}
    fan_mode_dict = {'auto':BEMOSS_ONTOLOGY.FAN_MODE.POSSIBLE_VALUES.AUTO,
                  'on':BEMOSS_ONTOLOGY.FAN_MODE.POSSIBLE_VALUES.ON}

    # GET Open the URL and read the data
    def getDataFromDevice(self):
        response = requests.get(self.transport_url + "/v2/mobile/user." + self.userid,
                                headers={"user-agent": "Nest/1.1.0.10 CFNetwork/548.0.4",
                                         "Authorization": "Basic " + self.access_token,
                                         "X-nl-user-id": self.userid,
                                         "X-nl-protocol-version": "1"}, timeout=30)
        response.raise_for_status()
        _theJSON = response.json()
        if self._debug: print _theJSON
        devicedata = dict()
        self.structure_id = _theJSON["structure"].keys()[0]
        self.status = _theJSON

        # 1. temperature
        current_temperature = self.status["shared"][self.serial]["current_temperature"]
        current_temperature = float('%.1f' % self.temp_out(current_temperature))
        devicedata['current_temperature'] = current_temperature

        # 2. thermostat_mode
        target_temperature_type = self.status["shared"][self.serial]["target_temperature_type"]
        if target_temperature_type in ['off','heat','cool','range']:
            devicedata['target_temperature_type'] = self.target_temperature_type_dict[target_temperature_type]
        else:
            print("Invalid value for device target_temperature_type")

        # 3. fan_mode
        fan_mode = self.status["device"][self.serial]["fan_mode"]
        if fan_mode in ['auto','on']:
           devicedata['fan_mode'] = self.fan_mode_dict[fan_mode]
        else:
            print(" Invalid value for fan_mode")

        # 6. thermostat_state
        devicedata['tstate'] = devicedata['target_temperature_type']

        # 7. fan_state
        devicedata['fstate'] = devicedata['fan_mode']

        # 8. battery
        battery_level = self.status["device"][self.serial]["battery_level"]
        if battery_level >= 3.9:
            battery = 100
        elif battery_level <= 3.6:
            battery = 0
        else:
            battery = int(((battery_level - 3.6) / 0.3) * 100)
        devicedata['battery_level'] = battery

        # 9. Setpoint
        target_temp = self.status["shared"][self.serial]["target_temperature"]
        target_temp = float('%.1f' % self.temp_out(target_temp))
        if devicedata['target_temperature_type'] == "HEAT":
            devicedata['t_heat'] = target_temp
        if devicedata['target_temperature_type'] == "COOL":
            devicedata['t_cool'] = target_temp

        print devicedata
        return devicedata

    def setDeviceData(self, postmsg):
        setDeviceDataResult = True
        # step2: send message to change status of the device
        if self.isPostmsgValid(postmsg) == True:  # check if the data is valid
            try:
                self.sendPostMsg(postmsg)
                print ("NEST thermostat DONE!! set device status")
            except:
                setDeviceDataResult = False
                print ("ERROR: classAPI_Nest failure at setDeviceStatus")
        else:
            print(
            "The POST message is invalid, check thermostat_mode, heat_setpoint, cool_setpoint setting and try again\n")
        return setDeviceDataResult

    def isPostmsgValid(self,postmsg):  # check validity of postmsg
        dataValidity = True
        for k,v in postmsg.items():
            if k == BEMOSS_ONTOLOGY.THERMOSTAT_MODE.NAME:
                if postmsg.get(BEMOSS_ONTOLOGY.THERMOSTAT_MODE.NAME) == BEMOSS_ONTOLOGY.THERMOSTAT_MODE.POSSIBLE_VALUES.HEAT:
                    for k,v in postmsg.items():
                        if k == BEMOSS_ONTOLOGY.COOL_SETPOINT.NAME:
                            dataValidity = False
                            break
                elif postmsg.get(BEMOSS_ONTOLOGY.THERMOSTAT_MODE.NAME) == BEMOSS_ONTOLOGY.THERMOSTAT_MODE.POSSIBLE_VALUES.COOL:
                    for k,v in postmsg.items():
                        if k == BEMOSS_ONTOLOGY.HEAT_SETPOINT.NAME:
                            dataValidity = False
                            break
        return dataValidity

    def _set(self, data, which):
        if (self._debug): print json.dumps(data)
        url = "%s/v2/put/%s.%s" % (self.transport_url, which, self.serial)
        if (self._debug): print url
        response = requests.post(url,
                                 data=json.dumps(data),
                                 headers={"user-agent": "Nest/1.1.0.10 CFNetwork/548.0.4",
                                          "Authorization": "Basic " + self.access_token,
                                          "X-nl-protocol-version": "1"}, timeout=30)

        if response.status_code > 200:
            if (self._debug): print response.content
        response.raise_for_status()
        return response

    def _set_shared(self, data):
       self._set(data, "shared")

    def _set_device(self, data):
       self._set(data, "device")

    def set_temperature(self, temp):
       return self._set_shared({
             "target_change_pending": True,
             self.dict_rev_translate(self.ontology(),BEMOSS_ONTOLOGY.SETPOINT): self.temp_in(temp)
             })

    def set_fan(self, state):
       return self._set_device({
             self.dict_rev_translate(self.ontology(),BEMOSS_ONTOLOGY.FAN_MODE): str(state)
             })

    def set_mode(self, state):
        return self._set_shared({
            self.dict_rev_translate(self.ontology(),BEMOSS_ONTOLOGY.THERMOSTAT_MODE): str(state)
        })

    def sendPostMsg(self, postmsg):
        if BEMOSS_ONTOLOGY.THERMOSTAT_MODE.NAME not in postmsg:
            if BEMOSS_ONTOLOGY.HEAT_SETPOINT.NAME in postmsg:
                self.set_mode('heat')
                self.set_temperature(int(postmsg.get(BEMOSS_ONTOLOGY.HEAT_SETPOINT.NAME)))
            elif BEMOSS_ONTOLOGY.COOL_SETPOINT.NAME in postmsg:
                self.set_mode('cool')
                self.set_temperature(int(postmsg.get(BEMOSS_ONTOLOGY.COOL_SETPOINT.NAME)))
            else:
                pass
        else:
            pass
        for k, v in postmsg.items():
            if k == BEMOSS_ONTOLOGY.THERMOSTAT_MODE.NAME:
                if postmsg.get(BEMOSS_ONTOLOGY.THERMOSTAT_MODE.NAME).upper() == BEMOSS_ONTOLOGY.THERMOSTAT_MODE.POSSIBLE_VALUES.HEAT:
                    self.set_mode('heat')
                    time.sleep(1)
                    if postmsg.get(BEMOSS_ONTOLOGY.HEAT_SETPOINT.NAME) is None:
                        self.set_temperature(72)
                    else:
                        self.set_temperature(int(postmsg.get(BEMOSS_ONTOLOGY.HEAT_SETPOINT.NAME)))
                elif postmsg.get(BEMOSS_ONTOLOGY.THERMOSTAT_MODE.NAME).upper() == BEMOSS_ONTOLOGY.THERMOSTAT_MODE.POSSIBLE_VALUES.COOL:
                    self.set_mode('cool')
                    time.sleep(1)
                    if postmsg.get(BEMOSS_ONTOLOGY.COOL_SETPOINT.NAME) is None:
                        self.set_temperature(75)
                    else:
                        self.set_temperature(int(postmsg.get(BEMOSS_ONTOLOGY.COOL_SETPOINT.NAME)))
                elif postmsg.get(BEMOSS_ONTOLOGY.THERMOSTAT_MODE.NAME).upper() == BEMOSS_ONTOLOGY.THERMOSTAT_MODE.POSSIBLE_VALUES.OFF:
                    self.set_mode('off')
                elif postmsg.get(BEMOSS_ONTOLOGY.THERMOSTAT_MODE.NAME).upper() == BEMOSS_ONTOLOGY.THERMOSTAT_MODE.POSSIBLE_VALUES.AUTO:
                    self.set_mode('range')
                else:
                    print("invalid argument for thermostat_mode")
            if k == BEMOSS_ONTOLOGY.FAN_MODE.NAME:
                if postmsg.get(BEMOSS_ONTOLOGY.FAN_MODE.NAME) == BEMOSS_ONTOLOGY.FAN_MODE.POSSIBLE_VALUES.AUTO:
                    self.set_fan('auto')
                elif postmsg.get(BEMOSS_ONTOLOGY.FAN_MODE.NAME) == BEMOSS_ONTOLOGY.FAN_MODE.POSSIBLE_VALUES.ON:
                    self.set_fan('on')
                else:
                    print("invalid argument for fan_mode")

    def identifyDevice(self):
        identifyDeviceResult = False
        devicedata = self.getDataFromDevice()
        mode = devicedata[BEMOSS_ONTOLOGY.THERMOSTAT_MODE.NAME]
        try:
            print(" {0}Agent for {1} is identifying itself by changing mode for 10 seconds "
                  "then back to original mode please wait ...".format(self.variables.get('agent_id', None),
                                                                      self.variables.get('model', None)))
            if mode == 'COOL':
                _temp = devicedata['cool_setpoint']
                self.setDeviceData({BEMOSS_ONTOLOGY.THERMOSTAT_MODE.NAME: 'HEAT', "heat_setpoint": 90})  # To be able to see orange color
                # _temp = self.get_variable('cool_setpoint')
            elif mode == 'HEAT':
                _temp = devicedata['heat_setpoint']
                self.setDeviceData({BEMOSS_ONTOLOGY.THERMOSTAT_MODE.NAME: 'COOL', "cool_setpoint": 50})  # To be able to see blue color
                # _temp = self.get_variable('heat_setpoint')
            # self.getDeviceStatus()
            self.timeDelay(10)
            if mode == 'COOL':
                self.setDeviceData({BEMOSS_ONTOLOGY.THERMOSTAT_MODE.NAME: mode, "cool_setpoint": _temp})
            elif mode == 'HEAT':
                self.setDeviceData({BEMOSS_ONTOLOGY.THERMOSTAT_MODE.NAME: mode, "heat_setpoint": _temp})
            else:
                pass
            # self.getDeviceStatus()
            identifyDeviceResult = True
        except Exception as er:
            print er
            print("ERROR: classAPI_Nest failure! @ identifyDevice")

        return identifyDeviceResult


# This main method will not be executed when this class is used as a module
def main():
    # Step1: create an object with initialized data from DeviceDiscovery Agent
    # requirements for instantiation1. model, 2.type, 3.api, 4. address
    Nest = API(model='Nest', agent_id='wifithermostat1', api='API', username='nest.bemoss@gmail.com',
               password='VTbemoss2017!', mac_address='fake17584BA76AB1')
    # print Nest.discover('nest.bemoss@gmail.com', 'VTbemoss2017!')
    Nest.getDeviceStatus()
    Nest.setDeviceData({"thermostat_mode":"heat", "heat_setpoint":72, "fan_mode":'AUTO'})
    Nest.getDeviceStatus()
    # Nest.identifyDevice()

if __name__ == "__main__": main()
