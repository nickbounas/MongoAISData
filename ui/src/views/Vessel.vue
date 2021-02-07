<template>
    <div>
        <h1>{{ mmsi }}</h1>
  
    </div>
</template>

<script>

export default {
    name: 'Vessel',
    props: ['mmsi'],
}
</script>