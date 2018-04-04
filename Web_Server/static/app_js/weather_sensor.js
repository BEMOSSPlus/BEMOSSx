/**

 *  Authors: Kruthika Rathinavel
 *  Version: 2.0
 *  Email: kruthika@vt.edu
 *  Created: "2014-10-13 18:45:40"
 *  Updated: "2015-02-13 15:06:41"


 * Copyright © 2014 by Virginia Polytechnic Institute and State University
 * All rights reserved

 * Virginia Polytechnic Institute and State University (Virginia Tech) owns the copyright for the BEMOSS software and its
 * associated documentation ("Software") and retains rights to grant research rights under patents related to
 * the BEMOSS software to other academic institutions or non-profit research institutions.
 * You should carefully read the following terms and conditions before using this software.
 * Your use of this Software indicates your acceptance of this license agreement and all terms and conditions.

 * You are hereby licensed to use the Software for Non-Commercial Purpose only.  Non-Commercial Purpose means the
 * use of the Software solely for research.  Non-Commercial Purpose excludes, without limitation, any use of
 * the Software, as part of, or in any way in connection with a product or service which is sold, offered for sale,
 * licensed, leased, loaned, or rented.  Permission to use, copy, modify, and distribute this compilation
 * for Non-Commercial Purpose to other academic institutions or non-profit research institutions is hereby granted
 * without fee, subject to the following terms of this license.

 * Commercial Use: If you desire to use the software for profit-making or commercial purposes,
 * you agree to negotiate in good faith a license with Virginia Tech prior to such profit-making or commercial use.
 * Virginia Tech shall have no obligation to grant such license to you, and may grant exclusive or non-exclusive
 * licenses to others. You may contact the following by email to discuss commercial use:: vtippatents@vtip.org

 * Limitation of Liability: IN NO EVENT WILL VIRGINIA TECH, OR ANY OTHER PARTY WHO MAY MODIFY AND/OR REDISTRIBUTE
 * THE PROGRAM AS PERMITTED ABOVE, BE LIABLE TO YOU FOR DAMAGES, INCLUDING ANY GENERAL, SPECIAL, INCIDENTAL OR
 * CONSEQUENTIAL DAMAGES ARISING OUT OF THE USE OR INABILITY TO USE THE PROGRAM (INCLUDING BUT NOT LIMITED TO
 * LOSS OF DATA OR DATA BEING RENDERED INACCURATE OR LOSSES SUSTAINED BY YOU OR THIRD PARTIES OR A FAILURE
 * OF THE PROGRAM TO OPERATE WITH ANY OTHER PROGRAMS), EVEN IF VIRGINIA TECH OR OTHER PARTY HAS BEEN ADVISED
 * OF THE POSSIBILITY OF SUCH DAMAGES.

 * For full terms and conditions, please visit https://bitbucket.org/bemoss/bemoss_os.

 * Address all correspondence regarding this license to Virginia Tech's electronic mail address:: vtippatents@vtip.org

**/

$(document).ready(function() {
    $.csrftoken();

    var ws = new WebSocket("ws://" + window.location.host +  "/socket_agent/"+device_data.agent_id);

     ws.onopen = function () {
         ws.send("WS opened from html page");
     };

     ws.onmessage = function (event) {
         var _data = event.data;
         _data = $.parseJSON(_data);
         var topic = _data['topic'];
          // from/agent_id/device_status_response
         // from/agent_id/device_update_response
         if (topic) {
             topic = topic.split('/');
             console.log(topic);
             if (topic[1] == device_data.agent_id && topic[2] == 'device_status_response') {
                 if ($.type( _data['message'] ) === "string"){
                     var _message = $.parseJSON(_data['message']);
                     if ($.type(_message) != "object"){
                         _message = $.parseJSON(_message)
                     }
                     change_weather_sensor_values(_message);
                 } else if ($.type( _data['message'] ) === "object"){
                     change_weather_sensor_values(_data['message']);
                 }

             }
         }
     };

    function change_weather_sensor_values(_data) {
        var date_max_temp = new Date(1000*_data.date_max_temp);
        var date_min_temp = new Date(1000*_data.date_min_temp);
        var outdoor_date_max_temp = new Date(1000*_data.outdoor_date_max_temp);
        var outdoor_date_min_temp = new Date(1000*_data.outdoor_date_min_temp);
        //Indoor Values
        $("#temperature").text(_data.temperature);
        $("#pressure").text(_data.pressure);
        $("#humidity").text(_data.humidity);
        $("#co2").text(_data.co2);
        $("#noise").text(_data.noise);
        $("#date_max_temp").text(date_max_temp.toLocaleString());
        $("#max_temp").text(_data.max_temp);
        $("#date_min_temp").text(date_min_temp.toLocaleString());
        $("#min_temp").text(_data.min_temp);
        //Outdoor values
        $("#outdoor_temperature").text(_data.outdoor_temperature);
        $("#outdoor_humidity").text(_data.outdoor_humidity);
        $("#outdoor_date_max_temp").text(outdoor_date_max_temp.toLocaleString());
        $("#outdoor_max_temp").text(_data.outdoor_max_temp);
        $("#outdoor_date_min_temp").text(outdoor_date_min_temp.toLocaleString());
        $("#outdoor_min_temp").text(_data.outdoor_min_temp);
    }

    (function get_weather_sensor_data(){
	values = {
		    "device_info": device_info
		    };
	var jsonText = JSON.stringify(values);
	setTimeout(function()
	{
		$.ajax({
		  url : '/wsstat/',
		  type: 'POST',
		  data: jsonText,
		  dataType: 'json',
		  success : function(data) {
		  	//change_tstat_values(data);
		  	get_weather_sensor_data();
		  },
		  error: function(data) {
			get_weather_sensor_data();
		  }
		 });
	},60000);
	})();


});