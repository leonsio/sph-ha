# Schulspezifische Schul-Profile

Dieser Ordner enthält die Dokumentation zu den vorhandenen schulspezifischen Profilen.

Die allgemeine Benutzer-Dokumentation befindet sich unter [`../SCHOOL_PROFILES.md`](../SCHOOL_PROFILES.md). Die Entwickler-API und Anleitung für neue Profile ist unter [`../SCHOOL_PROFILES_DEVELOPMENT.md`](../SCHOOL_PROFILES_DEVELOPMENT.md) beschrieben.

## Vorhandene Profile

| Profil | Schule | Dokumentation |
|---|---|---|
| `kfg` | Kaiserin-Friedrich-Gymnasium Bad Homburg | [KFG](kfg/README.md) |

## Struktur

Ein Profil kann aus zwei Teilen bestehen:

```text
custom_components/sph/school_profiles/<name>.py
custom_components/sph/static/school-profiles/<name>.js
```

Der Python-Teil verarbeitet schulspezifische Daten für Sensoren, JSON und Kalender. Der JavaScript-Teil ist optional und enthält nur Darstellungsregeln für die mitgelieferten Lovelace-Karten.

Für jedes neue Profil wird zusätzlich eine Schuldokumentation angelegt:

```text
docs/schools/<name>/README.md
```

## Grundregel

Profile sollen langfristig möglichst klein bleiben. Sobald eine Regel schulübergreifend sinnvoll ist, sollte sie in die allgemeine Integration verschoben werden.

Schulspezifische externe Entities gehören ausschließlich in das jeweilige Profil. Beispielsweise ist `sensor.kfg_kollegium` nur Bestandteil des KFG-Profils und keine allgemeine Abhängigkeit von SPH-HA.
