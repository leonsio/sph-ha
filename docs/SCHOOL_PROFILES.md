# Schul-Profile

Schul-Profile bündeln Besonderheiten einer bestimmten Schule und werden **pro Kind** im jeweiligen Integrationseintrag ausgewählt.

## Zweck

SPH-HA bildet allgemeine Funktionen möglichst schulübergreifend im Core ab. Schul-Profile ergänzen ausschließlich schulspezifische Abweichungen, zum Beispiel:

- Lehrerkürzel in vollständige Namen auflösen
- schulspezifische Fachnamen verwenden
- besondere Vertretungscodes benennen
- Beschreibungen in Sensoren und Kalendern aufbereiten
- A/B-Wochen oder andere Darstellungsregeln in den SPH-Lovelace-Karten anpassen

Ein Profil kann sowohl serverseitige Daten als auch optionale Darstellungsregeln beeinflussen. Dadurch stehen schulspezifisch aufbereitete Werte – soweit fachlich sinnvoll – in Sensoren, JSON-Ausgaben, Kalendern und Lovelace zur Verfügung.

## Auswahl

Bei der Einrichtung eines Kindes gibt es den Parameter **Schul-Profil**. Die Auswahl kann später in den Optionen des jeweiligen Integrationseintrags geändert werden.

Standard:

```text
Standard / kein Schulprofil
```

Vorhandene Profile:

| Profil | Schule |
|---|---|
| `kfg` | Kaiserin-Friedrich-Gymnasium Bad Homburg |

## Pro Kind

Das Profil gehört zum Config-Entry des Kindes. Mehrere Kinder in derselben Home-Assistant-Installation können daher unterschiedliche Profile verwenden.

## Stundenplan-Auswahl

Das Schul-Profil ändert **nicht**, welcher Stundenplan verwendet wird. Die Einstellung **Stundenplan-Ausgabe** bleibt maßgeblich.

Bei **„Nur eigener Plan“** werden Profilanpassungen auf `eigener_plan` angewandt. `tage` bleibt entsprechend der Konfiguration leer.

Bei **„Eigener Plan + vollständiger SPH-Stundenplan“** werden dieselben Profilanpassungen auf beide veröffentlichten Bereiche angewandt:

- `eigener_plan` – persönlicher Stundenplan des Kindes
- `tage` – vollständiger vom SPH gelieferter Stundenplan

`eigener_grundplan` wird nicht als alternative Profilquelle verwendet und nicht durch das Profil umgeschrieben.

Das ist wichtig, weil vollständige Schulpläne je nach Schule mehrere parallele Angebote enthalten können, die nicht alle für ein einzelnes Kind gelten.

## Sensoren und JSON

Die bestehende Struktur der Sensoren und JSON-Sensoren bleibt erhalten. Profile passen Werte an, ohne vorhandene Schlüssel und Verschachtelungen unnötig zu verändern.

Profilierte Payloads enthalten zusätzlich:

```yaml
school_profile: kfg
```

Die SPH-Lovelace-Karten können das Profil dadurch automatisch erkennen.

## Kalender

Serverseitige Profilanpassungen werden auch in nativen Kalender-Entities berücksichtigt. Dadurch können beispielsweise aufgelöste Lehrernamen oder schulspezifische Fachnamen auch in Kalenderterminen erscheinen.

Datumsabhängige Änderungen wie eine konkrete Vertretung werden nur in Kontexten angewandt, in denen das konkrete Datum bekannt ist. Sie werden nicht dauerhaft in einen wiederverwendeten Wochenplan geschrieben.

## Lovelace

Wenn das Profil im Integrationseintrag ausgewählt ist, ist normalerweise kein zusätzlicher Kartenparameter erforderlich.

Beispiel:

```yaml
type: custom:sph-stundenplan-grid-card
entity: sensor.stundenplan_maxim_mk
```

Für Tests oder einen gezielten Karten-Override kann das Profil direkt angegeben werden:

```yaml
school-profile: kfg
```

Mit

```yaml
school-profile: false
```

kann die Profil-Darstellung einer einzelnen Karte deaktiviert werden, auch wenn der Sensor ein Profil meldet.

## KFG

Das Profil `kfg` enthält die Besonderheiten des Kaiserin-Friedrich-Gymnasiums Bad Homburg. Dazu gehören insbesondere:

- KFG-spezifische Vertretungsbezeichnungen
- Auflösung von Lehrerkürzeln über die KFG-eigene Kollegiums-Entity
- KFG-spezifische A/B-Wochen-Darstellung der Lovelace-Karten
- Grid-Wochenüberschrift
- Wechsel der Wochenansicht nach Ende der letzten Freitagsstunde

`sensor.kfg_kollegium` gehört ausschließlich zum KFG-Profil und ist keine allgemeine Voraussetzung für SPH-HA.

Weitere Details: [KFG-Profil](schools/kfg/README.md)

## Eigene Profile entwickeln

Die vollständige Entwickler-API ist separat dokumentiert:

[Schul-Profile entwickeln](SCHOOL_PROFILES_DEVELOPMENT.md)
