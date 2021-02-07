<template>
<div id="mapLayout" class="p-grid">

    <div class="p-col-2 filters">
        <div class="p-grid">
            <div class="p-col">
                <h3>Filters</h3>
                <Calendar label="Date Time" v-model="day" :showTime="true"  dateFormat="dd/mm/yy" />
                 <div class="p-col">
                    <Button label="Find" class="p-button p-component p-button-secondary" @click="find()"/>
                </div>
            </div>
        </div>
    </div>
    <div class="p-col-10" id="mapContainer">
        
    </div>
    </div>

</template>

<script>
import L from "leaflet";
import axios from 'axios'
import Calendar from 'primevue/calendar';
import Button from 'primevue/button';

const client = axios.create({
    baseURL: process.env.VUE_APP_API_URL
});

// const marker = L.icon({
//     iconUrl: require("../assets/marker.png"),
//     iconSize: [15, 15],
//     iconAnchor: [20, 40],
//     popupAnchor: [0, -60]
// });

class QueryService {
    getOnDateTime(day, bottom_left, top_right) {

		return client.get('/vessels-last-position',{params: {
            day: day,
            bottom_left_x: bottom_left.lat, 
            bottom_left_y: bottom_left.lng,
            top_right_x: top_right.lat, 
            top_right_y: top_right.lng
        }}).then(res => res.data);
	}
}

export default {
    name: "Dashboard",
    data() {
        return{
            mode: "lastSeenAt",
            center: L.latLng(49.4, -4),
            day: new Date('2016-03-01T00:00:00.000Z'),
            map: null,
            vessels: null,
            geoJSON: null
        }
    },
    components: {
        Calendar,
        Button
    },
    methods: {
        find: function(){
            this.map.removeLayer(this.geoJSON);
            this.getLastSeenAt()
        },
        vesselClicked: function(e){
            console.log(e)
        },
        onZoomed: function(){
           
            switch(this.mode) {
                case "lastSeenAt":
                    console.log(this.vessels);
                    this.map.removeLayer(this.geoJSON);
                    this.getLastSeenAt()
            }
        },
        onMarker: function(feature, layer) {
            layer.bindPopup('<h3><a href="/vessel/' + feature.properties.mmsi +'">'+feature.properties.mmsi+'</a></h3><p>at: '+feature.properties.lastSeen+'</p>');
            layer.on('click', function () {
                console.log(feature);
            });
        },
        setupLeafletMap: function () {
            const mapDiv = L.map("mapContainer").setView(this.center, 7);
            
            L.tileLayer(
            "https://api.mapbox.com/styles/v1/{id}/tiles/{z}/{x}/{y}?access_token={accessToken}",
            {
                attribution:
                'Map data (c) <a href="https://www.openstreetmap.org/">OpenStreetMap</a> contributors, <a href="https://creativecommons.org/licenses/by-sa/2.0/">CC-BY-SA</a>, Imagery (c) <a href="https://www.mapbox.com/">Mapbox</a>',
                maxZoom: 18,
                id: "mapbox/streets-v11",
                accessToken: "pk.eyJ1IjoiaXBoaWxpcHBhcyIsImEiOiJja2p5b3NkcWMwZHo4MnNvMjQ5Nndld2piIn0.v0jeUKn191c4SlrT6NdARg",
            }
            ).addTo(mapDiv);

            this.map = mapDiv;
        },

        getLastSeenAt: function() {
            let bounds = this.map.getBounds();
            if(this.geoJSON){
                if (this.map.hasLayer(this.geoJSON)){
                    this.map.removeLayer(this.geoJSON);
                }
            }

            this.queryService.getOnDateTime(this.day, bounds.getSouthEast(), bounds.getNorthWest()).then((vessels) => {
                this.vessels = vessels;
                this.geoJSON = L.geoJSON(this.vessels, {onEachFeature: this.onMarker});
                this.map.addLayer(this.geoJSON);
            });
    
            this.map.on('zoomend', this.onZoomed);
        }
    },
    queryService: null,

    created() {
        this.queryService = new QueryService();
    },
    
    mounted() {  
        this.setupLeafletMap();
        this.getLastSeenAt();
    },
}
</script>