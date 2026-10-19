"""Write the current database to data/seed.json so it can be committed to git."""

from . import storage

if __name__ == "__main__":
    storage.export_json()
    print(f"Wrote {storage.SEED_FILE}")
