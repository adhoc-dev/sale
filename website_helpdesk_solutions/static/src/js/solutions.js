odoo.define('website_helpdesk_solutions.solutions',['web.ajax'],function(require){
    'use strict';
    var ajax = require('web.ajax');

    $(document).ready(function(){
        var container = document.getElementById("solution");

        if (container) {
            container.innerHTML = "";
            container.innerHTML = "<div class='col text-center'>Cargando</div>"

            ajax.jsonRpc('/get_solution', 'call', {'test'}).then(function(data){
                container.innerHTML = "";
                console.log(data);
                for (var i=0; i< data.length; i++) {
                    container.innerHTML += '<div>' + data[i].name + data[i].ticket_description + '</div>';
                }
            });
        }
    });
});
