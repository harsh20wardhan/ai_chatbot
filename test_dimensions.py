from qdrant_client import QdrantClient
client = QdrantClient(url="https://5eb98ed2-2314-4049-b417-a580896bc274.us-west-2-0.aws.cloud.qdrant.io", api_key="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhY2Nlc3MiOiJtIn0.IztgMmNayZiIyrgLKs467JRudqlennsRarB7tv7VCIo")
collections = client.get_collections()
for collection in collections.collections:
    info = client.get_collection(collection.name)
    print(f"Collection: {collection.name}, Vector size: {info.config.params.vectors.size}")