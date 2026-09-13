# SPH Vertretungsplan

Die Karte `custom:sph-vertretungsplan-card` zeigt die veröffentlichten Vertretungsplantage aus dem Schulportal Hessen. Sie stellt Vertretungen, Raumwechsel, Ausfälle und allgemeine Hinweise der Schule dar.

## Minimalbeispiel

```yaml
type: custom:sph-vertretungsplan-card
entity: sensor.vertretungsplan_maxim_mk
title: Vertretungsplan Maxim
```

Alternativ kann die Karte über `child` den passenden Sensor anhand von Name oder Kürzel auswählen:

```yaml
type: custom:sph-vertretungsplan-card
child: mk
```

## Optionen

| Option | Standard | Wirkung |
|---|---|---|
| `entity` / `sensor` | automatisch | Expliziter Vertretungsplan-Sensor |
| `child` | – | Name oder Kürzel des Kindes für die automatische Sensorwahl |
| `title` | – | Kartenüberschrift |
| `days` | alle | Maximale Anzahl angezeigter Tage |
| `hide_empty` | `false` | Tage ohne Einträge ausblenden |
| `only_cancellations` | `false` | Nur Einträge anzeigen, die als Entfall erkannt wurden |

Ausfälle werden hervorgehoben und das Fach wird durchgestrichen dargestellt. Bei Raumänderungen wird der vorherige Raum zusätzlich angezeigt.

## Sensoren

Das Modul erzeugt bei einem Kind `Maxim` mit Kürzel `Mk` unter anderem:

```text
sensor.vertretungsplan_maxim_mk
sensor.vertretungsplan_maxim_mk_json
binary_sensor.erste_stunde_entfaellt_heute_maxim_mk
binary_sensor.erste_stunde_entfaellt_morgen_maxim_mk
```

Der JSON-Sensor enthält im Attribut `json` denselben vollständigen Payload wie der normale Sensor, unter anderem `tage`, `heute`, `morgen`, Entfall-Zähler, Hinweise und den Zeitstempel der letzten Planänderung.

Die Bezugsstunde der beiden Binärsensoren wird in den Integrationsoptionen über **Bezugsstunde für Entfall-Sensoren** festgelegt. Solange für den jeweiligen Tag noch kein Plan veröffentlicht wurde, bleibt der Binärsensor `unavailable` statt fälschlich `off` anzuzeigen.
