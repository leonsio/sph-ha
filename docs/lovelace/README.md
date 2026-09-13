# Lovelace-Karten

SPH-HA registriert seine JavaScript-Ressourcen automatisch. Nach einem Integrationsupdate genügt normalerweise ein Home-Assistant-Neustart und anschließend ein Neuladen des Dashboards.

Dokumentationsstand: **0.5.0**.

## Verfügbare Karten

| Karte | Typ | Zweck |
|---|---|---|
| [SPH Stundenplan](sph-stundenplan-card.md) | `custom:sph-stundenplan-card` | Persönlicher Wochenstundenplan als Liste |
| [SPH Tagesstundenplan](sph-stundenplan-tag-card.md) | `custom:sph-stundenplan-tag-card` | Aktueller bzw. nächster Unterrichtstag |
| [SPH Stundenplan Raster](sph-stundenplan-grid-card.md) | `custom:sph-stundenplan-grid-card` | Wochenstundenplan als Raster |
| [SPH Mein Unterricht](sph-meinunterricht-card.md) | `custom:sph-meinunterricht-card` | Hausaufgaben anzeigen und lokale Einträge verwalten |
| [SPH Lerngruppen](sph-lerngruppen-card.md) | `custom:sph-lerngruppen-card` | Leistungskontrollen anzeigen und lokale Termine verwalten |
| [SPH Kalender](sph-kalender-card.md) | `custom:sph-kalender-card` | Tag-/Woche-/Monat-Darstellung der SPH-Kalender |
| [SPH Vertretungsplan](sph-vertretungsplan-card.md) | `custom:sph-vertretungsplan-card` | Vertretungen, Raumwechsel, Entfälle und Hinweise |

## Gemeinsame Entity-Auswahl

Viele Karten unterstützen:

- `entity` – explizite Entity-ID,
- `sensor` – Alias für `entity`,
- `child` – Auswahl über `kind_kürzel` bzw. Kindnamen.

Bei mehreren Kindern ist eine explizite `entity` oder ein eindeutiges `child` empfehlenswert.

## Vertretungsdaten in Stundenplankarten

Seit 0.5.0 verwenden die drei allgemeinen Stundenplankarten automatisch den zum Kind passenden internen SPH-Vertretungsplan.

Damit können sie direkt an einer Stunde darstellen:

- Entfall/Ausfall,
- Vertretung,
- Fachwechsel,
- Raumänderung,
- Vertretungslehrkraft,
- Hinweise/Nachricht des Tages.

Ohne School Hack ist der interne SPH-Vertretungsplan die primäre Quelle.

## School Hacks

Schulspezifische Anpassungen werden auf denselben allgemeinen Karten aktiviert:

```yaml
type: custom:sph-stundenplan-grid-card
entity: sensor.stundenplan_maxim_mk
school-hacks: kfg
```

Bei einem aktiven School Hack gilt:

1. explizit gesetzte Vertretungsquelle bleibt autoritativ,
2. die schulische Profilquelle wird bevorzugt,
3. der interne SPH-Vertretungsplan kann als Fallback dienen.

Dadurch lassen sich weitere Schulen über eigene Profildateien ergänzen, ohne neue Kartenklassen zu kopieren.

Allgemeine School-Hacks-Doku: [school-hacks.md](school-hacks.md).

Schulspezifische Profile: [../schools/README.md](../schools/README.md).

Aktuell vorhanden:

- `kfg` – [Kaiserin-Friedrich-Gymnasium Bad Homburg](../schools/kfg/README.md)

## Ressourcen und Cache

Die Ressourcen werden versioniert unter `/api/sph/static/...` registriert. Alte separate KFG-Kartentypen werden nicht mehr verwendet.

Nach einem Update:

1. Home Assistant neu starten,
2. Dashboard bzw. Browser-Cache neu laden.

Manuelle `/local/...`-Ressourceneinträge sind für aktuelle Home-Assistant-Versionen nicht erforderlich.
