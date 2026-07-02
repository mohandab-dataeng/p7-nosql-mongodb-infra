#!/bin/bash
sleep 15

# Init config servers
mongosh --host config_svr_1 --port 27019 --eval '
rs.initiate({_id:"configRS",configsvr:true,members:[{_id:0,host:"config_svr_1:27019"},{_id:1,host:"config_svr_2:27020"},{_id:2,host:"config_svr_3:27021"}]})
'

sleep 5

# Init shard 1
mongosh --host shard_1 --port 27031 --eval '
rs.initiate({_id:"shard1RS",members:[{_id:0,host:"shard_1:27031"}]})
'

# Init shard 2
mongosh --host shard_2 --port 27032 --eval '
rs.initiate({_id:"shard2RS",members:[{_id:0,host:"shard_2:27032"}]})
'

sleep 5

# Connecter les shards via mongos
mongosh --host mongos --port 27017 --eval '
sh.addShard("shard1RS/shard_1:27031")
sh.addShard("shard2RS/shard_2:27032")
sh.enableSharding("airbnb")
sh.shardCollection("airbnb.listings", {city: "hashed"})
'
