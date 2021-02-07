xA=float(input("Give the lon for the point-centerA: "))
yA=float(input("Give the lat for the point-centerA: "))
xB=float(input("Give the lon for the point-centerB: "))
yB=float(input("Give the lat for the point-centerB: "))
xC=float(input("Give the lon for the point-centerC: "))
yC=float(input("Give the lat for the point-centerC: "))
r=float(input("Set up the Radius in miles for Points A,B,C (Remember the equatorial radius of the Earth is approximately 3,963.2 miles!!):  "))
start=(input("From when fmt(year-month-day hour:minutes:seconds): "))
final = (input("Till when fmt(year-month-day hour:minutes:seconds): "))
str_to_start = datetime.datetime.strptime(start, '%Y-%m-%d %H:%M:%S')
str_to_final = datetime.datetime.strptime(final, '%Y-%m-%d %H:%M:%S')
start1=datetime.datetime.now()
idsA={}
idsB={}
idsC={}
mydocA = nari.aggregate([{"$match":{"$and":[{"_id":{"$gt": str_to_start.timestamp(),"$lt": str_to_final.timestamp()}},{"ship.coordinates":{ "$geoWithin":{ "$centerSphere":[ [ xA,yA ] ,r/ 3963.2]}}}]}},{ "$unwind" : "$ship" }, { "$match" : {"ship.coordinates":{ "$geoWithin":{ "$centerSphere": [[ xA,yA] , r/3963.2]}}}},{"$project":{"ship.sourcemmsi":1,"_id":1,"ship.coordinates":1}}])
for doc in mydocA:
    if doc["ship"]["sourcemmsi"] not in idsA.keys():
            idsA[doc["ship"]["sourcemmsi"]]={"Enable"}
print(" A : ",(datetime.datetime.now()-start1)," Seconds")
mydocB = nari.aggregate([{"$match":{"$and":[{"_id":{"$gt": str_to_start.timestamp(),"$lt": str_to_final.timestamp()}},{"ship.coordinates":{ "$geoWithin":{ "$centerSphere":[ [ xB,yB ] ,r / 3963.2]}}}]}},{ "$unwind" : "$ship" }, { "$match" :{"$and":[{"ship.sourcemmsi": {"$in": list(idsA.keys())}},{"ship.coordinates":{ "$geoWithin":{ "$centerSphere": [[ xB,yB] , r/3963.2]}}}]}},{"$project":{"ship.sourcemmsi":1,"_id":1,"ship.coordinates":1}}])
for doc1 in mydocB:
        if doc1["ship"]["sourcemmsi"] not in idsB.keys():
             idsB[doc1["ship"]["sourcemmsi"]]={"Enable"}
print(" B : ",(datetime.datetime.now()-start1)," Seconds")
mydocC = nari.aggregate([{"$match":{"$and":[{"_id":{"$gt": str_to_start.timestamp(),"$lt": str_to_final.timestamp()}},{"ship.coordinates":{ "$geoWithin":{ "$centerSphere":[ [ xC,yC ] ,r / 3963.2]}}}]}},{ "$unwind" : "$ship" }, { "$match":{"$and":[{"ship.sourcemmsi":{'$in': list(idsB.keys())}}, {"ship.coordinates":{ "$geoWithin":{ "$centerSphere": [[ xC,yC] , r/3963.2]}}}]}},{"$project":{"ship.sourcemmsi":1,"_id":1,"ship.coordinates":1}}])
for doc2 in mydocC:
        if doc2["ship"]["sourcemmsi"] not in idsC.keys():
             idsC[doc2["ship"]["sourcemmsi"]]={"Enable"}
print(" C : ",(datetime.datetime.now()-start1)," Seconds")
troxies = nari.aggregate([{'$match': {"$and":[{"_id":{ "$gt": str_to_start.timestamp(), "$lt": str_to_final.timestamp()}},{"ship.sourcemmsi": {'$in': list(idsB.keys())}}]}},{ '$unwind' : "$ship" },{ '$match' : {"ship.sourcemmsi":{'$in': list(idsC.keys())}}},{"$project":{"ship.sourcemmsi":1,"ship.coordinates":1,"_id":1}}])
ploia={}
for doc3 in troxies:
        lon=[]
        lat=[]
        t=[]
        if doc3["ship"]["sourcemmsi"] in ploia.keys():
            ploia[doc3["ship"]["sourcemmsi"]]['lon'].append(float((doc3["ship"]["coordinates"][0])))
            ploia[doc3["ship"]["sourcemmsi"]]['lat'].append(float((doc3["ship"]["coordinates"][1])))
            ploia[doc3["ship"]["sourcemmsi"]]['t'].append(doc3["_id"])
        elif doc3["ship"]["sourcemmsi"] not in ploia.keys():
            lon.append(float((doc3["ship"]["coordinates"][0])))
            lat.append(float((doc3["ship"]["coordinates"][1])))
            t.append(doc3["_id"])
            ploia[doc3["ship"]["sourcemmsi"]]={
                    "lon":lon,
                    "lat":lat,
                    't':t
                }