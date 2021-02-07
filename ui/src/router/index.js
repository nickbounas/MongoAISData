import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  {
    path: '/',
    name: 'Dashboard',
    component: () => import( '../views/Dashboard.vue')
    //component: import('../views/Dashboard.vue')
  },
  {
    path: '/vessel/:mmsi',
    name: 'Vessel',
    props: true,
    component: () => import('../views/Vessel.vue')
  },
  {
    path: '/vessel-trajectory',
    name: 'VesselTrajectory',
    component: () => import( '../views/VesselTrajectory.vue')
    //component: import('../views/VesselTrajectory.vue')
  },
  {
    path: '/custom-similar',
    name: 'CustomSimilar',
    component: () => import( '../views/CustomSimilar.vue')
    //component: import('../views/VesselTrajectory.vue')
  },
  {
    path: '/vessels-in-polygon',
    name: 'VesselsInPolygon',
    component: () => import( '../views/VesselsInPolygon.vue')
    //component: import('../views/VesselsInPolygon.vue')
  },
  {
    path: '/knn',
    name: 'Knn',
    component: () => import( '../views/Knn.vue')
    //component: import('../views/Knn.vue')
  },
  {
    path: '/distance-join',
    name: 'DistanceJoin',
    component: () => import( '../views/DistanceJoin.vue')
    //component: import('../views/DistanceJoin.vue')
  },
  {
    path: '/complex',
    name: 'Complex',
    component: () => import( '../views/Complex.vue')
    //component: import('../views/Complex.vue')
  },
]

const router = createRouter({
  history: createWebHistory(process.env.BASE_URL),
  routes
})

export default router
