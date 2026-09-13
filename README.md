# Schulportal Hessen für Home Assistant

Home-Assistant-Custom-Integration für Daten aus dem **Schulportal Hessen (SPH)**.

Aktueller Dokumentationsstand: **Version 0.5.0**.

## Funktionen

Die Integration wird pro Kind eingerichtet und umfasst fünf unabhängig aktivierbare Module:

- **Stundenplan** – persönlicher Stundenplan, A/B-Wochen, freie Tage und nativer Kalender.
- **Schulkalender** – SPH-Kalender mit Sensor, JSON-Sensor und Home-Assistant-Kalender.
- **Mein Unterricht** – Hausaufgaben, Kurs-/Fachnormalisierung, Fachübersichten und lokale Ergänzungen.
- **Lerngruppen** – Leistungskontrollen, Kalendertermine und lokale Ergänzungen.
- **Vertretungsplan** – Vertretungen, Entfälle, Raum-/Fachwechsel, Hinweise, JSON-Sensor und Entfall-Binärsensoren.

Zusätzlich werden Lovelace-Karten automatisch als Ressourcen registriert. Schulspezifische Anpassungen können über **School Hacks** aktiviert werden, ohne separate Kartenkopien anzulegen.

## Installation über HACS

Repository als **Integration** in HACS hinzufügen:

```text
https://github.com/leonsio/sph-ha
```

Anschließend unter **Einstellungen → Geräte & Dienste → Integration hinzufügen** nach **Schulportal Hessen** suchen.

## Einrichtung

Für jedes Kind wird ein eigener Integrationseintrag angelegt. Benötigt werden insbesondere:

- Schulnummer
- SPH-Benutzername
- SPH-Passwort
- Name des Kindes
- Kürzel des Kindes
- Aktualisierungsintervall

Das Standardintervall beträgt **60 Minuten**. Module, Zugangsdaten und weitere Optionen können später geändert werden.

Zusätzliche Optionen betreffen unter anderem:

- aktive Module,
- Stundenplan-Ausgabe,
- Schulkalenderarten,
- Bezugsstunde für die Vertretungsplan-Binärsensoren,
- Schulamtsbezirk für bewegliche Ferientage,
- getrennte oder zusammengefasste SPH-Kalender.

## Beispiel-Entities

Für `Maxim` mit Kürzel `Mk` entstehen – abhängig von den aktivierten Modulen – beispielsweise:

```text
sensor.stundenplan_maxim_mk
sensor.stundenplan_maxim_mk_json
sensor.schulkalender_maxim_mk
sensor.schulkalender_maxim_mk_json
sensor.mein_unterricht_maxim_mk
sensor.mein_unterricht_maxim_mk_json
sensor.lerngruppen_maxim_mk
sensor.lerngruppen_maxim_mk_json
sensor.vertretungsplan_maxim_mk
sensor.vertretungsplan_maxim_mk_json
binary_sensor.erste_stunde_entfaellt_heute_maxim_mk
binary_sensor.erste_stunde_entfaellt_morgen_maxim_mk
calendar.stundenplan_maxim_mk
calendar.schulkalender_maxim_mk
calendar.lerngruppen_maxim_mk
calendar.sph_maxim_mk
calendar.bewegliche_ferientage_maxim_mk
```

Je nach Kalendereinstellung existieren entweder die einzelnen Kalender oder zusätzlich bzw. alternativ der zusammengefasste `calendar.sph_*`.

## Stundenplan

Der persönliche Plan steht unter `eigener_plan`. Zusätzlich stehen unter anderem `wochenkennung`, `wochenbeginn`, `freie_tage` und `eigener_grundplan` zur Verfügung.

Der native Stundenplan-Kalender erzeugt Unterrichtstermine für ein rollierendes Zeitfenster von zwei Wochen Vergangenheit bis acht Wochen Zukunft. A/B-Wochen werden relativ zur aktuellen SPH-Wochenkennung fortgeschrieben. Freie Tage aus `calendar.deutschland_he` und den konfigurierten beweglichen Ferientagen werden berücksichtigt.

### Vertretungen im Stundenplan

Seit 0.5.0 werden Daten aus dem internen SPH-Vertretungsplan auch in den allgemeinen Stundenplankarten und in der nativen Kalendergenerierung berücksichtigt.

Die allgemeinen `sph-stundenplan-*` Karten verwenden automatisch den zum Kind passenden `sensor.vertretungsplan_*` und können damit unter anderem darstellen:

- Entfall/Ausfall,
- Vertretungen,
- Fachwechsel,
- Raumänderungen,
- Vertretungslehrkräfte,
- Hinweise/Nachricht des Tages.

Der native Stundenplan-Kalender verwendet serverseitig ausschließlich den internen SPH-Vertretungsplan. Dabei werden bestehende Unterrichtstermine angepasst; stabile UIDs verhindern unnötige doppelte Termine.

## Vertretungsplan

Das Modul liest `vertretungsplan.php`. Die Tabellen werden anhand der SPH-`data-field`-Kennzeichnungen ausgewertet und sind dadurch nicht an eine feste Spaltenreihenfolge gebunden.

