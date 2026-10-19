"""Write every tree's database to its JSON snapshot in data/trees/ so it can be committed."""

from . import trees

if __name__ == "__main__":
    for slug in trees.export_all():
        print(f"Wrote {trees.seed_path(slug)}")
