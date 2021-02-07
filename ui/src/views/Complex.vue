<template>
<div id="mapLayout" class="p-grid">

    <div class="p-col-2 filters">
        <div class="p-grid">
            <div class="p-col">
                <h3>Filters</h3>


                <label for="points" class="p-col-12">Points</label>
                <Textarea class="p-col-12" v-model="points" rows="5" cols="30" />

                <div class="p-col-12">
                    <Button label="Show Points" class="p-col-12 p-button p-component p-button-secondary" @click="showPoints()"/>
                </div>

                <label for="start" class="p-col-12">Start</label>
                <Calendar class="p-col-12" v-model="start" :showTime="true"  dateFormat="dd/mm/yy" />
                
                <label for="dt" class="p-col-12">Maximum Time Delta in mins</label>
                <InputText class="p-col-12" id="dt" type="text" v-model="dt" />

                <label for="radius" class="p-col-12">Radius in m</label>
                <InputText class="p-col-12" id="radius" type="text" v-model="radius" />

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
    complex(points, start, dt, radius) {
      
		return client.get('/complex',{ params: {
            points: points,
            start: start,
            dt: dt,
            radius: radius,
        }}).then(res => res.data);
    }

}

export default {
    name: "DistanceJoin",
    data() {
        return{
            center: L.latLng(49.4, -4),
            dt: 30,
            start: new Date("2015-12-04 16:55"),
            vessel: null,
            vessels: null,
            map: null,
            geoJSON: null,
            radius: 1000,
            geoJSONTr: null,
            points: "-4.493672,48.37688\n-4.48944,48.30498\n-4.510285,48.29559"
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

        getPoints: function(){
            return this.points.trim().split('\n').map((p) => {
                let r = p.split(',');
                return r.map( c => parseFloat(c.trim()));
            });
        },

        showPoints: function(){
            if(this.geoJSONTr){
                if (this.map.hasLayer(this.geoJSONTr)){
                    this.map.removeLayer(this.geoJSONTr);
                }
            }
            
            let points = this.getPoints();

            let geoJsonPoints = points.map(p => {
                let j =  {
                    type: "Feature",
                    geometry: { 
                        type: "Point",
                        coordinates: [p[0], p[1]]
                    }
                };

                return j; 
            });
            console.log(geoJsonPoints);
            this.geoJSONTr = L.geoJSON(geoJsonPoints,  {onEachFeature: this.onPointMarker});
            this.map.addLayer(this.geoJSONTr);
            this.map.fitBounds(this.geoJSONTr.getBounds());
           
        },

        run: function() {
            if(this.geoJSON){
                if (this.map.hasLayer(this.geoJSON)){
                    this.map.removeLayer(this.geoJSON);
                }
            }

            if(this.geoJSON){
                if (this.map.hasLayer(this.geoJSONTr)){
                    this.map.removeLayer(this.geoJSONTr);
                }
            }

            this.showPoints();
        
            this.queryService.complex(this.points, this.start, this.dt, this.radius).then((vessels) => {
                this.vessels = vessels;
                this.geoJSON = L.geoJSON(this.vessels,  {onEachFeature: this.onMarker});
                this.map.addLayer(this.geoJSON);
                this.map.fitBounds(this.geoJSON.getBounds());
            });
    
        },

        onMarker: function(feature, layer) {
            layer.bindPopup('<h3><a href="/vessel/' + feature.properties.mmsi +'">'+feature.properties.mmsi+'</a></h3>');
        },

         onPointMarker: function(feature, layer) {
            layer.bindPopup('<h3>' + feature.geometry.coordinates[0] + ' - ' + feature.geometry.coordinates[1] +'</h3>');
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