# School Hacks – Legacy-Hinweis

Mit SPH-HA **0.6.0** wurde die bisherige Lovelace-only-Funktion **School Hacks** durch **Schul-Profile / School Profiles** ersetzt.

Die aktuelle Dokumentation befindet sich hier:

- [Schul-Profile](../SCHOOL_PROFILES.md)
- [Schul-Profile entwickeln](../SCHOOL_PROFILES_DEVELOPMENT.md)
- [Schulspezifische Profile](../schools/README.md)

## Migration

Bisher:

```yaml
school-hacks: kfg
```

Neu als expliziter Karten-Override:

```yaml
school-profile: kfg
```

Normalerweise ist ab 0.6.0 gar kein Kartenparameter mehr erforderlich. Das Profil wird pro Kind in der Integration ausgewählt und über die Sensorattribute automatisch erkannt.

Der alte Parameter `school-hacks` bleibt in 0.6.0 als Legacy-Alias erhalten.

## Architekturänderung

School Hacks beeinflussten ausschließlich die Lovelace-Darstellung. Schul-Profile besitzen zusätzlich eine serverseitige Python-Ebene und können deshalb schulspezifische Werte auch in Sensoren, JSON-Sensoren und Home-Assistant-Kalendern aufbereiten.

Die bestehenden Dateien unter `static/school-hacks*` dienen nur noch als Kompatibilitätsbrücke zur neuen `school-profile`-Implementierung.
