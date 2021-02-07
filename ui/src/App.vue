<link href="https://unpkg.com/primeicons/primeicons.css" rel="stylesheet">
<template>
<div>
  <div class="layout-topbar">
    <router-link to="/"><img src="./assets/logo-sm.png" /></router-link>
  </div>
  <div class="layout-sidebar">
    
    <div class="layout-menu">
      <div class="menu-category">Queries</div>
      <div class="menu-items">
        <router-link to="/">Last Seen At</router-link>
        <router-link to="/vessel-trajectory">Vessel Trajectory</router-link>
        <router-link to="/custom-similar">Custom Algorithm Similar</router-link>
        <router-link to="/distance-join">Distance Join</router-link>
        <router-link to="/knn">KNN spatio-temporal</router-link>
        <router-link to="/complex">Complex</router-link>
      </div>
    </div>
  </div>
  <div class="layout-content">
    <router-view/>
  </div>
</div>
</template>

<script>

export default {
  
  props: {

	},
	
  methods: {
    visibleLeft() {
			return true;
		}
  },
  created () {
    document.title = "AIS Analytics";
  }
}
</script>
