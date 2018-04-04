# -*- coding: utf-8 -*-
from __future__ import division
'''
Copyright (c) 2014 by Virginia Polytechnic Institute and State University
All rights reserved

Virginia Polytechnic Institute and State University (Virginia Tech) owns the copyright for the BEMOSS software and its
associated documentation (“Software”) and retains rights to grant research rights under patents related to
the BEMOSS software to other academic institutions or non-profit research institutions.
You should carefully read the following terms and conditions before using this software.
Your use of this Software indicates your acceptance of this license agreement and all terms and conditions.

You are hereby licensed to use the Software for Non-Commercial Purpose only.  Non-Commercial Purpose means the
use of the Software solely for research.  Non-Commercial Purpose excludes, without limitation, any use of
the Software, as part of, or in any way in connection with a product or service which is sold, offered for sale,
licensed, leased, loaned, or rented.  Permission to use, copy, modify, and distribute this compilation
for Non-Commercial Purpose to other academic institutions or non-profit research institutions is hereby granted
without fee, subject to the following terms of this license.

Commercial Use If you desire to use the software for profit-making or commercial purposes,
you agree to negotiate in good faith a license with Virginia Tech prior to such profit-making or commercial use.
Virginia Tech shall have no obligation to grant such license to you, and may grant exclusive or non-exclusive
licenses to others. You may contact the following by email to discuss commercial use: vtippatents@vtip.org

Limitation of Liability IN NO EVENT WILL VIRGINIA TECH, OR ANY OTHER PARTY WHO MAY MODIFY AND/OR REDISTRIBUTE
THE PROGRAM AS PERMITTED ABOVE, BE LIABLE TO YOU FOR DAMAGES, INCLUDING ANY GENERAL, SPECIAL, INCIDENTAL OR
CONSEQUENTIAL DAMAGES ARISING OUT OF THE USE OR INABILITY TO USE THE PROGRAM (INCLUDING BUT NOT LIMITED TO
LOSS OF DATA OR DATA BEING RENDERED INACCURATE OR LOSSES SUSTAINED BY YOU OR THIRD PARTIES OR A FAILURE
OF THE PROGRAM TO OPERATE WITH ANY OTHER PROGRAMS), EVEN IF VIRGINIA TECH OR OTHER PARTY HAS BEEN ADVISED
OF THE POSSIBILITY OF SUCH DAMAGES.

For full terms and conditions, please visit https://bitbucket.org/bemoss/bemoss_os.

Address all correspondence regarding this license to Virginia Tech’s electronic mail address: vtippatents@vtip.org

__author__ =  "BEMOSS Team"
__credits__ = ""
__version__ = "3.5"
__maintainer__ = "BEMOSS Team""
__email__ = "aribemoss@gmail.com"
__website__ = ""
__status__ = "Prototype"
__created__ = "2016-10-24 16:12:00"
__lastUpdated__ = "2016-10-25 13:25:00"
'''
import csv
from collections import Counter, defaultdict
import os
import gevent
from DeviceAPI.BaseAPI import baseAPI
from csv import DictWriter
from bacpypes.object import get_datatype
from bacpypes.primitivedata import Enumerated, Unsigned, Boolean, Integer, Real, Double
debug = True

