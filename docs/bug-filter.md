# Bug CSW : recherche plein texte (`AnyText` + wildcard) cassée

- **Service concerné** : `https://data.geopf.fr/csw` (CSW 2.0.2, Géoplateforme / IGN)
- **Issue de suivi** : [mborne/gpf-catalogue#7](https://github.com/mborne/gpf-catalogue/issues/7)
- **Tests automatisés** : [`tests/test_csw_anytext_search.py`](../tests/test_csw_anytext_search.py)
- **Constaté le** : 2026-09-25

## Résumé

Dès qu'une requête `GetRecords` contient un filtre `PropertyIsLike` sur
`AnyText` dont le littéral comporte le caractère `%` (le wildcard), le
service répond **HTTP 200** avec un `ows:ExceptionReport` :

```
java.lang.RuntimeException: java.util.UnknownFormatConversionException: Conversion = 'p'
```

C'est le seul queryable qui permette une recherche par mot-clé côté CSW
(`AnyText`) — il est donc inutilisable pour une recherche plein texte "à la
Google" (`%mot%`), ce qui est la manière normale d'utiliser ce filtre.

## Comment on a vérifié que ce n'est pas une erreur de requête

Avant de pointer du doigt le serveur, on a vérifié que des requêtes voisines,
syntaxiquement correctes, fonctionnent :

| Requête (POST, `ogc:Filter`) | Résultat |
|---|---|
| `PropertyIsEqualTo(AnyText, 'pont')` | `200`, résultats corrects |
| `PropertyIsLike(AnyText, 'pont')` *(pas de `%`)* | `200`, résultats corrects |
| `PropertyIsLike(AnyText, '%pont%')` | `200` + `ows:ExceptionReport` |
| `PropertyIsLike(AnyText, 'pont%')` | `200` + `ows:ExceptionReport` |
| `PropertyIsLike(AnyText, '%pont')` | `200` + `ows:ExceptionReport` |

Seule la présence du caractère `%` dans le littéral change l'issue. Le
serveur, le type de filtre (`PropertyIsLike`) et l'endpoint sont identiques
dans tous les cas : la variable qui fait basculer la requête en échec est
bien le wildcard, pas une erreur de notre côté.

Ces cinq requêtes sont couvertes par les tests
`CswBaselineTests` et `CswFullTextSearchTests` du fichier de test.

## Piste sur la cause : un `%` utilisateur qui atterrit dans un `String.format` Java

En faisant varier le caractère qui suit (ou précède) le `%`, le message
d'erreur change de façon cohérente avec un bug classique de *format string
injection* côté serveur (le littéral fourni par l'utilisateur est repassé,
sans échappement, dans un `java.util.Formatter`/`String.format(...)`
Java) :

| Littéral | `Conversion = '?'` observé |
|---|---|
| `%pont%`, `%pont` | `'p'` |
| `pont%` | `'"'` |
| `%xyz%`, `%contour%` | `'"'` |

`'p'` n'est pas une conversion `String.format` valide, d'où l'échec
immédiat sur le premier `%`. Ce n'est **pas prouvé** (on n'a pas le code
source du service), mais le comportement observé — un message d'erreur qui
dépend du caractère suivant le wildcard — est la signature typique de ce
type de bug plutôt que d'un problème réseau ou de sérialisation XML.

## Constat annexe : le flavor GET/KVP échoue *avant même* d'atteindre ce bug

Une requête `GetRecords` en GET/KVP avec `CONSTRAINTLANGUAGE=CQL_TEXT` et
`CONSTRAINT=AnyText like '...'` (avec ou sans `%`) ne renvoie jamais
l'`ows:ExceptionReport` ci-dessus : elle échoue plus tôt, avec un
**HTTP 500 au corps vide**, dès que le mot-clé `LIKE` apparaît dans la
requête — wildcard ou non. Le comportement porte les marques d'un blocage
en amont du service CSW lui-même (répondeur `x-iplb-*` dans les en-têtes,
probablement un WAF/API gateway IGN plutôt que le backend CSW).

C'est un problème distinct de celui décrit plus haut :
- il empêche de reproduire le bug applicatif via une simple URL GET (d'où
  l'usage de POST + `ogc:Filter` XML dans les reproductions ci-dessous et
  dans les tests) ;
- il peut évoluer indépendamment (règle de filtrage réseau) du bug
  applicatif (code du service CSW) ;
- il est couvert par son propre test,
  `test_get_kvp_cql_like_constraint_returns_results`, pour ne pas être
  confondu avec le bug principal.

## Reproduire en une commande

```bash
cat > /tmp/getrecords_anytext_like.xml << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
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
</csw:GetRecords>
EOF

curl -s -X POST -H "Content-Type: application/xml" \
  --data-binary @/tmp/getrecords_anytext_like.xml \
  "https://data.geopf.fr/csw"
```

Réponse observée :

```xml
<?xml version="1.0" encoding="UTF-8"?>
<ows:ExceptionReport xmlns:ows="http://www.opengis.net/ows" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" version="1.2.0" xsi:schemaLocation="http://www.opengis.net/ows http://schemas.opengis.net/ows/1.0.0/owsExceptionReport.xsd">
  <ows:Exception exceptionCode="NoApplicableCode">
    <ows:ExceptionText>java.lang.RuntimeException: java.util.UnknownFormatConversionException: Conversion = 'p'</ows:ExceptionText>
  </ows:Exception>
</ows:ExceptionReport>
```

## Tests automatisés

Avec [uv](https://docs.astral.sh/uv/) (installe pytest dans un venv local,
géré par `pyproject.toml`/`uv.lock`) :

```bash
uv sync
uv run pytest -v
```

Sans uv, la suite ne dépend que de la bibliothèque standard Python 3 (aucun
`pip install` requis) :

```bash
python3 -m unittest discover -s tests -v
```

Les tests appellent le service CSW en direct, il n'y a rien à mocker
puisque le bug est dans le service lui-même. `CSW_URL` permet de pointer
vers un autre endpoint si besoin (ex: environnement de recette IGN).

- `CswBaselineTests` : vérifie que le service répond, et que les requêtes
  "voisines" (égalité, `LIKE` sans wildcard) fonctionnent — sert de
  contrôle négatif pour écarter une erreur de notre côté. Ces tests
  **doivent toujours passer**.
- `CswFullTextSearchTests` : décrit le comportement *attendu* d'une
  recherche plein texte (`PropertyIsLike` + wildcard → `200` avec les
  résultats attendus, sur POST/XML comme sur GET/KVP). Tant que le bug est
  présent, **ces tests échouent** — c'est le signal recherché : un run
  rouge documente le problème, un run vert confirmera qu'IGN l'a corrigé.

État actuel (2026-09-25) :

```
$ uv run pytest -v
...
5 failed, 4 passed in 2.64s
```

Les 5 échecs sont attendus et correspondent chacun à une ligne du tableau
plus haut (wildcard en tête, en fin, sans résultat, requête de référence,
et flavor GET/KVP). Si l'un d'eux se met à passer, c'est qu'IGN a corrigé
tout ou partie du bug — il faut alors mettre à jour ce document et
l'issue associée en conséquence.
