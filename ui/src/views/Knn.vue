<template>
<div id="mapLayout" class="p-grid">

    <div class="p-col-2 filters">
        <div class="p-grid">
            <div class="p-col">
                <h3>Filters</h3>

                <label for="mmsi" class="p-col-12">MMSI</label>
                <InputText class="p-col-12" id="mmsi" type="text" v-model="mmsi" />

                <label for="when" class="p-col-12">When</label>
                <Calendar id="when" class="p-col-12" label="when" v-model="when" :showTime="true"  dateFormat="dd/mm/yy" />

                <div class="p-col-12">
                    <Button label="Find Vessel" class="p-col-12 p-button p-component p-button-secondary" @click="getVessel()"/>
                </div>

                <label for="max_distance" class="p-col-12">Max distance in m</label>
                <InputText class="p-col-12" id="max_istance" type="text" v-model="max_distance" />

                <label for="dt" class="p-col-12">Maximum Time Delta</label>
                <InputText class="p-col-12" id="dt" type="text" v-model="dt" />

                <label for="k" class="p-col-12">Neighbours?</label>
                <InputText class="p-col-12" id="k" type="text" v-model="k" />

                <div class="p-col-12">
                    <Button label="Find KNN" class="p-col-12 p-button p-component p-button-secondary" @click="findKnn()"/>
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
    getKnn(mmsi, when, max_distance, dt, k) {
        if (k === '') {
            k = null;
        }
		return client.get('/knn',{ params: {
            mmsi: mmsi,
            when: when,
            max_distance: max_distance,
            dt: dt,
            k: k
        }}).then(res => res.data);
    }

    getVessel(mmsi, when) {

		return client.get('/vessel',{ params: {
            mmsi: mmsi,
            when: when
        }}).then(res => res.data);
    }

}

export default {
    name: "Knn",
    data() {
        return{
            center: L.latLng(49.4, -4),
            when: new Date("2015-10-01 01:00"),
            dt: 1,
            vessel: null,
            vessels: null,
            mmsi: 245257000,
            map: null,
            geoJSON: null,
            max_distance: 2000,
            k: null,
            geoJSONTr: null
        }
    },
    components: {
        Calendar,
        Button,
        InputText
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


        findKnn: function() {
            if(this.geoJSON){
                if (this.map.hasLayer(this.geoJSON)){
                    this.map.removeLayer(this.geoJSON);
                }
            }
        
            this.queryService.getKnn(this.mmsi, this.when, this.max_distance, this.dt, this.k).then((vessels) => {
                this.vessels = vessels;
                this.geoJSON = L.geoJSON(this.vessels,  {onEachFeature: this.onMarker});
                this.map.addLayer(this.geoJSON);

                this.map.fitBounds(this.geoJSON.getBounds());
            });
    
        },

        onMarker: function(feature, layer) {
            layer.bindPopup('<h3><a href="/vessel/' + feature.properties.mmsi +'">'+feature.properties.mmsi+'</a></h3><p>at: '+feature.properties.minDist+' m</p>');
            layer.on('click', function () {
                console.log(feature);
            });
        },

        getVessel: function() {

            if(this.geoJSONTr){
                if (this.map.hasLayer(this.geoJSONTr)){
                    this.map.removeLayer(this.geoJSONTr);
                }
            }

            if(this.geoJSON){
                if (this.map.hasLayer(this.geoJSON)){
                    this.map.removeLayer(this.geoJSON);
                }
            }

            this.queryService.getVessel(this.mmsi, this.when).then((vessel) => {
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