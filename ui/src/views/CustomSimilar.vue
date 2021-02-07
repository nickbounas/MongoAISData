<template>
<div id="mapLayout" class="p-grid">

    <div class="p-col-2 filters">
        <div class="p-grid">
            <div class="p-col">
                <h3>Filters</h3>

                <label for="mmsi" class="p-col-12">MMSI</label>
                <InputText class="p-col-12" id="mmsi" type="text" v-model="mmsi" />

                <label for="from_date" class="p-col-12">From Date</label>
                <Calendar id="from_date" class="p-col-12" label="From Date" v-model="from_date" :showTime="true"  dateFormat="dd/mm/yy" />

                <label for="to_date" class="p-col-12">To Date</label>
                <Calendar id="to_date" class="p-col-12" label="To Date" v-model="to_date" :showTime="true"  dateFormat="dd/mm/yy" />

                <div class="p-col-12">
                    <Button label="Find" class="p-col-12 p-button p-component p-button-secondary" @click="find()"/>
                </div>

                <label for="mmsi" class="p-col-12">Distance In Km</label>
                <InputText class="p-col-12" id="distance" type="text" v-model="distance" />

                <div class="p-col-12">
                    <Button label="Find Similar Trajectories" class="p-col-12 p-button p-component p-button-secondary" @click="findSimilarTrajectories()"/>
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
import InputText from 'primevue/inputtext';

const client = axios.create({
    baseURL: process.env.VUE_APP_API_URL
});

class QueryService {
    getVesselTrajectory(mmsi, from_date, to_date) {

		return client.get('/vessel-trajectory',{params: {
            mmsi: mmsi,
            from_date: from_date,
            to_date: to_date
        }}).then(res => res.data);
    }
    
    getSimilarTrajectories(mmsi, from_date, to_date, distance) {

		return client.get('/custom-similar',{params: {
            mmsi: mmsi,
            from_date: from_date,
            to_date: to_date,
            distance: distance
        }}).then(res => res.data);
	}
}

export default {
    name: "VesselTrajectory",
    data() {
        return{
            center: L.latLng(49.4, -4),
            from_date: new Date("2015-12-04 16:55"),
            to_date: new Date("2015-12-04 17:30"),
            vessel: null,
            mmsi: 227574020,
            map: null,
            geoJSON: null,
            distance: null,
            geoJSONTr: null
        }
    },
    components: {
        Calendar,
        Button,
        InputText
    },
    methods: {
        onMarker: function(feature, layer) {
            layer.bindPopup('<h3><a href="/vessel/' + feature.properties.mmsi +'">'+feature.properties.mmsi+'</a></h3><p>start: '+feature.properties.start+'</p><p>start: '+feature.properties.end+'</p>');
            layer.on('click', function () {
                console.log(feature);
            });
        },

        find: function(){

            if(this.geoJSON){
                if (this.map.hasLayer(this.geoJSON)){
                    this.map.removeLayer(this.geoJSON);
                }
            }

            if(this.geoJSONTr){
                if (this.map.hasLayer(this.geoJSONTr)){
                    this.map.removeLayer(this.geoJSONTr);
                }
            }
            
            this.getVesselTrajectory()
        },

        findSimilarTrajectories: function(){

            if(this.geoJSONTr){
                if (this.map.hasLayer(this.geoJSONTr)){
                    this.map.removeLayer(this.geoJSONTr);
                }
            }
            
            this.getSimilarTrajectories()
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

        getVesselTrajectory: function() {
        
            this.queryService.getVesselTrajectory(this.mmsi, this.from_date, this.to_date).then((vessel) => {
                this.vessel = vessel;
                this.geoJSON = L.geoJSON(this.vessel);
                this.map.addLayer(this.geoJSON);

                this.map.fitBounds(this.geoJSON.getBounds());
            });
    
        },

        getSimilarTrajectories: function() {
        
            this.queryService.getSimilarTrajectories(this.mmsi, this.from_date, this.to_date, this.distance).then((vessel) => {
                this.vessel = vessel;
                this.geoJSONTr = L.geoJSON(this.vessel,  {onEachFeature: this.onMarker});
                this.map.addLayer(this.geoJSONTr);

                this.map.fitBounds(this.geoJSONTr.getBounds());
            });
    
        }
    },
    created() {
        this.queryService = new QueryService();
    },
    
    mounted() {  
        this.setupLeafletMap();
    },
}

</script>