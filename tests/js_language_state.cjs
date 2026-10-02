const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const source = fs.readFileSync('web/i18n.js', 'utf8');
const i18next = require('../web/vendor/i18next/i18next-26.0.0.min.js');
const resources = {en:{translation:require('../web/locales/en.json')},de:{translation:require('../web/locales/de.json')}};

function page(url, {saved, disabledStorage = false, anchorTop = 100} = {}) {
  const storage = new Map(saved ? [['eea-language-state', saved]] : []);
  const events = {}, navigations = [], frames = [], scrolls = [];
  const anchors = [{getClientRects:()=>[{}],getBoundingClientRect:()=>({top:anchorTop})}];
  const links = ['de','en'].map(language => ({dataset:{language},addEventListener:(_,handler)=>{events[language]=handler;}}));
  const location = {href:url,protocol:'http:',assign:next=>navigations.push(next)};
  const window = {i18next, ATLAS_TRANSLATIONS:resources, location, scrollX:320, scrollY:900,
    scrollTo:position=>scrolls.push(position)};
  const document = {documentElement:{lang:new URL(url).searchParams.get('lang') || 'de'},
    querySelectorAll:selector=>selector==='[data-language]' ? links : anchors,
    addEventListener:(_,handler)=>{events.ready=handler;}};
  vm.runInNewContext(source, {window,document,location,URL,Date,fetch:()=>{},
    requestAnimationFrame:callback=>frames.push(callback), sessionStorage:{
      getItem:key=>{if(disabledStorage)throw Error('disabled');return storage.get(key);},
      setItem:(key,value)=>{if(disabledStorage)throw Error('disabled');storage.set(key,value);},
      removeItem:key=>storage.delete(key)}});
  function click(language, extra = {}) {
    let prevented = false;
    events[language]({button:0,preventDefault:()=>{prevented=true;},...extra});
    return prevented;
  }
  return {window,events,navigations,scrolls,storage,frames,anchors,click};
}

const url = 'http://127.0.0.1:8873/api.html?lang=en&year=2025#rules';
const first = page(url);
first.events.ready();
assert.equal(first.click('en'), true);
assert.equal(first.navigations.length, 0, 'The active language must not reload');
assert.equal(first.click('de', {ctrlKey:true}), false);
assert.equal(first.navigations.length, 0, 'Modified clicks must keep native link behaviour');
assert.equal(first.click('de'), true);
assert.equal(first.navigations[0], url.replace('lang=en','lang=de'));
const saved = first.storage.get('eea-language-state');
const second = page(first.navigations[0], {saved,anchorTop:250});
second.events.ready();
second.frames.forEach(callback=>callback());
assert.equal(second.scrolls[0].left, 320, 'Horizontal desktop navigation must survive');
assert.equal(second.scrolls[0].top, 1050, 'Translated content height must retain the visible section');
assert.equal(second.storage.size, 0, 'State must be consumed once');
assert.equal(second.window.AtlasI18n.restoreState(), null);

for (const record of [
  {...JSON.parse(saved), url:'http://127.0.0.1:8873/privacy.html?lang=de'},
  {...JSON.parse(saved), time:Date.now()-61000},
]) {
  const target = page(first.navigations[0], {saved:JSON.stringify(record)});
  target.events.ready();
  assert.equal(target.frames.length, 0, 'Unrelated or expired state must not restore');
}
const disabled = page(url, {disabledStorage:true});
disabled.events.ready();
disabled.click('de');
assert.equal(disabled.navigations.length, 1, 'Language navigation must work without storage');

const atlas = page(url);
atlas.window.AtlasI18n.captureState = () => ({countries:['DE','FR']});
atlas.events.ready();
atlas.click('de');
assert.deepEqual(JSON.parse(atlas.storage.get('eea-language-state')).state, {countries:['DE','FR']});
console.log('PASS language navigation, public viewport, translation reflow, one-shot state and disabled storage');
