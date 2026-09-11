// Kaiserin-Friedrich-Gymnasium: only school-specific settings live here.
export default {
  weekBadges: ["A", "B"],
  unbadgedFallback: true,
  teachers: { entity: "sensor.kfg_kollegium", attribute: "lehrer", descriptionLabels: ["lehrer", "lehrkraft", "verantwortlich"] },
  substitution: {
    classPrefix: "sensor.vertretungsplan_",
    fallback: "sensor.vertretungsplan",
    news: true,
    labels: {
      Betr: "Betreuung", Vertr: "Vertretung", Entf: "Entfall", Taus: "Tausch",
      Freis: "Freistunde", Raum: "Raumänderung", "Statt-Vertretung": "Statt-Vertretung",
      Paus: "Pausenaufsicht", SES: "Sonderunterricht", "Vtr. ohne Lehrer": "Vertretung ohne Lehrer"
    }
  }
};
