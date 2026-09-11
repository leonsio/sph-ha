# SPH Lerngruppen

Kartentyp: `custom:sph-lerngruppen-card`

## Funktionsweise

Die Karte zeigt die vom SPH-Lerngruppen-Modul bereitgestellten Leistungskontrollen in einer Tabelle. Angezeigt werden Datum, Art, Fach/Kurs, Dauer, Stunden, Lehrkraft und Quelle.

Neben den vom Schulportal geladenen Daten können direkt über die Karte eigene Termine angelegt werden. Manuelle Termine werden lokal in SPH-HA gespeichert und mit den SPH-Daten zusammengeführt. Nur manuell angelegte Einträge erhalten eine Lösch-Schaltfläche; importierte SPH-Termine bleiben schreibgeschützt.

Beim Anlegen können Datum, Art, Fach/Kurs, Dauer in Minuten, Schulstunden und Lehrkraft angegeben werden. Stundenangaben wie `3,4` oder Bereiche werden vom Backend normalisiert. Sind zu den angegebenen Stunden Zeiten aus dem persönlichen Stundenplan bekannt, kann das Lerngruppen-Modul daraus zeitlich begrenzte Kalendertermine ableiten; andernfalls bleibt der Termin ganztägig.

## Entity-Auswahl

Reihenfolge:

1. `entity` oder `sensor`, falls konfiguriert und vorhanden.
2. Bei gesetztem `child`: ein `sensor.lerngruppen_*` mit passendem `kind_kürzel`.
3. Andernfalls der erste passende `sensor.lerngruppen_*` mit dem Attribut `leistungskontrollen`.

JSON-Sensoren mit `_json` werden nicht verwendet.

## Konfigurationsparameter

| Parameter | Typ | Standard | Beschreibung |
|---|---|---|---|
| `type` | String | erforderlich | `custom:sph-lerngruppen-card` |
| `title` | String | `Lerngruppen – Leistungskontrollen` | Kartentitel |
| `entity` | Entity-ID | automatisch | Expliziter Lerngruppen-Sensor |
| `sensor` | Entity-ID | automatisch | Alias für `entity` |
| `child` | String | leer | Auswahl über `kind_kürzel` |

## Beispiel

```yaml
type: custom:sph-lerngruppen-card
title: Leistungskontrollen
child: mk
```

Explizite Entity:

```yaml
type: custom:sph-lerngruppen-card
entity: sensor.lerngruppen_maxim_mk
```

## Eigene Termine

Mit `+ Termin hinzufügen` öffnet die Karte einen Dialog mit folgenden Feldern:

| Feld | Pflicht | Beschreibung |
|---|---|---|
| Datum | ja | Datum der Leistungskontrolle |
| Art | ja | z. B. Arbeit, Test, Klausur |
| Fach/Kurs | ja | Fach oder Kursbezeichnung |
| Dauer (Min) | nein | 1 bis 1440 Minuten |
| Stunden | nein | z. B. `3,4` oder `3-4` |
| Lehrkraft | nein | Freitext |

Die Karte verwendet dafür die SPH-Services `sph.lerngruppen_termin_hinzufuegen` und `sph.lerngruppen_termin_loeschen`.

## Hinweise

- Importierte SPH-Einträge können aus der Karte nicht gelöscht werden.
- Die Tabelle ist auf schmalen Displays horizontal scrollbar.
- Während ein Dialog geöffnet ist, versucht die Karte Eingabewerte und Fokus auch bei Sensorupdates beizubehalten.
