# Lovelace-Karten

SPH-HA registriert seine Lovelace-JavaScript-Ressourcen automatisch. Nach Installation oder Update der Integration genügt normalerweise ein Neustart von Home Assistant und anschließend ein Neuladen des Browsers.

## Verfügbare Karten

| Karte | Typ | Zweck |
|---|---|---|
| [SPH Stundenplan](sph-stundenplan-card.md) | `custom:sph-stundenplan-card` | Persönlicher Wochenstundenplan als Liste |
| [SPH Tagesstundenplan](sph-stundenplan-tag-card.md) | `custom:sph-stundenplan-tag-card` | Aktueller bzw. nächster Unterrichtstag |
| [SPH Stundenplan Raster](sph-stundenplan-grid-card.md) | `custom:sph-stundenplan-grid-card` | Wochenstundenplan als klassisches Raster |
| [SPH Mein Unterricht](sph-meinunterricht-card.md) | `custom:sph-meinunterricht-card` | Hausaufgaben anzeigen und eigene Einträge verwalten |
| [SPH Lerngruppen](sph-lerngruppen-card.md) | `custom:sph-lerngruppen-card` | Leistungskontrollen anzeigen und eigene Termine verwalten |
| [SPH Kalender](sph-kalender-card.md) | `custom:sph-kalender-card` | Tag-/Woche-/Monat-Kalender für die SPH-Kalender-Entities |

Schulanpassungen werden auf den normalen Karten mit `school-hacks: kfg` aktiviert.
[Schulprofile und Umstieg](school-hacks.md). Die alten KFG-Kartentypen wurden entfernt.

## Gemeinsame Auswahlparameter

Die Stundenplan-, Mein-Unterricht- und Lerngruppen-Karten unterstützen grundsätzlich die explizite Entity-Auswahl über `entity` beziehungsweise den Alias `sensor`. Wird keine Entity angegeben, kann bei mehreren Kindern mit `child` das in den Sensorattributen hinterlegte `kind_kürzel` ausgewählt werden.

Beispiel:

```yaml
type: custom:sph-stundenplan-card
child: mk
title: Maxim – Stundenplan
```

Für produktive Dashboards ist bei mehreren SPH-Konfigurationen eine explizite `entity` oder ein eindeutiges `child` empfehlenswert.
