
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from webapps.deviceinfos.models import DeviceMetadata
from webapps.device.models import Devicedata
from bemoss_lib.utils.VIP_helper import vip_publish, vip_publish_bulk
from bemoss_lib.utils.BEMOSS_ONTOLOGY import BEMOSS_ONTOLOGY
from django.core.exceptions import ObjectDoesNotExist
import json
import settings


ALEXAKEY = settings.ALEXA_KEY


def get_member_variables(cls):
    var = vars(cls)
    del var['__doc__']
    del var['__module__']
    return var


ONTOLOGY_DICT = get_member_variables(BEMOSS_ONTOLOGY)

DEVICE_TYPES ={''}

def nom(var): #normalize names for loose comparison
    return var.lower().replace(' ', '').replace('_', '')

def find_ontology(variable_name):
    variable_name = nom(variable_name)
    for key,value in ONTOLOGY_DICT.items():
        if nom(key) == variable_name or nom(value.NAME) == variable_name:
            return value
        if hasattr(value, 'SPOKEN_NAMES'):
            for spoken_name in value.SPOKEN_NAMES:
                if variable_name == nom(spoken_name):
                    return value

    return None

def find_in_nicknames(device_name):
    device_name = nom(device_name)
    nickname_list = [dev.nickname for dev in DeviceMetadata.objects.all()]
    for nickname in nickname_list:
        if nom(nickname) == device_name:
            return nickname
    return None

def find_in_device_types(device_type):
    device_type = nom(device_type)

    device_type_list = [dev.nickname for dev in DeviceMetadata.objects.all()]
    for dev_type in device_type_list:
        if nom(dev_type.device_type) == device_type:
            return dev_type
    return None

def validate_request(request):
    if not request.data['auth'] == ALEXAKEY:
        response = {'success': 0, 'cause': 'Unauthorized!'}
        return Response(response)

    if not request.method == 'POST':
        return Response(status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'POST'])
def device_monitor(request):
    print "device_monitor"
    print request.data
    validate_request(request)

    received_data = request.data
    if isinstance(received_data, dict):
        data = json.loads(received_data['dumps'])
    else:
        myDict = dict(received_data.iterlists())
        data = dict()
        for key, value in myDict.iteritems():
            data[key.encode('utf8')] = value[0].encode('utf8')
    device_nickname = data['nickname']
    var = data['variable']

    db_nickname = find_in_nicknames(device_nickname)
    if db_nickname:
        device_info = DeviceMetadata.objects.get(nickname__icontains=db_nickname)
    else:
        response = {'success': 0, 'cause': 'No such device found'}
        return Response(response)
    agent_id = device_info.agent_id
    device_data = Devicedata.objects.get(agent_id=agent_id).data
    if 'variable' in data.keys():
        try:
            var = data['variable']
            if var == '':
                response = {'success': 0, 'cause': 'Empty variable.'}
            else:
                try:
                    response = {'success': 1, 'value': device_data[var]}
                except KeyError:
                    ont = find_ontology(var)
                    if ont: #ontology found
                        var = ont.NAME
                    response = {'success': 1, 'value': device_data[var]}
            return Response(response)
        except KeyError:
            response = {'success': 0, 'cause': 'variable does not exist'}
            return Response(response)
    else:
        response = {'success': 1}
        response.update({'value': device_data})
        return Response(response)


@api_view(['POST', 'GET'])
def device_control(request):
    print "device_control"
    print request.data
    validate_request(request)

    data=dict()
    failed_variables=list()
    senddata=dict()
    received_data=request.data
    # myDict=dict(received_data.iterlists())
    # for key,value in myDict.iteritems():
    #     data[key.encode('utf8')]=value[0].encode('utf8')
    data = json.loads(received_data['dumps'])
    nickname = str(data['nickname'])
    variables = json.loads(json.dumps(data['variable']))
    #The format is {'nickname':'device1','variable':{'cool setpoint':34}
    if nickname.startswith("all_"):
        device_type = nickname[4:]
        if device_type[-1] == 's': #if it is plural, make it singular
            device_type = device_type[:-1]
        devices = []
        for device in DeviceMetadata.objects.all():
            if ' '+device_type.lower() in device.nickname.replace('_',' ').lower(): #make lights match with bedroom_light and bedroom light but not flight thermostat
                devices.append(device)
    else:
        db_nickname = find_in_nicknames(nickname)
        if db_nickname:
            devices = [DeviceMetadata.objects.get(nickname__icontains=db_nickname)]
        else:
            response = {'success': 0, 'cause': 'No such device found'}
            return Response(response)

    if not devices:
        response = {'success': 0, 'cause': 'No such device found'}
        return Response(response)

    vip_message_list = list()
    for device in devices:
        agent_id = device.agent_id
        validdata = False
        device_data = Devicedata.objects.get(agent_id=agent_id).data
        for variable,val in variables.items():
            ont = find_ontology(variable)
            if ont and hasattr(ont,'POSSIBLE_VALUES'): #convert the provided value into BEMOSS_ONTOLOGY value
                if type(val) in [str, unicode]:
                    val = val.lower()
                if hasattr(ont,'POSSIBLE_SPOKEN_VALUES'): #if POSSIBLE_SPOKEN_VALUES is defined, use that
                    for possible_ont_value, spoken_list in ont.POSSIBLE_SPOKEN_VALUES.items():
                        if nom(val) in spoken_list:
                            val = possible_ont_value
                            break
                    else:
                        #failed_variables.append(variable) #can't match, use as it is
                        pass
                else:
                    possible_vals_dict = get_member_variables(ont.POSSIBLE_VALUES) #if not, just try to match with POSSIBLE_VALUES
                    for key, possible_value in possible_vals_dict.items():
                        if nom(val) == nom(possible_value):
                            val = possible_value
                            break
                    else:
                        #failed_variables.append(variable)  # can't match, then use as it is
                        pass
            if ont:
                if ont.TYPE in ['double','float']:
                    val = float(val)
                elif ont.TYPE in ['int']:
                    val = int(val)

            if variable not in device_data.keys():
                if ont and ont.NAME in device_data.keys():
                    validdata = True
                    senddata[ont.NAME] = val
                else:
                    message = "invalid attribute selected to change"
                    failed_variables.append(variable)
                    continue
            else:
                validdata = True
                senddata[variable] = val

        update_send_topic = 'to/' + agent_id + '/from/ui/update'
        update_send_topic2 = 'to/' + agent_id + '/update/from/ui'
        vip_message_list.append((update_send_topic, senddata))
        vip_message_list.append((update_send_topic2, senddata))

    if vip_message_list:
        vip_publish_bulk(vip_message_list)

    if failed_variables:
        if validdata:
            response = {'success':2,'cause':'One or more variable invalid'}
        else:
            response = {'success': 0, 'cause': 'invalid variables'}
        return Response(response)
    response = {'success': 1}
    return Response(response)

