var mosca = require('mosca');

console.log("Here!");

var pubsubsettings = {
    type: 'mongo',
    url: 'mongodb://localhost:27017/mqtt',
    pubsubCollection: 'ascoltatori',
    mongo : {}
};

var moscaSettings = {
    port : 1883,
    backend : pubsubsettings,
    http : {
        port : 3000,
        bundle : true,
        static : './'
    }
};

var clients = {};

var server = new mosca.Server(moscaSettings);
server.on('ready',setup);

function setup() {
    console.log('Mosca server is up and running.');
}

server.on('published', function(packet) {
    try{
        clients[packet.topic].value = packet.payload.toString();
    } catch(err) {
	if (packet.topic.charAt(0) != "$") {
        clients[packet.topic] = ({"value" : packet.payload.toString()});
	} else {
	    console.log(err);
	}
    }
    console.log(packet);
    console.log('Published', packet.payload.toString());
});

server.on('subscribed', function(topic, client) {
    if (topic != "#") {
        clients[topic] = ({"value": 1});
        server.publish({
            topic:"clients",
            payload:JSON.stringify(clients),
            qos:0,
            retain:false
        }, function() {
            console.log("Sent client lists.");
        });
    } else {
        server.publish({
            topic:"clients",
            payload:JSON.stringify(clients),
            qos:0,
            retain:false
        }, function() {
            console.log("Sent client lists.");
        });

    }
    console.log(topic);
});

server.on('clientConnected', function(client) {
    console.log('Client Connected:', client.id);
});

server.on('clientDisconnected', function(client) {
    console.log('Client Disconnected:', client.id);
});
