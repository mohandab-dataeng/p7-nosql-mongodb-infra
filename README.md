# NosCites - Pipeline NoSQL MongoDB

Pipeline ETL et infrastructure distribuee pour l'analyse de donnees d'un scraping Airbnb (Paris + Lyon) sur MongoDB.

## Architecture

```
docker compose up -d
  -> 3 config servers (ReplicaSet configRS)
  -> 2 shards (Paris + Lyon, chacun 3 noeuds)
  -> 1 routeur mongos (port 27017)
  -> 1 init-cluster.sh (configuration automatique)
  -> 1 ETL pipeline (chargement des donnees)
  -> 1 Metabase (dashboard BI, port 3000)
```

14 conteneurs au total.

## Stack

| Composant | Technologie |
|-----------|-------------|
| System | Kubuntu (Noble)|
| Base de donnees | MongoDB 8 |
| Langage | Python 3.13 |
| DataFrame | Polars |
| Driver | PyMongo |
| Conteneurisation | Docker / Docker Compose |
| BI | Metabase |
| Gestion deps | uv |

## Donnees

| Dataset | Lignes |
|---------|--------|
| Paris | ~95 885 |
| Lyon | ~10 000 |
| **Total** | **105 858** |

Source : [Inside Airbnb](http://insideairbnb.com/)

## Pipeline ETL (main.py)

1. **Extract** - Chargement automatique des CSV via `glob`, extraction de la ville depuis le nom du fichier
2. **Clean** - Suppression doublons, colonnes vides (>99% null), strip des strings
3. **Cast** - Typage : Int64, Float64, Boolean, Datetime, List (json_decode)
4. **Reshape** - 75 colonnes regroupees en 7 sous-documents (struct) + 8 champs root (à la racine)
5. **Load** - Insertion dans MongoDB via PyMongo (.insert_many()...105 858 documents)

## Lancement

```bash
# Cloner le projet
git clone <repo-url>
cd p7-nosql-mongodb-infra

# Placer les CSV dans data/
# listingsParis.csv + listingsLyon.csv

# Lancer tout le cluster
docker compose -f docker-compose.cluster.yml up -d
```

> **Note** : le cluster est ouvert, sans authentification (pas de keyFile ni d'utilisateur).
> En production, il faudrait ajouter un keyFile partage entre tous les noeuds + un utilisateur admin.

## Connexion

### Metabase (BI)

1. Ouvrir http://localhost:3000
2. Creer un compte administrateur
3. Ajouter une base de donnees :
   - Type : **MongoDB**
   - Host : **mongos**
   - Port : **27017**
   - Database : **airbnb**
4. Les donnees sont accessibles dans l'onglet "Nouvelle question"

### Compass (exploration)

- URI : `mongodb://localhost:27017`
- Base : `airbnb`
- Collection : `listings`

## Fichiers

```
main.py                      # Pipeline ETL
Dockerfile                   # Image Python pour l'ETL
docker-compose.cluster.yml   # Cluster sharde (14 conteneurs)
docker-compose.replicaset.yml # ReplicaSet simple (3 noeuds)
init-cluster.sh              # Script d'initialisation du cluster
.env                         # MONGO_URI
pyproject.toml               # Dependances Python
data/                        # Datasets CSV
notes/                       # Guides et documentation
```

## Sharding

- Shard key : `{city: "hashed"}`
- Distribution uniforme entre les shards
- Chaque shard est un ReplicaSet (3 noeuds)
