# gpf-csw-test

<!-- Generated with Claude Code (https://claude.com/claude-code) -->

Tests fonctionnels reproduisant un bug de recherche plein texte (`AnyText` +
wildcard `%`) sur le service CSW de la Géoplateforme
(`https://data.geopf.fr/csw`).

- **Bug documenté** : [docs/bug-filter.md](docs/bug-filter.md)
- **Issue de suivi** : [mborne/gpf-catalogue#7](https://github.com/mborne/gpf-catalogue/issues/7)

## Reproduire le bug en une commande

```bash
curl -s -X POST -H "Content-Type: application/xml" "https://data.geopf.fr/csw" --data '<?xml version="1.0" encoding="UTF-8"?>
<csw:GetRecords xmlns:csw="http://www.opengis.net/cat/csw/2.0.2"
    xmlns:ogc="http://www.opengis.net/ogc"
    service="CSW" version="2.0.2"
    resultType="results" outputSchema="csw:IsoRecord"
    maxRecords="10">
  <csw:Query typeNames="csw:Record">
    <csw:ElementSetName>brief</csw:ElementSetName>
    <csw:Constraint version="1.1.0">
      <ogc:Filter>
        <ogc:PropertyIsLike wildCard="%" singleChar="_" escapeChar="\">
          <ogc:PropertyName>AnyText</ogc:PropertyName>
          <ogc:Literal>%pont%</ogc:Literal>
        </ogc:PropertyIsLike>
      </ogc:Filter>
    </csw:Constraint>
  </csw:Query>
</csw:GetRecords>'
```

Réponse attendue si le bug est présent : `HTTP 200` avec un
`ows:ExceptionReport` (`UnknownFormatConversionException`) au lieu des
résultats. Détails et variantes testées : [docs/bug-filter.md](docs/bug-filter.md).

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
