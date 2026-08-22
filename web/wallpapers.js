(() => {
  "use strict";
  const OVERLOAD_STORAGE_KEY = "eea-europa-overload";
  const REACTION_STORAGE_KEY = "eea-europa-overload-reactions";

  function highResolutionImage(file) {
    return `https://commons.wikimedia.org/wiki/Special:Redirect/file/${encodeURIComponent(file)}?width=3840`;
  }

  const WALLPAPERS = Object.freeze([
    {title: "Akropolis bei Nacht", country: "Griechenland", file: "1029 Acropolis of Athens in Greece at night Photo by Giles Laurent.jpg", width: 8640, height: 5760, author: "Giles Laurent", license: "CC BY-SA 4.0"},
    {title: "Oia auf Santorin", country: "Griechenland", file: "Oia sunset - panoramio (2).jpg", width: 5202, height: 3465, author: "TomasEE", license: "CC BY 3.0"},
    {title: "Glencoe", country: "Vereinigtes Königreich", file: "GlencoeVillage.jpg", width: 4288, height: 2848, author: "Simonm72", license: "CC BY 3.0"},
    {title: "Kolosseum", country: "Italien", file: "Colosseo 2020.jpg", width: 12051, height: 8442, author: "FeaturedPics", license: "CC BY-SA 4.0"},
    {title: "Dolomiten bei Cortina", country: "Italien", file: "Faloria Cortina d'Ampezzo 10.jpg", width: 4340, height: 3000, author: "kallerna", license: "CC BY-SA 4.0"},
    {title: "Tower Bridge im Morgenlicht", country: "Vereinigtes Königreich", file: "Tower Bridge at Dawn.jpg", width: 5554, height: 3703, author: "Fuzzypiggy", license: "CC BY-SA 3.0"},
    {title: "Schloss Chambord", country: "Frankreich", file: "Aerial image of Château de Chambord (view from the southeast).jpg", width: 3600, height: 2700, author: "Carsten Steger", license: "CC BY-SA 4.0"},
    {title: "Klöster von Meteora", country: "Griechenland", file: "Meteora's monastery 2.jpg", width: 7360, height: 4912, author: "Stathis floros", license: "CC BY-SA 4.0"},
    {title: "Schloss Schönbrunn", country: "Österreich", file: "Wien - Schloss Schönbrunn.JPG", width: 5650, height: 3860, author: "C.Stadler/Bwag", license: "CC BY-SA 4.0"},
    {title: "Gamla Stan", country: "Schweden", file: "Gamla stan September 2014 01.jpg", width: 6016, height: 4016, author: "Arild Vågen", license: "CC BY-SA 4.0"},
    {title: "Dom von Florenz", country: "Italien", file: "Cattedrale di Santa Maria del Fiore – Il Duomo di Firenze.jpg", width: 3872, height: 2592, author: "Gary Campbell-Hall", license: "CC BY 2.0"},
    {title: "Schloss Neuschwanstein", country: "Deutschland", file: "Schloss Neuschwanstein 2013.jpg", width: 5979, height: 4468, author: "Thomas Wolf", license: "CC BY-SA 3.0 DE"},
    {title: "Lauterbrunnental", country: "Schweiz", file: "1 lauterbrunnen valley wengen 2022.jpg", width: 14077, height: 9464, author: "Chensiyuan", license: "CC BY-SA 4.0"},
    {title: "Hallstatt", country: "Österreich", file: "Hallstatt - Zentrum .JPG", width: 3937, height: 2717, author: "C.Stadler/Bwag", license: "CC BY-SA 4.0"},
    {title: "Cliffs of Moher", country: "Irland", file: "Cliffs-Of-Moher-OBriens-From-South.JPG", width: 4608, height: 3456, author: "Bjørn Christian Tørrissen", license: "CC BY-SA 3.0"},
    {title: "Schloss Bran", country: "Rumänien", file: "Castelul Bran2.jpg", width: 3791, height: 2516, author: "Dobre Cezar", license: "CC BY-SA 3.0 RO"},
    {title: "Karlsbrücke", country: "Tschechien", file: "Prague 07-2016 view from Lesser Town Tower of Charles Bridge img3.jpg", width: 4555, height: 3037, author: "A.Savin", license: "FAL"},
    {title: "Sächsische Schweiz", country: "Deutschland", file: "Lilienstein Saxon Switzerland.jpg", width: 4146, height: 2764, author: "Merops", license: "CC BY-SA 3.0"},
    {title: "Lofoten", country: "Norwegen", file: "Moskenes Reinebringen lub 2025-07-21 img09 Aussicht.jpg", width: 7952, height: 5304, author: "Lukas Beck", license: "CC BY 4.0"},
    {title: "Cinque Terre", country: "Italien", file: "Cinque Terre (Italy, October 2020) - 24 (50543603956).jpg", width: 5438, height: 3626, author: "Bruno Rijsman", license: "CC BY-SA 2.0"},
    {title: "Kloster Ostrog", country: "Montenegro", file: "Monasterio de Ostrog, Montenegro, 2014-04-14, DD 14.JPG", width: 5395, height: 3597, author: "Diego Delso", license: "CC BY-SA 3.0"},
    {title: "Geirangerfjord", country: "Norwegen", file: "Geirangerfjord .jpg", width: 7193, height: 4795, author: "Andreas Trepte", license: "CC BY-SA 2.5"},
    {title: "Nyhavn", country: "Dänemark", file: "The Nyhavn Canal 3.jpg", width: 5464, height: 3640, author: "Europäische Kommission", license: "CC BY 4.0"},
    {title: "Warschauer Königsschloss", country: "Polen", file: "Royal Castle in Warsaw, Poland, 2022, 03.jpg", width: 3741, height: 2806, author: "Chris Olszewski", license: "CC BY-SA 4.0"},
    {title: "Bleder See", country: "Slowenien", file: "Lake Bled from the Mountain.jpg", width: 4000, height: 3000, author: "Canadianhockey91", license: "CC BY-SA 3.0"},
    {title: "Altstadt von Riga", country: "Lettland", file: "Views from St. Peter's Church Spire, Riga 20180808-2.jpg", width: 5184, height: 3456, author: "Suicasmo", license: "CC BY-SA 4.0"},
    {title: "Wasserburg Trakai", country: "Litauen", file: "Trakai castle 2016.jpg", width: 4976, height: 3374, author: "Aleksandr Petukhov", license: "CC BY-SA 4.0"},
    {title: "Prinsengracht", country: "Niederlande", file: "Prinsengracht.jpg", width: 4608, height: 3072, author: "Kaz Alting", license: "CC BY-SA 3.0"},
    {title: "Brügge vom Belfried", country: "Belgien", file: "Brügge Blick vom Belfried 4.jpg", width: 4520, height: 2896, author: "Zairon", license: "CC BY-SA 4.0"},
    {title: "Château de Chillon am Genfersee", country: "Schweiz", file: "001 Chateau de Chillon and Dents du Midi Photo by Giles Laurent.jpg", width: 7952, height: 5304, author: "Giles Laurent", license: "CC BY-SA 4.0"},
    {title: "Burg Tropsztyn am Czchów-See", country: "Polen", file: "Tropsztyn Castle overlooking Czchów Lake, Wytrzyszczka, Lesser Poland Voivodeship, 20251025 0803 5046.jpg", width: 5858, height: 3885, author: "Jakub Hałun", license: "CC BY 4.0"},
    {title: "Dubrovnik aus der Festung", country: "Kroatien", file: "Casco viejo de Dubrovnik, Croacia, 2014-04-13, DD 18.JPG", width: 5225, height: 3385, author: "Diego Delso", license: "CC BY-SA 3.0"},
    {title: "Engelsburg in der Dämmerung", country: "Italien", file: "Castel Sant'Angelo at dusk, Rome, Italy.jpg", width: 4371, height: 2898, author: "Jebulon", license: "CC0"},
    {title: "Festung Bard", country: "Italien", file: "Castle of Bard (3).jpg", width: 5158, height: 3675, author: "Krzysztof Golik", license: "CC BY-SA 4.0"},
    {title: "Schloss Książ", country: "Polen", file: "Ksiaz - zamek 01.jpg", width: 8123, height: 5161, author: "Jar.ciurus", license: "CC BY-SA 3.0 PL"},
    {title: "Schloss Litomyšl", country: "Tschechien", file: "Litomyšl (Leitomischl) chateau - by Pudelek.jpg", width: 4074, height: 2622, author: "Pudelek", license: "CC BY-SA 4.0"},
    {title: "Muiderslot", country: "Niederlande", file: "Muiden, Muiderslot. 09-05-2022. (actm.) 07.jpg", width: 4908, height: 3362, author: "Agnes Monkelbaan", license: "CC BY-SA 4.0"},
    {title: "Ribblehead-Viadukt", country: "Vereinigtes Königreich", file: "2015 Ribblehead Viaduct 1.jpg", width: 4452, height: 2968, author: "Kreuzschnabel", license: "CC BY-SA 3.0"},
    {title: "Gavarnie-Tal in den Pyrenäen", country: "Frankreich", file: "2019 - Parc national des Pyrenees - Vallée de Gavarnie.jpg", width: 4493, height: 2995, author: "Moahim", license: "CC BY-SA 4.0"},
    {title: "Las Cañadas und Roques de García", country: "Spanien", file: "Caldera Las Cañadas mit Roques de García und TF-21.jpg", width: 5426, height: 3615, author: "Thomas Wolf", license: "CC BY-SA 3.0 DE"},
    {title: "Morgendämmerung über Sète", country: "Frankreich", file: "Dawn on Sète and the Étang de Thau.jpg", width: 4280, height: 2675, author: "Christian Ferrer", license: "CC BY-SA 3.0"},
    {title: "Monsanto im Morgenlicht", country: "Portugal", file: "Granite boulder formations near the Monsanto Castle at sunrise, Aldeia de Monsanto, Portugal (2) julesvernex2-3.jpg", width: 9254, height: 6021, author: "Jules Verne Times Two", license: "CC BY-SA 4.0"},
    {title: "Nyhavn im Sonnenuntergang", country: "Dänemark", file: "2018 - Nyhavn on sunset.jpg", width: 4040, height: 2620, author: "Moahim", license: "CC BY-SA 4.0"},
    {title: "Atrani an der Amalfiküste", country: "Italien", file: "Atrani (Costiera Amalfitana, 23-8-2011).jpg", width: 4200, height: 2790, author: "Paolo Costa Baldi", license: "GFDL"},
    {title: "Tallinn vom Domberg", country: "Estland", file: "Ayuntamiento, vistas panorámicas desde Toompea, Tallin, Estonia, 2012-08-05, DD 21.JPG", width: 4670, height: 2921, author: "Diego Delso", license: "CC BY-SA 3.0"},
    {title: "Bath vom Bathwick Hill", country: "Vereinigtes Königreich", file: "Bathwick Hill, Bath, Somerset, UK - Diliff.jpg", width: 4000, height: 2810, author: "Diliff", license: "CC BY-SA 3.0"},
    {title: "Canal Grande und Santa Maria della Salute", country: "Italien", file: "Canal Grande Chiesa della Salute e Dogana dal ponte dell Accademia.jpg", width: 7307, height: 4912, author: "Wolfgang Moroder", license: "GFDL"},
    {title: "Buitrago del Lozoya", country: "Spanien", file: "Buitrago del Lozoya - 04.jpg", width: 3888, height: 2592, author: "Carlos Delgado", license: "CC BY-SA 3.0"},
    {title: "Geirangerfjord vom Flydalsjuvet", country: "Norwegen", file: "Fiordo de Geiranger desde Flydalsjuvet, Noruega, 2019-09-07, DD 59.jpg", width: 7580, height: 5064, author: "Diego Delso", license: "CC BY-SA 4.0"},
    {title: "Doberaner Münster", country: "Deutschland", file: "Doberaner Münster, NW view, 2024-02-17.jpg", width: 4569, height: 3456, author: "Radomianin", license: "CC BY-SA 4.0"},
    {title: "Speyerer Dom in der Abendsonne", country: "Deutschland", file: "Speyer - Altstadt - Altpörtel - Blick auf Domfassade und Kirchtürme mit Abendsonne.jpg", width: 7649, height: 5222, author: "Roman Eisele", license: "CC BY-SA 4.0"},
    {title: "Abtei Fontenay", country: "Frankreich", file: "Abbaye Fontenay eglise facade.jpg", width: 4288, height: 2848, author: "Myrabella", license: "CC BY-SA 4.0"},
    {title: "Kathedrale von Le Mans", country: "Frankreich", file: "Le Mans - Cathedrale St Julien ext autumn.jpg", width: 4593, height: 3042, author: "Selbymay", license: "CC BY-SA 3.0"},
    {title: "Die beiden Dome von Brescia bei Nacht", country: "Italien", file: "Duomo vecchio e duomo nuovo notturna Brescia.jpg", width: 11702, height: 8355, author: "Wolfgang Moroder", license: "CC BY-SA 3.0"},
    {title: "Basilika San Francesco in Assisi", country: "Italien", file: "Rear NW Basilica Francesco Assisi Sep23 A7C 07913.jpg", width: 4136, height: 2757, author: "Timothy A. Gonsalves", license: "CC BY-SA 4.0"},
    {title: "Kathedrale von Segovia", country: "Spanien", file: "Catedral de Santa María de Segovia - 01.jpg", width: 4640, height: 3093, author: "Carlos Delgado", license: "CC BY-SA 3.0"},
    {title: "Sagrada Família", country: "Spanien", file: "Sagrada Familia March 2015-10a.jpg", width: 6249, height: 4698, author: "Alvesgaspar", license: "CC BY-SA 4.0"},
    {title: "Kirche am Steinhof", country: "Österreich", file: "20250503 Kirche am Steinhof 03.jpg", width: 5904, height: 3941, author: "Flocci Nivis", license: "CC BY-SA 4.0"},
    {title: "Stift Melk von Westen", country: "Österreich", file: "Stift Melk Westseite 01.jpg", width: 16065, height: 10383, author: "Uoaei1", license: "CC BY-SA 4.0"},
    {title: "Limburger Dom", country: "Deutschland", file: "Cathedral Limburg - Limburger Dom - October 26th 2013 - 06.jpg", width: 6466, height: 4315, author: "Norbert Nagel", license: "CC BY-SA 3.0"},
    {title: "Burg Niedzica", country: "Polen", file: "20170305 Niedzica zamek 5195.jpg", width: 4274, height: 2831, author: "Jakub Hałun", license: "CC BY-SA 4.0"},
    {title: "Bischofsburg Lidzbark Warmiński", country: "Polen", file: "Lidzbark Warmiński 2023 16 Grabowski Palace Castle.jpg", width: 4512, height: 3000, author: "Scotch Mist", license: "CC BY-SA 4.0"},
    {title: "Storkyrkan und Königliches Schloss", country: "Schweden", file: "Storkyrkan and Kungliga slottet Stockholm 2016 01.jpg", width: 4096, height: 2735, author: "Julian Herzog", license: "GFDL"},
    {title: "Schweriner Schloss", country: "Deutschland", file: "15-05-05-Schloß-Schwerin-RalfR-DSCF5191-2.jpg", width: 4736, height: 3158, author: "Ralf Roletschek", license: "GFDL 1.2"},
    {title: "Burg Eltz im Morgenlicht", country: "Deutschland", file: "Burg Eltz am frühen Morgen.jpg", width: 5307, height: 3462, author: "Johannes Dörrstock", license: "CC BY-SA 4.0"},
    {title: "Eilean Donan Castle", country: "Vereinigtes Königreich", file: "Eilean Donan castle - 95mm.jpg", width: 4188, height: 2792, author: "Eusebius", license: "CC BY 3.0"},
    {title: "Römerberg in Frankfurt", country: "Deutschland", file: "Römerberg Frankfurt abends.jpg", width: 4478, height: 2985, author: "Thomas Wolf", license: "CC BY-SA 3.0"},
    {title: "Seebrücke Sellin am Abend", country: "Deutschland", file: "Seebrücke Sellin abends.jpg", width: 5296, height: 3588, author: "Thomas Wolf", license: "CC BY-SA 3.0"},
    {title: "Neues Rathaus Hannover", country: "Deutschland", file: "Neues Rathaus Hannover abends.jpg", width: 5055, height: 3654, author: "Thomas Wolf", license: "CC BY-SA 3.0 DE"},
    {title: "Nokia Arena in Tampere", country: "Finnland", file: "Nokia Arena November 2021 5.jpg", width: 5340, height: 3575, author: "kallerna", license: "CC BY-SA 4.0"},
    {title: "Glockenturm der Kathedrale von Split", country: "Kroatien", file: "Split Cathedral Bell Tower From The Vestibule - Split.jpg", width: 6000, height: 4000, author: "Sumitsurai", license: "CC BY-SA 4.0"},
    {title: "Mariä-Himmelfahrt-Kathedrale in Varna", country: "Bulgarien", file: "Catedral de la Dormición de la Madre de Dios, Varna, Bulgaria, 2016-05-27, DD 109-111 HDR.jpg", width: 8135, height: 5628, author: "Diego Delso", license: "CC BY-SA 4.0"},
    {title: "Triumphbogen im Jubelpark", country: "Belgien", file: "Brussels Cinquantenaire R03.jpg", width: 3720, height: 2562, author: "Marc Ryckaert", license: "CC BY 3.0"},
    {title: "Arco da Rua Augusta in Lissabon", country: "Portugal", file: "Arco Triunfal da Rua Augusta, Plaza del Comercio, Lisboa, Portugal, 2012-05-12, DD 02.JPG", width: 4924, height: 3340, author: "Diego Delso", license: "CC BY-SA 3.0"},
    {title: "Jahrhunderthalle in Breslau", country: "Polen", file: "Wroclaw - Hala Stulecia 03.jpg", width: 4640, height: 3018, author: "Jar.ciurus", license: "CC BY-SA 3.0 PL"},
    {title: "Feuerwerk über dem Ponte Vecchio", country: "Italien", file: "Fireworks over Ponte Vecchio.JPG", width: 4719, height: 3122, author: "Martin Falbisoner", license: "CC BY-SA 3.0"},
    {title: "Elbphilharmonie und Hamburger Hafen", country: "Deutschland", file: "Hamburg, HafenCity, Elbphilharmonie -- 2016 -- 3062.jpg", width: 5472, height: 3648, author: "Dietmar Rabich", license: "CC BY-SA 4.0"},
    {title: "Atomium in Brüssel", country: "Belgien", file: "2017-10-17-bruessel-atomium-04.jpg", width: 5184, height: 3456, author: "Axel Kirch", license: "CC BY-SA 4.0"},
    {title: "Turning Torso in Malmö", country: "Schweden", file: "Malmö (S), Sekundarschule ProCivitas und Turning Torso -- 2017 -- 1655.jpg", width: 4705, height: 3137, author: "Dietmar Rabich", license: "CC BY-SA 4.0"},
    {title: "Öresundbrücke", country: "Dänemark / Schweden", file: "Øresund Bridge from the air in September 2015.jpg", width: 4000, height: 3000, author: "Nick-D", license: "CC BY-SA 4.0"},
    {title: "Frankfurter Altstadt und Skyline", country: "Deutschland", file: "Frankfurter Altstadt mit Skyline 2012-04.jpg", width: 3972, height: 2648, author: "Thomas Wolf", license: "CC BY-SA 3.0"},
    {title: "Frankfurter Skyline bei Nacht", country: "Deutschland", file: "Frankfurt Skyline 2022 bei Nacht.jpg", width: 6221, height: 4000, author: "Jörg Braukmann", license: "CC BY-SA 4.0"},
    {title: "Todi in Umbrien", country: "Italien", file: "Todi panorama.jpg", width: 5849, height: 3697, author: "Livioandronico2013", license: "CC BY-SA 4.0"},
    {title: "Bitola und die Pelagonische Ebene", country: "Nordmazedonien", file: "Битола и Пелагонија од Националниот парк Пелистер.jpg", width: 4927, height: 3263, author: "Шпиц", license: "CC BY-SA 4.0"},
    {title: "Tübinger Neckarfront", country: "Deutschland", file: "Tübingen - Altstadt - Neckarfront - Ansicht von Neckarinsel mit Stocherkahn.jpg", width: 7287, height: 4796, author: "Roman Eisele", license: "CC BY-SA 4.0"},
    {title: "Berlin vom Großen Stern", country: "Deutschland", file: "Siegessaeule Aussicht 10-13 img4 Tiergarten.jpg", width: 5184, height: 3456, author: "A.Savin", license: "CC BY-SA 3.0"},
    {title: "Abteikirche Saint-Ouen in Rouen", country: "Frankreich", file: "Panorama of Abbatiale Saint-Ouen (30268716114).jpg", width: 6107, height: 4649, author: "Jorge Láscar", license: "CC BY 2.0"},
    {title: "Westminster-Palast im Panorama", country: "Vereinigtes Königreich", file: "Palace-of-westminster-panorama-3.jpeg", width: 5828, height: 3975, author: "Rob.ng15", license: "CC BY 3.0"},
    {title: "Viadukt von Millau und Tarn-Tal", country: "Frankreich", file: "Panorama de la vallée de Millau.jpg", width: 5994, height: 3781, author: "Tobi 87", license: "CC BY-SA 3.0"},
    {title: "Rila-Kloster im Gebirgspanorama", country: "Bulgarien", file: "Рилски манастир Panorama.jpg", width: 5669, height: 3670, author: "CHILIEV", license: "CC BY-SA 4.0"},
    {title: "Torre de Belém", country: "Portugal", file: "Torre de Belém por Rodrigo Tetsuo Argenton (4).jpg", width: 6000, height: 4000, author: "Rodrigo Tetsuo Argenton", license: "CC BY-SA 4.0"},
    {title: "Stockholmer Rathaus am Wasser", country: "Schweden", file: "Stockholm Sweden Stadshuset-01.jpg", width: 4813, height: 3209, author: "CEphoto, Uwe Aranas", license: "CC BY-SA 4.0"},
    {title: "Schwarzhäupterhaus und Petrikirche", country: "Lettland", file: "House of Blackheads and St. Peter's Church Tower, Riga, Latvia - Diliff.jpg", width: 7000, height: 4922, author: "Diliff", license: "CC BY-SA 3.0"},
    {title: "Drei Brücken und Prešerenplatz", country: "Slowenien", file: "Triple Bridge and Preseren Square fron the Ljubljanica.jpg", width: 5184, height: 3456, author: "Valerio2468", license: "CC BY-SA 4.0"},
    {title: "Dom des Heiligen Sava", country: "Serbien", file: "Temple of Saint Sava (Crkva Svetog Save, Beograd).jpg", width: 5216, height: 3601, author: "Petar Milošević", license: "CC BY-SA 4.0"},
    {title: "Nidarosdom in Trondheim", country: "Norwegen", file: "Trondheim Nidarosdom Fassade 12.JPG", width: 3444, height: 2586, author: "Zairon", license: "CC BY-SA 3.0"},
    {title: "Adolphe-Brücke · Ansicht 1", country: "Luxemburg", file: "Adolphe Bridge in 2019.01.jpg", width: 4032, height: 3024, author: "CAPTAIN RAJU", license: "CC BY-SA 4.0"},
    {title: "Burg Bratislava · Ansicht 1", country: "Slowakei", file: "20230501.Ansicht von Bratislava.-040.jpg", width: 9248, height: 6936, author: "Bybbisch94, Christian Gebhardt", license: "CC BY-SA 4.0"},
    {title: "Ungarisches Parlament · Ansicht 1", country: "Ungarn", file: "Budapest, Kossuth Lajos tér, Országház, Parlament, 13.jpg", width: 4160, height: 3120, author: "Random photos 1989", license: "CC BY-SA 4.0"},
    {title: "Tallinner Rathaus · Ansicht 1", country: "Estland", file: "07-06-21-tallinn-by-RalfR-025.jpg", width: 3920, height: 3228, author: "Ralf Roletschek", license: "FAL"},
    {title: "Dom von Helsinki · Ansicht 1", country: "Finnland", file: "Helsingin Tuomiokirkko ja Senaatintori - D671 - hkm.HKMS000005-km002mzm.jpg", width: 3543, height: 2578, author: "SKY-FOTO Möller", license: "CC BY 4.0"},
    {title: "Trinity College Dublin · Ansicht 1", country: "Irland", file: "Dublin - Trinity College Dublin - 20150315204112.jpg", width: 5184, height: 3456, author: "Dieglop", license: "CC BY-SA 4.0"},
    {title: "Wasserburg Trakai · Ansicht 1", country: "Litauen", file: "Trakai 15.jpg", width: 5472, height: 3648, author: "FrDr", license: "CC BY-SA 4.0"},
    {title: "Adolphe-Brücke · Ansicht 2", country: "Luxemburg", file: "Adolphe Bridge in 2019.02.jpg", width: 4032, height: 3024, author: "CAPTAIN RAJU", license: "CC BY-SA 4.0"},
    {title: "Kloster Ostrog · Ansicht 1", country: "Montenegro", file: "E17 - Manastir Ostrog.jpg", width: 6000, height: 4000, author: "Misa.stefanovic.07", license: "CC BY-SA 4.0"},
    {title: "Steinbrücke in Skopje · Ansicht 1", country: "Nordmazedonien", file: "03 Skopje.jpg", width: 4608, height: 3456, author: "Делфина", license: "CC BY-SA 3.0"},
    {title: "Schloss Peleș · Ansicht 1", country: "Rumänien", file: "\u0022Castelul Peles\u0022.JPG", width: 4608, height: 3456, author: "Bejan Neculai", license: "CC BY-SA 4.0"},
    {title: "Dom des Heiligen Sava · Ansicht 1", country: "Serbien", file: "Belgrado, chiesa di San Sava 01.jpg", width: 4190, height: 3143, author: "Syrio", license: "CC BY-SA 4.0"},
    {title: "Burg Bratislava · Ansicht 2", country: "Slowakei", file: "20230501.Ansicht von Bratislava.-066.jpg", width: 6123, height: 6857, author: "Bybbisch94, Christian Gebhardt", license: "CC BY-SA 4.0"},
    {title: "Ungarisches Parlament · Ansicht 2", country: "Ungarn", file: "Budapest, Kossuth Lajos tér, Országház, Parlament, 14.jpg", width: 4160, height: 3120, author: "Random photos 1989", license: "CC BY-SA 4.0"},
    {title: "Alexander-Newski-Kathedrale · Ansicht 1", country: "Bulgarien", file: "Nevski Cathedral (15842207544).jpg", width: 5781, height: 3844, author: "Francisco Anzola", license: "CC BY 2.0"},
    {title: "Nyhavn in Kopenhagen · Ansicht 1", country: "Dänemark", file: "20200327 KBH Nyhavn 3 50A3944 (49720348422).jpg", width: 5760, height: 3840, author: "News Oresund", license: "CC BY 2.0"},
    {title: "Tallinner Rathaus · Ansicht 2", country: "Estland", file: "At Tallinn 2024 052.jpg", width: 6960, height: 4640, author: "Photograph by Mike Peel (www.mikepeel.net).", license: "CC BY-SA 4.0"},
    {title: "Dom von Helsinki · Ansicht 2", country: "Finnland", file: "Helsingin Tuomiokirkko ja Senaatintori - D672 - hkm.HKMS000005-km002mzn.jpg", width: 3543, height: 2625, author: "SKY-FOTO Möller", license: "CC BY 4.0"},
    {title: "Trinity College Dublin · Ansicht 2", country: "Irland", file: "Dublin - Trinity College Dublin - 20170825165318.jpg", width: 5869, height: 3913, author: "Oliver Gargan", license: "CC BY-SA 4.0"},
    {title: "Stadtmauern von Dubrovnik · Ansicht 1", country: "Kroatien", file: "29.12.16 Dubrovnik Evening 21 (31847480831).jpg", width: 5472, height: 3648, author: "donald judge", license: "CC BY 2.0"},
    {title: "Schwarzhäupterhaus in Riga · Ansicht 1", country: "Lettland", file: "House of Blackheads (Riga) 20180808.jpg", width: 5184, height: 3456, author: "Suicasmo", license: "CC BY-SA 4.0"},
    {title: "Wasserburg Trakai · Ansicht 2", country: "Litauen", file: "Trakai 16.jpg", width: 5472, height: 3648, author: "FrDr", license: "CC BY-SA 4.0"},
    {title: "Adolphe-Brücke · Ansicht 3", country: "Luxemburg", file: "Adolphe Bridge in 2019.03.jpg", width: 4032, height: 3024, author: "CAPTAIN RAJU", license: "CC BY-SA 4.0"},
    {title: "Kloster Ostrog · Ansicht 2", country: "Montenegro", file: "EXH21 - Manastir Ostrog.jpg", width: 6000, height: 4000, author: "Misa.stefanovic.07", license: "CC BY-SA 4.0"},
    {title: "Steinbrücke in Skopje · Ansicht 2", country: "Nordmazedonien", file: "04 Skopje.jpg", width: 4608, height: 3456, author: "Делфина", license: "CC BY-SA 3.0"},
    {title: "Schloss Peleș · Ansicht 2", country: "Rumänien", file: "20140628 Peleş Castle 01.jpg", width: 3968, height: 2976, author: "Mark Ahsmann", license: "CC BY-SA 4.0"},
    {title: "Kapellbrücke in Luzern · Ansicht 1", country: "Schweiz", file: "20240906.Ansichten von Luzern.-016.1.jpg", width: 8841, height: 6631, author: "Bybbisch94", license: "CC BY 4.0"},
    {title: "Dom des Heiligen Sava · Ansicht 2", country: "Serbien", file: "Belgrado, chiesa di San Sava 02.jpg", width: 4608, height: 3456, author: "Syrio", license: "CC BY-SA 4.0"},
    {title: "Burg Bratislava · Ansicht 3", country: "Slowakei", file: "Bratislava Castle (51857416231).jpg", width: 6166, height: 4111, author: "Radek Kucharski from Warsaw, Poland", license: "CC BY 2.0"},
    {title: "Bleder Insel · Ansicht 1", country: "Slowenien", file: "Bled (49480708878).jpg", width: 8800, height: 5867, author: "bmw3528", license: "CC BY 2.0"},
    {title: "Prager Burg · Ansicht 1", country: "Tschechien", file: "13-03-30-praha-by-RalfR-206.jpg", width: 4288, height: 2848, author: "Ralf Roletschek", license: "FAL"},
    {title: "Ungarisches Parlament · Ansicht 3", country: "Ungarn", file: "Budapest, Kossuth Lajos tér, Országház, Parlament, 3.jpg", width: 4096, height: 3072, author: "Random photos 1989", license: "CC BY-SA 4.0"},
    {title: "Grand-Place in Brüssel · Ansicht 1", country: "Belgien", file: "06 2023 Grand Place (Brussels) IMG 7557.jpg", width: 5790, height: 3703, author: "Alexander-93", license: "CC BY-SA 4.0"},
    {title: "Alexander-Newski-Kathedrale · Ansicht 2", country: "Bulgarien", file: "Sofia Alexander Nevsky Cathedral 04.jpg", width: 4048, height: 4544, author: "Ad Meskens", license: "CC BY-SA 4.0"},
    {title: "Nyhavn in Kopenhagen · Ansicht 2", country: "Dänemark", file: "20200327 KBH Nyhavn 50A3948 (49720348327).jpg", width: 5760, height: 3840, author: "News Oresund", license: "CC BY 2.0"},
    {title: "Tallinner Rathaus · Ansicht 3", country: "Estland", file: "At Tallinn 2024 056.jpg", width: 6168, height: 4640, author: "Photograph by Mike Peel (www.mikepeel.net).", license: "CC BY-SA 4.0"},
    {title: "Dom von Helsinki · Ansicht 3", country: "Finnland", file: "Senaatintori - XLVIII-1631 - hkm.HKMS000005-km0000mnh7.jpg", width: 5317, height: 3876, author: "Unknown authorUnknown author", license: "CC BY 4.0"},
    {title: "Parthenon in Athen · Ansicht 1", country: "Griechenland", file: "1010 Parthenon of the Acropolis of Athens Photo by Giles Laurent.jpg", width: 8640, height: 5760, author: "Giles Laurent", license: "CC BY-SA 4.0"},
    {title: "Trinity College Dublin · Ansicht 3", country: "Irland", file: "Dublin - Trinity College Dublin - 20211204175408.jpg", width: 4032, height: 3024, author: "Dieglop", license: "CC BY-SA 4.0"},
    {title: "Stadtmauern von Dubrovnik · Ansicht 2", country: "Kroatien", file: "29.12.16 Dubrovnik Evening 28 (31847688211).jpg", width: 5472, height: 3648, author: "donald judge", license: "CC BY 2.0"},
    {title: "Schwarzhäupterhaus in Riga · Ansicht 2", country: "Lettland", file: "House of Blackheads in Riga (1).JPG", width: 4608, height: 3456, author: "Avi1111 dr. avishai teicher", license: "CC BY-SA 3.0"},
    {title: "Wasserburg Trakai · Ansicht 3", country: "Litauen", file: "Trakai 21.jpg", width: 5472, height: 3648, author: "FrDr", license: "CC BY-SA 4.0"},
    {title: "Adolphe-Brücke · Ansicht 4", country: "Luxemburg", file: "Adolphe Bridge in 2019.04.jpg", width: 4032, height: 3024, author: "CAPTAIN RAJU", license: "CC BY-SA 4.0"},
    {title: "Kloster Ostrog · Ansicht 3", country: "Montenegro", file: "Manastir Ostrog - panoramio (1).jpg", width: 6000, height: 4000, author: "Dragan Jankovic Faza…", license: "CC BY-SA 3.0"},
    {title: "Steinbrücke in Skopje · Ansicht 3", country: "Nordmazedonien", file: "05 Skopje.JPG", width: 4608, height: 3456, author: "Делфина", license: "CC BY-SA 3.0"},
    {title: "Torre de Belém · Ansicht 1", country: "Portugal", file: "Belém Tower and the 25 de Abril Bridge in the background.jpg", width: 6763, height: 4510, author: "Lisbon Photoshoots", license: "CC BY-SA 4.0"},
    {title: "Schloss Peleș · Ansicht 3", country: "Rumänien", file: "Ansamblul Castelului Peleș, oraș Sinaia.jpg", width: 4032, height: 3024, author: "Prymasal", license: "CC BY-SA 4.0"},
    {title: "Kapellbrücke in Luzern · Ansicht 2", country: "Schweiz", file: "20240906.Ansichten von Luzern.-016.2.jpg", width: 9248, height: 6936, author: "Bybbisch94", license: "CC BY 4.0"},
    {title: "Dom des Heiligen Sava · Ansicht 3", country: "Serbien", file: "Belgrado, tempio e chiesa di San Sava.jpg", width: 4280, height: 3210, author: "Syrio", license: "CC BY-SA 4.0"},
    {title: "Burg Bratislava · Ansicht 4", country: "Slowakei", file: "Bratislava-Old Town, Slovakia - panoramio (153).jpg", width: 6016, height: 4016, author: "Андрей Бобровский", license: "CC BY 3.0"},
    {title: "Bleder Insel · Ansicht 2", country: "Slowenien", file: "Bled Island (53953798046).jpg", width: 5184, height: 3888, author: "David Blaikie from Hampshire, UK", license: "CC BY 2.0"},
    {title: "Prager Burg · Ansicht 2", country: "Tschechien", file: "19.7.16 Prague Castle 16 (27811781254).jpg", width: 6016, height: 4000, author: "donald judge", license: "CC BY 2.0"},
    {title: "Ungarisches Parlament · Ansicht 4", country: "Ungarn", file: "Budapest, Kossuth Lajos tér, Országház, Parlament, 4.jpg", width: 4096, height: 3072, author: "Random photos 1989", license: "CC BY-SA 4.0"},
    {title: "Grand-Place in Brüssel · Ansicht 2", country: "Belgien", file: "Bruxelles - Grand-Place (32427731957).jpg", width: 5184, height: 3456, author: "Fred Romero from Paris, France", license: "CC BY 2.0"},
    {title: "Alexander-Newski-Kathedrale · Ansicht 3", country: "Bulgarien", file: "Sofia Alexander Nevsky Cathedral 05.jpg", width: 4088, height: 4208, author: "Ad Meskens", license: "CC BY-SA 4.0"},
    {title: "Nyhavn in Kopenhagen · Ansicht 3", country: "Dänemark", file: "20211706 Nyhavn EN 750A7163 (51254144840).jpg", width: 5760, height: 3840, author: "News Oresund", license: "CC BY 2.0"},
    {title: "Tallinner Rathaus · Ansicht 4", country: "Estland", file: "Plaza del ayuntamiento, Tallinn, Estonia, 2012-08-05, DD 01.JPG", width: 5151, height: 3529, author: "Diego Delso", license: "CC BY-SA 3.0"},
    {title: "Dom von Helsinki · Ansicht 4", country: "Finnland", file: "Snellmaninaukio. Snellmaninkatu 6, Kirkkokatu 16. - Helsinki 1950 -luku - D7122 - hkm.HKMS000005-km0000n71f.jpg", width: 4584, height: 3032, author: "Arvo Kajantie", license: "CC BY 4.0"},
    {title: "Parthenon in Athen · Ansicht 2", country: "Griechenland", file: "1026 Parthenon of the Acropolis of Athens Photo by Giles Laurent.jpg", width: 8640, height: 5760, author: "Giles Laurent", license: "CC BY-SA 4.0"},
    {title: "Trinity College Dublin · Ansicht 4", country: "Irland", file: "Dublin - Trinity College Dublin - 20220729121524.jpg", width: 4032, height: 3024, author: "Jonjobaker", license: "CC BY-SA 4.0"},
    {title: "Stadtmauern von Dubrovnik · Ansicht 3", country: "Kroatien", file: "29.12.16 Dubrovnik Old City Walls 020 (31960183875).jpg", width: 5472, height: 3648, author: "donald judge", license: "CC BY 2.0"},
    {title: "Schwarzhäupterhaus in Riga · Ansicht 3", country: "Lettland", file: "House of Blackheads Riga Latvia.jpg", width: 5485, height: 3587, author: "Ksenija Vinogradova", license: "CC BY-SA 4.0"},
    {title: "Wasserburg Trakai · Ansicht 4", country: "Litauen", file: "Trakai 22.jpg", width: 5472, height: 3648, author: "FrDr", license: "CC BY-SA 4.0"},
    {title: "Adolphe-Brücke · Ansicht 5", country: "Luxemburg", file: "Adolphe Bridge in Luxembourg.jpg", width: 4096, height: 3072, author: "Tunegravity", license: "CC0"},
    {title: "Kloster Ostrog · Ansicht 4", country: "Montenegro", file: "Manastir Ostrog - panoramio.jpg", width: 6000, height: 4000, author: "Dragan Jankovic Faza…", license: "CC BY-SA 3.0"},
    {title: "Steinbrücke in Skopje · Ansicht 4", country: "Nordmazedonien", file: "06 Skopje.jpg", width: 4608, height: 3456, author: "Делфина", license: "CC BY-SA 3.0"},
    {title: "Nidarosdom in Trondheim · Ansicht 1", country: "Norwegen", file: "Nidarosdomen 85130 2024-2.jpg", width: 8007, height: 6187, author: "Bjørn Erik Pedersen", license: "CC BY-SA 4.0"},
    {title: "Schloss Schönbrunn · Ansicht 1", country: "Österreich", file: "20190206 Schönbrunn 5118 (47460588212).jpg", width: 7952, height: 5304, author: "Ray Swi-hymn from Sijhih-Taipei, Taiwan", license: "CC BY-SA 2.0"},
    {title: "Torre de Belém · Ansicht 2", country: "Portugal", file: "Monastery of the Hieronymites and Tower of Belém 26 (42670757985).jpg", width: 5184, height: 3888, author: "Kyle Magnuson from Los Angeles, United States", license: "CC BY 2.0"},
    {title: "Schloss Peleș · Ansicht 4", country: "Rumänien", file: "Castello di Peleș.jpg", width: 6000, height: 4000, author: "Anto.cast", license: "CC BY 4.0"},
    {title: "Stockholmer Rathaus · Ansicht 1", country: "Schweden", file: "20180624 Stadshus 6969 (48412243881).jpg", width: 7952, height: 5304, author: "Ray Swi-hymn from Sijhih-Taipei, Taiwan", license: "CC BY-SA 2.0"},
    {title: "Kapellbrücke in Luzern · Ansicht 3", country: "Schweiz", file: "20240906.Ansichten von Luzern.-016.3.jpg", width: 9248, height: 6936, author: "Bybbisch94", license: "CC BY 4.0"},
    {title: "Dom des Heiligen Sava · Ansicht 4", country: "Serbien", file: "Beograd Crkva Svetog Save sa ulice.jpg", width: 3462, height: 2530, author: "Ivanpancic", license: "CC BY-SA 4.0"},
    {title: "Burg Bratislava · Ansicht 5", country: "Slowakei", file: "Bratislava-Old Town, Slovakia - panoramio (156).jpg", width: 6016, height: 4016, author: "Андрей Бобровский", license: "CC BY 3.0"},
    {title: "Bleder Insel · Ansicht 3", country: "Slowenien", file: "BLEDSKI OTOK 2021.jpg", width: 5152, height: 3864, author: "August Dominus", license: "CC BY-SA 4.0"},
    {title: "Sagrada Família · Ansicht 1", country: "Spanien", file: "Sagrada Família (51970333757).jpg", width: 4032, height: 3024, author: "Chris Yunker from St. Louis, United States", license: "CC BY 2.0"},
    {title: "Prager Burg · Ansicht 3", country: "Tschechien", file: "2018-08-15 CZ Praha 01, Pražský hrad (50116668027).jpg", width: 5976, height: 3736, author: "Paul Korecky", license: "CC BY-SA 2.0"},
    {title: "Ungarisches Parlament · Ansicht 5", country: "Ungarn", file: "Budapest, Kossuth Lajos tér, Országház, Parlament, 6.jpg", width: 4160, height: 3120, author: "Random photos 1989", license: "CC BY-SA 4.0"},
    {title: "Grand-Place in Brüssel · Ansicht 3", country: "Belgien", file: "Bruxelles - Grand-Place (32427732307).jpg", width: 5184, height: 3456, author: "Fred Romero from Paris, France", license: "CC BY 2.0"},
    {title: "Alexander-Newski-Kathedrale · Ansicht 4", country: "Bulgarien", file: "Sofia Alexander Nevsky Cathedral 08.jpg", width: 5347, height: 3670, author: "Ad Meskens", license: "CC BY-SA 4.0"},
    {title: "Nyhavn in Kopenhagen · Ansicht 4", country: "Dänemark", file: "2026-07-27-Nyhavn-060661.jpg", width: 6000, height: 4000, author: "Superbass", license: "CC BY-SA 4.0"},
    {title: "Tallinner Rathaus · Ansicht 5", country: "Estland", file: "Plaza del ayuntamiento, Tallinn, Estonia, 2012-08-05, DD 02.JPG", width: 4857, height: 3361, author: "Diego Delso", license: "CC BY-SA 3.0"},
    {title: "Dom von Helsinki · Ansicht 5", country: "Finnland", file: "Sofiankatu Helsinki.jpg", width: 5152, height: 3864, author: "Mikkoau", license: "CC BY-SA 4.0"},
    {title: "Parthenon in Athen · Ansicht 3", country: "Griechenland", file: "East steps of the Parthenon.jpg", width: 4096, height: 3072, author: "Twospoonfuls", license: "CC BY-SA 4.0"},
    {title: "Trinity College Dublin · Ansicht 5", country: "Irland", file: "Dublin - Trinity College Dublin - 2024-09-27 14-39-00 001.jpg", width: 3556, height: 2667, author: "Ste.photos03", license: "CC BY-SA 4.0"},
    {title: "Stadtmauern von Dubrovnik · Ansicht 4", country: "Kroatien", file: "29.12.16 Dubrovnik Old City Walls 030 (31843774401).jpg", width: 5472, height: 3648, author: "donald judge", license: "CC BY 2.0"},
    {title: "Schwarzhäupterhaus in Riga · Ansicht 4", country: "Lettland", file: "House of the Blackheads - panoramio.jpg", width: 5196, height: 3457, author: "TomasEE", license: "CC BY 3.0"},
    {title: "Wasserburg Trakai · Ansicht 5", country: "Litauen", file: "Trakai 23.jpg", width: 5472, height: 3648, author: "FrDr", license: "CC BY-SA 4.0"},
    {title: "Adolphe-Brücke · Ansicht 6", country: "Luxemburg", file: "Adolphe Bridge over the valley of Petrusse in Luxembourg City.jpg", width: 6000, height: 4000, author: "Krzysztof Golik", license: "CC BY-SA 4.0"},
    {title: "Kloster Ostrog · Ansicht 5", country: "Montenegro", file: "Monasterio de Ostrog, Montenegro, 2014-04-14, DD 13.JPG", width: 5025, height: 3539, author: "Diego Delso", license: "CC BY-SA 3.0"},
    {title: "Steinbrücke in Skopje · Ansicht 5", country: "Nordmazedonien", file: "Macedonia-02809 - Stone Bridge.jpg", width: 6000, height: 4000, author: "Dennis G. Jarvis", license: "CC BY-SA 2.0"},
    {title: "Nidarosdom in Trondheim · Ansicht 2", country: "Norwegen", file: "Nidarosdomen 85130 2024-5.jpg", width: 8200, height: 6336, author: "Bjørn Erik Pedersen", license: "CC BY-SA 4.0"},
    {title: "Schloss Schönbrunn · Ansicht 2", country: "Österreich", file: "20190206 Schönbrunn 5153 (40547358523).jpg", width: 7952, height: 5304, author: "Ray Swi-hymn from Sijhih-Taipei, Taiwan", license: "CC BY-SA 2.0"},
    {title: "Torre de Belém · Ansicht 3", country: "Portugal", file: "Padrao e Torre Belem Alinhados no final de dia FJMC9721.jpg", width: 5240, height: 3493, author: "Costajosemanuel", license: "CC BY-SA 4.0"},
    {title: "Schloss Peleș · Ansicht 5", country: "Rumänien", file: "Castelul Peles - alb negru.jpg", width: 5120, height: 3840, author: "DanielValahul", license: "CC BY-SA 4.0"},
    {title: "Stockholmer Rathaus · Ansicht 2", country: "Schweden", file: "20180624 Stadshus 6970 (48412392437).jpg", width: 7952, height: 5304, author: "Ray Swi-hymn from Sijhih-Taipei, Taiwan", license: "CC BY-SA 2.0"},
    {title: "Kapellbrücke in Luzern · Ansicht 4", country: "Schweiz", file: "20240906.Ansichten von Luzern.-016.4.jpg", width: 9248, height: 6936, author: "Bybbisch94", license: "CC BY 4.0"},
    {title: "Dom des Heiligen Sava · Ansicht 5", country: "Serbien", file: "Beograd Crkva Svetog Save unutrašnjost sa lusterom.jpg", width: 4068, height: 2712, author: "Ivanpancic", license: "CC BY-SA 4.0"},
    {title: "Burg Bratislava · Ansicht 6", country: "Slowakei", file: "Bratislava, hrad, areál 03.jpg", width: 8000, height: 6000, author: "Aktron", license: "CC BY-SA 4.0"},
    {title: "Bleder Insel · Ansicht 4", country: "Slowenien", file: "Bledski otok prosinca 2021.jpg", width: 5152, height: 3864, author: "August Dominus", license: "CC BY-SA 4.0"},
    {title: "Sagrada Família · Ansicht 2", country: "Spanien", file: "Sagrada Família (51971900540).jpg", width: 4032, height: 3024, author: "Chris Yunker from St. Louis, United States", license: "CC BY 2.0"},
    {title: "Prager Burg · Ansicht 4", country: "Tschechien", file: "2018-08-17 CZ Praha 01, Pražský hrad (50291028342).jpg", width: 4932, height: 3699, author: "Paul Korecky", license: "CC BY-SA 2.0"},
    {title: "Ungarisches Parlament · Ansicht 6", country: "Ungarn", file: "Budapest, Kossuth Lajos tér, Országház, Parlament, 7.jpg", width: 4096, height: 3072, author: "Random photos 1989", license: "CC BY-SA 4.0"},
    {title: "Grand-Place in Brüssel · Ansicht 4", country: "Belgien", file: "Bruxelles - Grand-Place (33493256988).jpg", width: 5184, height: 3456, author: "Fred Romero from Paris, France", license: "CC BY 2.0"},
    {title: "Alexander-Newski-Kathedrale · Ansicht 5", country: "Bulgarien", file: "St. Alexander Nevsky Cathedral.png", width: 5206, height: 3793, author: "EverlastingStar", license: "CC BY-SA 4.0"},
    {title: "Nyhavn in Kopenhagen · Ansicht 5", country: "Dänemark", file: "2026-07-27-Nyhavn-060688.jpg", width: 6000, height: 4000, author: "Superbass", license: "CC BY-SA 4.0"},
    {title: "Tallinner Rathaus · Ansicht 6", country: "Estland", file: "Plaza del ayuntamiento, Tallinn, Estonia, 2012-08-05, DD 14.JPG", width: 4923, height: 3423, author: "Diego Delso", license: "CC BY-SA 3.0"},
    {title: "Parthenon in Athen · Ansicht 4", country: "Griechenland", file: "Parthénon - Athènes (GRA1) - 2022-03-26 - 14.jpg", width: 4032, height: 3024, author: "Chabe01", license: "CC BY-SA 4.0"},
    {title: "Trinity College Dublin · Ansicht 6", country: "Irland", file: "Dublin - Trinity College Dublin.jpeg", width: 4032, height: 3024, author: "Thoslee", license: "CC BY-SA 4.0"},
    {title: "Stadtmauern von Dubrovnik · Ansicht 5", country: "Kroatien", file: "29.12.16 Dubrovnik Old City Walls 034 (31923622576).jpg", width: 5472, height: 3648, author: "donald judge", license: "CC BY 2.0"},
    {title: "Schwarzhäupterhaus in Riga · Ansicht 5", country: "Lettland", file: "House of the Blackheads - Riga’s Town Hall Square (23075737683).jpg", width: 5520, height: 3680, author: "Jorge Láscar from Melbourne, Australia", license: "CC BY 2.0"},
    {title: "Wasserburg Trakai · Ansicht 6", country: "Litauen", file: "Trakai castle view.jpg", width: 6582, height: 4407, author: "Mattias Hill", license: "CC BY-SA 4.0"},
    {title: "Adolphe-Brücke · Ansicht 7", country: "Luxemburg", file: "Adolphe-Brücke, Luxemburg - Flickr - Klaus Wessel.jpg", width: 5511, height: 3674, author: "Klaus Wessel", license: "CC BY 2.0"},
    {title: "Kloster Ostrog · Ansicht 6", country: "Montenegro", file: "Montenegro Ostrog monastery.JPG", width: 4320, height: 3240, author: "Dickelbers", license: "CC BY-SA 3.0"},
    {title: "Steinbrücke in Skopje · Ansicht 6", country: "Nordmazedonien", file: "Skopje capital of The Republic of Macedonia (16298504251).jpg", width: 4608, height: 3456, author: "Clay Gilliland from Chandler, U.S.A.", license: "CC BY-SA 2.0"},
    {title: "Nidarosdom in Trondheim · Ansicht 3", country: "Norwegen", file: "Nidarosdomen Trondheim 2022-08-18 01.jpg", width: 8384, height: 5612, author: "Leonhard Lenz", license: "CC0"},
    {title: "Schloss Schönbrunn · Ansicht 3", country: "Österreich", file: "20190206 SchönbrunnSchloss 5149 (33636656648).jpg", width: 7952, height: 5304, author: "Ray Swi-hymn from Sijhih-Taipei, Taiwan", license: "CC BY-SA 2.0"},
    {title: "Wawel in Krakau · Ansicht 1", country: "Polen", file: "02022 0371 Wawel Castle.jpg", width: 4110, height: 2633, author: "Silar", license: "CC BY-SA 4.0"},
    {title: "Torre de Belém · Ansicht 4", country: "Portugal", file: "Portugal, Lisbon, Belem Tower (52593881361).jpg", width: 5023, height: 3147, author: "Lark Ascending", license: "Public domain"},
    {title: "Schloss Peleș · Ansicht 6", country: "Rumänien", file: "Castelul Peleș din Sinaia 07.jpg", width: 3968, height: 2976, author: "Nicubunu", license: "CC BY-SA 4.0"},
    {title: "Stockholmer Rathaus · Ansicht 3", country: "Schweden", file: "20180624 Stadshus 6973 (48412239801).jpg", width: 7952, height: 5304, author: "Ray Swi-hymn from Sijhih-Taipei, Taiwan", license: "CC BY-SA 2.0"},
    {title: "Kapellbrücke in Luzern · Ansicht 5", country: "Schweiz", file: "20240906.Ansichten von Luzern.-016.5.jpg", width: 9248, height: 6936, author: "Bybbisch94", license: "CC BY 4.0"},
    {title: "Dom des Heiligen Sava · Ansicht 6", country: "Serbien", file: "Свјетлопис цркве и Храма Светог Саве на Велики Петак 2023.jpg", width: 4000, height: 3000, author: "Andrija12345678", license: "CC BY-SA 4.0"},
    {title: "Burg Bratislava · Ansicht 7", country: "Slowakei", file: "Bratislava, hrad, areál.jpg", width: 8000, height: 6000, author: "Aktron", license: "CC BY-SA 4.0"},
    {title: "Bleder Insel · Ansicht 5", country: "Slowenien", file: "Bledski otok u prosincu 2021.jpg", width: 5152, height: 3864, author: "August Dominus", license: "CC BY-SA 4.0"},
    {title: "Prager Burg · Ansicht 5", country: "Tschechien", file: "2018-08-17 CZ Praha 01, Pražský hrad, Starý královský palác (50271070361).jpg", width: 5551, height: 3700, author: "Paul Korecky", license: "CC BY-SA 2.0"},
    {title: "Ungarisches Parlament · Ansicht 7", country: "Ungarn", file: "Hungarian Parliament Building (42253972024).jpg", width: 7952, height: 5304, author: "Nan Palmero from San Antonio, TX, USA", license: "CC BY 2.0"},
    {title: "Tower Bridge in London · Ansicht 1", country: "Vereinigtes Königreich", file: "2009-07-21 Tower Bridge, London.jpg", width: 6000, height: 4001, author: "Matthias Bethke", license: "CC BY-SA 4.0"},
    {title: "Grand-Place in Brüssel · Ansicht 5", country: "Belgien", file: "Bruxelles - Grand-Place (46646257044).jpg", width: 5184, height: 3456, author: "Fred Romero from Paris, France", license: "CC BY 2.0"},
    {title: "Alexander-Newski-Kathedrale · Ansicht 6", country: "Bulgarien", file: "Зима е...(Alexander Nevsky Cathedral) - panoramio.jpg", width: 5419, height: 3613, author: "Nikolai Karaneschev", license: "CC BY 3.0"},
    {title: "Nyhavn in Kopenhagen · Ansicht 6", country: "Dänemark", file: "394DK Nyhavn (15320383611).jpg", width: 6423, height: 4273, author: "Rüdiger Stehn from Kiel, Deutschland", license: "CC BY-SA 2.0"},
    {title: "Tallinner Rathaus · Ansicht 7", country: "Estland", file: "Plaza del ayuntamiento, Tallinn, Estonia, 2012-08-05, DD 16.JPG", width: 3777, height: 3351, author: "Diego Delso", license: "CC BY-SA 3.0"},
    {title: "Schloss Versailles · Ansicht 1", country: "Frankreich", file: "Façade of Versailles (24277036086).jpg", width: 7360, height: 4912, author: "Jorge Láscar from Melbourne, Australia", license: "CC BY 2.0"},
    {title: "Parthenon in Athen · Ansicht 5", country: "Griechenland", file: "Parthenon 5.jpg", width: 4080, height: 3072, author: "Kurtkaiser", license: "CC0"},
    {title: "Trinity College Dublin · Ansicht 7", country: "Irland", file: "Ireland Dublin Trinity College BW 2025-09-15 15-00-37.jpg", width: 5682, height: 4253, author: "Berthold Werner", license: "CC BY-SA 4.0"},
    {title: "Stadtmauern von Dubrovnik · Ansicht 6", country: "Kroatien", file: "29.12.16 Dubrovnik Old City Walls 040 (31151326673).jpg", width: 5472, height: 3648, author: "donald judge", license: "CC BY 2.0"},
    {title: "Schwarzhäupterhaus in Riga · Ansicht 6", country: "Lettland", file: "House of the Blackheads - Riga’s Town Hall Square (23702958675).jpg", width: 5520, height: 3680, author: "Jorge Láscar from Melbourne, Australia", license: "CC BY 2.0"},
    {title: "Wasserburg Trakai · Ansicht 7", country: "Litauen", file: "Trakai Island 02.jpg", width: 5681, height: 3773, author: "Scotch Mist", license: "CC BY-SA 4.0"},
    {title: "Adolphe-Brücke · Ansicht 8", country: "Luxemburg", file: "Luxembourg Pont Adolphe 01.jpg", width: 6016, height: 4016, author: "Calips", license: "CC BY-SA 3.0"},
    {title: "Kloster Ostrog · Ansicht 7", country: "Montenegro", file: "Ostrog konak 2011.jpg", width: 4320, height: 3240, author: "Dickelbers", license: "CC BY-SA 3.0"},
    {title: "Steinbrücke in Skopje · Ansicht 7", country: "Nordmazedonien", file: "Skopje, Macedonia (16900275099).jpg", width: 5472, height: 3648, author: "Juan Antonio F. Segal from Madrid, Spain", license: "CC BY 2.0"},
    {title: "Nidarosdom in Trondheim · Ansicht 4", country: "Norwegen", file: "Nidarosdomen Trondheim 2022-08-18 02.jpg", width: 8384, height: 5612, author: "Leonhard Lenz", license: "CC0"},
    {title: "Schloss Schönbrunn · Ansicht 4", country: "Österreich", file: "Austria-00165 - Schönbrunn Palace (9157578611).jpg", width: 6000, height: 4000, author: "Dennis G. Jarvis", license: "CC BY-SA 2.0"},
    {title: "Wawel in Krakau · Ansicht 2", country: "Polen", file: "Exterior of the St. Stanislaus Church and Wawel Castle seen across the Vistula River, Kraków.jpg", width: 3914, height: 2709, author: "Kgbo", license: "CC BY-SA 4.0"},
    {title: "Torre de Belém · Ansicht 5", country: "Portugal", file: "Rio Tejo e Torre de Belém - Lisboa - Portugal (51248936208).jpg", width: 3873, height: 2578, author: "Vitor Oliveira from Torres Vedras, PORTUGAL", license: "CC BY-SA 2.0"},
    {title: "Schloss Peleș · Ansicht 7", country: "Rumänien", file: "Castelul Peles la Apus.jpg", width: 3546, height: 4432, author: "6thphoto", license: "CC BY-SA 4.0"},
    {title: "Stockholmer Rathaus · Ansicht 4", country: "Schweden", file: "20180625 Stadshus 7909 (48413120367).jpg", width: 7952, height: 5304, author: "Ray Swi-hymn from Sijhih-Taipei, Taiwan", license: "CC BY-SA 2.0"},
    {title: "Kapellbrücke in Luzern · Ansicht 6", country: "Schweiz", file: "20240906.Ansichten von Luzern.-016.6.jpg", width: 9248, height: 6936, author: "Bybbisch94", license: "CC BY 4.0"},
    {title: "Dom des Heiligen Sava · Ansicht 7", country: "Serbien", file: "Храм Светог Саве, вече.jpg", width: 4000, height: 3000, author: "Дидаскалос", license: "CC BY-SA 4.0"},
    {title: "Burg Bratislava · Ansicht 8", country: "Slowakei", file: "Bratislava, hrad, kaštany a trávník.jpg", width: 8000, height: 6000, author: "Aktron", license: "CC BY-SA 4.0"},
    {title: "Bleder Insel · Ansicht 6", country: "Slowenien", file: "Bledski otok u prosincu.jpg", width: 5152, height: 3864, author: "August Dominus", license: "CC BY-SA 4.0"},
    {title: "Prager Burg · Ansicht 6", country: "Tschechien", file: "20190203 PragueCastleView 3585 (40488542683).jpg", width: 7952, height: 5304, author: "Ray Swi-hymn from Sijhih-Taipei, Taiwan", license: "CC BY-SA 2.0"},
    {title: "Ungarisches Parlament · Ansicht 8", country: "Ungarn", file: "Hungarian Parliament Building illuminated at night, Budapest (2025).jpg", width: 7952, height: 5304, author: "Paul Colin Hennig firstdorsal.eu", license: "CC BY-SA 4.0"},
    {title: "Tower Bridge in London · Ansicht 2", country: "Vereinigtes Königreich", file: "20191021.London.Tower Bridge.-013.jpg", width: 5788, height: 4341, author: "Bybbisch94, Christian Gebhardt", license: "CC BY-SA 4.0"},
  ].map(({image: _preview, ...wallpaper}) => Object.freeze({
    ...wallpaper,
    image: highResolutionImage(wallpaper.file),
  })));

  const stream = document.getElementById("wallpaper-stream");
  if (!stream) return;

  function randomIndex(maximum) {
    if (globalThis.crypto?.getRandomValues) {
      return crypto.getRandomValues(new Uint32Array(1))[0] % maximum;
    }
    return Math.floor(Math.random() * maximum);
  }

  function shuffled(items) {
    const result = [...items];
    for (let index = result.length - 1; index > 0; index -= 1) {
      const target = randomIndex(index + 1);
      [result[index], result[target]] = [result[target], result[index]];
    }
    return result;
  }

  function sourcePage(wallpaper) {
    return `https://commons.wikimedia.org/wiki/File:${encodeURIComponent(wallpaper.file)}`;
  }

  function postcardStep() {
    return Math.max(220, viewportHeight * .28);
  }

  function createCaption(wallpaper) {
    const caption = document.createElement("div");
    caption.className = "wallpaper-caption";
    const title = document.createElement("strong");
    title.textContent = wallpaper.title;
    const details = document.createElement("span");
    details.textContent = `${wallpaper.country} · ${wallpaper.author}`;
    caption.append(title, details);
    return caption;
  }

  function readReactions() {
    try {
      const stored = JSON.parse(globalThis.localStorage?.getItem(REACTION_STORAGE_KEY) || "{}");
      return stored && typeof stored === "object" && !Array.isArray(stored) ? stored : {};
    } catch (_error) {
      return {};
    }
  }

  function persistReactions() {
    try {
      globalThis.localStorage?.setItem(REACTION_STORAGE_KEY, JSON.stringify(reactions));
    } catch (_error) {
      // Reactions are a local enhancement and must not affect the Atlas in restricted browsing modes.
    }
  }

  const reactions = readReactions();
  let activeLightbox = null;
  let focusBeforeLightbox = null;
  let lockedScrollY = 0;
  let bodyStylesBeforeLightbox = null;

  const lightbox = document.createElement("section");
  lightbox.id = "wallpaper-lightbox";
  lightbox.className = "wallpaper-lightbox";
  lightbox.hidden = true;
  lightbox.setAttribute("role", "dialog");
  lightbox.setAttribute("aria-modal", "true");
  lightbox.setAttribute("aria-labelledby", "wallpaper-lightbox-title");
  lightbox.tabIndex = -1;

  const lightboxCard = document.createElement("div");
  lightboxCard.className = "wallpaper-lightbox-card";
  const closeButton = document.createElement("button");
  closeButton.type = "button";
  closeButton.className = "wallpaper-lightbox-close";
  closeButton.setAttribute("aria-label", "Postkarte schließen");
  const closeStar = document.createElement("img");
  closeStar.src = "/assets/europe-star.svg";
  closeStar.alt = "";
  closeButton.append(closeStar);
  const lightboxImage = document.createElement("img");
  lightboxImage.className = "wallpaper-lightbox-image";
  const lightboxInfo = document.createElement("div");
  lightboxInfo.className = "wallpaper-lightbox-info";
  const lightboxTitle = document.createElement("h2");
  lightboxTitle.id = "wallpaper-lightbox-title";
  const lightboxDetails = document.createElement("p");
  lightboxDetails.className = "wallpaper-lightbox-details";
  const lightboxAttribution = document.createElement("p");
  lightboxAttribution.className = "wallpaper-lightbox-attribution";
  const lightboxSource = document.createElement("a");
  lightboxSource.className = "wallpaper-lightbox-source";
  lightboxSource.target = "_blank";
  lightboxSource.rel = "noopener noreferrer";
  lightboxSource.textContent = "Quelle auf Wikimedia Commons";
  const reactionsBar = document.createElement("div");
  reactionsBar.className = "wallpaper-reactions";
  reactionsBar.setAttribute("aria-label", "Lokale Bewertung");
  const likeButton = document.createElement("button");
  likeButton.type = "button";
  likeButton.dataset.reaction = "like";
  likeButton.textContent = "Gefällt mir";
  const dislikeButton = document.createElement("button");
  dislikeButton.type = "button";
  dislikeButton.dataset.reaction = "dislike";
  dislikeButton.textContent = "Gefällt mir nicht";
  reactionsBar.append(likeButton, dislikeButton);
  lightboxInfo.append(lightboxTitle, lightboxDetails, lightboxAttribution, lightboxSource, reactionsBar);
  lightboxCard.append(closeButton, lightboxImage, lightboxInfo);
  lightbox.append(lightboxCard);
  document.body.append(lightbox);

  function updateReactionButtons() {
    const reaction = activeLightbox ? reactions[activeLightbox.file] : null;
    likeButton.setAttribute("aria-pressed", String(reaction === "like"));
    dislikeButton.setAttribute("aria-pressed", String(reaction === "dislike"));
  }

  function setReaction(reaction) {
    if (!activeLightbox) return;
    const key = activeLightbox.file;
    if (reactions[key] === reaction) delete reactions[key];
    else reactions[key] = reaction;
    persistReactions();
    updateReactionButtons();
  }

  function lockBackgroundScroll() {
    lockedScrollY = window.scrollY;
    bodyStylesBeforeLightbox = {
      overflow: document.body.style.overflow,
      position: document.body.style.position,
      top: document.body.style.top,
      width: document.body.style.width,
    };
    document.body.classList.add("overload-lightbox-open");
    document.body.style.overflow = "hidden";
    document.body.style.position = "fixed";
    document.body.style.top = `-${lockedScrollY}px`;
    document.body.style.width = "100%";
  }

  function unlockBackgroundScroll() {
    if (bodyStylesBeforeLightbox) {
      Object.assign(document.body.style, bodyStylesBeforeLightbox);
      bodyStylesBeforeLightbox = null;
    }
    document.body.classList.remove("overload-lightbox-open");
    window.scrollTo({top: lockedScrollY, behavior: "auto"});
  }

  function closeLightbox({restoreFocus = true} = {}) {
    if (!activeLightbox) return;
    lightbox.classList.remove("is-open");
    lightbox.hidden = true;
    lightboxImage.removeAttribute("src");
    activeLightbox = null;
    unlockBackgroundScroll();
    if (restoreFocus && focusBeforeLightbox?.isConnected) {
      focusBeforeLightbox.focus({preventScroll: true});
    }
    focusBeforeLightbox = null;
  }

  function openLightbox(index, panel) {
    if (!active || !sequence[index]) return;
    activeLightbox = sequence[index];
    focusBeforeLightbox = panel;
    lightboxTitle.textContent = activeLightbox.title;
    lightboxDetails.textContent = activeLightbox.country;
    lightboxAttribution.textContent = `${activeLightbox.author} · ${activeLightbox.license}`;
    lightboxSource.href = sourcePage(activeLightbox);
    lightboxImage.src = activeLightbox.image;
    lightboxImage.alt = activeLightbox.title;
    updateReactionButtons();
    lockBackgroundScroll();
    lightbox.hidden = false;
    requestAnimationFrame(() => lightbox.classList.add("is-open"));
    closeButton.focus({preventScroll: true});
  }

  function handleLightboxKeydown(event) {
    if (!activeLightbox) return;
    if (event.key === "Escape") {
      event.preventDefault();
      closeLightbox();
      return;
    }
    if (event.key !== "Tab") return;
    const focusable = [...lightbox.querySelectorAll("button, a[href]")].filter(item => !item.disabled);
    const first = focusable[0];
    const last = focusable.at(-1);
    if (!first || !last) return;
    if (event.shiftKey && document.activeElement === first) {
      event.preventDefault();
      last.focus();
    } else if (!event.shiftKey && document.activeElement === last) {
      event.preventDefault();
      first.focus();
    }
  }

  closeButton.addEventListener("click", () => closeLightbox());
  likeButton.addEventListener("click", () => setReaction("like"));
  dislikeButton.addEventListener("click", () => setReaction("dislike"));
  lightbox.addEventListener("click", event => {
    if (event.target === lightbox) closeLightbox();
  });
  document.addEventListener("keydown", handleLightboxKeydown);

  let sequence = [];
  const panels = [];
  let viewportHeight = Math.max(1, window.innerHeight);
  let scrollFrame = null;
  let layoutTimer = null;

  function loadPanel(panel) {
    if (!active || panel.dataset.loaded || panel.dataset.loading) return;
    const index = Number(panel.dataset.wallpaperIndex);
    const wallpaper = sequence[index];
    panel.dataset.loading = "true";
    const image = new Image();
    image.decoding = "async";
    image.onload = () => {
      if (!active || !panel.isConnected) return;
      panel.style.backgroundImage = `url("${wallpaper.image}")`;
      panel.dataset.loaded = "true";
      delete panel.dataset.loading;
      panel.classList.add("is-loaded");
    };
    image.onerror = () => {
      delete panel.dataset.loading;
      panel.classList.add("is-unavailable");
    };
    image.src = wallpaper.image;
  }

  function createPanel(index) {
    const panel = document.createElement("div");
    panel.className = "wallpaper-panel";
    panel.dataset.wallpaperIndex = String(index);
    panel.tabIndex = 0;
    panel.setAttribute("role", "button");
    panel.setAttribute("aria-label", `Postkarte öffnen: ${sequence[index].title}`);
    panel.style.top = `${index * postcardStep() + Math.max(24, viewportHeight * .06)}px`;
    panel.style.setProperty("--postcard-index", String(index));
    panel.append(createCaption(sequence[index]));
    panel.addEventListener("click", () => openLightbox(index, panel));
    panel.addEventListener("keydown", event => {
      if (event.key !== "Enter" && event.key !== " ") return;
      event.preventDefault();
      openLightbox(index, panel);
    });
    stream.appendChild(panel);
    panels.push(panel);
    return panel;
  }

  function centeredWallpaperIndex() {
    return Math.min(
      panels.length - 1,
      Math.max(0, Math.floor((window.scrollY + viewportHeight / 2) / postcardStep())),
    );
  }

  function updateWallpaperForScroll() {
    if (!active) return;
    scrollFrame = null;
    const index = centeredWallpaperIndex();
    for (const nearby of [index - 1, index, index + 1]) {
      if (panels[nearby]) loadPanel(panels[nearby]);
    }
  }

  function scheduleWallpaperUpdate() {
    if (!active) return;
    if (scrollFrame !== null) return;
    scrollFrame = requestAnimationFrame(updateWallpaperForScroll);
  }

  function layoutWallpapers() {
    if (!active) return;
    viewportHeight = Math.max(1, window.innerHeight);
    const main = document.querySelector("main");
    const contentHeight = Math.max(
      viewportHeight,
      main ? main.offsetTop + main.offsetHeight : document.documentElement.scrollHeight,
    );
    const requiredPanels = Math.min(sequence.length, Math.max(1, Math.ceil(contentHeight / postcardStep())));
    while (panels.length < requiredPanels) createPanel(panels.length);
    panels.forEach((panel, index) => {
      panel.style.top = `${index * postcardStep() + Math.max(24, viewportHeight * .06)}px`;
      panel.style.setProperty("--postcard-index", String(index));
    });
    stream.style.height = `${contentHeight}px`;
    updateWallpaperForScroll();
  }

  function scheduleLayout() {
    if (!active) return;
    clearTimeout(layoutTimer);
    layoutTimer = setTimeout(layoutWallpapers, 120);
  }

  function readOptIn() {
    try {
      return globalThis.localStorage?.getItem(OVERLOAD_STORAGE_KEY) === "true";
    } catch (_error) {
      return false;
    }
  }

  function persistOptIn(enabled) {
    try {
      globalThis.localStorage?.setItem(OVERLOAD_STORAGE_KEY, String(enabled));
    } catch (_error) {
      // Private browsing and restrictive browser settings must not affect the Atlas.
    }
  }

  let active = false;
  let resizeObserver = null;

  function notifyState() {
    document.dispatchEvent(new CustomEvent("atlas-overload-change", {detail: {enabled: active}}));
  }

  function start() {
    if (active) return;
    active = true;
    sequence = shuffled(WALLPAPERS);
    layoutWallpapers();
    window.addEventListener("scroll", scheduleWallpaperUpdate, {passive: true});
    window.addEventListener("resize", scheduleLayout, {passive: true});
    if ("ResizeObserver" in window) {
      resizeObserver = new ResizeObserver(scheduleLayout);
      resizeObserver.observe(document.querySelector("main"));
    }
  }

  function stop() {
    closeLightbox({restoreFocus: false});
    active = false;
    window.removeEventListener("scroll", scheduleWallpaperUpdate);
    window.removeEventListener("resize", scheduleLayout);
    if (scrollFrame !== null) cancelAnimationFrame(scrollFrame);
    scrollFrame = null;
    clearTimeout(layoutTimer);
    layoutTimer = null;
    resizeObserver?.disconnect();
    resizeObserver = null;
    panels.splice(0).forEach(panel => panel.remove());
    stream.replaceChildren();
    stream.style.height = "";
  }

  function setEnabled(enabled) {
    if (enabled) start();
    else stop();
    persistOptIn(Boolean(enabled));
    notifyState();
  }

  const controller = Object.freeze({
    setEnabled,
    isEnabled: () => active,
  });
  window.__atlasWallpaper = controller;
  window.__atlasWallpaperTest = {wallpapers: WALLPAPERS, highResolutionImage, controller};
  if (readOptIn()) setEnabled(true);
})();
