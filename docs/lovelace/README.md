# Lovelace-Karten

SPH-HA registriert seine JavaScript-Ressourcen automatisch. Nach einem Integrationsupdate genügt normalerweise ein Home-Assistant-Neustart und anschließend ein Neuladen des Dashboards.

Dokumentationsstand: **0.6.0**.

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

Die drei allgemeinen Stundenplankarten verwenden automatisch den zum Kind passenden internen SPH-Vertretungsplan.

Damit können sie direkt an einer Stunde darstellen:

- Entfall/Ausfall,
- Vertretung,
- Fachwechsel,
- Raumänderung,
- Vertretungslehrkraft,
- Hinweise/Nachricht des Tages.

Die Verknüpfung erfolgt datumsbezogen. Konkrete Vertretungen werden nicht dauerhaft in einen wiederverwendeten Wochenplan geschrieben.

## Schul-Profile

Ab 0.6.0 wird ein Schul-Profil normalerweise **nicht mehr in jeder Karte konfiguriert**. Das Profil wird pro Kind im Integrationseintrag ausgewählt und von den Karten über das Sensorattribut `school_profile` automatisch erkannt.

Beispiel:

```yaml
type: custom:sph-stundenplan-grid-card
entity: sensor.stundenplan_maxim_mk
```

Wenn der zugehörige Sensor enthält:

```yaml
school_profile: kfg
```

lädt die Karte automatisch das KFG-Frontendprofil.

### Expliziter Override

Für Tests oder Sonderfälle kann das Profil direkt an der Karte gesetzt werden:

```yaml
type: custom:sph-stundenplan-grid-card
entity: sensor.stundenplan_maxim_mk
school-profile: kfg
```

Ein explizites

```yaml
school-profile: false
```

unterdrückt die Profil-Darstellung der Karte, auch wenn der Sensor ein Profil meldet.

### Legacy

Der bisherige Parameter

```yaml
school-hacks: kfg
```

bleibt in 0.6.0 als Alias bestehen. Neue Konfigurationen sollten ihn nicht mehr verwenden.

Allgemeine Profil-Dokumentation: [Schul-Profile](../SCHOOL_PROFILES.md).

Entwickler-API: [Schul-Profile entwickeln](../SCHOOL_PROFILES_DEVELOPMENT.md).

Schulspezifische Profile: [../schools/README.md](../schools/README.md).

Aktuell vorhanden:

- `kfg` – [Kaiserin-Friedrich-Gymnasium Bad Homburg](../schools/kfg/README.md)

## Ressourcen und Cache

Die Ressourcen werden versioniert unter `/api/sph/static/...` registriert. In 0.6.0 verwenden die Stundenplankarten `school-profile.js` und `substitution-adapter.js` mit Version `0.6.0`.

Die alten `school-hacks`-Dateien bleiben nur als Kompatibilitätsbrücke erhalten. Alte separate KFG-Kartentypen werden nicht mehr verwendet.

Nach einem Update:

1. Home Assistant neu starten,
2. Dashboard bzw. Browser-Cache neu laden.

Manuelle `/local/...`-Ressourceneinträge sind für aktuelle Home-Assistant-Versionen nicht erforderlich.
