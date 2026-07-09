#!/bin/bash

until mongosh --host cfg_svr_1 --port 27018 --eval "db.runCommand('ping')" > /dev/null 2>&1; do
  sleep 2
done

# Configuration des serveurs - metadonnées de la table de routage (commande mongosh)
mongosh --host cfg_svr_1 --port 27018 --eval '
rs.initiate({_id:"configRS",configsvr:true,members:[
{_id:0,host:"cfg_svr_1:27018"},
{_id:1,host:"cfg_svr_2:27019"},
{_id:2,host:"cfg_svr_3:27020"}
]})
'

until mongosh --host shardParis_node1 --port 27031 --eval "db.runCommand('ping')" > /dev/null 2>&1; do
  sleep 2
done

# Init shard 1
mongosh --host shardParis_node1 --port 27031 --eval '
rs.initiate({_id:"shardParisRS",members:[
  {_id:0,host:"shardParis_node1:27031"},
  {_id:1,host:"shardParis_node2:27032"},
  {_id:2,host:"shardParis_node3:27033"}
]})
'
until mongosh --host shardLyon_node1 --port 27041 --eval "db.runCommand('ping')" > /dev/null 2>&1; do
  sleep 2
done

# Init shard 2
mongosh --host shardLyon_node1 --port 27041 --eval '
rs.initiate({_id:"shardLyonRS",members:[
  {_id:0,host:"shardLyon_node1:27041"},
  {_id:1,host:"shardLyon_node2:27042"},
  {_id:2,host:"shardLyon_node3:27043"}
]})
'

until mongosh --host mongos --port 27017 --eval "db.runCommand('ping')" > /dev/null 2>&1; do
  sleep 2
done

# Connexion des shards (mongos) > hash sur city
mongosh --host mongos --port 27017 --eval '
sh.addShard("shardParisRS/shardParis_node1:27031,shardParis_node2:27032,shardParis_node3:27033")
sh.addShard("shardLyonRS/shardLyon_node1:27041,shardLyon_node2:27042,shardLyon_node3:27043")
sh.enableSharding("airbnb")
sh.shardCollection("airbnb.listings", {city: 1}) 
'