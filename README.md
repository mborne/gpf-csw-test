# gpf-csw-test

<!-- Generated with Claude Code (https://claude.com/claude-code) -->

Tests fonctionnels reproduisant un bug de recherche plein texte (`AnyText` +
wildcard `%`) sur le service CSW de la Géoplateforme
(`https://data.geopf.fr/csw`).

- **Bug documenté** : [docs/bug-filter.md](docs/bug-filter.md)
- **Issue de suivi** : [mborne/gpf-catalogue#7](https://github.com/mborne/gpf-catalogue/issues/7)

## Exécuter les tests

Avec [uv](https://docs.astral.sh/uv/) :

```bash
uv sync
uv run pytest -v
```

Sans uv (bibliothèque standard Python 3 uniquement, aucune dépendance) :

```bash
python3 -m unittest discover -s tests -v
```

Les tests appellent le service CSW en direct (pas de mock, le bug est dans
le service lui-même) et passent tant que le bug est présent. `CSW_URL`
permet de pointer vers un autre endpoint si besoin.

## Structure

```
docs/bug-filter.md   explication détaillée du bug, preuve, reproduction curl
tests/               suite de tests fonctionnels (voir docs/bug-filter.md)
```
