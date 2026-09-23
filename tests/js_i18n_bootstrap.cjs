// Use the real, pinned translation engine in the existing lightweight DOM tests.
const i18next = require('../web/vendor/i18next/i18next-26.0.0.min.js');
const instance = i18next.createInstance();
instance.init({lng:'de', fallbackLng:'en', initImmediate:false,
  keySeparator:false, nsSeparator:false, interpolation:{escapeValue:false},
  resources:{de:{translation:require('../web/locales/de.json')}, en:{translation:require('../web/locales/en.json')}}});
window.AtlasI18n = {t:instance.t.bind(instance), locale:'de-DE', language:'de', apiFetch:global.fetch};