Wichtige Daten:

- `tage`, `heute`, `morgen`
- `anzahl_heute`, `anzahl_morgen`
- `entfaelle_heute`, `entfaelle_morgen`
- Hinweise
- `aktualisiert`, `wird_aktualisiert`
- `art` und normalisiertes `art_lang`
- `stunde`, `stunden`, `von_stunde`, `bis_stunde`
- `entfall`

Abkürzungen wie `Vertr`, `Entf.` oder `Freis` werden zusätzlich als Langform bereitgestellt. Der JSON-Sensor enthält denselben vollständigen Payload im Attribut `json`.

Die beiden Binärsensoren prüfen die konfigurierte Bezugsstunde. Wenn für einen Tag noch kein Plan veröffentlicht wurde, bleibt der betreffende Sensor `unavailable` statt fälschlich `off` zu melden.

## Mein Unterricht

Kursnamen werden auf ein gemeinsames Fach normalisiert. Klassenkennungen wie `05cG`, `7n` oder `5` werden entfernt und bekannte Kürzel ausgeschrieben. Beispielsweise werden `D 05cG` und `Deutsch 7n` beide dem Fach **Deutsch** zugeordnet; der Originalkurs bleibt in `kurs` erhalten.

Normaler und JSON-Sensor liefern zusätzlich:

- `faecher`
- `faecher_gesamt`
- `faecher_offen`

Manuelle Hausaufgaben werden lokal gespeichert, mit SPH-Daten zusammengeführt und sieben Tage nach ihrem Aufgabendatum automatisch entfernt.

Services:

```text
sph.meinunterricht_hausaufgabe_hinzufuegen
sph.meinunterricht_hausaufgabe_loeschen
```

## Lerngruppen

Das Modul liest Leistungskontrollen aus `lerngruppen.php`. Schulstunden werden nach Möglichkeit über den persönlichen Stundenplan in konkrete Start-/Endzeiten übersetzt. Manuelle Leistungskontrollen werden lokal gespeichert und mit SPH-Daten zusammengeführt.

Services:

```text
sph.lerngruppen_termin_hinzufuegen
sph.lerngruppen_termin_loeschen
```

## Schulkalender

Das Modul verwendet das aktuelle hessische Schuljahr. CSV wird bevorzugt, iCal dient als Fallback. Kalenderarten können gefiltert werden; ohne Filter werden alle Arten übernommen.

## School Hacks

School Hacks erweitern die normalen `sph-*` Karten um schulabhängige Regeln. Es werden **keine separaten Kartenvarianten pro Schule** gepflegt.

Beispiel:

```yaml
type: custom:sph-stundenplan-grid-card
entity: sensor.stundenplan_maxim_mk
school-hacks: kfg
```

Datenquellen für Vertretungen:

1. Explizit in der Karte gesetzte Vertretungsquelle bleibt autoritativ.
2. Bei aktivem School Hack wird zuerst die im Schulprofil definierte schulische Quelle verwendet.
3. Liefert sie für die konkrete Stunde keinen Treffer, kann der interne SPH-Vertretungsplan als Fallback verwendet werden.
4. Ohne School Hack wird direkt der interne SPH-Vertretungsplan verwendet.

Derzeit vorhandenes Schulprofil:

- [`kfg` – Kaiserin-Friedrich-Gymnasium Bad Homburg](docs/schools/kfg/README.md)

Allgemeine Architektur und Anleitung für weitere Schulen: [`docs/lovelace/school-hacks.md`](docs/lovelace/school-hacks.md).

## Lovelace-Karten

Verfügbar sind:

- `custom:sph-stundenplan-card`
- `custom:sph-stundenplan-tag-card`
- `custom:sph-stundenplan-grid-card`
- `custom:sph-meinunterricht-card`
- `custom:sph-lerngruppen-card`
- `custom:sph-kalender-card`
- `custom:sph-vertretungsplan-card`

Die Ressourcen werden automatisch registriert; für aktuelle Home-Assistant-Versionen ist kein manueller `/local/...`-Eintrag erforderlich.

Vollständige Karten-Dokumentation: [`docs/lovelace/README.md`](docs/lovelace/README.md).

## Robustheit

Bei temporären Abruffehlern bleiben zuletzt erfolgreich geladene Daten erhalten, soweit das jeweilige Modul bereits Daten besitzt. Lokal gespeicherte Hausaufgaben, Leistungskontrollen und eigene Kalendertermine bleiben unabhängig von der SPH-Erreichbarkeit bestehen.

## Technische Dokumentation

- [Architektur](docs/ARCHITEKTUR.md)
- [Lovelace-Karten](docs/lovelace/README.md)
- [School Hacks](docs/lovelace/school-hacks.md)
- [Schulspezifische Profile](docs/schools/README.md)

## Hinweis

Dieses Projekt ist ein unabhängiges Community-Projekt und steht nicht in offizieller Verbindung mit dem Schulportal Hessen.