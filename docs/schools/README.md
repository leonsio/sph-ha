# Schulspezifische School-Hacks-Profile

Dieser Ordner enthält die Dokumentation zu den vorhandenen schulspezifischen Profilen.

Die eigentliche allgemeine School-Hacks-Architektur ist unter [`../lovelace/school-hacks.md`](../lovelace/school-hacks.md) dokumentiert.

## Vorhandene Profile

| Profil | Schule | Dokumentation |
|---|---|---|
| `kfg` | Kaiserin-Friedrich-Gymnasium Bad Homburg | [KFG](kfg/README.md) |

## Regel für neue Schulen

Für jedes neue Profil unter

```text
custom_components/sph/static/school-hacks/<name>.js
```

wird eine eigene Dokumentation angelegt unter

```text
docs/schools/<name>/README.md
```

Die Schul-README beschreibt ausschließlich schulbezogene Besonderheiten, externe Datenquellen, Voraussetzungen und empfohlene YAML-Konfigurationen. Allgemeine Adapter- und Prioritätslogik bleibt in der zentralen School-Hacks-Dokumentation.
