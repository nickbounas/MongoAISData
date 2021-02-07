<template>
<div id="mapLayout" class="p-grid">

    <div class="p-col-2 filters">
        <div class="p-grid">
            <div class="p-col">
                <h3>Filters</h3>


                <label for="polygon" class="p-col-12">Polygon</label>
                <Textarea class="p-col-12" v-model="polygon" rows="5" cols="30" />

                <label for="when" class="p-col-12">When</label>
                <Calendar class="p-col-12" v-model="when" :showTime="true"  dateFormat="dd/mm/yy" />
                
                <label for="dt" class="p-col-12">Maximum Time Delta</label>
                <InputText class="p-col-12" id="dt" type="text" v-model="dt" />

                <label for="distance" class="p-col-12">Distance</label>
                <InputText class="p-col-12" id="distance" type="text" v-model="distance" />

                <div class="p-col-12">
                    <Button label="Find Neighboors" class="p-col-12 p-button p-component p-button-secondary" @click="run()"/>
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
import Button from 'primevue/button';
import InputText from 'primevue/inputtext';
import Textarea from 'primevue/textarea';
import Calendar from 'primevue/calendar';

const client = axios.create({
    baseURL: process.env.VUE_APP_API_URL
});

class QueryService {
    getNeighboors(polygon, when, distance, dt) {
       // polygon = polygon.split(/\r?\n/)
        console.log(polygon, distance, dt);
		return client.get('/distance-join',{ params: {
            polygon: polygon,
            when: when,
            distance: distance,
            dt: dt,
        }}).then(res => res.data);
    }

}

export default {
    name: "DistanceJoin",
    data() {
        return{
            center: L.latLng(49.4, -4),
            dt: 120,
            when: new Date("2016-01-19 23:38"),
            vessel: null,
            vessels: null,
            map: null,
            geoJSON: null,
            distance: 600,
            geoJSONTr: null,
            polygon: "-13.6450195,47.5765257\n-4.5922852,46.785016\n-5.8666992,49.6960618\n-15.402832,51.2894059\n-13.6450195,47.5765257"
        }
    },
    components: {
        Button,
        InputText,
        Textarea,
        Calendar
    },
    methods: {
       

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


        run: function() {
            if(this.geoJSON){
                if (this.map.hasLayer(this.geoJSON)){
                    this.map.removeLayer(this.geoJSON);
                }
            }
        
            this.queryService.getNeighboors(this.polygon, this.when, this.distance, this.dt, this.k).then((vessels) => {
                this.vessels = vessels;
                this.geoJSON = L.geoJSON(this.vessels,  {onEachFeature: this.onMarker});
                this.map.addLayer(this.geoJSON);

                this.map.fitBounds(this.geoJSON.getBounds());
            });
    
        },

        onMarker: function(feature, layer) {
            layer.bindPopup('<h3><a href="/vessel/' + feature.properties.mmsi +'">'+feature.properties.mmsi+'</a></h3><p>at: '+feature.properties.timestamp+'</p>');
            layer.on('click', function () {
                console.log(feature);
            });
        },

       
    },
    created() {
        this.queryService = new QueryService();
    },
    
    mounted() {  
        this.setupLeafletMap();
    },
}

</script>