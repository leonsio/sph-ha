# SPH Mein Unterricht

Kartentyp: `custom:sph-meinunterricht-card`

## Funktionsweise

Die Karte zeigt die vom SPH-Modul „Mein Unterricht“ bereitgestellten Hausaufgaben tabellarisch. Angezeigt werden Datum, Fach/Kurs, Thema, Aufgabe, Lehrer, Status und Quelle.

Zusätzlich können eigene Hausaufgaben direkt in der Karte angelegt werden. Diese werden lokal in SPH-HA gespeichert und mit den vom Schulportal geladenen Einträgen zusammengeführt. Nur manuell erstellte Hausaufgaben können aus der Karte wieder gelöscht werden.

Manuelle Hausaufgaben werden sieben Tage nach dem eingetragenen Hausaufgabendatum automatisch aus dem lokalen Speicher entfernt.

## Entity-Auswahl

Reihenfolge:

1. `entity` oder `sensor`, falls konfiguriert und vorhanden.
2. Bei gesetztem `child`: ein `sensor.mein_unterricht_*` mit passendem `kind_kürzel`.
3. Andernfalls der erste passende `sensor.mein_unterricht_*` mit dem Attribut `aufgaben`.

JSON-Sensoren mit `_json` werden nicht verwendet.

## Konfigurationsparameter

| Parameter | Typ | Standard | Beschreibung |
|---|---|---|---|
| `type` | String | erforderlich | `custom:sph-meinunterricht-card` |
| `title` | String | `Mein Unterricht – Hausaufgaben` | Kartentitel |
| `entity` | Entity-ID | automatisch | Expliziter Mein-Unterricht-Sensor |
| `sensor` | Entity-ID | automatisch | Alias für `entity` |
| `child` | String | leer | Auswahl über `kind_kürzel` |

## Beispiel

```yaml
type: custom:sph-meinunterricht-card
title: Hausaufgaben
child: mk
```

Explizite Entity:

```yaml
type: custom:sph-meinunterricht-card
entity: sensor.mein_unterricht_maxim_mk
```

## Eigene Hausaufgaben

Mit `+ Hausaufgabe hinzufügen` öffnet die Karte einen Dialog mit folgenden Feldern:

| Feld | Pflicht | Beschreibung |
|---|---|---|
| Datum | ja | Datum der Hausaufgabe |
| Fach | ja | Fachbezeichnung |
| Kurs | nein | Optionaler Kursname |
| Lehrer | nein | Freitext |
| Thema | nein | Optionales Thema |
| Hausaufgabe | ja | Beschreibung der Aufgabe |
| Bereits erledigt | nein | Setzt den Status direkt auf erledigt |

Die Karte verwendet dafür die SPH-Services `sph.meinunterricht_hausaufgabe_hinzufuegen` und `sph.meinunterricht_hausaufgabe_loeschen`.

## Hinweise

- Vom Schulportal geladene Hausaufgaben sind schreibgeschützt.
- Manuelle Einträge werden in der Spalte `Quelle` als `Manuell` gekennzeichnet.
- Der Status wird als `Offen` oder `Erledigt` dargestellt.
- Die Tabelle ist auf schmalen Displays horizontal scrollbar.
- Dialoginhalt und Fokus werden bei Sensorupdates möglichst erhalten.