class BACnetAPI(baseAPI):

    def __init__(self, parent,converter={},scale={},CONFIG_FILE=None,**kwargs):
        baseAPI.__init__(self,**kwargs)
        self.device_supports_auto = True
        self._debug = True
        self.parent = parent
        self.converter = converter
        self.scale = scale
        self.proxy_address = "platform.bacnet_proxy"
        self.config_file = CONFIG_FILE
        if not hasattr(self, 'number'):
            self.number="1"
        if 'vip' in self.variables.keys():
            self.vip = self.variables['vip']
    #        self.core = BasicCore(self)
            self.core= self.variables['core']

    def discover(self):

        try:
            deviceinfo = self.broadcast()
            return deviceinfo

        except Exception as e:
            print e
            return None

    def broadcast(self, *args):

        deviceinfo = list()
        try:

            Remote_address=list()
            Identifier=list()
            discovery2=list()
            discovery1=list()
            retries=2

            while retries>0:
                try:
                    addresses = self.vip.rpc.call(self.proxy_address, 'broadcast', *args).get(timeout=10.0)
                except gevent.Timeout:
                    print "Discovery call timeout"
                    return None
                for a,b in addresses:
                    discovery1.append(a)
                    discovery2.append(b)
                retries=retries-1
            Remote_addresses=zip(discovery1,discovery2)
            Remote_addresses=list(set(Remote_addresses))
            for Address, property_instance in Remote_addresses:
                Remote_address.append(Address)
                Identifier.append(property_instance)
            for i in range(0, len(Identifier)):
                Address = Remote_address[i]  # destination address
                object_instance = Identifier[i]
                if object_instance!=4194303:
                    if object_instance!=0:
                        model,vendor=self.GetModelVendor(Address,object_instance)
                        deviceinfo.append({'address': Address, 'mac': str(object_instance),
                               'model': model, 'vendor': vendor, })
            config_path = os.path.dirname(os.path.abspath(__file__))
            config_path = config_path + "/Bacnetdata"
            for device in deviceinfo:
                address = device["address"]
                device_id = device["mac"]
                filename = str(device_id) + ".csv"
                success = False
                for files in os.listdir(config_path):
                    if files.endswith(filename):
                        success = True
                if not success:
                        self.configure_data(address, device_id)
            #search for config

            return deviceinfo
        except Exception as e:
            print e
            return deviceinfo


    def GetModelVendor(self,Address,object_instance):

        model= ""
        vendor = ""
        retries = 2
        while retries > 0:
            try:
                    propertylist=["modelName","vendorName"]
                    value= self.vip.rpc.call(self.proxy_address, 'simple_read', Address,object_instance,propertylist).get(timeout=10.0)
                    if value and len(value)==2:
                        vendor,model=value
                    return model,vendor
            except Exception as e:
                print e
                retries=retries-1
            except gevent.Timeout:
                retries=retries-1
        return model,vendor

    def getDataFromDevice(self):

        bacnetread = self.Bacnet_read()
        return bacnetread

    def setDeviceData(self, postmsg):

         try:
            result = self.sendcommand(postmsg)
            return result
         except Exception as e:
            print e
            return False

    def Bacnet_read(self):

        results={}
        needed_points = list()
        needed_objecttype = list()
        needed_index = list()
        data = self.readcsv()
        if data:
            device_count = data["Device number"]
            device_map = self.duplicates_indices(device_count)
            for device, values in device_map.iteritems():
                if self.number == device:
                    for value in values:
                        if data['Reference Point Name'][value] in self.ontology():
                            needed_points.append(data['Reference Point Name'][value])
                            needed_objecttype.append(data['BACnet Object Type'][value])
                            needed_index.append(data['Index'][value])
                    devicepoints = zip(needed_points, needed_objecttype, needed_index)
                    try:
                        results = self.Bemoss_read(devicepoints)
                        print results
                        for key, value in results.iteritems():
                            if key in self.scale:
                                value=value*self.scale[key]
                            try:
                                if key in self.converter.keys():
                                        results[key] = self.dict_rev_translate(self.converter[key], value)
                                if type(value) ==float:
                                    results[key] = round(value, 2)
                            except ValueError:
                                continue
                    except Exception as e:
                        return results

                    return results

    def sendcommand(self, postmsg):

            point_names = list()
            setpoint=list()
            setvalues=list()
            needed_points = list()
            needed_objecttype = list()
            needed_index = list()
            for variable_name,set_value in postmsg.iteritems():
                #if variable_name in self.ontology().keys():
                    for key, ont_name in self.ontology().iteritems():
                        if variable_name == ont_name.NAME:
                            point_names.append(key)
                            setpoint.append(set_value)
                            break
            final_message=dict(zip(point_names, setpoint))
            devicepoints=list()
            data = self.readcsv()
            if data and final_message:
                device_count = data["Device number"]
                device_map = self.duplicates_indices(device_count)
                for device, values in device_map.iteritems():

                    if self.number == device:
                        for value in values:
                            param=data['Reference Point Name'][value]
                            if param in final_message.keys():

                                needed_points.append(param)
                                needed_objecttype.append(data['BACnet Object Type'][value])
                                needed_index.append(data['Index'][value])
                                if param in self.converter.keys():
                                    setvalues.append((self.converter[param][final_message[param]]))
                                else:
                                    setvalues.append(final_message[param])
                        devicepoints = zip(needed_points, needed_objecttype, needed_index,setvalues)
                        break
            if devicepoints:
                results = self.writedata(devicepoints)
            return True

    def writedata(self, postmessage,priority=8):

        target_address = self.variables['address']
        for needed_points, needed_objecttype, needed_index,setvalue in postmessage:

            setvalue = setvalue
            object_type=needed_objecttype
            instance_number=needed_index
            property="presentValue"
            try:
                args = [target_address, setvalue,
                        object_type,
                        int(instance_number),
                        property,
                        priority]
                result = self.vip.rpc.call(self.proxy_address, 'write_property', *args).get(timeout=10.0)
            except gevent.Timeout:
                    print "Write function timeout "
                    return False
            except Exception as e:
                    print e
                    return False
        writeresults=True
        return writeresults

    def readcsv(self):
        config_path = os.path.dirname(os.path.abspath(__file__))
        device_path = config_path + self.config_file

        with open(os.path.join(device_path), 'rU') as infile:
            reader = csv.DictReader(infile)
            data = {}
            for row in reader:
                for header, value in row.items():
                    try:
                        data[header].append(value)
                    except KeyError:
                        data[header] = [value]
        return data

    def duplicates_indices(self,lst):
        dup, ind = self.duplicates(lst), defaultdict(list)
        for i, v in enumerate(lst):
            if v in dup: ind[v].append(i)
        return ind

    def duplicates(self,lst):
        cnt = Counter(lst)
        return [key for key in cnt.keys() if cnt[key] >= 1]


    def Bemoss_read(self,devicepoints):
        point_map = {}
        result={}
        target_address=self.variables['address']
        for point_name,object_type,instance_number in devicepoints:

                point_map[point_name] = [object_type,
                                                  int(instance_number),
                                                  "presentValue"]
        try:
            result = self.vip.rpc.call(self.proxy_address, 'read_properties',
                                       target_address, point_map,
                                           ).get(timeout=10.0)
        except gevent.Timeout:
            print "BEMOSS Read function timeout "
        return result

    def configure_data(self, address, mac):

        try:
            config_path = os.path.dirname(os.path.abspath(__file__))
            config_path = config_path + "/Bacnetdata/"
            device_id=int(mac)
            target_address=address

            filename = str(device_id) + ".csv"
            try:
                Objectlist = ["objectList"]
                result = self.vip.rpc.call(self.proxy_address, 'simple_read', target_address, device_id,
                                           Objectlist).get(timeout=10.0)
            except TypeError:
                Objectlist = ["structuredObjectList"]
                result = self.vip.rpc.call(self.proxy_address, 'simple_read', target_address, device_id,
                                           Objectlist).get(timeout=10.0)
            if not result:
                return
            objectlist = result[0]

            with open (config_path+filename, 'wb')as fp:

                config_writer = DictWriter(fp,
                                           ('Reference Point Name',
                                            'BACnet Object Type',
                                            'Index',
                                            ))

                config_writer.writeheader()
                for object in objectlist:

                    obj_type= object[0]
                    index=object[1]
                    self.process_object(target_address, obj_type, index, config_writer)
        except Exception as e:
            print e
            return None
        except gevent.Timeout:
            print "objectlist call timeout"
            return None

    def process_object(self, address, obj_type, index, config_writer, max_range_report=None):

        try:
            description = self.vip.rpc.call(self.proxy_address, 'simple_read', address, index, propertylist=["objectName"], obj_type=obj_type).get(timeout=10.0)
            if not description:
                object_name = None
            else:
                object_name = description[0]
        except TypeError:
            object_name = None
        if object_name==None:
            try:
                object_name = self.vip.rpc.call(self.proxy_address, 'simple_read', address, index,propertylist=["description"], obj_type=obj_type).get(timeout=10.0)
                if not object_name:
                    object_name=''
                else:
                    object_name=object_name[0]
            except TypeError:
                object_name = ''
        results = {}
        results['Reference Point Name'] = object_name
        results['BACnet Object Type'] = obj_type
        results['Index'] = index
        config_writer.writerow(results)


