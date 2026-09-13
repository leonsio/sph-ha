# Schul-Profile

Ab Version 0.6.0 unterstützt SPH-HA **Schul-Profile**. Ein Profil bündelt Besonderheiten einer bestimmten Schule und wird **pro Kind** in der Integration ausgewählt.

## Zweck

SPH-HA versucht möglichst viele Funktionen allgemein für alle Schulen abzubilden. Manche Schulen verwenden jedoch eigene Kürzel, Zuordnungen oder Darstellungsregeln. Solche Abweichungen können über ein Schul-Profil ergänzt werden.

Ein Profil kann sowohl serverseitige Daten als auch die mitgelieferten Lovelace-Karten beeinflussen. Dadurch erscheinen schulspezifisch aufbereitete Werte nicht nur in einer Karte, sondern – soweit sinnvoll – auch in Sensoren, JSON-Ausgaben und Kalendern.

Typische Beispiele:

- Lehrerkürzel in Namen auflösen
- schulspezifische Fachnamen verwenden
- besondere Vertretungscodes benennen
- Kalenderbeschreibungen anpassen
- A/B-Wochen in den SPH-Karten schulspezifisch darstellen

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

Das Profil gehört immer zum Config-Entry des Kindes. Zwei Kinder in derselben Home-Assistant-Installation können daher unterschiedliche Profile verwenden.

## Stundenplan-Auswahl bleibt unabhängig

Das Schul-Profil ändert **nicht**, welcher Stundenplan verwendet wird.

Die vorhandene Einstellung **Stundenplan-Ausgabe** bleibt maßgeblich. Das Profil verarbeitet ausschließlich die Daten, die durch die normale Konfiguration für das Kind vorgesehen sind.

Insbesondere wird `eigener_grundplan` nicht als alternative Quelle für Profilanpassungen verwendet.

Das ist wichtig, weil umfangreichere Stundenpläne je nach Schule mehrere parallele Angebote enthalten können, z. B. gleichzeitig katholische Religion, evangelische Religion und Ethik. Für das Kind bleibt der konfigurierte persönliche Stundenplan maßgeblich.

## Sensoren und JSON

Die bestehende Struktur der Sensoren und JSON-Sensoren bleibt erhalten. Profile sollen Werte anpassen, aber bestehende Schlüssel und Verschachtelungen nicht unnötig verändern.

Zusätzlich wird das aktive Profil als Metadatum ausgegeben:

```yaml
school_profile: kfg
```

Die SPH-Lovelace-Karten können das Profil dadurch automatisch erkennen.

## Kalender

Serverseitige Profilanpassungen werden auch bei den nativen Kalender-Entities berücksichtigt. Dadurch können beispielsweise aufgelöste Lehrernamen oder schulspezifische Fachnamen auch im Kalender erscheinen.

Datumsabhängige Änderungen wie eine konkrete Vertretung werden nur dort angewandt, wo das konkrete Datum bekannt ist. Sie werden nicht dauerhaft in einen wiederverwendeten Wochenplan geschrieben.

## Lovelace

Bei einem in der Integration ausgewählten Profil muss normalerweise kein zusätzlicher Parameter in der Karte gesetzt werden.

Beispiel:

```yaml
type: custom:sph-stundenplan-grid-card
entity: sensor.stundenplan_maxim_mk
```

Für Tests oder einen expliziten Override kann verwendet werden:

```yaml
school-profile: kfg
```

Der bisherige Parameter

```yaml
school-hacks: kfg
```

bleibt in Version 0.6.0 aus Kompatibilitätsgründen als Legacy-Alias bestehen. Neue Konfigurationen sollten `school-profile` verwenden bzw. das Profil direkt in der Integration auswählen.

## KFG

Das bisherige KFG-School-Hacks-Profil wurde in das neue KFG-Schul-Profil übernommen.

Das Profil enthält unter anderem:

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
