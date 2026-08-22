(() => {
  "use strict";
  const OVERLOAD_STORAGE_KEY = "eea-europa-overload";

  function highResolutionImage(file) {
    return `https://commons.wikimedia.org/wiki/Special:Redirect/file/${encodeURIComponent(file)}?width=3840`;
  }

  const WALLPAPERS = Object.freeze([
    {title: "Akropolis bei Nacht", country: "Griechenland", file: "1029 Acropolis of Athens in Greece at night Photo by Giles Laurent.jpg", author: "Giles Laurent", license: "CC BY-SA 4.0", image: "https://upload.wikimedia.org/wikipedia/commons/thumb/2/2c/1029_Acropolis_of_Athens_in_Greece_at_night_Photo_by_Giles_Laurent.jpg/1920px-1029_Acropolis_of_Athens_in_Greece_at_night_Photo_by_Giles_Laurent.jpg"},
    {title: "Eiffelturm", country: "Frankreich", file: "Tour Eiffel Wikimedia Commons (cropped).jpg", author: "Benh LIEU SONG", license: "Public Domain", image: "https://upload.wikimedia.org/wikipedia/commons/thumb/8/85/Tour_Eiffel_Wikimedia_Commons_%28cropped%29.jpg/1920px-Tour_Eiffel_Wikimedia_Commons_%28cropped%29.jpg"},
    {title: "Oia auf Santorin", country: "Griechenland", file: "Oia sunset - panoramio (2).jpg", author: "TomasEE", license: "CC BY 3.0", image: "https://upload.wikimedia.org/wikipedia/commons/thumb/3/37/Oia_sunset_-_panoramio_%282%29.jpg/1920px-Oia_sunset_-_panoramio_%282%29.jpg"},
    {title: "Glencoe", country: "Vereinigtes Königreich", file: "GlencoeVillage.jpg", author: "Simonm72", license: "CC BY 3.0", image: "https://upload.wikimedia.org/wikipedia/commons/thumb/2/21/GlencoeVillage.jpg/1920px-GlencoeVillage.jpg"},
    {title: "Lavendelfelder der Provence", country: "Frankreich", file: "Lavender field and Mont Ventoux.jpg", author: "Robert Brink", license: "CC BY-SA 3.0", image: "https://upload.wikimedia.org/wikipedia/commons/thumb/0/03/Lavender_field_and_Mont_Ventoux.jpg/1920px-Lavender_field_and_Mont_Ventoux.jpg"},
    {title: "Kolosseum", country: "Italien", file: "Colosseo 2020.jpg", author: "FeaturedPics", license: "CC BY-SA 4.0", image: "https://upload.wikimedia.org/wikipedia/commons/thumb/d/de/Colosseo_2020.jpg/1920px-Colosseo_2020.jpg"},
    {title: "Altstadt von Dubrovnik", country: "Kroatien", file: "The walls of the fortress and View of the old city. panorama.jpg", author: "Zysko serhii", license: "CC BY-SA 4.0", image: "https://upload.wikimedia.org/wikipedia/commons/thumb/6/67/The_walls_of_the_fortress_and_View_of_the_old_city._panorama.jpg/1920px-The_walls_of_the_fortress_and_View_of_the_old_city._panorama.jpg"},
    {title: "Dolomiten bei Cortina", country: "Italien", file: "Faloria Cortina d'Ampezzo 10.jpg", author: "kallerna", license: "CC BY-SA 4.0", image: "https://upload.wikimedia.org/wikipedia/commons/thumb/3/36/Faloria_Cortina_d%27Ampezzo_10.jpg/1920px-Faloria_Cortina_d%27Ampezzo_10.jpg"},
    {title: "Tower Bridge im Morgenlicht", country: "Vereinigtes Königreich", file: "Tower Bridge at Dawn.jpg", author: "Fuzzypiggy", license: "CC BY-SA 3.0", image: "https://upload.wikimedia.org/wikipedia/commons/thumb/5/59/Tower_Bridge_at_Dawn.jpg/1920px-Tower_Bridge_at_Dawn.jpg"},
    {title: "Kölner Dom", country: "Deutschland", file: "Kölner Dom - Westfassade 2022 ohne Gerüst-0968 b.jpg", author: "Raimond Spekking", license: "CC BY-SA 4.0", image: "https://upload.wikimedia.org/wikipedia/commons/thumb/0/04/K%C3%B6lner_Dom_-_Westfassade_2022_ohne_Ger%C3%BCst-0968_b.jpg/1920px-K%C3%B6lner_Dom_-_Westfassade_2022_ohne_Ger%C3%BCst-0968_b.jpg"},
    {title: "Schloss Chambord", country: "Frankreich", file: "Aerial image of Château de Chambord (view from the southeast).jpg", author: "Carsten Steger", license: "CC BY-SA 4.0", image: "https://upload.wikimedia.org/wikipedia/commons/thumb/1/1f/Aerial_image_of_Ch%C3%A2teau_de_Chambord_%28view_from_the_southeast%29.jpg/1920px-Aerial_image_of_Ch%C3%A2teau_de_Chambord_%28view_from_the_southeast%29.jpg"},
    {title: "Klöster von Meteora", country: "Griechenland", file: "Meteora's monastery 2.jpg", author: "Stathis floros", license: "CC BY-SA 4.0", image: "https://upload.wikimedia.org/wikipedia/commons/thumb/7/7c/Meteora%27s_monastery_2.jpg/1920px-Meteora%27s_monastery_2.jpg"},
    {title: "Schloss Schönbrunn", country: "Österreich", file: "Wien - Schloss Schönbrunn.JPG", author: "C.Stadler/Bwag", license: "CC BY-SA 4.0", image: "https://upload.wikimedia.org/wikipedia/commons/thumb/c/c9/Wien_-_Schloss_Sch%C3%B6nbrunn.JPG/1920px-Wien_-_Schloss_Sch%C3%B6nbrunn.JPG"},
    {title: "Gamla Stan", country: "Schweden", file: "Gamla stan September 2014 01.jpg", author: "Arild Vågen", license: "CC BY-SA 4.0", image: "https://upload.wikimedia.org/wikipedia/commons/thumb/8/8a/Gamla_stan_September_2014_01.jpg/1920px-Gamla_stan_September_2014_01.jpg"},
    {title: "Dom von Florenz", country: "Italien", file: "Cattedrale di Santa Maria del Fiore – Il Duomo di Firenze.jpg", author: "Gary Campbell-Hall", license: "CC BY 2.0", image: "https://upload.wikimedia.org/wikipedia/commons/thumb/c/c7/Cattedrale_di_Santa_Maria_del_Fiore_%E2%80%93_Il_Duomo_di_Firenze.jpg/1920px-Cattedrale_di_Santa_Maria_del_Fiore_%E2%80%93_Il_Duomo_di_Firenze.jpg"},
    {title: "Schloss Neuschwanstein", country: "Deutschland", file: "Schloss Neuschwanstein 2013.jpg", author: "Thomas Wolf", license: "CC BY-SA 3.0 DE", image: "https://upload.wikimedia.org/wikipedia/commons/thumb/f/f8/Schloss_Neuschwanstein_2013.jpg/1920px-Schloss_Neuschwanstein_2013.jpg"},
    {title: "Mont-Saint-Michel", country: "Frankreich", file: "Mont-Saint-Michel vu du ciel.jpg", author: "Amaustan", license: "CC BY-SA 4.0", image: "https://upload.wikimedia.org/wikipedia/commons/thumb/7/78/Mont-Saint-Michel_vu_du_ciel.jpg/1920px-Mont-Saint-Michel_vu_du_ciel.jpg"},
    {title: "Matterhorn", country: "Schweiz", file: "Matterhorn from Domhütte - 2.jpg", author: "chil / Zacharie Grossen", license: "CC BY-SA 3.0", image: "https://upload.wikimedia.org/wikipedia/commons/6/60/Matterhorn_from_Domh%C3%BCtte_-_2.jpg"},
    {title: "Lauterbrunnental", country: "Schweiz", file: "1 lauterbrunnen valley wengen 2022.jpg", author: "Chensiyuan", license: "CC BY-SA 4.0", image: "https://upload.wikimedia.org/wikipedia/commons/thumb/2/29/1_lauterbrunnen_valley_wengen_2022.jpg/1920px-1_lauterbrunnen_valley_wengen_2022.jpg"},
    {title: "Plitvicer Seen", country: "Kroatien", file: "View in Plitvice Lakes National Park.jpg", author: "Zysko serhii", license: "CC BY-SA 4.0", image: "https://upload.wikimedia.org/wikipedia/commons/thumb/3/39/View_in_Plitvice_Lakes_National_Park.jpg/1920px-View_in_Plitvice_Lakes_National_Park.jpg"},
    {title: "Bucht von Kotor", country: "Montenegro", file: "Kotor aerial 1.jpg", author: "kallerna", license: "CC BY-SA 4.0", image: "https://upload.wikimedia.org/wikipedia/commons/thumb/b/b2/Kotor_aerial_1.jpg/1920px-Kotor_aerial_1.jpg"},
    {title: "Hallstatt", country: "Österreich", file: "Hallstatt - Zentrum .JPG", author: "C.Stadler/Bwag", license: "CC BY-SA 4.0", image: "https://upload.wikimedia.org/wikipedia/commons/thumb/b/b0/Hallstatt_-_Zentrum_.JPG/1920px-Hallstatt_-_Zentrum_.JPG"},
    {title: "Palácio da Pena", country: "Portugal", file: "Sintra Portugal Palácio da Pena-01.jpg", author: "Uwe Aranas", license: "CC BY-SA 3.0", image: "https://upload.wikimedia.org/wikipedia/commons/thumb/7/74/Sintra_Portugal_Pal%C3%A1cio_da_Pena-01.jpg/1920px-Sintra_Portugal_Pal%C3%A1cio_da_Pena-01.jpg"},
    {title: "Windmühlen von Kinderdijk", country: "Niederlande", file: "KinderdijkMolens02.jpg", author: "Lucas Hirschegger", license: "CC BY-SA 3.0", image: "https://upload.wikimedia.org/wikipedia/commons/f/ff/KinderdijkMolens02.jpg"},
    {title: "Cliffs of Moher", country: "Irland", file: "Cliffs-Of-Moher-OBriens-From-South.JPG", author: "Bjørn Christian Tørrissen", license: "CC BY-SA 3.0", image: "https://upload.wikimedia.org/wikipedia/commons/thumb/d/d1/Cliffs-Of-Moher-OBriens-From-South.JPG/1920px-Cliffs-Of-Moher-OBriens-From-South.JPG"},
    {title: "Schloss Bran", country: "Rumänien", file: "Castelul Bran2.jpg", author: "Dobre Cezar", license: "CC BY-SA 3.0 RO", image: "https://upload.wikimedia.org/wikipedia/commons/thumb/1/17/Castelul_Bran2.jpg/1920px-Castelul_Bran2.jpg"},
    {title: "Karlsbrücke", country: "Tschechien", file: "Prague 07-2016 view from Lesser Town Tower of Charles Bridge img3.jpg", author: "A.Savin", license: "FAL", image: "https://upload.wikimedia.org/wikipedia/commons/thumb/2/22/Prague_07-2016_view_from_Lesser_Town_Tower_of_Charles_Bridge_img3.jpg/1920px-Prague_07-2016_view_from_Lesser_Town_Tower_of_Charles_Bridge_img3.jpg"},
    {title: "Sächsische Schweiz", country: "Deutschland", file: "Lilienstein Saxon Switzerland.jpg", author: "Merops", license: "CC BY-SA 3.0", image: "https://upload.wikimedia.org/wikipedia/commons/thumb/3/33/Lilienstein_Saxon_Switzerland.jpg/1920px-Lilienstein_Saxon_Switzerland.jpg"},
    {title: "Lofoten", country: "Norwegen", file: "Moskenes Reinebringen lub 2025-07-21 img09 Aussicht.jpg", author: "Lukas Beck", license: "CC BY 4.0", image: "https://upload.wikimedia.org/wikipedia/commons/thumb/5/59/Moskenes_Reinebringen_lub_2025-07-21_img09_Aussicht.jpg/1920px-Moskenes_Reinebringen_lub_2025-07-21_img09_Aussicht.jpg"},
    {title: "Canal Grande", country: "Italien", file: "View of the Grand Canal from Rialto to Ca'Foscari.jpg", author: "Didier Descouens", license: "CC BY-SA 4.0", image: "https://upload.wikimedia.org/wikipedia/commons/thumb/5/51/View_of_the_Grand_Canal_from_Rialto_to_Ca%27Foscari.jpg/1920px-View_of_the_Grand_Canal_from_Rialto_to_Ca%27Foscari.jpg"},
    {title: "Veitsdom in Prag", country: "Tschechien", file: "PragueCathedral03.jpg", author: "MathKnight und Zachi Evenor", license: "CC BY 2.5", image: "https://upload.wikimedia.org/wikipedia/commons/thumb/f/f4/PragueCathedral03.jpg/1920px-PragueCathedral03.jpg"},
    {title: "Cinque Terre", country: "Italien", file: "Cinque Terre (Italy, October 2020) - 24 (50543603956).jpg", author: "Bruno Rijsman", license: "CC BY-SA 2.0", image: "https://upload.wikimedia.org/wikipedia/commons/thumb/7/70/Cinque_Terre_%28Italy%2C_October_2020%29_-_24_%2850543603956%29.jpg/1920px-Cinque_Terre_%28Italy%2C_October_2020%29_-_24_%2850543603956%29.jpg"},
    {title: "Kloster Rila", country: "Bulgarien", file: "Rila Monastery, August 2013.jpg", author: "Raggatt2000", license: "CC BY-SA 3.0", image: "https://upload.wikimedia.org/wikipedia/commons/thumb/4/46/Rila_Monastery%2C_August_2013.jpg/1920px-Rila_Monastery%2C_August_2013.jpg"},
    {title: "Kloster Ostrog", country: "Montenegro", file: "Monasterio de Ostrog, Montenegro, 2014-04-14, DD 14.JPG", author: "Diego Delso", license: "CC BY-SA 3.0", image: "https://upload.wikimedia.org/wikipedia/commons/thumb/5/54/Monasterio_de_Ostrog%2C_Montenegro%2C_2014-04-14%2C_DD_14.JPG/1920px-Monasterio_de_Ostrog%2C_Montenegro%2C_2014-04-14%2C_DD_14.JPG"},
    {title: "Bâlea-See", country: "Rumänien", file: "Bileato.jpg", author: "siehe Dateiseite", license: "CC BY-SA 3.0", image: "https://upload.wikimedia.org/wikipedia/commons/d/d4/Bileato.jpg"},
    {title: "Stari Most", country: "Bosnien und Herzegowina", file: "Mostar Old Town Panorama 2007.jpg", author: "Ramirez", license: "CC BY-SA 4.0", image: "https://upload.wikimedia.org/wikipedia/commons/thumb/d/d7/Mostar_Old_Town_Panorama_2007.jpg/1920px-Mostar_Old_Town_Panorama_2007.jpg"},
    {title: "Geirangerfjord", country: "Norwegen", file: "Geirangerfjord .jpg", author: "Andreas Trepte", license: "CC BY-SA 2.5", image: "https://upload.wikimedia.org/wikipedia/commons/thumb/4/46/Geirangerfjord_.jpg/1920px-Geirangerfjord_.jpg"},
    {title: "Nyhavn", country: "Dänemark", file: "The Nyhavn Canal 3.jpg", author: "Europäische Kommission", license: "CC BY 4.0", image: "https://upload.wikimedia.org/wikipedia/commons/thumb/a/ad/The_Nyhavn_Canal_3.jpg/1920px-The_Nyhavn_Canal_3.jpg"},
    {title: "Warschauer Königsschloss", country: "Polen", file: "Royal Castle in Warsaw, Poland, 2022, 03.jpg", author: "Chris Olszewski", license: "CC BY-SA 4.0", image: "https://upload.wikimedia.org/wikipedia/commons/thumb/b/bb/Royal_Castle_in_Warsaw%2C_Poland%2C_2022%2C_03.jpg/1920px-Royal_Castle_in_Warsaw%2C_Poland%2C_2022%2C_03.jpg"},
    {title: "Ungarisches Parlament", country: "Ungarn", file: "Hungarian Parliament Building from across the Danube, 2025-01-11.jpg", author: "Kilyann Le Hen", license: "CC BY 4.0", image: "https://upload.wikimedia.org/wikipedia/commons/thumb/9/99/Hungarian_Parliament_Building_from_across_the_Danube%2C_2025-01-11.jpg/1920px-Hungarian_Parliament_Building_from_across_the_Danube%2C_2025-01-11.jpg"},
    {title: "Bleder See", country: "Slowenien", file: "Lake Bled from the Mountain.jpg", author: "Canadianhockey91", license: "CC BY-SA 3.0", image: "https://upload.wikimedia.org/wikipedia/commons/thumb/8/84/Lake_Bled_from_the_Mountain.jpg/1920px-Lake_Bled_from_the_Mountain.jpg"},
    {title: "Marienburg", country: "Polen", file: "Zespół Zamku Krzyżackiego MALBORK 01.jpg", author: "Gregy", license: "CC BY-SA 3.0 PL", image: "https://upload.wikimedia.org/wikipedia/commons/e/e6/Zesp%C3%B3%C5%82_Zamku_Krzy%C5%BCackiego_MALBORK_01.jpg"},
    {title: "Altstadt von Riga", country: "Lettland", file: "Views from St. Peter's Church Spire, Riga 20180808-2.jpg", author: "Suicasmo", license: "CC BY-SA 4.0", image: "https://upload.wikimedia.org/wikipedia/commons/thumb/6/6c/Views_from_St._Peter%27s_Church_Spire%2C_Riga_20180808-2.jpg/1920px-Views_from_St._Peter%27s_Church_Spire%2C_Riga_20180808-2.jpg"},
    {title: "Wasserburg Trakai", country: "Litauen", file: "Trakai castle 2016.jpg", author: "Aleksandr Petukhov", license: "CC BY-SA 4.0", image: "https://upload.wikimedia.org/wikipedia/commons/thumb/a/a8/Trakai_castle_2016.jpg/1920px-Trakai_castle_2016.jpg"},
    {title: "Prinsengracht", country: "Niederlande", file: "Prinsengracht.jpg", author: "Kaz Alting", license: "CC BY-SA 3.0", image: "https://upload.wikimedia.org/wikipedia/commons/thumb/6/6d/Prinsengracht.jpg/1920px-Prinsengracht.jpg"},
    {title: "Brügge vom Belfried", country: "Belgien", file: "Brügge Blick vom Belfried 4.jpg", author: "Zairon", license: "CC BY-SA 4.0", image: "https://upload.wikimedia.org/wikipedia/commons/thumb/9/9a/Br%C3%BCgge_Blick_vom_Belfried_4.jpg/1920px-Br%C3%BCgge_Blick_vom_Belfried_4.jpg"},
    {title: "Valbonatal", country: "Albanien", file: "2013-10-05 Valbona, Albania 8265.jpg", author: "Tobias Klenze", license: "CC BY 3.0", image: "https://upload.wikimedia.org/wikipedia/commons/thumb/d/d5/2013-10-05_Valbona%2C_Albania_8265.jpg/1920px-2013-10-05_Valbona%2C_Albania_8265.jpg"},
    {title: "Altstadt von Tallinn", country: "Estland", file: "Old Town of Tallinn, Tallinn, Estonia - panoramio (58).jpg", author: "Ben Bender", license: "CC BY-SA 3.0", image: "https://upload.wikimedia.org/wikipedia/commons/thumb/e/ed/Old_Town_of_Tallinn%2C_Tallinn%2C_Estonia_-_panoramio_%2858%29.jpg/1920px-Old_Town_of_Tallinn%2C_Tallinn%2C_Estonia_-_panoramio_%2858%29.jpg"},
    {title: "Château de Chillon am Genfersee", country: "Schweiz", file: "001 Chateau de Chillon and Dents du Midi Photo by Giles Laurent.jpg", author: "Giles Laurent", license: "CC BY-SA 4.0"},
    {title: "Schloss Tarnowski", country: "Polen", file: "2014 Tarnobrzeg, Zamek Tarnowskich 01.JPG", author: "Jacek Halicki", license: "CC BY-SA 3.0 PL"},
    {title: "Schloss Alatskivi", country: "Estland", file: "Alatskivi mõisa peahoone.jpg", author: "Ivar Leidus", license: "CC BY-SA 3.0 EE"},
    {title: "Festung Bač", country: "Serbien", file: "Bac Fortress (4).jpg", author: "Tournasol7", license: "CC BY-SA 4.0"},
    {title: "Burg Tropsztyn am Czchów-See", country: "Polen", file: "Tropsztyn Castle overlooking Czchów Lake, Wytrzyszczka, Lesser Poland Voivodeship, 20251025 0803 5046.jpg", author: "Jakub Hałun", license: "CC BY 4.0"},
    {title: "Schloss Bogesund", country: "Schweden", file: "Bogesunds slott February 2013 04.jpg", author: "Arild Vågen", license: "CC BY-SA 3.0"},
    {title: "Alhambra über Granada", country: "Spanien", file: "Granada - View from Mirador de San Nicolás - 02.jpg", author: "Benjamin Smith / Diego Delso", license: "GFDL"},
    {title: "Dubrovnik aus der Festung", country: "Kroatien", file: "Casco viejo de Dubrovnik, Croacia, 2014-04-13, DD 18.JPG", author: "Diego Delso", license: "CC BY-SA 3.0"},
    {title: "Engelsburg in der Dämmerung", country: "Italien", file: "Castel Sant'Angelo at dusk, Rome, Italy.jpg", author: "Jebulon", license: "CC0"},
    {title: "Maurenburg von Sintra", country: "Portugal", file: "Castelo dos Mouros, Sintra, Portugal, 2019-05-25, DD 112-121 PAN.jpg", author: "Diego Delso", license: "CC BY-SA 4.0"},
    {title: "Prager Burg", country: "Tschechien", file: "Castillo de Praga, Praga, República Checa, 2022-07-01, DD 23-25 HDR.jpg", author: "Diego Delso", license: "CC BY-SA 4.0"},
    {title: "Festung Bard", country: "Italien", file: "Castle of Bard (3).jpg", author: "Krzysztof Golik", license: "CC BY-SA 4.0"},
    {title: "Schloss Christiansborg", country: "Dänemark", file: "Christiansborg Slot Copenhagen 2014 01.jpg", author: "Julian Herzog", license: "GFDL"},
    {title: "Festung Vaxholm", country: "Schweden", file: "Vaxholms kastell November 2013.jpg", author: "Arild Vågen", license: "CC BY-SA 3.0"},
    {title: "Schloss Werdenberg", country: "Schweiz", file: "Grabs SG asv2022-10 Schloss Werdenberg img2.jpg", author: "A.Savin", license: "FAL"},
    {title: "Schloss Mailath", country: "Kroatien", file: "Mailath Castle in Donji Miholjac (3).jpg", author: "Tournasol7", license: "CC BY-SA 4.0"},
    {title: "Burg Hunedoara", country: "Rumänien", file: "Hunedoara Castle (Vajdahunyadi vár) by Pudelek.jpg", author: "Pudelek", license: "CC BY-SA 4.0"},
    {title: "Schloss Książ", country: "Polen", file: "Ksiaz - zamek 01.jpg", author: "Jar.ciurus", license: "CC BY-SA 3.0 PL"},
    {title: "Schloss Lednice", country: "Tschechien", file: "Lednice (Eisgrub) - zámek.JPG", author: "Pudelek / Marcin Szala", license: "CC BY-SA 3.0"},
    {title: "Schloss Vaduz", country: "Liechtenstein", file: "Liechtenstein asv2022-10 img01 Vaduz Schloss.jpg", author: "A.Savin", license: "FAL"},
    {title: "Schloss Litomyšl", country: "Tschechien", file: "Litomyšl (Leitomischl) chateau - by Pudelek.jpg", author: "Pudelek", license: "CC BY-SA 4.0"},
    {title: "Muiderslot", country: "Niederlande", file: "Muiden, Muiderslot. 09-05-2022. (actm.) 07.jpg", author: "Agnes Monkelbaan", license: "CC BY-SA 4.0"},
    {title: "Sion mit Tourbillon und Valère", country: "Schweiz", file: "Panorama of Sion, Switzerland from the north-west, with Tourbillon Castle and Valère Basilica (2022) edited.jpg", author: "Chensiyuan / Aristeas", license: "CC BY-SA 4.0"},
    {title: "Schloss Lenzburg", country: "Schweiz", file: "Schloss Lenzburg - Gesamtansicht1.jpg", author: "Wladyslaw Sojka / Taxiarchos228", license: "FAL"},
    {title: "Schloss Örebro", country: "Schweden", file: "Örebro slott May 2014 01.jpg", author: "Arild Vågen", license: "CC BY-SA 3.0"},
    {title: "Ribblehead-Viadukt", country: "Vereinigtes Königreich", file: "2015 Ribblehead Viaduct 1.jpg", author: "Kreuzschnabel", license: "CC BY-SA 3.0"},
    {title: "Gavarnie-Tal in den Pyrenäen", country: "Frankreich", file: "2019 - Parc national des Pyrenees - Vallée de Gavarnie.jpg", author: "Moahim", license: "CC BY-SA 4.0"},
    {title: "Austnesfjord auf den Lofoten", country: "Norwegen", file: "A Late evening view to Austnesfjorden at Sildpollnes Church, Austvågøya, Lofoten, Norway, 2015 April.jpg", author: "Simo Räsänen", license: "CC BY-SA 4.0"},
    {title: "Jägersee bei Kleinarl", country: "Österreich", file: "Kleinarl Jägersee 20180209.jpg", author: "Uoaei1", license: "CC BY-SA 4.0"},
    {title: "Aguarales de Valpalmas", country: "Spanien", file: "Aguarales de Valpalmas, Zaragoza, España, 2015-01-06, DD 06-11 PAN.JPG", author: "Diego Delso", license: "CC BY-SA 4.0"},
    {title: "Vulkanhöhle Algar do Carvão", country: "Portugal", file: "Algar do Carvao, isla de Terceira, Azores, Portugal, 2020-07-25, DD 68-70 HDR.jpg", author: "Diego Delso", license: "CC BY-SA 4.0"},
    {title: "Andiast in Graubünden", country: "Schweiz", file: "Andiast-Breil-Brigels. 24-09-2025. (d.j.b.) 08.jpg", author: "Dominicus Johannes Bergsma", license: "CC BY-SA 4.0"},
    {title: "Lyngenfjord bei Spåkenes", country: "Norwegen", file: "At Lyngen fjord, Spåkenes in 2012 June.jpg", author: "Simo Räsänen", license: "CC BY-SA 3.0"},
    {title: "Austerdalen", country: "Norwegen", file: "Austerdalen LC0364.jpg", author: "Jörg Hempel", license: "CC BY-SA 3.0 DE"},
    {title: "Berchtesgadener Alpen", country: "Deutschland", file: "Berchtesgaden 02.jpg", author: "Dmytro Balkhovitin", license: "CC BY-SA 4.0"},
    {title: "Panorama von Kranj", country: "Slowenien", file: "Kranj - panorama 03.jpg", author: "Mihael Grmek", license: "CC BY-SA 4.0"},
    {title: "Steinwald bei Varna", country: "Bulgarien", file: "Bosque de Piedra, provincia de Varna, Bulgaria, 2016-05-27, DD 73.jpg", author: "Diego Delso", license: "CC BY-SA 4.0"},
    {title: "Caldeira auf Faial", country: "Portugal", file: "Caldeira, isla de Fayal, Azores, Portugal, 2020-07-28, DD 25-30 PAN.jpg", author: "Diego Delso", license: "CC BY-SA 4.0"},
    {title: "Las Cañadas und Roques de García", country: "Spanien", file: "Caldera Las Cañadas mit Roques de García und TF-21.jpg", author: "Thomas Wolf", license: "CC BY-SA 3.0 DE"},
    {title: "Morgendämmerung über Sète", country: "Frankreich", file: "Dawn on Sète and the Étang de Thau.jpg", author: "Christian Ferrer", license: "CC BY-SA 3.0"},
    {title: "Eisriesenwelt im Tennengebirge", country: "Österreich", file: "Eisriesenwelt, Macizos de Tennen, Austria, 2019-05-18, DD 58.jpg", author: "Diego Delso", license: "CC BY-SA 4.0"},
    {title: "Monsanto im Morgenlicht", country: "Portugal", file: "Granite boulder formations near the Monsanto Castle at sunrise, Aldeia de Monsanto, Portugal (2) julesvernex2-3.jpg", author: "Jules Verne Times Two", license: "CC BY-SA 4.0"},
    {title: "Wasserfall Gullfoss", country: "Island", file: "Gullfoss, Suðurland, Islandia, 2014-08-16, DD 119.JPG", author: "Diego Delso", license: "CC BY-SA 4.0"},
    {title: "Neskaupstaður", country: "Island", file: "Icelandic Landscape near Neskaupstaður July 2014.JPG", author: "Martin Falbisoner", license: "CC BY-SA 4.0"},
    {title: "Kirche von Jamnik", country: "Slowenien", file: "Jamnik 05.jpg", author: "Mihael Grmek", license: "CC BY-SA 4.0"},
    {title: "Toledo im Abendlicht", country: "Spanien", file: "1 toledo spain evening sunset 2014 DXR edit.jpg", author: "Chensiyuan", license: "CC BY-SA 3.0"},
    {title: "Kirche über der Bucht von Kotor", country: "Montenegro", file: "20090719 Crkva Gospa od Zdravlja Kotor Bay Montenegro.jpg", author: "Ggia", license: "CC BY-SA 3.0"},
    {title: "Altstadt von Bystrzyca Kłodzka", country: "Polen", file: "2014 Bystrzyca Kłodzka, stare miasto 11.jpg", author: "Jacek Halicki", license: "CC BY-SA 3.0 PL"},
    {title: "Breslau an der Oder", country: "Polen", file: "Wrocław - widok z Wyspy Slodowej - wyspa Tamka.jpg", author: "Jar.ciurus", license: "CC BY-SA 3.0 PL"},
    {title: "Salzburg an der Salzach bei Nacht", country: "Österreich", file: "2018 - May - Salzach River at night in Salzburg.jpg", author: "Max Dawncat", license: "CC BY 2.0"},
    {title: "Nyhavn im Sonnenuntergang", country: "Dänemark", file: "2018 - Nyhavn on sunset.jpg", author: "Moahim", license: "CC BY-SA 4.0"},
    {title: "Akropolis und Athen", country: "Griechenland", file: "Akropolis mit Umgebung.jpg", author: "Thomas Wolf", license: "CC BY-SA 3.0 DE"},
    {title: "Albi im Sonnenuntergang", country: "Frankreich", file: "Albi Panorama Sunset Panini General.jpg", author: "Benh LIEU SONG", license: "CC BY-SA 4.0"},
    {title: "Altstadt von Zürich", country: "Schweiz", file: "Altstadt Zürich 2015.jpg", author: "Thomas Wolf", license: "CC BY-SA 3.0 DE"},
    {title: "Amsterdamer Grachten", country: "Niederlande", file: "Amsterdam Canals - July 2006.jpg", author: "Diliff", license: "GFDL"},
    {title: "Atrani an der Amalfiküste", country: "Italien", file: "Atrani (Costiera Amalfitana, 23-8-2011).jpg", author: "Paolo Costa Baldi", license: "GFDL"},
    {title: "Rechtstädtisches Rathaus in Danzig", country: "Polen", file: "Ayuntamiento Principal, Gdansk, Polonia, 2013-05-20, DD 01.jpg", author: "Diego Delso", license: "CC BY-SA 3.0"},
    {title: "Tallinn vom Domberg", country: "Estland", file: "Ayuntamiento, vistas panorámicas desde Toompea, Tallin, Estonia, 2012-08-05, DD 21.JPG", author: "Diego Delso", license: "CC BY-SA 3.0"},
    {title: "Basel von der Münsterpfalz", country: "Schweiz", file: "Basel - Münsterpfalz1.jpg", author: "Taxiarchos228", license: "FAL"},
    {title: "Berlin vom Fernsehturm", country: "Deutschland", file: "Berlin-Panorama vom Fernsehturm.jpg", author: "Jörg Braukmann", license: "CC BY-SA 4.0"},
    {title: "Bern vom Rosengarten", country: "Schweiz", file: "Bern Panorama von Rosengarten 20211007.jpg", author: "Daniel Kraft", license: "CC BY-SA 3.0"},
    {title: "Bath vom Bathwick Hill", country: "Vereinigtes Königreich", file: "Bathwick Hill, Bath, Somerset, UK - Diliff.jpg", author: "Diliff", license: "CC BY-SA 3.0"},
    {title: "Dorf Belcastel", country: "Frankreich", file: "Belcastel 4.jpg", author: "kallerna", license: "CC BY-SA 4.0"},
    {title: "Canal Grande und Santa Maria della Salute", country: "Italien", file: "Canal Grande Chiesa della Salute e Dogana dal ponte dell Accademia.jpg", author: "Wolfgang Moroder", license: "GFDL"},
    {title: "Coimbra am Mondego", country: "Portugal", file: "Coimbra November 2012-1.jpg", author: "Alvesgaspar", license: "CC BY-SA 3.0"},
    {title: "Dürnstein in der Wachau", country: "Österreich", file: "Dürnstein Panorama 02.jpg", author: "Uoaei1", license: "CC BY-SA 4.0"},
    {title: "Altstadt von Gent", country: "Belgien", file: "Ghent April 2012-2.jpg", author: "Alvesgaspar", license: "CC BY-SA 3.0"},
    {title: "Buitrago del Lozoya", country: "Spanien", file: "Buitrago del Lozoya - 04.jpg", author: "Carlos Delgado", license: "CC BY-SA 3.0"},
    {title: "Rathaus von Goslar", country: "Deutschland", file: "Goslar asv2022-06 img29 Rathaus.jpg", author: "A.Savin", license: "FAL"},
    {title: "Cogden Bridge", country: "Vereinigtes Königreich", file: "2013 Cogden Bridge.jpg", author: "Kreuzschnabel", license: "CC BY-SA 3.0"},
    {title: "Wanderweg am Fremington Edge", country: "Vereinigtes Königreich", file: "2014 Track on Fremington Edge.jpg", author: "Kreuzschnabel", license: "CC BY-SA 3.0"},
    {title: "Swaledale vom Kisdon Hill", country: "Vereinigtes Königreich", file: "2015 Swaledale from Kisdon Hill.jpg", author: "Kreuzschnabel", license: "CC BY-SA 3.0"},
    {title: "Hochalppass im Großen Walsertal", country: "Österreich", file: "360° Hochalppass Panorama.jpg", author: "Böhringer Friedrich", license: "CC BY-SA 2.5"},
    {title: "Barranco de Pecenescal", country: "Spanien", file: "Barranco de Pecenescal - Fuerteventura.jpg", author: "H. Zell", license: "GFDL"},
    {title: "Hohllay bei Berdorf", country: "Luxemburg", file: "Berdorf (LU), Hohllay -- 2015 -- 6097-101.jpg", author: "Dietmar Rabich", license: "CC BY-SA 4.0"},
    {title: "Lag da Breil", country: "Schweiz", file: "Breil-Brigels, Lag da Breil- Flem. 23-09-2022. (d.j.b) 04.jpg", author: "Dominicus Johannes Bergsma", license: "CC BY-SA 4.0"},
    {title: "Búðahraun auf Snæfellsnes", country: "Island", file: "Cabaña subterránea en la región de Búðahraun, Vesturland, Islandia, 2014-08-14, DD 046.JPG", author: "Diego Delso", license: "CC BY-SA 4.0"},
    {title: "Silfra-Schlucht in Þingvellir", country: "Island", file: "Cañón Silfra, Parque Nacional de Þingvellir, Suðurland, Islandia, 2014-08-16, DD 055.JPG", author: "Diego Delso", license: "CC BY-SA 4.0"},
    {title: "Cirque de Gavarnie", country: "Frankreich", file: "Cirque de Gavarnie, Haute-Pyrénées, France.jpg", author: "Benh LIEU SONG", license: "CC BY-SA 2.0"},
    {title: "Crest dil Cut und Crest Ault", country: "Schweiz", file: "Crest dil Cut and Crest Ault as seen from Präzer Höhi 2.jpg", author: "Dominicus Johannes Bergsma", license: "CC BY-SA 4.0"},
    {title: "Einsiedelei Virgen de la Peña", country: "Spanien", file: "Ermita de la Virgen de la Peña, LIC Sierras de Santo Domingo y Caballera, Aniés, Huesca, España, 2015-01-06, DD 08-09 PAN.JPG", author: "Diego Delso", license: "CC BY-SA 4.0"},
    {title: "Geirangerfjord vom Flydalsjuvet", country: "Norwegen", file: "Fiordo de Geiranger desde Flydalsjuvet, Noruega, 2019-09-07, DD 59.jpg", author: "Diego Delso", license: "CC BY-SA 4.0"},
    {title: "Wilder Kaiser bei Going", country: "Österreich", file: "Going am Wilden Kaiser Panorama 2011-01-29.jpg", author: "Bernie Kohl", license: "Public Domain"},
    {title: "Bucht von Kotor bei Orahovac", country: "Montenegro", file: "Gornji Orahovac, Bosnia y Herzegovina, 2014-04-14, DD 10-13 PAN.jpg", author: "Diego Delso", license: "CC BY-SA 3.0"},
    {title: "Mont Seuc und die Geislergruppe", country: "Italien", file: "Gran palusc de Mont Seuc Odles.jpg", author: "Wolfgang Moroder", license: "CC BY-SA 3.0"},
    {title: "Haut-Languedoc bei Rosis", country: "Frankreich", file: "Haut-Languedoc, Rosis cf06.jpg", author: "Christian Ferrer", license: "CC BY 4.0"},
    {title: "Kosiak und Wertatscha", country: "Österreich", file: "Kosiak - Wertatscha 20230714.jpg", author: "Uoaei1", license: "CC BY-SA 4.0"},
    {title: "Lac de Montriond", country: "Frankreich", file: "Lac de Montriond 06.jpg", author: "Krzysztof Golik", license: "CC BY-SA 4.0"},
    {title: "Comer See", country: "Italien", file: "Lago de Como, Italia, 2016-06-25, DD 02-06 PAN.jpg", author: "Diego Delso", license: "CC BY-SA 4.0"},
    {title: "Lagangarbh und Buachaille Etive Mòr", country: "Vereinigtes Königreich", file: "Lagangarbh cottage with Buachaille Etive Mòr.jpg", author: "Colin", license: "CC BY-SA 4.0"},
    {title: "Latzfonser Kreuz mit Dolomiten", country: "Italien", file: "Latzfonser Kreuz mit Dolomiten.jpg", author: "Jörg Braukmann", license: "CC BY-SA 4.0"},
    {title: "Kaiserdom Königslutter", country: "Deutschland", file: "20170902 Koenigslutter Kaiserdom DSC05568 PtrQs.JPG", author: "PtrQs", license: "CC BY-SA 4.0"},
    {title: "Doberaner Münster", country: "Deutschland", file: "Doberaner Münster, NW view, 2024-02-17.jpg", author: "Radomianin", license: "CC BY-SA 4.0"},
    {title: "Wallfahrtskirche Maria Gern", country: "Deutschland", file: "Maria Gern mit Untersberg.jpg", author: "Jörg Braukmann", license: "CC BY-SA 4.0"},
    {title: "Speyerer Dom in der Abendsonne", country: "Deutschland", file: "Speyer - Altstadt - Altpörtel - Blick auf Domfassade und Kirchtürme mit Abendsonne.jpg", author: "Roman Eisele", license: "CC BY-SA 4.0"},
    {title: "Hamburger Michel als Spiegelung", country: "Deutschland", file: "Reflection of St. Michaelis Church, Hamburg, Deutschland IMG 4822 edit.jpg", author: "Christoph Braun", license: "CC0"},
    {title: "Basilika Saint-Remi in Reims", country: "Frankreich", file: "Basilique Saint-Remi de Reims Exterior 1, Reims, France - Diliff.jpg", author: "Diliff", license: "CC BY-SA 3.0"},
    {title: "Abtei Fontenay", country: "Frankreich", file: "Abbaye Fontenay eglise facade.jpg", author: "Myrabella", license: "CC BY-SA 4.0"},
    {title: "Kathedrale von Le Mans", country: "Frankreich", file: "Le Mans - Cathedrale St Julien ext autumn.jpg", author: "Selbymay", license: "CC BY-SA 3.0"},
    {title: "Kathedrale von Rouen", country: "Frankreich", file: "Rouen Cathedral as seen from Gros Horloge 140215 4.jpg", author: "DXR", license: "CC BY-SA 3.0"},
    {title: "Kirche Sainte-Radegonde in Talmont", country: "Frankreich", file: "Talmont 17 Église remparts 2013.jpg", author: "JLPC", license: "CC BY-SA 3.0"},
    {title: "Kapelle von Savault unter der Milchstraße", country: "Frankreich", file: "Savault Chapel Under Milky Way BLS.jpg", author: "Benh LIEU SONG", license: "CC BY-SA 4.0"},
    {title: "Die beiden Dome von Brescia bei Nacht", country: "Italien", file: "Duomo vecchio e duomo nuovo notturna Brescia.jpg", author: "Wolfgang Moroder", license: "CC BY-SA 3.0"},
    {title: "Basilika im Sonnenuntergang", country: "Italien", file: "La basilica al tramonto.jpg", author: "Domeian", license: "CC BY-SA 4.0"},
    {title: "Basilika San Francesco in Assisi", country: "Italien", file: "Rear NW Basilica Francesco Assisi Sep23 A7C 07913.jpg", author: "Timothy A. Gonsalves", license: "CC BY-SA 4.0"},
    {title: "Dom und Schiefer Turm von Pisa", country: "Italien", file: "The Duomo and Tower of Pisa at sunrise.jpg", author: "MHoser", license: "CC BY-SA 4.0"},
    {title: "Johanniskapelle vor den Geislerspitzen", country: "Italien", file: "Villnöß Johanniskapelle mit Geisler.jpg", author: "Wolfgang Moroder", license: "CC BY-SA 3.0"},
    {title: "Kathedrale von Segovia", country: "Spanien", file: "Catedral de Santa María de Segovia - 01.jpg", author: "Carlos Delgado", license: "CC BY-SA 3.0"},
    {title: "Kloster Montserrat", country: "Spanien", file: "Montserrat Abbey (6).jpg", author: "Krzysztof Golik", license: "CC BY-SA 4.0"},
    {title: "Felsenkloster San Juan de la Peña", country: "Spanien", file: "Real Monasterio de San Juan de la Peña, Huesca, España, 2023-01-05, DD 48-50 HDR.jpg", author: "Diego Delso", license: "CC BY-SA 4.0"},
    {title: "Sagrada Família", country: "Spanien", file: "Sagrada Familia March 2015-10a.jpg", author: "Alvesgaspar", license: "CC BY-SA 4.0"},
    {title: "Basílica del Pilar in Saragossa", country: "Spanien", file: "WLM - 2020 - Catedral-basílica de Nuestra Señora del Pilar - 02.jpg", author: "Moahim", license: "CC BY-SA 4.0"},
    {title: "Kirche am Steinhof", country: "Österreich", file: "20250503 Kirche am Steinhof 03.jpg", author: "Flocci Nivis", license: "CC BY-SA 4.0"},
    {title: "Wallfahrtskirche Maria Siebenbrünn", country: "Österreich", file: "Arnoldstein Radendorf Wallfahrtskirche Maria Siebenbruenn mit Dobratsch 23052016 2048.jpg", author: "Johann Jaritz", license: "CC BY-SA 4.0"},
    {title: "Kirchen von Maria Wörth", country: "Österreich", file: "Maria Wörth Pfarrkirche hll. Primus und Felizian und Gerlitzen Ost-Ansicht 06052019 6854.jpg", author: "Johann Jaritz", license: "CC BY-SA 4.0"},
    {title: "Stift Göttweig", country: "Österreich", file: "Stift Göttweig 20230810 01.jpg", author: "Uoaei1", license: "CC BY-SA 4.0"},
    {title: "Stift Melk von Norden", country: "Österreich", file: "Stift Melk Nordseite 01.jpg", author: "Uoaei1", license: "CC BY-SA 4.0"},
    {title: "Stift Melk von Westen", country: "Österreich", file: "Stift Melk Westseite 01.jpg", author: "Uoaei1", license: "CC BY-SA 4.0"},
    {title: "Wallfahrtskirche Maria im Weingarten", country: "Deutschland", file: "Volkach Maria im Weingarten Luftbild-20221027-RM-171234.jpg", author: "Ermell", license: "CC BY-SA 4.0"},
    {title: "Limburger Dom", country: "Deutschland", file: "Cathedral Limburg - Limburger Dom - October 26th 2013 - 06.jpg", author: "Norbert Nagel", license: "CC BY-SA 3.0"},
    {title: "Schloss Staufenberg", country: "Deutschland", file: "2014.08.09.-11-Durbach--Weingut Schloss Staufenberg.jpg", author: "Andreas Eichler", license: "CC BY-SA 4.0"},
    {title: "Schloss Wojanów", country: "Polen", file: "2016 Pałac w Wojanowie 7.jpg", author: "Jacek Halicki", license: "CC BY 3.0"},
    {title: "Burg Niedzica", country: "Polen", file: "20170305 Niedzica zamek 5195.jpg", author: "Jakub Hałun", license: "CC BY-SA 4.0"},
    {title: "Schloss Swirsch", country: "Ukraine", file: "46-233-0009 Svirzh Castle RB.jpg", author: "Rbrechko", license: "CC BY-SA 4.0"},
    {title: "Festung Bourtzi auf Euböa", country: "Griechenland", file: "Bourtzi castle harbour Karystos Euboea Greece.jpg", author: "Jebulon", license: "CC0"},
    {title: "Marienburg an der Nogat", country: "Polen", file: "Castillo de Malbork, Polonia, 2013-05-19, DD 13.jpg", author: "Diego Delso", license: "CC BY-SA 3.0"},
    {title: "Schloss De Viron", country: "Belgien", file: "De Viron Castle (DSC 2198).jpg", author: "Benoit Brummer", license: "CC BY 4.0"},
    {title: "Festung Verrucole", country: "Italien", file: "Fortezza Verrucole Archeopark interno.jpg", author: "Simone Letari", license: "CC BY-SA 4.0"},
    {title: "Alte Festung von Korfu", country: "Griechenland", file: "Korfu (GR), Korfu, Alte Festung -- 2018 -- 1137.jpg", author: "Dietmar Rabich", license: "CC BY-SA 4.0"},
    {title: "Bischofsburg Lidzbark Warmiński", country: "Polen", file: "Lidzbark Warmiński 2023 16 Grabowski Palace Castle.jpg", author: "Scotch Mist", license: "CC BY-SA 4.0"},
    {title: "Burgruine Lilleborg", country: "Dänemark", file: "Lilleborg asv2024-07 img3.jpg", author: "A.Savin", license: "FAL"},
    {title: "Storkyrkan und Königliches Schloss", country: "Schweden", file: "Storkyrkan and Kungliga slottet Stockholm 2016 01.jpg", author: "Julian Herzog", license: "GFDL"},
    {title: "Schloss Val", country: "Frankreich", file: "Val Castle (15).jpg", author: "Tournasol7", license: "CC BY 4.0"},
    {title: "Schloss Zrinski in Čakovec", country: "Kroatien", file: "Zrinski Castle in Cakovec (13).jpg", author: "Krzysztof Golik", license: "CC BY-SA 4.0"},
    {title: "Schloss Mir", country: "Belarus", file: "Комплекс Мирского замка.JPG", author: "Vadzim Novikau", license: "CC BY-SA 3.0"},
    {title: "Schweriner Schloss", country: "Deutschland", file: "15-05-05-Schloß-Schwerin-RalfR-DSCF5191-2.jpg", author: "Ralf Roletschek", license: "GFDL 1.2"},
    {title: "Burg Eltz im Morgenlicht", country: "Deutschland", file: "Burg Eltz am frühen Morgen.jpg", author: "Johannes Dörrstock", license: "CC BY-SA 4.0"},
    {title: "Wartburg", country: "Deutschland", file: "Thuringia Eisenach asv2020-07 img23 Wartburg Castle.jpg", author: "A.Savin", license: "FAL"},
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
    panel.style.top = `${index * postcardStep() + Math.max(24, viewportHeight * .06)}px`;
    panel.style.setProperty("--postcard-index", String(index));
    panel.append(createCaption(sequence[index]));
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
