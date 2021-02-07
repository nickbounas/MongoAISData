from mongo import AsyncIOMotorClient, get_database
from fastapi import Depends
from settings import Settings, get_settings
from datetime import datetime, timedelta
from typing import List, Optional
from exceptions import ApplicationException
from utils import polygon_from_line_string
import math
from math import radians, cos, sin, asin, sqrt

class BaseRepository():
    def __init__(self, db: AsyncIOMotorClient=Depends(get_database), settings: Settings = Depends(get_settings)):
        self.conn = db
        self.db = db[settings.DB_NAME]
        self.settings = settings
        self.dynamic_collection = self.settings.DYNAMIC_COLLECTION

class DynamicDataRepository(BaseRepository):
    # Date Ranges: 01/10/15 - 31/03/16    
    
    async def get_vessel_at_box_on(self, box, from_date: datetime, to_date: datetime):
     
        pipeline = [
            { 
                '$match': { 
                    'location': { 
                        "$geoWithin": { "$box":  box} 
                    }
                } 
            },
            {
                '$match': {
                    'timestamp': {
                        '$gte': from_date, 
                        '$lt': to_date
                    }
                }
            },
            {
                '$sort': {
                    'timestamp': -1
                }
            }, 
            {
                '$group': {
                    '_id': "$mmsi",
                    'lastSeen': {
                        '$last': '$timestamp'
                    },
                    'position': {
                        '$last': '$location'
                    }
                }
            },
            {
                '$project': {
                    # Convert to GeoJson
                    '_id': 0,
                    'type': 'Feature',
                    'geometry': '$position',
                    'properties': {
                        'lastSeen': "$lastSeen",
                        'mmsi': '$_id'
                    }
                }
            }
        ]

        return await self.db[self.dynamic_collection].aggregate(pipeline).to_list(length=None)   

    async def get_vessels_in_range(self, coordinates: List[float], when: datetime, range_in_m: float):

        from_date = when - timedelta(hours=1)
        to_date = when

        pipeline = [
            {
                '$match': {
                    'timestamp': {
                        '$gte': from_date, 
                        '$lt': to_date
                    },
                    "location":{
                        '$geoWithin':  { 
                            '$centerSphere': [ coordinates, (range_in_m / 1000) / 6378.1 ]  
                        }
                    }
                }
            },
            {
                '$group': {
                    '_id': "$mmsi",
                    'lastTime': {
                        '$last': '$timestamp'
                    },
                    'position': {
                        '$last': '$location'
                    },
                    'mmsi': {
                        '$last': '$mmsi'
                    }
                }
            },
            {'$project': {'_id': 0}},

        ]


        return await self.db[self.dynamic_collection].aggregate(pipeline).to_list(length=None)  



    async def get_vessel_trajectory_in_timedelta(self, mmsi: str, from_date: datetime, to_date: datetime) -> List[dict]:
        pipeline = [
            {
                '$match': {
                    'mmsi': mmsi,
                    'timestamp': {
                        '$gte': from_date, 
                        '$lt': to_date
                    } 
                }
            },
            {'$sort': { 'timestamp': 1}},
            {
                '$group': {
                        '_id': "$mmsi",
                        'mmsi': {'$last': "mmsi"},
                        'trajectory': {
                                '$push': '$location.coordinates'
                            }
                        }
            },
            {
                '$project': {
                    # Convert to GeoJson
                    '_id': 0,
                    'type': 'Feature',
                    'geometry': {
                        'type': 'LineString',
                        'coordinates': "$trajectory"
                    },
                    'properties': {
                        'mmsi': '$_id'
                    }
                }
            }
        ]

        return await self.db[self.dynamic_collection].aggregate(pipeline).to_list(length=None)  
    
    async def get_vessels_in_polygon(self, polygon: List[float], from_date: datetime, to_date: datetime, grouped: bool = True, skip_aggregation=True):

        pipeline = [
            {
                '$match': {
                    'timestamp': {
                        '$gte': from_date, 
                        '$lt': to_date
                    },
                    'location': {       
                        '$geoWithin': {          
                            '$geometry': {             
                                'type': "Polygon" ,             
                                'coordinates': polygon         
                            }       
                        }    
                    }  
                }
            },
            {'$sort': {'timestamp': 1}},
            # {
            #     '$project': {
            #         # Convert to GeoJson
            #         '_id': 0,
            #         'type': 'Feature',
            #         'geometry': '$position',
            #         'properties': {
            #             'timestamp': "$timestamp",
            #             'mmsi': '$_id'
            #         }
            #     }
            # }
        ]

        if not skip_aggregation:
            if not grouped:
                pipeline.append({
                    '$group': {
                        '_id': "$mmsi",
                        'lastTime': {
                            '$last': '$timestamp'
                        },
                        'position': {
                            '$last': '$location'
                        },
                        'mmsi': {
                            '$last': '$mmsi'
                        }
                    }
                })

                pipeline += [{
                    '$project': {
                        # Convert to GeoJson
                        '_id': 0,
                        'type': 'Feature',
                        'geometry': {
                            'type': 'Point',
                            'coordinates': '$position.coordinates'
                        },
                        'properties': {
                            'mmsi': '$_id'
                        }
                    }
                }]
            
            else:
                pipeline += [{
                    '$group': {
                        '_id': "$mmsi",
                        'mmsi': {'$last': "$mmsi"},
                        'trajectory': {
                                '$push': '$location.coordinates'
                            }
                        }
                }]

                pipeline += [{
                    '$project': {
                        # Convert to GeoJson
                        '_id': 0,
                        'type': 'Feature',
                        'geometry': {
                            'type': 'lineString',
                            'coordinates': '$trajectory'
                        },
                        'properties': {
                            'mmsi': '$_id'
                        }
                    }
                }]
              

        


        pipeline.append({'$project': {'_id': 0}})


        r = await self.db[self.dynamic_collection].aggregate(pipeline).to_list(length=None)

        return r, len(r)

    
    async def get_vessel_trajectories_by_country(self, country: str, from_date: Optional[datetime] = None, to_date: Optional[datetime] = None) -> List[dict]:
        
        join_constrains = [
            { '$eq': [ "$country_code",  "$$c_country_code" ] },
        ]

        if from_date and to_date:
            join_constrains.append({'$gte': ["$timestamp", from_date]})
            join_constrains.append({'$lt': ["$timestamp", to_date]})


        dd_pipeline = [{ 
            '$match': { '$expr':
                { '$and': join_constrains
                }
            }
        }]
        
        pipeline = [
            {
                '$match': {
                    'country': country
                }
            }, {
                '$lookup': {
                
                    'from': 'dynamic_data', 
                    'let': { 'c_country_code': "$country_code"},
                    'pipeline': dd_pipeline,
                    'as': 'dn'
                }
            }, {
                '$unwind': {
                    'path': '$dn'
                }
            }, {
                '$project': {
                    '_id': 0, 
                    'dn': 1
                }
            }, {
                '$group': {
                    '_id': '$dn.mmsi', 
                    'mmsi': {
                        '$last': '$dn.mmsi'
                    }, 
                    'trajectory': {
                        '$push': '$dn.location'
                    }
                }
            }, {
                '$project': {
                    # Convert to GeoJson
                    '_id': 0,
                    'type': 'Feature',
                    'geometry': {
                        'type': 'LineString',
                        'coordinates': '$trajectory.coordinates'
                    },
                    'properties': {
                        'mmsi': '$_id'
                    }
                }
            }
        ]

     
        return await self.db.countries.aggregate(pipeline).to_list(length=None)
    
    async def get_similar_trajectories(self, mmsi: int, from_date: Optional[datetime] = None, to_date: Optional[datetime] = None, distance_in_km: float = 5) -> List[dict]:
        

        pipeline = [
            {
                '$match': {
                    'mmsi':  mmsi, 
                    'timestamp': {
                        '$gte': from_date, 
                        '$lt': to_date
                    }
                }
            }, {
                '$sort': {
                    'timestamp': 1
                }
            }, {
                '$group': {
                    '_id': '$mmsi', 
                    'locations': {
                        '$push': '$location'
                    }
                }
            }, {
                '$project': {
                    '_id': 0, 
                    'type': 'lineString', 
                    'locations': {
                        '$map': {
                            'input': '$locations', 
                            'as': 'location', 
                            'in': '$$location.coordinates'
                        }
                    }
                }
            }, 
        ]

        vessel_trajectories = await self.db.dynamic_data.aggregate(pipeline).to_list(length=None)
        

        if not len(vessel_trajectories):
            raise ApplicationException(404, "Trajectory Of this vessel was not found within this time limits")

        vessel_trajectory = vessel_trajectories[0]
        locations_count = len(vessel_trajectory['locations'])

        if not locations_count:
            raise ApplicationException(400, "Empty trajectory")

        polygon = polygon_from_line_string(vessel_trajectory['locations'], distance_in_km)
        last = vessel_trajectory['locations'][-1]
        first = vessel_trajectory['locations'][0]
  
        f = from_date - timedelta(days = 10)
        t = to_date + timedelta(days = 10)

        # return {
        #     'type': 'Feature',
        #     'geometry': {
        #         'type': 'Polygon',
        #         'coordinates': polygon
        #     },
        #     'properties': {}
        # }

        pipeline = [
            {
                '$match': {
                    'mmsi': {'$ne': mmsi},
                    'timestamp': {
                        '$gte': f, 
                        '$lt': t
                    },
                    'location': {       
                        '$geoWithin': {          
                            '$geometry': {             
                                'type': "Polygon" ,             
                                'coordinates': polygon         
                            }       
                        }    
                    }  
                }
            },
            {'$sort': {'timestamp': 1}},
            {
                '$group': 
                {
                    '_id': "$mmsi",
                    'trajectories': {
                        '$accumulator': {
                            'init': "function() { return [[]] }",
                            'accumulate': """function(state, location, timestamp) {
                                var calc_dist = function(v_coord, vessel_coord){
                                    var lat1 = v_coord[1]
                                    var lon1 =  v_coord[0]
                                    var lat2 = vessel_coord[1]
                                    var lon2= vessel_coord[0]

                                    var R = 6371e3; // metres
                                    var φ1 = lat1 * Math.PI/180; // φ, λ in radians
                                    var φ2 = lat2 * Math.PI/180;
                                    var Δφ = (lat2-lat1) * Math.PI/180;
                                    var Δλ = (lon2-lon1) * Math.PI/180;

                                    var a = Math.sin(Δφ/2) * Math.sin(Δφ/2) +
                                            Math.cos(φ1) * Math.cos(φ2) *
                                            Math.sin(Δλ/2) * Math.sin(Δλ/2);
                                    var c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a));

                                    var d = R * c; // in metres
                                    
                                    return d
                                }

                                var l = state.slice(-1)[0]
                                
                                if(l.length == 0){
                                l.push({coordinates: location.coordinates, timestamp: timestamp})
                                } else {
                                
                                    var llt = l.slice(-1)[0].timestamp
                                    var diff =(timestamp.getTime() - llt.getTime()) / 1000;
                                    diff /= 10; 
                                    
                                    if(diff > 60) {
                                        state.push([{coordinates: location.coordinates, timestamp: timestamp}])
                                    } else {
                                        llc = l.slice(-1)[0].coordinates

                                      

                                        var dist = calc_dist(location.coordinates, llc)

                                        if(dist > 10) {
                                            l.push({coordinates: location.coordinates, timestamp: timestamp})
                                        } 

                                       
                                    }
                                }
                                
                                return state
                            
                            }""",

                            'accumulateArgs': ["$location", "$timestamp"],

                            'merge': "function(state1, state2) { return state1.concat(state2) }"
                        }
                    }
                }
            },
            # {
            #     '$project': {
            #         '_id': 0,
            #         'mmsi': "$_id",
            #         'trajectories': {
            #             '$filter': {
            #                 "input": "$trajectories",
            #                 "as": "trajectory",
            #                 "cond": {'$gt': [{'$size': "$$trajectory"}, int(locations_count * 0.8)]} 
            #             }
            #         }
            #     }
            # },
            {
                '$project': {
                    '_id': 0,
                    'mmsi': "$_id",
                    'trajectories': '$trajectories'
                }
            },
        ]

        r = await self.db.dynamic_data.aggregate(pipeline, hint="location_m", allowDiskUse=True).to_list(length=None)

        result = []

        def calc_dist(lon1, lat1, lon2, lat2, cutoff=500):
            """
            Calculate the great circle distance between two points 
            on the earth (specified in decimal degrees)
            """
            # convert decimal degrees to radians 
            lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])

            # haversine formula 
            dlon = lon2 - lon1 
            dlat = lat2 - lat1 
            a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
            c = 2 * asin(sqrt(a)) 
            r = 6371100 # Radius of earth in m
            d = c * r

            if d > cutoff:
                return None
            
            return True


        def transform(trajectory):
            traject = [ pair["coordinates"] for pair in trajectory ]
            
            en = False
            st = False

            for pair in traject:
                if st and en:
                    break
                
                if not st:
                    if calc_dist(pair[0], pair[1], first[0], first[1], 500):
                        st = True
                
                if not en:
                    if calc_dist(pair[0], pair[1], last[0], last[1], 500):
                        en = True


            # en = calc_dist(traject[-1][0], traject[-1][1], last[0], last[1], 500)
            # st = calc_dist(traject[0][0], traject[0][1], first[0], first[1], 500)

            return st and en and traject

        for ship in r:
            
            coordinates = [ transform(trajectory) for trajectory in ship["trajectories"]]
            coordinates  = [ t for t in  coordinates if t]

            o = {
                'type': 'Feature',
                'geometry': {
                    'type': "MultiLineString",
                    'coordinates': coordinates
                },
                'properties': {
                    'mmsi': ship["mmsi"]
                }
            }

            if len(coordinates):
                result.append(o)
                
        return result



    async def get_similar_trajectories2(self, mmsi: int, from_date: Optional[datetime] = None, to_date: Optional[datetime] = None, distance_in_km: float = 5) -> List[dict]:
        

        pipeline = [
            {
                '$match': {
                    'mmsi':  mmsi, 
                    'timestamp': {
                        '$gte': from_date, 
                        '$lt': to_date
                    }
                }
            }, {
                '$sort': {
                    'timestamp': 1
                }
            }, {
                '$group': {
                    '_id': '$mmsi', 
                    'locations': {
                        '$push': '$location'
                    }
                }
            }, 
            {
                '$project': {
                    '_id': 0, 
                    'type': 'lineString', 
                    'locations': {
                        '$map': {
                            'input': '$locations', 
                            'as': 'location', 
                            'in': '$$location.coordinates'
                        }
                    }
                }
            }, 
        ]

        vessel_trajectories = await self.db[self.dynamic_collection].aggregate(pipeline).to_list(length=None)
        

        if not len(vessel_trajectories):
            raise ApplicationException(404, "Trajectory Of this vessel was not found within this time limits")

        vessel_trajectory = vessel_trajectories[0]
        locations_count = len(vessel_trajectory['locations'])
     

        if not locations_count:
            raise ApplicationException(400, "Empty trajectory")

        polygon = polygon_from_line_string(vessel_trajectory['locations'], distance_in_km)
        # last = vessel_trajectory['locations'][-1]
        # first = vessel_trajectory['locations'][0]
        # return {
        #     'type': 'Feature',
        #     'geometry': {
        #         'type': 'Polygon',
        #         'coordinates': polygon
        #     }
        # }
        f = from_date - timedelta(days = 10)
        t = to_date + timedelta(days = 10)
        pipeline = [
            {
                '$match': {
                    'mmsi': {'$ne': mmsi},
                    'timestamp': {
                        '$gte': f, 
                        '$lt': t
                    },
                    'location': {       
                        '$geoWithin': {          
                            '$geometry': {             
                                'type': "Polygon" ,             
                                'coordinates': polygon         
                            }       
                        }    
                    }  
                }
            },
            {'$sort': {'timestamp': 1}},
            {
                '$group': {
                    '_id': '$mmsi', 
                    'locations': {
                        '$push': '$location'
                    },
                    'start': {'$first': '$timestamp'},
                    'end': {'$last': '$timestamp'}
                }
            }, 
            {
                '$project': {
                    '_id': 0, 
                    'type': 'lineString', 
                    'mmsi': '$_id',
                    'locations': {
                        '$map': {
                            'input': '$locations', 
                            'as': 'location', 
                            'in': '$$location.coordinates'
                        }
                    },
                    'start': 1,
                    'end': 1
                }
            },
            {
                '$match': 
                {
                    '$expr': {
                        '$function': {
                            'body': """function(vessel, v){

                                ( function() {
  
    function DynamicTimeWarping ( ts1, ts2, distanceFunction ) {
        var ser1 = ts1;
        var ser2 = ts2;
        var distFunc = distanceFunction;
        var distance;
        var matrix;
        var path;

        var getDistance = function() {
            if ( distance !== undefined ) {
                return distance;
            }
            matrix = [];
            for ( var i = 0; i < ser1.length; i++ ) {
                matrix[ i ] = [];
                for ( var j = 0; j < ser2.length; j++ ) {
                    var cost = Infinity;
                    if ( i > 0 ) {
                        cost = Math.min( cost, matrix[ i - 1 ][ j ] );
                        if ( j > 0 ) {
                            cost = Math.min( cost, matrix[ i - 1 ][ j - 1 ] );
                            cost = Math.min( cost, matrix[ i ][ j - 1 ] );
                        }
                    } else {
                        if ( j > 0 ) {
                            cost = Math.min( cost, matrix[ i ][ j - 1 ] );
                        } else {
                            cost = 0;
                        }
                    }
                    matrix[ i ][ j ] = cost + distFunc( ser1[ i ], ser2[ j ] );
                }
            }

            return matrix[ ser1.length - 1 ][ ser2.length - 1 ];
        };

        this.getDistance = getDistance;

        var getPath = function() {
            if ( path !== undefined ) {
                return path;
            }
            if ( matrix === undefined ) {
                getDistance();
            }
            var i = ser1.length - 1;
            var j = ser2.length - 1;
            path = [ [ i, j ] ];
            while ( i > 0 || j > 0 ) {
                if ( i > 0 ) {
                    if ( j > 0 ) {
                        if ( matrix[ i - 1 ][ j ] < matrix[ i - 1 ][ j - 1 ] ) {
                            if ( matrix[ i - 1 ][ j ] < matrix[ i ][ j - 1 ] ) {
                                path.push( [ i - 1, j ] );
                                i--;
                            } else {
                                path.push( [ i, j - 1 ] );
                                j--;
                            }
                        } else {
                            if ( matrix[ i - 1 ][ j - 1 ] < matrix[ i ][ j - 1 ] ) {
                                path.push( [ i - 1, j - 1 ] );
                                i--;
                                j--;
                            } else {
                                path.push( [ i, j - 1 ] );
                                j--;
                            }
                        }
                    } else {
                        path.push( [ i - 1, j ] );
                        i--;
                    }
                } else {
                    path.push( [ i, j - 1 ] );
                    j--;
                }
            }
            path = path.reverse();

            return path;
        };

        this.getPath = getPath;
    }

    var root = typeof self === "object" && self.self === self && self ||
        typeof global === "object" && global.global === global && global ||
        this;

    if ( typeof exports !== "undefined" && !exports.nodeType ) {
        if ( typeof module !== "undefined" && !module.nodeType && module.exports ) {
            exports = module.exports = DynamicTimeWarping;
        }
        exports.DynamicTimeWarping = DynamicTimeWarping;
    } else {
        root.DynamicTimeWarping = DynamicTimeWarping;
    }

    if ( typeof define === "function" && define.amd ) {
        define( "dynamic-time-warping", [], function() {
            return DynamicTimeWarping;
        } );
    }
}() );

                               

                                var dtw = new DynamicTimeWarping(v, vessel, function(v_coord, vessel_coord){
                                    var lat1 = v_coord[1]
                                    var lon1 =  v_coord[0]
                                    var lat2 = vessel_coord[1]
                                    var lon2= vessel_coord[0]

                                    var R = 6371e3; // metres
                                    var φ1 = lat1 * Math.PI/180; // φ, λ in radians
                                    var φ2 = lat2 * Math.PI/180;
                                    var Δφ = (lat2-lat1) * Math.PI/180;
                                    var Δλ = (lon2-lon1) * Math.PI/180;

                                    var a = Math.sin(Δφ/2) * Math.sin(Δφ/2) +
                                            Math.cos(φ1) * Math.cos(φ2) *
                                            Math.sin(Δλ/2) * Math.sin(Δλ/2);
                                    var c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a));

                                    var d = R * c; // in metres
                                    
                                    return d
                                });

                                var path = dtw.getPath()
                                //return path.length > (0.7 * vessel.length)
                                return ((dtw.getDistance() / path.length) < 2000) && (path.length > (0.7 * vessel.length)) && (path.length > (1.2 * vessel.length));
                                
                            }""",
                            'args': [vessel_trajectory["locations"], '$locations'],
                            'lang': 'js'
                        }
                    }
                }
            },
            {
                '$project': {
                    # Convert to GeoJson
                    '_id': 0,
                    'type': 'Feature',
                    'geometry': {
                        'type': 'LineString',
                        'coordinates': '$locations'
                    },
                    'properties': {
                        'mmsi': '$mmsi',
                        'start': '$start',
                        'end': '$end'
                    },
                }
            }

        ]

        return  await self.db[self.dynamic_collection].aggregate(pipeline, hint="location_m", allowDiskUse=True).to_list(length=None)
       

    async def distance_join(self, polygon: List, when: datetime, dt: int=10, distance: float=600):
        f = when - timedelta(days = 1)
        t = when + timedelta(days = 1)
        await self.db.djoin.drop()
        first_pipeline = [
            {
                '$match': {
                    'timestamp': {
                        '$gte': f, 
                        '$lt': t
                    },
                    'location': {
                        '$geoWithin': {
                            '$geometry': {
                                'type': "Polygon",
                                'coordinates': polygon
                            }
                        }
                    }
                }
            },
            {
                '$sort': {
                    'timestamp': 1
                }
            },
            {'$limit': 1000},

            {'$out': 'djoin'}
        ]

        locations = await self.db[self.dynamic_collection].aggregate(first_pipeline).to_list(length=None)
    
        calculation_pipe_line = [
            {
                '$match': {
                    'timestamp': {
                        '$gte': f, 
                        '$lt': t
                    },
                    'location': {
                        '$geoWithin': {
                            '$geometry': {
                                'type': "Polygon",
                                'coordinates': polygon
                            }
                        }
                    }
                }
            },
            {
                '$sort': {
                    'timestamp': 1
                }
            },
            {'$limit': 1000},
            {
                '$lookup':
                {
                    'from': "djoin",
                    'let': { 'mmsi': '$mmsi', 'location': '$location', 'timestamp': '$timestamp' },
                    'pipeline': [
                        { '$match':
                            { '$expr':
                                {
                                    '$function':
                                    {
                                        'body': """function(mmsi, coordinates, timestamp, vmmsi, vcoordinates, vtimestamp, distance, dt) {
                                            var calc_dist = function(v_coord, vessel_coord){
                                                var lat1 = v_coord[1]
                                                var lon1 =  v_coord[0]
                                                var lat2 = vessel_coord[1]
                                                var lon2= vessel_coord[0]

                                                var R = 6371e3; // metres
                                                var φ1 = lat1 * Math.PI/180; // φ, λ in radians
                                                var φ2 = lat2 * Math.PI/180;
                                                var Δφ = (lat2-lat1) * Math.PI/180;
                                                var Δλ = (lon2-lon1) * Math.PI/180;

                                                var a = Math.sin(Δφ/2) * Math.sin(Δφ/2) +
                                                        Math.cos(φ1) * Math.cos(φ2) *
                                                        Math.sin(Δλ/2) * Math.sin(Δλ/2);
                                                var c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a));

                                                var d = R * c; // in metres
                                                
                                                return d
                                            }

                                            var calc_time_diff = function(v_time, vessel_time) {
                                              
                                                return  Math.abs((v_time.getTime() - vessel_time.getTime()) / 1000) < parseInt(dt);
                                            }
                                        
                                            return (vmmsi !== mmsi) && (calc_dist(vcoordinates, coordinates) < distance) && (calc_time_diff(vtimestamp, timestamp))
                                        }""",
                                        'args': [ '$mmsi', '$location.coordinates', '$timestamp', '$$mmsi', '$$location.coordinates', '$$timestamp', distance, dt],
                                        'lang': "js"
                                    }
                                }
                            }
                        },
                        {
                            '$project': {
                                '_id': 0,
                                'type': 'Feature',
                                'geometry': {
                                    'type': 'Point',
                                    'coordinates': '$location.coordinates'
                                },
                                'properties': {
                                    'mmsi': "$mmsi",
                                    'timestamp': '$timestamp',
                                    'neighboor': '$neighboor'
                                }
                            }
                        }
                    ],
                    'as': "neighboor"
                    
                }
            },
            {
                '$match': {
                    'neighboor.1': {'$exists': True}
                }
            },
            {
                '$unwind': '$neighboor' 
            },
            {
                '$project': {
                    '_id': 0,
                    'type': 'Feature',
                    'geometry': {
                        'type': 'Point',
                        'coordinates': '$neighboor.geometry.coordinates'
                    },
                    'properties': {
                        'mmsi': "$neighboor.properties.mmsi",
                        'timestamp': '$neighboor.properties.timestamp',
                
                    }
                }
            }
        ]

        
        q = await self.db[self.dynamic_collection].aggregate(calculation_pipe_line, allowDiskUse=True).to_list(length=None)
        await self.db.djoin.drop()

        return q
     

    
    async def get_vessel_at(self, mmsi: str, when: datetime):
        location_pipeline = [
            {
                '$match': {
                    'mmsi':  mmsi, 
                    'timestamp': {
                        '$gte': when - timedelta(seconds=30),
                        '$lt': when + timedelta(seconds=30)
                    }
                }
            },
            {'$limit': 1},
            {
                '$project': {
                    '_id': 0,
                    'type': 'Feature',
                    'geometry': {
                        'type': 'Point',
                        'coordinates': '$location.coordinates'
                    },
                    'properties': {
                        'mmsi': "$_mmsi",
                        'timestamp': '$timestamp',
                    }
                }
            }
        ]

        locations = await self.db[self.dynamic_collection].aggregate(location_pipeline).to_list(length=None)

        if not len(locations):
            raise ApplicationException(404, "No location for this mmsi in this location")

        return locations[0]
   

    async def knn(self, mmsi: str, when: datetime, max_distance: float = 1000, dt: int = 1, k: int=None):
        location_pipeline = [
            {
                '$match': {
                    'mmsi':  mmsi, 
                    'timestamp': {
                        '$gte': when - timedelta(seconds=30),
                        '$lt': when + timedelta(seconds=30)
                    }
                }
            },
            {'$limit': 1},
            {
                '$project': {
                    "_id": 0,
                    "location": 1
                }
            }
        ]

        locations = await self.db[self.dynamic_collection].aggregate(location_pipeline).to_list(length=None)

        if not len(locations):
            raise ApplicationException(404, "No location for this mmsi in this location")

        location = locations[0]['location']
   
        pipeline = [
            {
                '$geoNear': {
                    'near': location,
                    'distanceField': 'dist.calculated',
                    'maxDistance': max_distance,
                    'query': {
                        'mmsi': {"$ne": mmsi},
                        # 'timestamp': when
                        'timestamp': {
                            '$gte': when - timedelta(minutes=dt),
                            '$lt': when + timedelta(minutes=dt)
                        }
                    },
                    'includeLocs': 'dist.location',
                    'key': 'location',
                    'spherical': True
                }
            },
            {
                '$sort': {
                    'mmsi': 1,
                    'dist.calculated': 1
                }
            },
            {
                '$group': {
                    '_id': '$mmsi',
                    'locations': {'$first': '$dist'},
                    'timestamp': {'$first': '$timestamp'}
                }
            },            
            {
                '$project': {
                    '_id': 0,
                    'type': 'Feature',
                    'geometry': {
                        'type': 'Point',
                        'coordinates': '$locations.location.coordinates'
                    },
                    'properties': {
                        'mmsi': "$_id",
                        'timestamp': '$timestamp',
                        'minDist': '$locations.calculated'
                    }
                }
            }]

        if k:
            pipeline += [
                {
                '$sort': {
                    'properties.minDist': 1
                    }
                },
                {'$limit': k},
            ]

        return  await self.db[self.dynamic_collection].aggregate(pipeline).to_list(length=None)

    async def complex(self, points: List[List], start: datetime, dt: int, radius: float):
        end = start + timedelta(minutes=dt)
        pipeline = [{
            '$match': {
                '$and': [
                    {
                        'timestamp': {
                            '$gte': start,
                            '$lt': end
                        }
                    },
                    {'$or': []}
                ]
            }
        }]
        or_d = pipeline[0]['$match']['$and'][1]['$or']

        for point in points:
            or_d.append(
             
                {
                    'location': {
                        '$geoWithin': { '$centerSphere': [ point, radius/6378100 ] }
                    }
                }
            
            )

        pipeline += [
            {'$sort': {'timestamp': 1}},
            {
                '$group': {
                    '_id': '$mmsi',
                    'points': {'$push': '$location.coordinates'},
                    'start': {'$first': '$timestamp'},
                    'end': {'$last': '$timestamp'}
                }
            },
            {
                '$match': 
                {
                    '$expr': {
                        '$function': {
                            'body': """
                                function(points, start, end, qpoints, qstart, qend, radius){
                                    var calc_dist = function(v_coord, vessel_coord){
                                            var lat1 = v_coord[1]
                                            var lon1 =  v_coord[0]
                                            var lat2 = vessel_coord[1]
                                            var lon2= vessel_coord[0]

                                            var R = 6371e3; // metres
                                            var φ1 = lat1 * Math.PI/180; // φ, λ in radians
                                            var φ2 = lat2 * Math.PI/180;
                                            var Δφ = (lat2-lat1) * Math.PI/180;
                                            var Δλ = (lon2-lon1) * Math.PI/180;

                                            var a = Math.sin(Δφ/2) * Math.sin(Δφ/2) +
                                                    Math.cos(φ1) * Math.cos(φ2) *
                                                    Math.sin(Δλ/2) * Math.sin(Δλ/2);
                                            var c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a));

                                            var d = R * c; // in metres
                                            
                                            return d
                                        }

                                        var calc_time_diff = function(v_time, vessel_time) {
                                            
                                            return  Math.abs((v_time.getTime() - vessel_time.getTime()) / 1000) < parseInt(dt);
                                        }
                                        
                                        var matches = 0;
                                        var checks = qpoints.length

                                        for (var i = 0; i < checks; i++) {
                                            var ref = qpoints[i]

                                            for (var j = 0; j < points.length; j++) {
                                                var p = points.shift()
                                                
                                                if (calc_dist(p, ref) <= radius) {
                                                    matches = matches + 1
                                                    break;
                                                }

                                    
                                            }
                                        }
                                  
                                        return matches === checks
                                }
                            """,
                            'args': ['$points', '$start', '$end', points, start, end, radius],
                            'lang': 'js'
                        }
                    }
                }
            },
            {
                '$project': {
                    '_id': 0,
                    'mmsi': '$_id'
                }
            }
        ]

        matched = await self.db[self.dynamic_collection].aggregate(pipeline, allowDiskUse=True).to_list(length=None)
        matched_mmsi = [m["mmsi"] for m in matched]
      

        pipeline = [
            {
                '$match': {
                    'mmsi': { '$in': matched_mmsi},
                    'timestamp': {
                        '$gte': start,
                        '$lt': end
                    }
                },
            },
            {'$sort': {'timestamp': 1}},
            {
                '$group': {
                    '_id': '$mmsi', 
                    'locations': {
                        '$push': '$location.coordinates'
                    },
                    'start': {'$first': '$timestamp'},
                    'end': {'$last': '$timestamp'}
                }
            },
            {
                '$project': {
                    '_id': 0,
                    'type': 'Feature',
                    'geometry': {
                        'type': 'LineString',
                        'coordinates': '$locations'
                    },
                    'properties': {
                        'mmsi': "$_id",
                        'start': '$start',
                        'end': '$end'
                    }
                }
            }
        ]

        return  await self.db[self.dynamic_collection].aggregate(pipeline, allowDiskUse=True).to_list(length=None)
