(() => {
  "use strict";
  const OVERLOAD_STORAGE_KEY = "eea-europa-overload";
  const REACTION_STORAGE_KEY = "eea-europa-overload-reactions";

  function highResolutionImage(file) {
    return `https://commons.wikimedia.org/wiki/Special:Redirect/file/${encodeURIComponent(file)}?width=3840`;
  }

  const WALLPAPERS = Object.freeze([
    {title: "Akropolis bei Nacht", subject: "Akropolis bei Nacht", country: "Griechenland", file: "1029 Acropolis of Athens in Greece at night Photo by Giles Laurent.jpg", width: 8640, height: 5760, author: "Giles Laurent", license: "CC BY-SA 4.0"},
    {title: "Oia auf Santorin", subject: "Oia auf Santorin", country: "Griechenland", file: "Oia sunset - panoramio (2).jpg", width: 5202, height: 3465, author: "TomasEE", license: "CC BY 3.0"},
    {title: "Glencoe", subject: "Glencoe", country: "Vereinigtes Königreich", file: "GlencoeVillage.jpg", width: 4288, height: 2848, author: "Simonm72", license: "CC BY 3.0"},
    {title: "Kolosseum", subject: "Kolosseum", country: "Italien", file: "Colosseo 2020.jpg", width: 12051, height: 8442, author: "FeaturedPics", license: "CC BY-SA 4.0"},
    {title: "Altstadt von Dubrovnik", subject: "Altstadt von Dubrovnik", country: "Kroatien", file: "The walls of the fortress and View of the old city. panorama.jpg", width: 3543, height: 2198, author: "Zysko serhii", license: "CC BY-SA 4.0"},
    {title: "Dolomiten bei Cortina", subject: "Dolomiten bei Cortina", country: "Italien", file: "Faloria Cortina d'Ampezzo 10.jpg", width: 4340, height: 3000, author: "kallerna", license: "CC BY-SA 4.0"},
    {title: "Tower Bridge im Morgenlicht", subject: "Tower Bridge", country: "Vereinigtes Königreich", file: "Tower Bridge at Dawn.jpg", width: 5554, height: 3703, author: "Fuzzypiggy", license: "CC BY-SA 3.0"},
    {title: "Schloss Chambord", subject: "Schloss Chambord", country: "Frankreich", file: "Aerial image of Château de Chambord (view from the southeast).jpg", width: 3600, height: 2700, author: "Carsten Steger", license: "CC BY-SA 4.0"},
    {title: "Klöster von Meteora", subject: "Klöster von Meteora", country: "Griechenland", file: "Meteora's monastery 2.jpg", width: 7360, height: 4912, author: "Stathis floros", license: "CC BY-SA 4.0"},
    {title: "Schloss Schönbrunn", subject: "Schloss Schönbrunn", country: "Österreich", file: "Wien - Schloss Schönbrunn.JPG", width: 5650, height: 3860, author: "C.Stadler/Bwag", license: "CC BY-SA 4.0"},
    {title: "Gamla Stan", subject: "Gamla Stan", country: "Schweden", file: "Gamla stan September 2014 01.jpg", width: 6016, height: 4016, author: "Arild Vågen", license: "CC BY-SA 4.0"},
    {title: "Dom von Florenz", subject: "Dom von Florenz", country: "Italien", file: "Cattedrale di Santa Maria del Fiore – Il Duomo di Firenze.jpg", width: 3872, height: 2592, author: "Gary Campbell-Hall", license: "CC BY 2.0"},
    {title: "Schloss Neuschwanstein", subject: "Schloss Neuschwanstein", country: "Deutschland", file: "Schloss Neuschwanstein 2013.jpg", width: 5979, height: 4468, author: "Thomas Wolf", license: "CC BY-SA 3.0 DE"},
    {title: "Mont-Saint-Michel", subject: "Mont-Saint-Michel", country: "Frankreich", file: "Mont-Saint-Michel vu du ciel.jpg", width: 4000, height: 2250, author: "Amaustan", license: "CC BY-SA 4.0"},
    {title: "Lauterbrunnental", subject: "Lauterbrunnental", country: "Schweiz", file: "1 lauterbrunnen valley wengen 2022.jpg", width: 14077, height: 9464, author: "Chensiyuan", license: "CC BY-SA 4.0"},
    {title: "Bucht von Kotor", subject: "Bucht von Kotor", country: "Montenegro", file: "Kotor aerial 1.jpg", width: 3600, height: 2355, author: "kallerna", license: "CC BY-SA 4.0"},
    {title: "Hallstatt", subject: "Hallstatt", country: "Österreich", file: "Hallstatt - Zentrum .JPG", width: 3937, height: 2717, author: "C.Stadler/Bwag", license: "CC BY-SA 4.0"},
    {title: "Palácio da Pena", subject: "Palácio da Pena", country: "Portugal", file: "Sintra Portugal Palácio da Pena-01.jpg", width: 3500, height: 2333, author: "Uwe Aranas", license: "CC BY-SA 3.0"},
    {title: "Cliffs of Moher", subject: "Cliffs of Moher", country: "Irland", file: "Cliffs-Of-Moher-OBriens-From-South.JPG", width: 4608, height: 3456, author: "Bjørn Christian Tørrissen", license: "CC BY-SA 3.0"},
    {title: "Schloss Bran", subject: "Schloss Bran", country: "Rumänien", file: "Castelul Bran2.jpg", width: 3791, height: 2516, author: "Dobre Cezar", license: "CC BY-SA 3.0 RO"},
    {title: "Karlsbrücke", subject: "Karlsbrücke", country: "Tschechien", file: "Prague 07-2016 view from Lesser Town Tower of Charles Bridge img3.jpg", width: 4555, height: 3037, author: "A.Savin", license: "FAL"},
    {title: "Sächsische Schweiz", subject: "Sächsische Schweiz", country: "Deutschland", file: "Lilienstein Saxon Switzerland.jpg", width: 4146, height: 2764, author: "Merops", license: "CC BY-SA 3.0"},
    {title: "Lofoten", subject: "Lofoten", country: "Norwegen", file: "Moskenes Reinebringen lub 2025-07-21 img09 Aussicht.jpg", width: 7952, height: 5304, author: "Lukas Beck", license: "CC BY 4.0"},
    {title: "Canal Grande", subject: "Canal Grande", country: "Italien", file: "View of the Grand Canal from Rialto to Ca'Foscari.jpg", width: 7360, height: 4026, author: "Didier Descouens", license: "CC BY-SA 4.0"},
    {title: "Cinque Terre", subject: "Cinque Terre", country: "Italien", file: "Cinque Terre (Italy, October 2020) - 24 (50543603956).jpg", width: 5438, height: 3626, author: "Bruno Rijsman", license: "CC BY-SA 2.0"},
    {title: "Kloster Rila", subject: "Kloster Rila", country: "Bulgarien", file: "Rila Monastery, August 2013.jpg", width: 3690, height: 2460, author: "Raggatt2000", license: "CC BY-SA 3.0"},
    {title: "Kloster Ostrog", subject: "Kloster Ostrog", country: "Montenegro", file: "Monasterio de Ostrog, Montenegro, 2014-04-14, DD 14.JPG", width: 5395, height: 3597, author: "Diego Delso", license: "CC BY-SA 3.0"},
    {title: "Geirangerfjord", subject: "Geirangerfjord", country: "Norwegen", file: "Geirangerfjord .jpg", width: 7193, height: 4795, author: "Andreas Trepte", license: "CC BY-SA 2.5"},
    {title: "Nyhavn", subject: "Nyhavn", country: "Dänemark", file: "The Nyhavn Canal 3.jpg", width: 5464, height: 3640, author: "Europäische Kommission", license: "CC BY 4.0"},
    {title: "Warschauer Königsschloss", subject: "Warschauer Königsschloss", country: "Polen", file: "Royal Castle in Warsaw, Poland, 2022, 03.jpg", width: 3741, height: 2806, author: "Chris Olszewski", license: "CC BY-SA 4.0"},
    {title: "Ungarisches Parlament", subject: "Ungarisches Parlament", country: "Ungarn", file: "Hungarian Parliament Building from across the Danube, 2025-01-11.jpg", width: 4731, height: 2649, author: "Kilyann Le Hen", license: "CC BY 4.0"},
    {title: "Bleder See", subject: "Bleder See", country: "Slowenien", file: "Lake Bled from the Mountain.jpg", width: 4000, height: 3000, author: "Canadianhockey91", license: "CC BY-SA 3.0"},
    {title: "Altstadt von Riga", subject: "Altstadt von Riga", country: "Lettland", file: "Views from St. Peter's Church Spire, Riga 20180808-2.jpg", width: 5184, height: 3456, author: "Suicasmo", license: "CC BY-SA 4.0"},
    {title: "Wasserburg Trakai", subject: "Wasserburg Trakai", country: "Litauen", file: "Trakai castle 2016.jpg", width: 4976, height: 3374, author: "Aleksandr Petukhov", license: "CC BY-SA 4.0"},
    {title: "Prinsengracht", subject: "Prinsengracht", country: "Niederlande", file: "Prinsengracht.jpg", width: 4608, height: 3072, author: "Kaz Alting", license: "CC BY-SA 3.0"},
    {title: "Brügge vom Belfried", subject: "Brügge vom Belfried", country: "Belgien", file: "Brügge Blick vom Belfried 4.jpg", width: 4520, height: 2896, author: "Zairon", license: "CC BY-SA 4.0"},
    {title: "Château de Chillon am Genfersee", subject: "Château de Chillon am Genfersee", country: "Schweiz", file: "001 Chateau de Chillon and Dents du Midi Photo by Giles Laurent.jpg", width: 7952, height: 5304, author: "Giles Laurent", license: "CC BY-SA 4.0"},
    {title: "Burg Tropsztyn am Czchów-See", subject: "Burg Tropsztyn am Czchów-See", country: "Polen", file: "Tropsztyn Castle overlooking Czchów Lake, Wytrzyszczka, Lesser Poland Voivodeship, 20251025 0803 5046.jpg", width: 5858, height: 3885, author: "Jakub Hałun", license: "CC BY 4.0"},
    {title: "Alhambra über Granada", subject: "Alhambra über Granada", country: "Spanien", file: "Granada - View from Mirador de San Nicolás - 02.jpg", width: 6709, height: 3770, author: "Benjamin Smith / Diego Delso", license: "GFDL"},
    {title: "Dubrovnik aus der Festung", subject: "Dubrovnik aus der Festung", country: "Kroatien", file: "Casco viejo de Dubrovnik, Croacia, 2014-04-13, DD 18.JPG", width: 5225, height: 3385, author: "Diego Delso", license: "CC BY-SA 3.0"},
    {title: "Engelsburg in der Dämmerung", subject: "Engelsburg in der Dämmerung", country: "Italien", file: "Castel Sant'Angelo at dusk, Rome, Italy.jpg", width: 4371, height: 2898, author: "Jebulon", license: "CC0"},
    {title: "Torre de Belém", subject: "Torre de Belém", country: "Portugal", file: "Belém Tower and the 25 de Abril Bridge in the background.jpg", width: 6763, height: 4510, author: "Lisbon Photoshoots", license: "CC BY-SA 4.0"},
    {title: "Prager Burg", subject: "Prager Burg", country: "Tschechien", file: "Castillo de Praga, Praga, República Checa, 2022-07-01, DD 23-25 HDR.jpg", width: 7479, height: 3883, author: "Diego Delso", license: "CC BY-SA 4.0"},
    {title: "Festung Bard", subject: "Festung Bard", country: "Italien", file: "Castle of Bard (3).jpg", width: 5158, height: 3675, author: "Krzysztof Golik", license: "CC BY-SA 4.0"},
    {title: "Schloss Frederiksborg", subject: "Schloss Frederiksborg", country: "Dänemark", file: "Frederiksborg Castle and boat crop.jpg", width: 3833, height: 2533, author: "Casper Moller from London, United Kingdom", license: "CC BY 2.0"},
    {title: "Festung Vaxholm", subject: "Festung Vaxholm", country: "Schweden", file: "Vaxholms kastell November 2013.jpg", width: 5749, height: 3234, author: "Arild Vågen", license: "CC BY-SA 3.0"},
    {title: "Schloss Książ", subject: "Schloss Książ", country: "Polen", file: "Ksiaz - zamek 01.jpg", width: 8123, height: 5161, author: "Jar.ciurus", license: "CC BY-SA 3.0 PL"},
    {title: "Tanzendes Haus in Prag", subject: "Tanzendes Haus in Prag", country: "Tschechien", file: "Tanzendes Haus 2023.jpg", width: 3000, height: 3000, author: "Danny Alexander Lettkemann, Architekt", license: "CC BY-SA 4.0"},
    {title: "Schloss Litomyšl", subject: "Schloss Litomyšl", country: "Tschechien", file: "Litomyšl (Leitomischl) chateau - by Pudelek.jpg", width: 4074, height: 2622, author: "Pudelek", license: "CC BY-SA 4.0"},
    {title: "Muiderslot", subject: "Muiderslot", country: "Niederlande", file: "Muiden, Muiderslot. 09-05-2022. (actm.) 07.jpg", width: 4908, height: 3362, author: "Agnes Monkelbaan", license: "CC BY-SA 4.0"},
    {title: "Kapellbrücke in Luzern", subject: "Kapellbrücke", country: "Schweiz", file: "20240906.Ansichten von Luzern.-016.1.jpg", width: 8841, height: 6631, author: "Bybbisch94", license: "CC BY 4.0"},
    {title: "Bundeshaus in Bern", subject: "Bundeshaus in Bern", country: "Schweiz", file: "Bundeshaus 1128.jpg", width: 3072, height: 2048, author: "Mike Lehmann, Mike Switzerland (talk) 05:54, 14 July 2010 (UTC)", license: "CC BY-SA 3.0"},
    {title: "Ribblehead-Viadukt", subject: "Ribblehead-Viadukt", country: "Vereinigtes Königreich", file: "2015 Ribblehead Viaduct 1.jpg", width: 4452, height: 2968, author: "Kreuzschnabel", license: "CC BY-SA 3.0"},
    {title: "Gavarnie-Tal in den Pyrenäen", subject: "Gavarnie-Tal in den Pyrenäen", country: "Frankreich", file: "2019 - Parc national des Pyrenees - Vallée de Gavarnie.jpg", width: 4493, height: 2995, author: "Moahim", license: "CC BY-SA 4.0"},
    {title: "Nidarosdom in Trondheim", subject: "Nidarosdom in Trondheim", country: "Norwegen", file: "Nidarosdomen 85130 2024-2.jpg", width: 8007, height: 6187, author: "Bjørn Erik Pedersen", license: "CC BY-SA 4.0"},
    {title: "Grundtvigskirche", subject: "Grundtvigskirche", country: "Dänemark", file: "Grundtvig’s Church 02 (level and colour adjust).jpg", width: 2992, height: 2000, author: "Haydn Blackey from Cardiff, Wales", license: "CC BY-SA 2.0"},
    {title: "Eismeerkathedrale in Tromsø", subject: "Eismeerkathedrale in Tromsø", country: "Norwegen", file: "Arctic Cathedral in Tromsoe.jpg", width: 3072, height: 2048, author: "Henrik at English Wikipedia", license: "CC BY 2.5"},
    {title: "Adolphe-Brücke", subject: "Adolphe-Brücke", country: "Luxemburg", file: "Adolphe Bridge in 2019.01.jpg", width: 4032, height: 3024, author: "CAPTAIN RAJU", license: "CC BY-SA 4.0"},
    {title: "Bleder Insel", subject: "Bleder Insel", country: "Slowenien", file: "Bled (49480708878).jpg", width: 8800, height: 5867, author: "bmw3528", license: "CC BY 2.0"},
    {title: "Hieronymitenkloster in Belém", subject: "Hieronymitenkloster in Belém", country: "Portugal", file: "The Jerónimos Monastery or Hieronymites Monastery.png", width: 3000, height: 2000, author: "Heartshade", license: "CC BY 4.0"},
    {title: "Las Cañadas und Roques de García", subject: "Las Cañadas und Roques de García", country: "Spanien", file: "Caldera Las Cañadas mit Roques de García und TF-21.jpg", width: 5426, height: 3615, author: "Thomas Wolf", license: "CC BY-SA 3.0 DE"},
    {title: "Morgendämmerung über Sète", subject: "Morgendämmerung über Sète", country: "Frankreich", file: "Dawn on Sète and the Étang de Thau.jpg", width: 4280, height: 2675, author: "Christian Ferrer", license: "CC BY-SA 3.0"},
    {title: "Monsanto im Morgenlicht", subject: "Monsanto im Morgenlicht", country: "Portugal", file: "Granite boulder formations near the Monsanto Castle at sunrise, Aldeia de Monsanto, Portugal (2) julesvernex2-3.jpg", width: 9254, height: 6021, author: "Jules Verne Times Two", license: "CC BY-SA 4.0"},
    {title: "Sagrada Família", subject: "Sagrada Família", country: "Spanien", file: "Sagrada Família (51970333757).jpg", width: 4032, height: 3024, author: "Chris Yunker from St. Louis, United States", license: "CC BY 2.0"},
    {title: "Altstadt von Bystrzyca Kłodzka", subject: "Altstadt von Bystrzyca Kłodzka", country: "Polen", file: "2014 Bystrzyca Kłodzka, stare miasto 11.jpg", width: 4816, height: 2443, author: "Jacek Halicki", license: "CC BY-SA 3.0 PL"},
    {title: "Breslau an der Oder", subject: "Breslau an der Oder", country: "Polen", file: "Wrocław - widok z Wyspy Slodowej - wyspa Tamka.jpg", width: 4384, height: 2686, author: "Jar.ciurus", license: "CC BY-SA 3.0 PL"},
    {title: "Salzburg an der Salzach bei Nacht", subject: "Salzburg an der Salzach bei Nacht", country: "Österreich", file: "2018 - May - Salzach River at night in Salzburg.jpg", width: 5257, height: 2957, author: "Max Dawncat", license: "CC BY 2.0"},
    {title: "Großherzoglicher Palast Luxemburg", subject: "Großherzoglicher Palast Luxemburg", country: "Luxemburg", file: "Luxemburg BW 2016-09-15 11-46-49 stitch.jpg", width: 8100, height: 6624, author: "Berthold Werner", license: "CC BY-SA 4.0"},
    {title: "Parthenon in Athen", subject: "Parthenon in Athen", country: "Griechenland", file: "1010 Parthenon of the Acropolis of Athens Photo by Giles Laurent.jpg", width: 8640, height: 5760, author: "Giles Laurent", license: "CC BY-SA 4.0"},
    {title: "Alexander-Newski-Kathedrale Tallinn", subject: "Alexander-Newski-Kathedrale Tallinn", country: "Estland", file: "Catedral de Alejandro Nevsky, Tallin, Estonia, 2012-08-11, DD 46.JPG", width: 4829, height: 3253, author: "Diego Delso", license: "CC BY-SA 3.0"},
    {title: "Altstadt von Zürich", subject: "Altstadt von Zürich", country: "Schweiz", file: "Altstadt Zürich 2015.jpg", width: 11303, height: 6164, author: "Thomas Wolf", license: "CC BY-SA 3.0 DE"},
    {title: "Amsterdamer Grachten", subject: "Amsterdamer Grachten", country: "Niederlande", file: "Amsterdam Canals - July 2006.jpg", width: 4017, height: 2117, author: "Diliff", license: "GFDL"},
    {title: "Atrani an der Amalfiküste", subject: "Atrani an der Amalfiküste", country: "Italien", file: "Atrani (Costiera Amalfitana, 23-8-2011).jpg", width: 4200, height: 2790, author: "Paolo Costa Baldi", license: "GFDL"},
    {title: "Tallinn vom Domberg", subject: "Tallinn vom Domberg", country: "Estland", file: "Ayuntamiento, vistas panorámicas desde Toompea, Tallin, Estonia, 2012-08-05, DD 21.JPG", width: 4670, height: 2921, author: "Diego Delso", license: "CC BY-SA 3.0"},
    {title: "Basel von der Münsterpfalz", subject: "Basel von der Münsterpfalz", country: "Schweiz", file: "Basel - Münsterpfalz1.jpg", width: 8904, height: 4568, author: "Taxiarchos228", license: "FAL"},
    {title: "Burg Bratislava", subject: "Burg Bratislava", country: "Slowakei", file: "20230501.Ansicht von Bratislava.-040.jpg", width: 9248, height: 6936, author: "Bybbisch94, Christian Gebhardt", license: "CC BY-SA 4.0"},
    {title: "Grossmünster in Zürich", subject: "Grossmünster in Zürich", country: "Schweiz", file: "Grossmünster - Münsterhof 2014-05-23 12-08-43.JPG", width: 3200, height: 4800, author: "Roland zh", license: "CC BY-SA 3.0"},
    {title: "Bath vom Bathwick Hill", subject: "Bath vom Bathwick Hill", country: "Vereinigtes Königreich", file: "Bathwick Hill, Bath, Somerset, UK - Diliff.jpg", width: 4000, height: 2810, author: "Diliff", license: "CC BY-SA 3.0"},
    {title: "Canal Grande und Santa Maria della Salute", subject: "Canal Grande und Santa Maria della Salute", country: "Italien", file: "Canal Grande Chiesa della Salute e Dogana dal ponte dell Accademia.jpg", width: 7307, height: 4912, author: "Wolfgang Moroder", license: "GFDL"},
    {title: "Ponte Dom Luís I in Porto", subject: "Ponte Dom Luís I in Porto", country: "Portugal", file: "Dom Luís I Bridge (36961760686).jpg", width: 3861, height: 2942, author: "Deensel", license: "CC BY 2.0"},
    {title: "Stift Melk", subject: "Stift Melk", country: "Österreich", file: "Stift Melk, Westansicht.jpg", width: 6000, height: 4000, author: "Thomas Ledl", license: "CC BY-SA 4.0"},
    {title: "Grand-Place in Brüssel", subject: "Grand-Place in Brüssel", country: "Belgien", file: "06 2023 Grand Place (Brussels) IMG 7557.jpg", width: 5790, height: 3703, author: "Alexander-93", license: "CC BY-SA 4.0"},
    {title: "Buitrago del Lozoya", subject: "Buitrago del Lozoya", country: "Spanien", file: "Buitrago del Lozoya - 04.jpg", width: 3888, height: 2592, author: "Carlos Delgado", license: "CC BY-SA 3.0"},
    {title: "Festung Hohensalzburg", subject: "Festung Hohensalzburg", country: "Österreich", file: "Salzburg - Festung Hohensalzburg.JPG", width: 5460, height: 3641, author: "C.Stadler/Bwag", license: "CC BY-SA 4.0"},
    {title: "Tallinner Rathaus", subject: "Tallinner Rathaus", country: "Estland", file: "07-06-21-tallinn-by-RalfR-025.jpg", width: 3920, height: 3228, author: "Ralf Roletschek", license: "FAL"},
    {title: "Geirangerfjord vom Flydalsjuvet", subject: "Geirangerfjord vom Flydalsjuvet", country: "Norwegen", file: "Fiordo de Geiranger desde Flydalsjuvet, Noruega, 2019-09-07, DD 59.jpg", width: 7580, height: 5064, author: "Diego Delso", license: "CC BY-SA 4.0"},
    {title: "Karlskirche in Wien", subject: "Karlskirche in Wien", country: "Österreich", file: "Karlskirche Abendsonne 1.jpg", width: 8724, height: 5816, author: "Thomas Ledl", license: "CC BY-SA 4.0"},
    {title: "Kathedrale von Kotor", subject: "Kathedrale von Kotor", country: "Montenegro", file: "Kotor Cathedral church.jpg", width: 6000, height: 4000, author: "Geotiger18", license: "CC BY-SA 3.0"},
    {title: "Dom von Helsinki", subject: "Dom von Helsinki", country: "Finnland", file: "Helsingin Tuomiokirkko ja Senaatintori - D671 - hkm.HKMS000005-km002mzm.jpg", width: 3543, height: 2578, author: "SKY-FOTO Möller", license: "CC BY 4.0"},
    {title: "Trinity College Dublin", subject: "Trinity College Dublin", country: "Irland", file: "Dublin - Trinity College Dublin - 20150315204112.jpg", width: 5184, height: 3456, author: "Dieglop", license: "CC BY-SA 4.0"},
    {title: "Lagangarbh und Buachaille Etive Mòr", subject: "Lagangarbh und Buachaille Etive Mòr", country: "Vereinigtes Königreich", file: "Lagangarbh cottage with Buachaille Etive Mòr.jpg", width: 9429, height: 5304, author: "Colin", license: "CC BY-SA 4.0"},
    {title: "Burg Vianden", subject: "Burg Vianden", country: "Luxemburg", file: "Burg Vianden, Luxemburg.jpg", width: 4868, height: 3163, author: "Jeff Croisé", license: "CC BY-SA 4.0"},
    {title: "Doberaner Münster", subject: "Doberaner Münster", country: "Deutschland", file: "Doberaner Münster, NW view, 2024-02-17.jpg", width: 4569, height: 3456, author: "Radomianin", license: "CC BY-SA 4.0"},
    {title: "Speyerer Dom in der Abendsonne", subject: "Speyerer Dom in der Abendsonne", country: "Deutschland", file: "Speyer - Altstadt - Altpörtel - Blick auf Domfassade und Kirchtürme mit Abendsonne.jpg", width: 7649, height: 5222, author: "Roman Eisele", license: "CC BY-SA 4.0"},
    {title: "Königspalast von Madrid", subject: "Königspalast von Madrid", country: "Spanien", file: "Palacio Real de Madrid Julio 2016 (cropped).jpg", width: 2784, height: 2104, author: "Tim Adams", license: "CC BY-SA 4.0"},
    {title: "Kathedrale von Le Mans", subject: "Kathedrale von Le Mans", country: "Frankreich", file: "Le Mans - Cathedrale St Julien ext autumn.jpg", width: 4593, height: 3042, author: "Selbymay", license: "CC BY-SA 3.0"},
    {title: "Die beiden Dome von Brescia bei Nacht", subject: "Die beiden Dome von Brescia bei Nacht", country: "Italien", file: "Duomo vecchio e duomo nuovo notturna Brescia.jpg", width: 11702, height: 8355, author: "Wolfgang Moroder", license: "CC BY-SA 3.0"},
    {title: "Basilika San Francesco in Assisi", subject: "Basilika San Francesco in Assisi", country: "Italien", file: "Rear NW Basilica Francesco Assisi Sep23 A7C 07913.jpg", width: 4136, height: 2757, author: "Timothy A. Gonsalves", license: "CC BY-SA 4.0"},
    {title: "Kathedrale von Segovia", subject: "Kathedrale von Segovia", country: "Spanien", file: "Catedral de Santa María de Segovia - 01.jpg", width: 4640, height: 3093, author: "Carlos Delgado", license: "CC BY-SA 3.0"},
    {title: "Mezquita-Catedral von Córdoba", subject: "Mezquita-Catedral von Córdoba", country: "Spanien", file: "Mezquita de Córdoba desde el aire (Córdoba, España).jpg", width: 4288, height: 2848, author: "Toni Castillo Quero", license: "CC BY-SA 2.0"},
    {title: "Kirche am Steinhof", subject: "Kirche am Steinhof", country: "Österreich", file: "20250503 Kirche am Steinhof 03.jpg", width: 5904, height: 3941, author: "Flocci Nivis", license: "CC BY-SA 4.0"},
    {title: "Festung Belgrad", subject: "Festung Belgrad", country: "Serbien", file: "P037152-661920 - Belgrade fortress stand at the downtown of Belgrade.jpg", width: 5514, height: 3419, author: "Oliver Bunic", license: "CC BY 4.0"},
    {title: "Stift Melk von Westen", subject: "Stift Melk von Westen", country: "Österreich", file: "Stift Melk Westseite 01.jpg", width: 16065, height: 10383, author: "Uoaei1", license: "CC BY-SA 4.0"},
    {title: "Limburger Dom", subject: "Limburger Dom", country: "Deutschland", file: "Cathedral Limburg - Limburger Dom - October 26th 2013 - 06.jpg", width: 6466, height: 4315, author: "Norbert Nagel", license: "CC BY-SA 3.0"},
    {title: "Burg Niedzica", subject: "Burg Niedzica", country: "Polen", file: "20170305 Niedzica zamek 5195.jpg", width: 4274, height: 2831, author: "Jakub Hałun", license: "CC BY-SA 4.0"},
    {title: "Festung Bourtzi auf Euböa", subject: "Festung Bourtzi auf Euböa", country: "Griechenland", file: "Bourtzi castle harbour Karystos Euboea Greece.jpg", width: 6000, height: 3663, author: "Jebulon", license: "CC0"},
    {title: "Marienburg an der Nogat", subject: "Marienburg an der Nogat", country: "Polen", file: "Castillo de Malbork, Polonia, 2013-05-19, DD 13.jpg", width: 5072, height: 2880, author: "Diego Delso", license: "CC BY-SA 3.0"},
    {title: "Bischofsburg Lidzbark Warmiński", subject: "Bischofsburg Lidzbark Warmiński", country: "Polen", file: "Lidzbark Warmiński 2023 16 Grabowski Palace Castle.jpg", width: 4512, height: 3000, author: "Scotch Mist", license: "CC BY-SA 4.0"},
    {title: "Storkyrkan und Königliches Schloss", subject: "Storkyrkan und Königliches Schloss", country: "Schweden", file: "Storkyrkan and Kungliga slottet Stockholm 2016 01.jpg", width: 4096, height: 2735, author: "Julian Herzog", license: "GFDL"},
    {title: "Steinbrücke in Skopje", subject: "Steinbrücke in Skopje", country: "Nordmazedonien", file: "03 Skopje.jpg", width: 4608, height: 3456, author: "Делфина", license: "CC BY-SA 3.0"},
    {title: "Schweriner Schloss", subject: "Schweriner Schloss", country: "Deutschland", file: "15-05-05-Schloß-Schwerin-RalfR-DSCF5191-2.jpg", width: 4736, height: 3158, author: "Ralf Roletschek", license: "GFDL 1.2"},
    {title: "Burg Eltz im Morgenlicht", subject: "Burg Eltz im Morgenlicht", country: "Deutschland", file: "Burg Eltz am frühen Morgen.jpg", width: 5307, height: 3462, author: "Johannes Dörrstock", license: "CC BY-SA 4.0"},
    {title: "Wartburg", subject: "Wartburg", country: "Deutschland", file: "Thuringia Eisenach asv2020-07 img23 Wartburg Castle.jpg", width: 7616, height: 4284, author: "A.Savin", license: "FAL"},
    {title: "Eilean Donan Castle", subject: "Eilean Donan Castle", country: "Vereinigtes Königreich", file: "Eilean Donan castle - 95mm.jpg", width: 4188, height: 2792, author: "Eusebius", license: "CC BY 3.0"},
    {title: "Schloss Chenonceau am Cher", subject: "Schloss Chenonceau am Cher", country: "Frankreich", file: "Chateau de Chenonceau 2008E.jpg", width: 5208, height: 2800, author: "Ra-smit / Derivative work", license: "GFDL"},
    {title: "Schloss Peleș", subject: "Schloss Peleș", country: "Rumänien", file: "\u0022Castelul Peles\u0022.JPG", width: 4608, height: 3456, author: "Bejan Neculai", license: "CC BY-SA 4.0"},
    {title: "Römerberg in Frankfurt", subject: "Römerberg in Frankfurt", country: "Deutschland", file: "Römerberg Frankfurt abends.jpg", width: 4478, height: 2985, author: "Thomas Wolf", license: "CC BY-SA 3.0"},
    {title: "Hamburger Speicherstadt am Abend", subject: "Hamburger Speicherstadt am Abend", country: "Deutschland", file: "Speicherstadt abends.jpg", width: 5565, height: 3325, author: "Thomas Wolf", license: "CC BY-SA 3.0"},
    {title: "Seebrücke Sellin am Abend", subject: "Seebrücke Sellin am Abend", country: "Deutschland", file: "Seebrücke Sellin abends.jpg", width: 5296, height: 3588, author: "Thomas Wolf", license: "CC BY-SA 3.0"},
    {title: "Neues Rathaus Hannover", subject: "Neues Rathaus Hannover", country: "Deutschland", file: "Neues Rathaus Hannover abends.jpg", width: 5055, height: 3654, author: "Thomas Wolf", license: "CC BY-SA 3.0 DE"},
    {title: "Bayerische Staatskanzlei", subject: "Bayerische Staatskanzlei", country: "Deutschland", file: "Gobierno Estatal de Bavaria, Múnich, Alemania, 2013-02-03, DD 04.JPG", width: 4742, height: 2953, author: "Diego Delso", license: "CC BY-SA 3.0"},
    {title: "Hauptbahnhof Helsinki", subject: "Hauptbahnhof Helsinki", country: "Finnland", file: "HelsinkiStationEntranceAndClockTower.jpg", width: 2736, height: 3648, author: "SebastianJFromTheBurg", license: "CC BY-SA 4.0"},
    {title: "Glockenturm der Kathedrale von Split", subject: "Glockenturm der Kathedrale von Split", country: "Kroatien", file: "Split Cathedral Bell Tower From The Vestibule - Split.jpg", width: 6000, height: 4000, author: "Sumitsurai", license: "CC BY-SA 4.0"},
    {title: "Alexander-Newski-Kathedrale in Sofia", subject: "Alexander-Newski-Kathedrale", country: "Bulgarien", file: "AlexanderNevskyCathedral-Sofia-6.jpg", width: 3127, height: 1986, author: "Plamen Agov", license: "CC BY-SA 4.0"},
    {title: "Mariä-Himmelfahrt-Kathedrale in Varna", subject: "Mariä-Himmelfahrt-Kathedrale in Varna", country: "Bulgarien", file: "Catedral de la Dormición de la Madre de Dios, Varna, Bulgaria, 2016-05-27, DD 109-111 HDR.jpg", width: 8135, height: 5628, author: "Diego Delso", license: "CC BY-SA 4.0"},
    {title: "Stabkirche Heddal", subject: "Stabkirche Heddal", country: "Norwegen", file: "Stavechurch-heddal.jpg", width: 3218, height: 2840, author: "Micha L. Rieser", license: "Attribution"},
    {title: "Dom des Heiligen Sava", subject: "Dom des Heiligen Sava", country: "Serbien", file: "Belgrado, chiesa di San Sava 01.jpg", width: 4190, height: 3143, author: "Syrio", license: "CC BY-SA 4.0"},
    {title: "Elisabeth-Dom in Košice", subject: "Elisabeth-Dom in Košice", country: "Slowakei", file: "St Elisabeth Cathedral Kosice.jpeg", width: 5946, height: 4511, author: "Ingo Mehling", license: "CC BY-SA 3.0"},
    {title: "Albaicín und Sacromonte", subject: "Albaicín und Sacromonte", country: "Spanien", file: "Albaicin 2012 San Nicolas Sacromonte.jpg", width: 3086, height: 2083, author: "Jebulon", license: "CC0"},
    {title: "Kathedrale von Santiago de Compostela", subject: "Kathedrale von Santiago de Compostela", country: "Spanien", file: "Santiago cathedral 2021.jpg", width: 3507, height: 4384, author: "Fernando", license: "CC BY-SA 4.0"},
    {title: "Triumphbogen im Jubelpark", subject: "Triumphbogen im Jubelpark", country: "Belgien", file: "Brussels Cinquantenaire R03.jpg", width: 3720, height: 2562, author: "Marc Ryckaert", license: "CC BY 3.0"},
    {title: "Arco da Rua Augusta in Lissabon", subject: "Arco da Rua Augusta in Lissabon", country: "Portugal", file: "Arco Triunfal da Rua Augusta, Plaza del Comercio, Lisboa, Portugal, 2012-05-12, DD 02.JPG", width: 4924, height: 3340, author: "Diego Delso", license: "CC BY-SA 3.0"},
    {title: "Jahrhunderthalle in Breslau", subject: "Jahrhunderthalle in Breslau", country: "Polen", file: "Wroclaw - Hala Stulecia 03.jpg", width: 4640, height: 3018, author: "Jar.ciurus", license: "CC BY-SA 3.0 PL"},
    {title: "WU-Campus in Wien", subject: "WU-Campus in Wien", country: "Österreich", file: "Campus WU LC D1 TC DSC 1440w.jpg", width: 5624, height: 3339, author: "P e z i", license: "CC BY-SA 3.0"},
    {title: "Stonehenge", subject: "Stonehenge", country: "Vereinigtes Königreich", file: "Stonehenge2007 07 30.jpg", width: 2816, height: 2112, author: "garethwiscombe", license: "CC BY 2.0"},
    {title: "Kettenbrücke in Budapest", subject: "Kettenbrücke in Budapest", country: "Ungarn", file: "Széchenyi Chain Bridge in Budapest at night.jpg", width: 3580, height: 2000, author: "Wilfredor", license: "CC0"},
    {title: "Feuerwerk über dem Ponte Vecchio", subject: "Feuerwerk über dem Ponte Vecchio", country: "Italien", file: "Fireworks over Ponte Vecchio.JPG", width: 4719, height: 3122, author: "Martin Falbisoner", license: "CC BY-SA 3.0"},
    {title: "Schloss Toompea", subject: "Schloss Toompea", country: "Estland", file: "Toompea loss 2014.jpg", width: 6000, height: 3334, author: "Abrget47j", license: "CC BY-SA 3.0"},
    {title: "Schloss Kadriorg", subject: "Schloss Kadriorg", country: "Estland", file: "Tallinn asv2022-04 img55 Kadriorg Palace.jpg", width: 6703, height: 3770, author: "A.Savin", license: "FAL"},
    {title: "Burg Turku", subject: "Burg Turku", country: "Finnland", file: "Turkucastle edit.jpg", width: 3917, height: 3141, author: "Otto Jula", license: "CC BY-SA 3.0"},
    {title: "Royal Pavilion in Brighton", subject: "Royal Pavilion in Brighton", country: "Vereinigtes Königreich", file: "Brighton royal pavilion Qmin.jpg", width: 5112, height: 3192, author: "Qmin", license: "CC BY-SA 3.0"},
    {title: "Kylemore Abbey", subject: "Kylemore Abbey", country: "Irland", file: "Kylemore October 2014-1a.jpg", width: 6311, height: 3820, author: "Alvesgaspar", license: "CC BY-SA 4.0"},
    {title: "Schwarzhäupterhaus in Riga", subject: "Schwarzhäupterhaus", country: "Lettland", file: "House of Blackheads (Riga) 20180808.jpg", width: 5184, height: 3456, author: "Suicasmo", license: "CC BY-SA 4.0"},
    {title: "Rigaer Schloss", subject: "Rigaer Schloss", country: "Lettland", file: "Castillo de Riga, Letonia, 2012-08-07, DD 04.JPG", width: 4152, height: 2939, author: "Diego Delso", license: "CC BY-SA 3.0"},
    {title: "Gediminas-Turm in Vilnius", subject: "Gediminas-Turm in Vilnius", country: "Litauen", file: "Gedimino kalnas 120.jpg", width: 4024, height: 2260, author: "Gytis Grižas https://www.wikidata.org/wiki/Q16452479", license: "CC BY-SA 4.0"},
    {title: "Kirche Sveti Jovan Kaneo", subject: "Kirche Sveti Jovan Kaneo", country: "Nordmazedonien", file: "Church of St. John at Kaneo 6.jpg", width: 5210, height: 3315, author: "kallerna", license: "CC BY-SA 4.0"},
    {title: "Rumänisches Athenäum", subject: "Rumänisches Athenäum", country: "Rumänien", file: "Ateneo Rumano, Bucarest, Rumanía, 2016-05-29, DD 73.jpg", width: 6592, height: 4963, author: "Diego Delso", license: "CC BY-SA 4.0"},
    {title: "Festung Kale in Skopje", subject: "Festung Kale in Skopje", country: "Nordmazedonien", file: "KaleFortress-Skopje1.JPG", width: 3648, height: 2736, author: "Yemc", license: "Public domain"},
    {title: "Klosterkirche Curtea de Argeș", subject: "Klosterkirche Curtea de Argeș", country: "Rumänien", file: "Man Curtea de Arges.SV.jpg", width: 4221, height: 2896, author: "Alexandru Baboş Albabos", license: "CC BY 3.0"},
    {title: "Festung Golubac", subject: "Festung Golubac", country: "Serbien", file: "Golubac Fortress (град Голубац).jpg", width: 10368, height: 7776, author: "Petar Milošević", license: "CC BY-SA 4.0"},
    {title: "Schloss Rundāle", subject: "Schloss Rundāle", country: "Lettland", file: "Rundale Palace (6483271573).jpg", width: 4272, height: 2848, author: "Arian Zwegers", license: "CC BY 2.0"},
    {title: "Schloss Bojnice", subject: "Schloss Bojnice", country: "Slowakei", file: "Bojnice (Bojnitz) Castle (by Pudelek).jpg", width: 3633, height: 2838, author: "Pudelek (talk)", license: "CC BY-SA 3.0"},
    {title: "Fischerbastei", subject: "Fischerbastei", country: "Ungarn", file: "Halászbástya 2017.jpg", width: 3456, height: 4608, author: "Brian Adamson", license: "CC BY 2.0"},
    {title: "Blarney Castle", subject: "Blarney Castle", country: "Irland", file: "Blarney Castle Ireland.jpg", width: 4934, height: 3289, author: "Ryanhuntmuzik", license: "CC BY-SA 4.0"},
    {title: "Ålesund vom Aksla", subject: "Ålesund vom Aksla", country: "Norwegen", file: "Vista de Ålesund desde Aksla, Noruega, 2019-09-01, DD 16.jpg", width: 6980, height: 4094, author: "Diego Delso", license: "CC BY-SA 4.0"},
    {title: "Kathedrale von Vilnius", subject: "Kathedrale von Vilnius", country: "Litauen", file: "Vilnius Cathedral 20.jpg", width: 6016, height: 4000, author: "Scotch Mist", license: "CC BY-SA 4.0"},
    {title: "Elbphilharmonie und Hamburger Hafen", subject: "Elbphilharmonie und Hamburger Hafen", country: "Deutschland", file: "Hamburg, HafenCity, Elbphilharmonie -- 2016 -- 3062.jpg", width: 5472, height: 3648, author: "Dietmar Rabich", license: "CC BY-SA 4.0"},
    {title: "Inselkirche Gospa od Škrpjela", subject: "Inselkirche Gospa od Škrpjela", country: "Montenegro", file: "Nuestra Señora de las Rocas, Perast, Bahía de Kotor, Montenegro, 2014-04-19, DD 19.JPG", width: 5616, height: 3330, author: "Diego Delso", license: "CC BY-SA 4.0"},
    {title: "Stadt der Künste und Wissenschaften", subject: "Stadt der Künste und Wissenschaften", country: "Spanien", file: "Hemispheric Twilight - Valencia, Spain - Jan 2007.jpg", width: 10598, height: 5656, author: "Diliff", license: "CC BY-SA 3.0"},
    {title: "Burg Kaunas", subject: "Burg Kaunas", country: "Litauen", file: "Kaunas castle 20160603.jpg", width: 4808, height: 3097, author: "Skelanard", license: "CC BY-SA 4.0"},
    {title: "Atomium in Brüssel", subject: "Atomium in Brüssel", country: "Belgien", file: "2017-10-17-bruessel-atomium-04.jpg", width: 5184, height: 3456, author: "Axel Kirch", license: "CC BY-SA 4.0"},
    {title: "Erlöserkirche Kopenhagen", subject: "Erlöserkirche Kopenhagen", country: "Dänemark", file: "Copenhagen - Church of Our Saviour - 2013.jpg", width: 2785, height: 4336, author: "Avda", license: "CC BY-SA 3.0"},
    {title: "Opernhaus Kopenhagen", subject: "Opernhaus Kopenhagen", country: "Dänemark", file: "Copenhagen Opera House - side view.jpg", width: 3981, height: 2149, author: "James Cridland", license: "CC BY 2.0"},
    {title: "Öresundbrücke", subject: "Öresundbrücke", country: "Dänemark / Schweden", file: "Øresund Bridge from the air in September 2015.jpg", width: 4000, height: 3000, author: "Nick-D", license: "CC BY-SA 4.0"},
    {title: "Rijksmuseum Amsterdam", subject: "Rijksmuseum Amsterdam", country: "Niederlande", file: "South facade of the Rijksmuseum Amsterdam (DSCF0528).jpg", width: 4291, height: 3123, author: "Trougnouf (Benoit Brummer)", license: "CC BY 4.0"},
    {title: "Rathaus von Subotica", subject: "Rathaus von Subotica", country: "Serbien", file: "Градска кућа у Суботици - централни детаљни приказ.jpg", width: 6000, height: 4000, author: "Sunce Niš", license: "CC BY-SA 4.0"},
    {title: "Frankfurter Altstadt und Skyline", subject: "Frankfurter Altstadt und Skyline", country: "Deutschland", file: "Frankfurter Altstadt mit Skyline 2012-04.jpg", width: 3972, height: 2648, author: "Thomas Wolf", license: "CC BY-SA 3.0"},
    {title: "Frankfurter Skyline bei Nacht", subject: "Frankfurter Skyline bei Nacht", country: "Deutschland", file: "Frankfurt Skyline 2022 bei Nacht.jpg", width: 6221, height: 4000, author: "Jörg Braukmann", license: "CC BY-SA 4.0"},
    {title: "Canary Wharf an der Themse", subject: "Canary Wharf an der Themse", country: "Vereinigtes Königreich", file: "Canary Wharf from Limehouse London June 2016 HDR.jpg", width: 4800, height: 2700, author: "King of Hearts", license: "CC BY-SA 4.0"},
    {title: "Schloss Greyerz", subject: "Schloss Greyerz", country: "Schweiz", file: "12 Chateau de Gruyères Photo by Giles Laurent.jpg", width: 3584, height: 2016, author: "Giles Laurent", license: "CC BY-SA 4.0"},
    {title: "Alter Basar von Skopje", subject: "Alter Basar von Skopje", country: "Nordmazedonien", file: "Поглед кон Сули Ан и Старата скопска чаршија.JPG", width: 4592, height: 3056, author: "Stotosenik", license: "CC BY-SA 3.0"},
    {title: "Avala-Turm bei Belgrad", subject: "Avala-Turm bei Belgrad", country: "Serbien", file: "Avala Tower amazing.jpg", width: 5774, height: 7166, author: "AlexShotss", license: "CC BY 4.0"},
    {title: "Blaue Kirche in Bratislava", subject: "Blaue Kirche in Bratislava", country: "Slowakei", file: "Blue Church, Bratislava 02.jpg", width: 3598, height: 3745, author: "Thomas Ledl", license: "CC BY-SA 4.0"},
    {title: "Arwaburg", subject: "Arwaburg", country: "Slowakei", file: "Oravský hrad (celkový pohled).jpg", width: 5184, height: 3456, author: "Lynx1211", license: "CC BY-SA 4.0"},
    {title: "Dubrovnik und die Adria", subject: "Dubrovnik und die Adria", country: "Kroatien", file: "Casco viejo de Dubrovnik, Croacia, 2014-04-14, DD 04.JPG", width: 5218, height: 2840, author: "Diego Delso", license: "CC BY-SA 3.0"},
    {title: "Höhlenburg Predjama", subject: "Höhlenburg Predjama", country: "Slowenien", file: "Höhlenburg Predjama in Slovenien.jpg", width: 5472, height: 3648, author: "Lettkemann", license: "CC BY-SA 4.0"},
    {title: "Todi in Umbrien", subject: "Todi in Umbrien", country: "Italien", file: "Todi panorama.jpg", width: 5849, height: 3697, author: "Livioandronico2013", license: "CC BY-SA 4.0"},
    {title: "Bitola und die Pelagonische Ebene", subject: "Bitola und die Pelagonische Ebene", country: "Nordmazedonien", file: "Битола и Пелагонија од Националниот парк Пелистер.jpg", width: 4927, height: 3263, author: "Шпиц", license: "CC BY-SA 4.0"},
    {title: "Potsdamer Platz in Berlin", subject: "Potsdamer Platz in Berlin", country: "Deutschland", file: "Potsdamer Platz, Berlin, 151024, ako.jpg", width: 10000, height: 5626, author: "Ansgar Koreng", license: "CC BY-SA 3.0 DE"},
    {title: "Donau City in Wien", subject: "Donau City in Wien", country: "Österreich", file: "Donau City Vienna from Donauinsel on 2014-08-28 crop.png", width: 5760, height: 3240, author: "Robert F. Tobler", license: "CC BY-SA 4.0"},
    {title: "Kirche von Bojana", subject: "Kirche von Bojana", country: "Bulgarien", file: "Boyana Church 2 TB.JPG", width: 3648, height: 2736, author: "Todor Bozhinov / Тодор Божинов", license: "CC BY-SA 3.0"},
    {title: "Kloster Batschkowo", subject: "Kloster Batschkowo", country: "Bulgarien", file: "Church of the Dormition, Bachkovo Monastery 01.jpg", width: 3888, height: 2592, author: "Kritzolina", license: "CC BY-SA 4.0"},
    {title: "Kranhäuser im Kölner Rheinauhafen", subject: "Kranhäuser im Kölner Rheinauhafen", country: "Deutschland", file: "Kranhäuser Cologne, April 2018 -01.jpg", width: 5078, height: 2804, author: "Martin Falbisoner", license: "CC BY-SA 4.0"},
    {title: "Dom zu Riga", subject: "Dom zu Riga", country: "Lettland", file: "Riga Petrikirche Blick vom Turm zum Dom 3.JPG", width: 3354, height: 4287, author: "Zairon", license: "CC BY-SA 4.0"},
    {title: "Forum Romanum vom Vittoriano", subject: "Forum Romanum vom Vittoriano", country: "Italien", file: "Foro Romano visto dal Vittoriano Roma.jpg", width: 11183, height: 6152, author: "Wolfgang Moroder", license: "CC BY-SA 3.0"},
    {title: "Stadtmauern von Dubrovnik", subject: "Stadtmauern von Dubrovnik", country: "Kroatien", file: "29.12.16 Dubrovnik Evening 21 (31847480831).jpg", width: 5472, height: 3648, author: "donald judge", license: "CC BY 2.0"},
    {title: "Friedenspalast in Den Haag", subject: "Friedenspalast in Den Haag", country: "Niederlande", file: "Friedenspalast Den Haag (100MP).jpg", width: 11089, height: 9020, author: "Thomas Wolf, www.foto-tw.de", license: "CC BY-SA 3.0 de"},
    {title: "Tübinger Neckarfront", subject: "Tübinger Neckarfront", country: "Deutschland", file: "Tübingen - Altstadt - Neckarfront - Ansicht von Neckarinsel mit Stocherkahn.jpg", width: 7287, height: 4796, author: "Roman Eisele", license: "CC BY-SA 4.0"},
    {title: "Zürich und der Zürichsee", subject: "Zürich und der Zürichsee", country: "Schweiz", file: "Zürich view Quaibrücke 20200702.jpg", width: 12732, height: 6619, author: "Daniel Kraft", license: "CC BY-SA 3.0"},
    {title: "Drachenbrücke in Ljubljana", subject: "Drachenbrücke in Ljubljana", country: "Slowenien", file: "Dragons Bridge, Ljubljana 2.jpg", width: 6000, height: 4000, author: "Thomas Ledl", license: "CC BY-SA 4.0"},
    {title: "Burg Gravensteen", subject: "Burg Gravensteen", country: "Belgien", file: "Gent Gravensteen R01.jpg", width: 4088, height: 2945, author: "Marc Ryckaert (MJJR)", license: "CC BY 3.0"},
    {title: "Poseidontempel am Kap Sounion", subject: "Poseidontempel am Kap Sounion", country: "Griechenland", file: "Greece Cape Sounion BW 2017-10-09 10-12-43.jpg", width: 5580, height: 3972, author: "Berthold Werner", license: "CC BY-SA 3.0"},
    {title: "Freiheitsdenkmal in Riga", subject: "Freiheitsdenkmal in Riga", country: "Lettland", file: "0873 LVA Riga freedom monument SE.jpg", width: 4267, height: 8463, author: "Virtual-Pano", license: "CC BY-SA 4.0"},
    {title: "Amphitheater von Pula", subject: "Amphitheater von Pula", country: "Kroatien", file: "Pula Arena (2024-10-10 1).jpg", width: 4032, height: 3024, author: "Olgierd Rudak", license: "CC BY-SA 4.0"},
    {title: "Duisburger Innenhafen am Abend", subject: "Duisburger Innenhafen am Abend", country: "Deutschland", file: "Duisburger Innenhafen Five Boats Abend 2014.jpg", width: 4854, height: 2582, author: "Tuxyso", license: "CC BY-SA 3.0"},
    {title: "Königlicher Palast Amsterdam", subject: "Königlicher Palast Amsterdam", country: "Niederlande", file: "Palacio Real, Ámsterdam, Países Bajos, 2016-05-30, DD 07-09 HDR.jpg", width: 7846, height: 5634, author: "Diego Delso", license: "CC BY-SA 4.0"},
    {title: "Stockholmer Schloss", subject: "Stockholmer Schloss", country: "Schweden", file: "The Royal Palace (15891592359).jpg", width: 6946, height: 4427, author: "Magnus Johansson", license: "CC BY-SA 2.0"},
    {title: "Hauptbahnhof Antwerpen", subject: "Hauptbahnhof Antwerpen", country: "Belgien", file: "Antwerpen - Station Antwerpen-Centraal (11).jpg", width: 5106, height: 3685, author: "Fred Romero from Paris, France", license: "CC BY 2.0"},
    {title: "Busludscha-Denkmal", subject: "Busludscha-Denkmal", country: "Bulgarien", file: "Sunset and Buzludza.jpg", width: 3701, height: 2478, author: "Annboeva", license: "CC BY-SA 4.0"},
    {title: "Markusturm und Dogenpalast", subject: "Markusturm und Dogenpalast", country: "Italien", file: "Saint Mark's Campanile and Palazzo Ducale, Venice, September 2017 -2.jpg", width: 4597, height: 2366, author: "Martin Falbisoner", license: "CC BY-SA 4.0"},
    {title: "Odeon des Herodes Atticus", subject: "Odeon des Herodes Atticus", country: "Griechenland", file: "Odeon of Herodes Atticus (34580450331).jpg", width: 4598, height: 2874, author: "Robert Anders from Hamburg, Germany", license: "CC BY 2.0"},
    {title: "Salzburger Altstadt im goldenen Abendlicht", subject: "Salzburger Altstadt im goldenen Abendlicht", country: "Österreich", file: "Salzburg Altstadt Panorama 20240728 Gold P.jpg", width: 13200, height: 6720, author: "Uoaei1", license: "CC BY-SA 4.0"},
    {title: "Trajansforum und Rom bei Nacht", subject: "Trajansforum und Rom bei Nacht", country: "Italien", file: "Foro Traiano dal Vittoriano Roma sera.jpg", width: 11119, height: 6195, author: "Wolfgang Moroder", license: "CC BY-SA 3.0"},
    {title: "Diokletianpalast in Split", subject: "Diokletianpalast in Split", country: "Kroatien", file: "Croatia-01239 - The Peristil (9551533404).jpg", width: 4000, height: 6000, author: "Dennis G. Jarvis", license: "CC BY-SA 2.0"},
    {title: "Lettische Nationaloper", subject: "Lettische Nationaloper", country: "Lettland", file: "Opera Nacional, Riga, Letonia, 2012-08-07, DD 04.JPG", width: 5209, height: 2817, author: "Diego Delso", license: "CC BY-SA 3.0"},
    {title: "Erasmusbrücke in Rotterdam", subject: "Erasmusbrücke in Rotterdam", country: "Niederlande", file: "Erasmusbrug, September 2019.jpg", width: 5530, height: 3202, author: "Martin Falbisoner", license: "CC BY-SA 4.0"},
    {title: "Dom zu Uppsala", subject: "Dom zu Uppsala", country: "Schweden", file: "Uppsala cathedral from southwest 02.jpg", width: 3114, height: 5544, author: "Szilas", license: "Public domain"},
    {title: "Hephaistostempel in Athen", subject: "Hephaistostempel in Athen", country: "Griechenland", file: "Temple of Hephaestus viewed from the Stoa of Attalos in Athens, Greece.jpg", width: 5431, height: 3766, author: "Julian Lupyan", license: "CC0"},
    {title: "Wawel in Krakau", subject: "Wawel in Krakau", country: "Polen", file: "02022 0371 Wawel Castle.jpg", width: 4110, height: 2633, author: "Silar", license: "CC BY-SA 4.0"},
    {title: "Abteikirche Saint-Ouen in Rouen", subject: "Abteikirche Saint-Ouen in Rouen", country: "Frankreich", file: "Panorama of Abbatiale Saint-Ouen (30268716114).jpg", width: 6107, height: 4649, author: "Jorge Láscar", license: "CC BY 2.0"},
    {title: "Westminster-Palast im Panorama", subject: "Westminster-Palast im Panorama", country: "Vereinigtes Königreich", file: "Palace-of-westminster-panorama-3.jpeg", width: 5828, height: 3975, author: "Rob.ng15", license: "CC BY 3.0"},
    {title: "Kathedrale von Zagreb", subject: "Kathedrale von Zagreb", country: "Kroatien", file: "Zagreb Cathedral 02.jpg", width: 2835, height: 4253, author: "Bernard Gagnon", license: "CC BY-SA 4.0"},
    {title: "Viadukt von Millau und Tarn-Tal", subject: "Viadukt von Millau und Tarn-Tal", country: "Frankreich", file: "Panorama de la vallée de Millau.jpg", width: 5994, height: 3781, author: "Tobi 87", license: "CC BY-SA 3.0"},
    {title: "Kubushäuser in Rotterdam", subject: "Kubushäuser in Rotterdam", country: "Niederlande", file: "GraphyArchy - Wikipedia 00096.jpg", width: 4500, height: 3000, author: "GraphyArchy", license: "CC BY-SA 4.0"},
    {title: "Mailänder Dom und Domplatz", subject: "Mailänder Dom und Domplatz", country: "Italien", file: "Milán, Duomo, katedrála.jpg", width: 12104, height: 6288, author: "Aktron", license: "CC BY 3.0"},
    {title: "Schloss Kalmar", subject: "Schloss Kalmar", country: "Schweden", file: "1285Kalmar slott.jpg", width: 5568, height: 3712, author: "L.G.foto", license: "CC BY-SA 4.0"},
    {title: "Markuskirche in Zagreb", subject: "Markuskirche in Zagreb", country: "Kroatien", file: "Zagreb Church of St. Mark (34411766366).jpg", width: 3946, height: 2630, author: "Jorge Franganillo", license: "CC BY 2.0"},
    {title: "Hauptbahnhof Rotterdam", subject: "Hauptbahnhof Rotterdam", country: "Niederlande", file: "Rtd CS-III.JPG", width: 4288, height: 2848, author: "Spoorjan", license: "CC BY-SA 3.0"},
    {title: "Brüsseler Grand-Place im Panorama", subject: "Brüsseler Grand-Place im Panorama", country: "Belgien", file: "Grand-Place, Brussels - panorama, June 2018.jpg", width: 10946, height: 6226, author: "Celuici", license: "CC BY-SA 4.0"},
    {title: "Rila-Kloster im Gebirgspanorama", subject: "Rila-Kloster im Gebirgspanorama", country: "Bulgarien", file: "Рилски манастир Panorama.jpg", width: 5669, height: 3670, author: "CHILIEV", license: "CC BY-SA 4.0"},
    {title: "Schloss Örebro", subject: "Schloss Örebro", country: "Schweden", file: "Örebro slott.jpg", width: 3148, height: 2110, author: "siehe Dateiseite", license: "CC0"},
    {title: "Kirche von Kiruna", subject: "Kirche von Kiruna", country: "Schweden", file: "Church of Kiruna 2011.jpg", width: 3914, height: 2596, author: "Heinz-Josef Lücking", license: "CC BY-SA 3.0 de"},
    {title: "Alcázar von Segovia", subject: "Alcázar von Segovia", country: "Spanien", file: "Panorámica Otoño Alcázar de Segovia.jpg", width: 3955, height: 2966, author: "Ángel Sanz de Andrés", license: "CC BY-SA 4.0"},
    {title: "Arc de Triomphe", subject: "Arc de Triomphe", country: "Frankreich", file: "Arc de Triomphe, Paris 21 October 2010.jpg", width: 4192, height: 3168, author: "Jiuguang Wang", license: "CC BY-SA 2.0"},
    {title: "Kulturpalast in Warschau", subject: "Kulturpalast in Warschau", country: "Polen", file: "Pałac Kultury i Nauki 2019.jpg", width: 4533, height: 7019, author: "Adrian Grycuk", license: "CC BY-SA 3.0 pl"},
    {title: "Kathedrale von Sevilla", subject: "Kathedrale von Sevilla", country: "Spanien", file: "Sevilla Cathedral - Southeast.jpg", width: 3900, height: 2908, author: "Ingo Mehling", license: "CC BY-SA 4.0"},
    {title: "Big Ben und Westminster", subject: "Big Ben und Westminster", country: "Vereinigtes Königreich", file: "Elizabeth Tower and the north front of the Palace of Westminster, London.jpg", width: 4347, height: 7728, author: "Christian David", license: "CC BY-SA 4.0"},
    {title: "Kathedrale Notre-Dame", subject: "Kathedrale Notre-Dame", country: "Frankreich", file: "Notre-Dame de Paris, 4 October 2017.jpg", width: 4938, height: 3261, author: "Ali Sabbagh", license: "CC0"},
    {title: "Marienkirche in Krakau", subject: "Marienkirche in Krakau", country: "Polen", file: "Church of Our Lady Assumed into Heaven, 5 Mariacki square, Old Town, Kraków, Poland.jpg", width: 5666, height: 3949, author: "Zygmunt Put", license: "CC BY-SA 4.0"},
    {title: "Clifton Suspension Bridge", subject: "Clifton Suspension Bridge", country: "Vereinigtes Königreich", file: "Clifton Suspension Bridge-9350.jpg", width: 3525, height: 2350, author: "Gothick", license: "CC BY-SA 3.0"},
    {title: "Louvre-Palast", subject: "Louvre-Palast", country: "Frankreich", file: "West facade of the Cour Carrée, Louvre Palace, Paris 5 October 2017.jpg", width: 5292, height: 3442, author: "Ali Sabbagh", license: "CC0"},
    {title: "Wilanów-Palast", subject: "Wilanów-Palast", country: "Polen", file: "Garden facade of the Wilanów Palace, 2019, 02.jpg", width: 4032, height: 2619, author: "Chris Olszewski", license: "CC BY-SA 4.0"},
    {title: "Kathedrale von Durham", subject: "Kathedrale von Durham", country: "Vereinigtes Königreich", file: "Durham MMB 02 Cathedral.jpg", width: 4668, height: 2814, author: "mattbuck (category)", license: "CC BY-SA 4.0"},
    {title: "Schloss Chenonceau", subject: "Schloss Chenonceau", country: "Frankreich", file: "Chateau de Chenonceau 2008E (adjusted2).jpg", width: 3885, height: 2595, author: "It is a derivative work of Ra-smit's photo.", license: "GFDL"},
    {title: "Kloster Jasna Góra", subject: "Kloster Jasna Góra", country: "Polen", file: "Częstochowa klasztor Jasna Góra-2162.jpg", width: 4717, height: 3124, author: "Jerzy Szota", license: "CC BY-SA 3.0 pl"},
    {title: "Tower of London", subject: "Tower of London", country: "Vereinigtes Königreich", file: "Tower of London from the Shard (8515883950).jpg", width: 4728, height: 3069, author: "[Duncan] from Nottingham, UK", license: "CC BY 2.0"},
    {title: "Breslauer Rathaus", subject: "Breslauer Rathaus", country: "Polen", file: "Old Town Hall in Wrocław, September 2022 07.jpg", width: 4000, height: 3000, author: "Szczecinolog", license: "CC BY-SA 4.0"},
    {title: "Pantheon in Rom", subject: "Pantheon in Rom", country: "Italien", file: "Pantheon (Rome) - Right side and front.jpg", width: 7512, height: 6048, author: "NikonZ7II", license: "CC BY-SA 4.0"},
    {title: "Burgpalast in Budapest", subject: "Burgpalast in Budapest", country: "Ungarn", file: "Budavári Palota, ABCDEF épület.jpg", width: 3568, height: 2408, author: "Varius", license: "CC BY-SA 3.0"},
    {title: "Palazzo Vecchio in Florenz", subject: "Palazzo Vecchio in Florenz", country: "Italien", file: "Piazza della signoria, palazzo vecchio, veduta 01.jpg", width: 4040, height: 4354, author: "Francesco Bini", license: "CC BY-SA 4.0"},
    {title: "Dresdner Frauenkirche", subject: "Dresdner Frauenkirche", country: "Deutschland", file: "100130 150006 Dresden Frauenkirche winter blue sky-2.jpg", width: 3075, height: 4559, author: "Netopyr", license: "CC BY-SA 3.0"},
    {title: "Riddarholmskirche", subject: "Riddarholmskirche", country: "Schweden", file: "Rhkyrkan fr staden.jpg", width: 2562, height: 3054, author: "Alexandru Baboş Albabos", license: "CC BY 3.0"},
    {title: "Castel del Monte", subject: "Castel del Monte", country: "Italien", file: "Castel del Monte - Andria.jpg", width: 8294, height: 5966, author: "ParisTaras", license: "CC BY-SA 4.0"},
    {title: "Heidelberger Schloss", subject: "Heidelberger Schloss", country: "Deutschland", file: "Heidelberg-2726936.jpg", width: 5919, height: 3365, author: "Motatcho", license: "CC BY-SA 4.0"},
    {title: "Großfürstenpalast von Litauen", subject: "Großfürstenpalast von Litauen", country: "Litauen", file: "Palace of the Grand Dukes of Lithuania (October 4, 2015).jpg", width: 5147, height: 2956, author: "aivas14", license: "CC BY 2.0"},
    {title: "Dom von Siena", subject: "Dom von Siena", country: "Italien", file: "Duomo di Siena-9635.jpg", width: 3164, height: 2845, author: "Raimond Spekking", license: "CC BY-SA 4.0"},
    {title: "Drei Brücken und Prešerenplatz", subject: "Drei Brücken und Prešerenplatz", country: "Slowenien", file: "Triple Bridge and Preseren Square fron the Ljubljanica.jpg", width: 5184, height: 3456, author: "Valerio2468", license: "CC BY-SA 4.0"},
    {title: "Schloss Sanssouci", subject: "Schloss Sanssouci", country: "Deutschland", file: "Schloss Sanssouci 2014.jpg", width: 3264, height: 2448, author: "ernstol", license: "CC BY-SA 3.0"},
    {title: "Palast von Caserta", subject: "Palast von Caserta", country: "Italien", file: "Aerial image of the Palace of Caserta (view from the south).jpg", width: 5200, height: 3400, author: "Carsten Steger", license: "CC BY-SA 4.0"},
    {title: "Markusdom in Venedig", subject: "Markusdom in Venedig", country: "Italien", file: "Venezia Basilica di San Marco Fassade 2.jpg", width: 4574, height: 3066, author: "Zairon", license: "Public domain"},
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
