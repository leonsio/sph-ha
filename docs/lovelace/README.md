# Lovelace-Karten

SPH-HA registriert seine Lovelace-JavaScript-Ressourcen automatisch. Nach Installation oder Update der Integration genügt normalerweise ein Neustart von Home Assistant und anschließend ein Neuladen des Browsers.

## Verfügbare Karten

| Karte | Typ | Zweck |
|---|---|---|
| [SPH Stundenplan](sph-stundenplan-card.md) | `custom:sph-stundenplan-card` | Persönlicher Wochenstundenplan als Liste |
| [SPH Tagesstundenplan](sph-stundenplan-tag-card.md) | `custom:sph-stundenplan-tag-card` | Aktueller bzw. nächster Unterrichtstag |
| [SPH Stundenplan Raster](sph-stundenplan-grid-card.md) | `custom:sph-stundenplan-grid-card` | Wochenstundenplan als klassisches Raster |
| [KFG Stundenplan](kfg-stundenplan-card.md) | `custom:kfg-stundenplan-card` | Wochenstundenplan mit KFG-Vertretungsplan |
| [KFG Tagesstundenplan](kfg-stundenplan-tag-card.md) | `custom:kfg-stundenplan-tag-card` | Tagesansicht mit KFG-Vertretungen und Tagesnachrichten |
| [KFG Stundenplan Raster](kfg-stundenplan-grid-card.md) | `custom:kfg-stundenplan-grid-card` | Rasteransicht mit KFG-Vertretungsinformationen |
| [SPH Mein Unterricht](sph-meinunterricht-card.md) | `custom:sph-meinunterricht-card` | Hausaufgaben anzeigen und eigene Einträge verwalten |
| [SPH Lerngruppen](sph-lerngruppen-card.md) | `custom:sph-lerngruppen-card` | Leistungskontrollen anzeigen und eigene Termine verwalten |
| [SPH Kalender](sph-kalender-card.md) | `custom:sph-kalender-card` | Tag-/Woche-/Monat-Kalender für die SPH-Kalender-Entities |

`kfg-stundenplan-compat.js` ist keine eigene Lovelace-Karte, sondern eine technische Kompatibilitätsschicht und wird deshalb nicht als Karte dokumentiert.

## Gemeinsame Auswahlparameter

Die Stundenplan-, Mein-Unterricht- und Lerngruppen-Karten unterstützen grundsätzlich die explizite Entity-Auswahl über `entity` beziehungsweise den Alias `sensor`. Wird keine Entity angegeben, kann bei mehreren Kindern mit `child` das in den Sensorattributen hinterlegte `kind_kürzel` ausgewählt werden.

Beispiel:

```yaml
type: custom:sph-stundenplan-card
child: mk
title: Maxim – Stundenplan
```

Für produktive Dashboards ist bei mehreren SPH-Konfigurationen eine explizite `entity` oder ein eindeutiges `child` empfehlenswert.
