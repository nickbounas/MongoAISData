import { createApp } from 'vue'
import App from './App.vue'
import router from './router'
import PrimeVue from 'primevue/config';

import "primevue/resources/themes/vela-green/theme.css"      
import "primevue/resources/primevue.min.css"              
import "primeicons/primeicons.css"
import 'primeflex/primeflex.css';
import "leaflet/dist/leaflet.css";

import '@/assets/App.scss';
import L from "leaflet";

delete L.Icon.Default.prototype._getIconUrl  
 
L.Icon.Default.mergeOptions({  
  iconRetinaUrl: require('leaflet/dist/images/marker-icon-2x.png'),  
  iconUrl: require('leaflet/dist/images/marker-icon.png'),  
  shadowUrl: require('leaflet/dist/images/marker-shadow.png')  
})

const app = createApp(App)

app.use(PrimeVue)
app.use(router)

app.mount('#app')
