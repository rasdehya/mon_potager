from .database import SessionLocal, engine, Base
from .models import Famille, Legume, Variete, Calendrier, Maladie


def init_db():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    if db.query(Famille).count() > 0:
        db.close()
        return

    familles_data = [
        {
            "nom": "Alliacées",
            "description": "Famille de plantes bulbeuses comprenant l'ail, l'oignon, l'échalote, le poireau et la ciboulette. Elles sont appréciées pour leurs propriétés aromatiques et médicinales, riches en composés soufrés aux vertus antiseptiques.",
        },
        {
            "nom": "Solanacées",
            "description": "Famille botanique majeure du potager incluant la tomate, le poivron, l'aubergine et la pomme de terre. Ces plantes originaires d'Amérique du Sud aiment la chaleur et les sols riches. Attention à la rotation des cultures pour éviter les maladies du sol.",
        },
        {
            "nom": "Cucurbitacées",
            "description": "Famille des courges et cucurbitacées comprenant le potimarron, la courgette, le concombre et le melon. Ce sont des plantes gourmandes qui apprécient les sols riches et le plein soleil. Leurs fruits offrent une grande diversité de formes, couleurs et saveurs.",
        },
        {
            "nom": "Chénopodiacées",
            "description": "Famille comprenant les épinards, betteraves et blettes. Ces plantes feuilles ou racines apprécient les sols frais et riches en matière organique. Elles sont riches en vitamines et minéraux et se cultivent facilement au potager.",
        },
    ]

    legumes_data = [
        {
            "famille_nom": "Alliacées",
            "nom": "Ail",
            "nom_scientifique": "Allium sativum",
            "description": "Plante bulbeuse vivace cultivée comme annuelle, produisant une tête composée de plusieurs gousses (caïeux) entourées d'une tunique. L'ail est un incontournable du potager et de la cuisine, utilisé comme condiment dans de nombreuses préparations culinaires à travers le monde.",
            "conseils_culture": "Planter les caïeux pointe vers le haut, à 3-5 cm de profondeur. Espacer de 15 cm sur le rang et 25 cm entre les rangs. Pailler légèrement pour protéger du gel en hiver. Rabattre les tiges (nouer) en juin pour favoriser la maturation des bulbes. Arroser modérément, surtout en fin de cycle. Récolter quand les feuilles jaunissent à moitié.",
            "exposition": "Plein soleil (minimum 6h par jour)",
            "sol": "Sol léger, drainant, riche en humus. pH neutre à légèrement calcaire. Éviter les sols argileux et asphyxiants.",
            "arrosage": "Faible : arroser seulement en cas de sécheresse prolongée. Stopper les arrosages 3 semaines avant la récolte.",
            "varietes": [
                (
                    "Blanc de la Drôme",
                    "Variété traditionnelle de Provence, gros bulbes blancs à la saveur puissante",
                    "Excellente conservation (8-10 mois). Plantation en octobre-novembre.",
                ),
                (
                    "Rose de Lautrec (AOC)",
                    "Ail rose emblématique du Tarn, à la saveur douce et parfumée",
                    "Reconnu AOC. Plantation en janvier-février. Récolte en juin-juillet.",
                ),
                (
                    "Violet de Cadours",
                    "Variété ancienne de Haute-Garonne, bulbes violacés",
                    "Saveur fine et légèrement piquante. Très bonne conservation.",
                ),
                (
                    "Messidrome",
                    "Variété moderne sélectionnée pour sa productivité et sa régularité",
                    "Blanc à tunique légèrement teintée. Très productif. Conservation 6-8 mois.",
                ),
                (
                    "Germidour",
                    "Variété rose précoce très rustique résistante au froid",
                    "Idéale pour les régions froides. Bulbes moyens, saveur prononcée.",
                ),
                (
                    "Ail Rocambole",
                    "Ail vivace produisant des bulbilles en haut de la tige",
                    "Saveur douce et subtile. Très rustique. Se ressème en partie seul.",
                ),
            ],
            "calendrier": [
                (
                    "plantation",
                    10,
                    2,
                    11,
                    4,
                    "Planter les caïeux d'ail blanc et violet de mi-octobre à fin novembre.",
                ),
                (
                    "plantation",
                    1,
                    1,
                    2,
                    4,
                    "Planter l'ail rose (Rose de Lautrec, Germidour) de janvier à février.",
                ),
                (
                    "action",
                    12,
                    1,
                    2,
                    4,
                    "Protéger du gel avec un paillage léger (paille, feuilles mortes) dans les régions froides.",
                ),
                (
                    "action",
                    6,
                    3,
                    6,
                    4,
                    "Nouer les tiges (faux-semblant) pour favoriser la maturation des bulbes.",
                ),
                (
                    "recolte",
                    6,
                    3,
                    7,
                    2,
                    "Récolter quand la moitié des feuilles sont jaunes, de mi-juin à mi-juillet.",
                ),
                (
                    "action",
                    7,
                    1,
                    7,
                    4,
                    "Séchage et conservation : tresser ou conserver en bottes dans un local sec, aéré et obscur.",
                ),
            ],
            "maladies": [
                (
                    "maladie",
                    "Rouille de l'ail (Puccinia allii)",
                    "Pustules orange vif sur les feuilles, déformation et jaunissement du feuillage",
                    "Pulvérisation de bouillie bordelaise (1%) toutes les 2 semaines. Infusion de prêle en préventif.",
                    "Rotation des cultures (4-5 ans). Éviter l'excès d'humidité. Planter des variétés résistantes.",
                ),
                (
                    "maladie",
                    "Mildiou (Peronospora destructor)",
                    "Taches jaunes puis brunes sur les feuilles, feutrage gris violacé par temps humide",
                    "Traiter à la bouillie bordelaise dès les premiers symptômes. Supprimer les feuilles atteintes.",
                    "Éviter les arrosages sur le feuillage. Assurer une bonne ventilation. Rotation des cultures.",
                ),
                (
                    "maladie",
                    "Pourriture blanche (Sclerotium cepivorum)",
                    "Feutrage blanc au collet, pourriture molle des bulbes, flétrissement rapide",
                    "Aucun traitement curatif efficace. Arracher et détruire les plants atteints. Ne pas composter.",
                    "Rotation longue (8-10 ans). Utiliser des plants sains. Éviter les sols trop humides.",
                ),
                (
                    "ravageur",
                    "Mouche de l'oignon (Delia antiqua)",
                    "Larves blanches dans les bulbes et racines, jaunissement des feuilles",
                    "Pièges chromotactiques jaunes. Filet anti-insectes à l'installation.",
                    "Planter à côté des carottes (association bénéfique). Paillage pour limiter la ponte.",
                ),
                (
                    "ravageur",
                    "Thrips du tabac (Thrips tabaci)",
                    "Feuilles argentées et déformées, petits insectes noirs visibles à la loupe",
                    "Pulvérisation de savon noir (5 cuillères à soupe/L) ou de purin d'ortie.",
                    "Favoriser les auxiliaires (punaises prédatrices). Paillage pour maintenir l'humidité.",
                ),
            ],
        },
        {
            "famille_nom": "Solanacées",
            "nom": "Poivron",
            "nom_scientifique": "Capsicum annuum",
            "description": "Plante annuelle buissonnante originaire d'Amérique centrale, produisant des fruits creux de forme variable (carrée, allongée, conique) et de couleurs changeant du vert au rouge, jaune ou orange en mûrissant. Le poivron est un légume-fruit riche en vitamine C, apprécié cru ou cuit dans de nombreuses cuisines.",
            "conseils_culture": "Semer en godet à 20°C minimum, repiquer après les dernières gelées. Tuteurer les variétés productives. Pincer les tiges pour favoriser la ramification. Supprimer les premiers fruits pour renforcer la plante. Arroser régulièrement au pied sans mouiller le feuillage. Apporter un engrais riche en potasse en cours de culture.",
            "exposition": "Plein soleil, chaud et abrité du vent",
            "sol": "Sol riche, profond, bien drainé. pH 6.0-6.8. Apport de compost mûr avant plantation.",
            "arrosage": "Régulier : maintenir le sol frais sans excès. Pailler pour conserver l'humidité. Arroser au pied avec eau tiède de préférence.",
            "varietes": [
                (
                    "California Wonder",
                    "Variété classique américaine, fruits carrés à 3-4 lobes, verts puis rouges à maturité",
                    "Chair épaisse et douce. Très productive. Maturité 70-80 jours.",
                ),
                (
                    "Marconi Rosso",
                    "Variété italienne traditionnelle, fruits longs (15-20 cm) effilés",
                    "Idéal pour les grillades. Saveur douce et sucrée. Maturité 75 jours.",
                ),
                (
                    "Doux Long des Landes",
                    "Variété du Sud-Ouest, long corne jaune virant au rouge",
                    "Très précoce. Parfum délicat. Peut se consommer vert. Maturité 65 jours.",
                ),
                (
                    "Cube de Yolo",
                    "Variété californienne, fruits carrés et épais, vert foncé à rouge",
                    "Chair très épaisse (1 cm). Bonne conservation. Maturité 78 jours.",
                ),
                (
                    "Sweet Chocolate",
                    "Variété originale, fruits en forme de cœur, brun chocolat à maturité",
                    "Saveur douce et fruitée. Très décoratif. Maturité 80 jours.",
                ),
                (
                    "Corno di Toro",
                    "Variété italienne en forme de corne de taureau, rouge vif",
                    "Chair fine et sucrée. Excellent pour farcir. Maturité 72 jours.",
                ),
            ],
            "calendrier": [
                (
                    "semis_serre_chaude",
                    2,
                    2,
                    3,
                    4,
                    "Semer à l'intérieur au chaud (20-25°C) en godets de mi-février à fin mars. Utiliser une mini-serre chauffante.",
                ),
                (
                    "semis_serre_froide",
                    3,
                    2,
                    4,
                    3,
                    "Semis de rattrapage en serre froide ou sous châssis de mi-mars à mi-avril.",
                ),
                (
                    "action",
                    4,
                    2,
                    4,
                    3,
                    "Repiquer les jeunes plants en godets individuels de 9 cm dès la 2ème vraie feuille.",
                ),
                (
                    "action",
                    5,
                    1,
                    5,
                    2,
                    "Acclimater les plants : sortir à l'extérieur la journée 1 à 2 semaines avant plantation.",
                ),
                (
                    "plantation",
                    5,
                    3,
                    6,
                    2,
                    "Repiquer en pleine terre après les Saints de Glace, de mi-mai à mi-juin. Distance 50×50 cm. Tuteurer.",
                ),
                (
                    "action",
                    6,
                    2,
                    7,
                    3,
                    "Pincer les gourmands et tailler à 2 tiges pour favoriser la production. Pailler au pied.",
                ),
                (
                    "action",
                    6,
                    1,
                    6,
                    4,
                    "Pailler au pied avec paille ou tonte séchée pour maintenir la fraîcheur.",
                ),
                (
                    "recolte",
                    7,
                    2,
                    9,
                    3,
                    "Récolter les fruits verts ou attendre la couleur finale (rouge, jaune, orange) pour plus de saveur.",
                ),
                (
                    "action",
                    10,
                    1,
                    10,
                    2,
                    "Avant les gelées : arracher les plants ou récolter tous les fruits verts qui mûriront à l'intérieur.",
                ),
            ],
            "maladies": [
                (
                    "maladie",
                    "Mildiou (Phytophthora capsici)",
                    "Taches brunes sur feuilles et tiges, pourriture du collet, flétrissement brutal",
                    "Pulvérisation de bouillie bordelaise préventive.",
                    "Rotation 3-4 ans. Drainage du sol. Variétés résistantes.",
                ),
                (
                    "maladie",
                    "Botrytis (Pourriture grise)",
                    "Moisissure grise sur les tiges et fruits, taches brunes molles",
                    "Supprimer les parties atteintes. Aérer. Traiter à l'infusion de prêle.",
                    "Éviter l'humidité excessive. Espacer les plants.",
                ),
                (
                    "maladie",
                    "Oïdium (Erysiphe)",
                    "Feutrage blanc poudreux sur les feuilles, déformation des jeunes pousses",
                    "Pulvérisation de soufre micronisé (5g/L) ou de lait dilué (1/10).",
                    "Arrosage régulier. Variétés résistantes.",
                ),
                (
                    "ravageur",
                    "Puceron vert (Myzus persicae)",
                    "Colonies sur jeunes pousses, feuilles enroulées et collantes",
                    "Pulvérisation de savon noir (5 cL/L). Introduire des coccinelles.",
                    "Planter capucines, soucis. Favoriser les auxiliaires.",
                ),
                (
                    "ravageur",
                    "Aleurode (Mouche blanche)",
                    "Petits papillons blancs sous les feuilles, fumagine",
                    "Pièges collants jaunes. Huile de neem. Savon noir.",
                    "Filet anti-insectes. Association œillet d'Inde.",
                ),
                (
                    "ravageur",
                    "Acarien tisserand (Tetranychus urticae)",
                    "Toiles fines sous les feuilles, taches jaunes par temps chaud",
                    "Pulvérisation d'eau froide. Acaricide biologique.",
                    "Brumisation régulière. Favoriser les phytoséiides.",
                ),
            ],
        },
        {
            "famille_nom": "Cucurbitacées",
            "nom": "Potimarron",
            "nom_scientifique": "Cucurbita maxima",
            "description": "Courge d'origine japonaise (Kabocha) au goût subtil de châtaigne et à la texture farineuse. Le potimarron se distingue par sa peau fine et comestible, sa chair orange vif et sa saveur sucrée. C'est un légume d'automne très nutritif, riche en bêta-carotène et en fibres, idéal pour les soupes, purées et gratins.",
            "conseils_culture": "Semer en godets individuels à 18-20°C ou en pleine terre après les gelées. Préparer des buttes enrichies de compost. Espacer généreusement (1m entre plants). Arroser copieusement au pied en été. Tailler après la 4ème feuille pour favoriser les ramifications. Retourner les fruits pour éviter le contact humide.",
            "exposition": "Plein soleil (indispensable pour une bonne production)",
            "sol": "Sol riche, profond, frais mais drainé. Apport massif de compost mûr (3-4 kg/m²) avant plantation.",
            "arrosage": "Abondant et régulier en été (2-3 fois/semaine). Pailler épais. Stopper les arrosages 2 semaines avant récolte.",
            "varietes": [
                (
                    "Uchiki Kuri",
                    "Petit potimarron rouge-orangé en forme de toupie, poids 1-2 kg",
                    "Saveur intense de châtaigne. Chair fine sans fibres. Peau comestible. Maturité 90 jours.",
                ),
                (
                    "Potimarron Vert du Japon",
                    "Potimarron à peau vert foncé zébrée de crème",
                    "Chair orange vif, saveur douce. Bonne conservation (4-5 mois). Maturité 95 jours.",
                ),
                (
                    "Galeuse d'Eysines",
                    "Variété ancienne française, peau verruqueuse orange rouge",
                    "Chair épaisse et sucrée. Longue conservation (6 mois). Maturité 110 jours.",
                ),
                (
                    "Jaune de Paris",
                    "Grosse courge ronde (5-10 kg) à la peau jaune-orangé",
                    "Chair jaune pâle, texture fondante. Maturité 120 jours.",
                ),
                (
                    "Blue Ballet",
                    "Potimarron à la peau bleu-gris, forme aplatie",
                    "Chair orange vif, saveur de châtaigne et noisette. Maturité 100 jours.",
                ),
                (
                    "Muscade de Provence",
                    "Courge allongée vert clair marbré, côte profonde",
                    "Chair orange épaisse, très parfumée. Idéale pour tartes. Maturité 115 jours.",
                ),
            ],
            "calendrier": [
                (
                    "semis_serre_chaude",
                    4,
                    1,
                    4,
                    4,
                    "Semer en godets à l'intérieur à 20°C, 3-4 semaines avant plantation. 2 graines par godet de 8cm.",
                ),
                (
                    "semis_serre_froide",
                    5,
                    1,
                    5,
                    2,
                    "Semis sous tunnel froid ou châssis pour les régions aux étés courts, début mai.",
                ),
                (
                    "semis_direct",
                    5,
                    3,
                    5,
                    4,
                    "Semis direct en pleine terre réchauffée après les dernières gelées, de mi à fin mai.",
                ),
                (
                    "plantation",
                    5,
                    3,
                    6,
                    2,
                    "Planter en buttes de 30 cm après les gelées. Distance 1m entre plants. Compost au fond du trou.",
                ),
                (
                    "action",
                    6,
                    1,
                    6,
                    4,
                    "Pailler généreusement au pied avec paille ou foin pour conserver l'humidité et protéger les fruits.",
                ),
                (
                    "action",
                    7,
                    1,
                    8,
                    4,
                    "Arrosage copieux au pied 2-3 fois/semaine. Apport de purin d'ortie dilué toutes les 2 semaines.",
                ),
                (
                    "action",
                    8,
                    2,
                    9,
                    2,
                    "Retourner les fruits régulièrement pour éviter le contact humide et prévenir le pourrissement.",
                ),
                (
                    "recolte",
                    9,
                    2,
                    10,
                    4,
                    "Récolter avant les premières gelées, lorsque le pédoncule se fend. Laisser sécher 1-2 semaines.",
                ),
                (
                    "action",
                    10,
                    1,
                    10,
                    4,
                    "Séchage des fruits au soleil 2 semaines. Conserver en cave fraîche (10-15°C) et sèche.",
                ),
            ],
            "maladies": [
                (
                    "maladie",
                    "Oïdium (Erysiphe cichoracearum)",
                    "Feutrage blanc poudreux sur feuilles, déformation, dessèchement",
                    "Pulvérisation de soufre micronisé (5g/L) ou bicarbonate de potassium (1g/L).",
                    "Variétés résistantes. Rotation 4 ans.",
                ),
                (
                    "maladie",
                    "Mildiou (Pseudoperonospora cubensis)",
                    "Taches anguleuses jaunes sur feuilles, puis brunes, chute prématurée",
                    "Bouillie bordelaise préventive. Infusion de prêle.",
                    "Rotation des cultures. Arrosage au pied.",
                ),
                (
                    "maladie",
                    "Fusariose (Fusarium solani)",
                    "Flétrissement progressif, jaunissement, pourriture du collet",
                    "Aucun traitement curatif. Arracher et détruire.",
                    "Rotation longue (6-7 ans). Sol drainant.",
                ),
                (
                    "ravageur",
                    "Puceron du melon (Aphis gossypii)",
                    "Colonies sur pousses, déformation, miellat",
                    "Savon noir (5 cL/L). Purin de rhubarbe. Coccinelles.",
                    "Capucines en bordure. Paillage réfléchissant.",
                ),
                (
                    "ravageur",
                    "Limaces et escargots",
                    "Feuilles perforées, jeunes plants dévorés, traces de bave",
                    "Pièges à bière. Cendres de bois. Granulés anti-limaces bio.",
                    "Paillage de lin. Favoriser hérissons. Arrosage matinal.",
                ),
                (
                    "ravageur",
                    "Punaise de la courge (Anasa tristis)",
                    "Taches brunes sur fruits, dessèchement des feuilles",
                    "Savon noir et ail. Ramassage manuel.",
                    "Rotation. Désherbage. Culture sous voile.",
                ),
            ],
        },
        {
            "famille_nom": "Chénopodiacées",
            "nom": "Épinard",
            "nom_scientifique": "Spinacia oleracea",
            "description": "Plante annuelle feuillue originaire de Perse, cultivée pour ses feuilles vert foncé riches en fer, vitamines (A, C, K) et antioxydants. L'épinard est un légume-feuille facile à cultiver et à croissance rapide, parfait pour les récoltes de printemps et d'automne.",
            "conseils_culture": "Semer directement en pleine terre en lignes espacées de 30 cm. Éclaircir à 10-15 cm. Arroser régulièrement pour éviter la montaison. Pailler pour conserver la fraîcheur. Apporter un engrais riche en azote.",
            "exposition": "Mi-ombre légère, supporte mal le plein soleil brûlant de l'été",
            "sol": "Sol frais, profond, riche en humus et bien drainé. pH 6.0-7.5.",
            "arrosage": "Régulier : maintenir le sol constamment frais. En cas de sécheresse, montaison rapide.",
            "varietes": [
                (
                    "Géant d'Hiver",
                    "Variété rustique ancienne, grandes feuilles épaisses vert foncé",
                    "Résiste au froid (-15°C). Idéale pour semis d'automne et d'hiver sous tunnel.",
                ),
                (
                    "Monstrueux de Viroflay",
                    "Variété française traditionnelle aux très grandes feuilles charnues",
                    "Croissance rapide (45-55 jours). Feuilles tendres. Semis de printemps.",
                ),
                (
                    "Goliath",
                    "Variété semi-été résistante à la montaison précoce",
                    "Feuilles épaisses et lisses. Idéal pour semis de printemps et d'été.",
                ),
                (
                    "Matador",
                    "Variété hollandaise de mi-saison, résistante au mildiou",
                    "Feuilles rondes et épaisses. Très productive. Résiste à la montaison.",
                ),
                (
                    "Viking",
                    "Variété résistante au froid pour culture automne-hiver",
                    "Feuilles semi-savoyardes. Saveur douce. Résiste aux gelées modérées.",
                ),
                (
                    "Butterflay",
                    "Variété moderne à très grandes feuilles, croissance rapide (35 jours)",
                    "Idéale pour baby-leaf. Résistante mildiou.",
                ),
            ],
            "calendrier": [
                (
                    "semis_direct",
                    3,
                    2,
                    4,
                    3,
                    "Semis de printemps en pleine terre de mi-mars à mi-avril. Température idéale 10-18°C.",
                ),
                (
                    "semis_direct",
                    8,
                    2,
                    9,
                    2,
                    "Semis d'automne de mi-août à mi-septembre. Variétés rustiques conseillées.",
                ),
                (
                    "semis_serre_froide",
                    9,
                    2,
                    10,
                    2,
                    "Semis sous tunnel non chauffé pour récoltes d'hiver, de mi-septembre à mi-octobre.",
                ),
                (
                    "action",
                    4,
                    1,
                    9,
                    3,
                    "Arroser régulièrement au pied. Pailler en été pour éviter la montaison.",
                ),
                (
                    "action",
                    11,
                    1,
                    2,
                    4,
                    "Protéger les cultures d'hiver avec un voile d'hivernage en cas de fortes gelées.",
                ),
                (
                    "recolte",
                    5,
                    1,
                    6,
                    2,
                    "Récolte de printemps des semis de mars-avril. Récolter avant l'apparition des tiges florales.",
                ),
                (
                    "recolte",
                    9,
                    3,
                    11,
                    2,
                    "Récolte d'automne-hiver des semis d'août-septembre. Protéger avec un voile.",
                ),
                (
                    "action",
                    3,
                    1,
                    3,
                    3,
                    "Fertilisation azotée légère : purin d'ortie dilué ou compost mûr en surface.",
                ),
            ],
            "maladies": [
                (
                    "maladie",
                    "Mildiou (Peronospora farinosa)",
                    "Taches jaunes sur le dessus, feutrage gris-violacé au revers",
                    "Supprimer les feuilles atteintes. Infusion de prêle ou bouillie bordelaise.",
                    "Variétés résistantes. Rotation 3-4 ans.",
                ),
                (
                    "maladie",
                    "Fusariose (Fusarium oxysporum)",
                    "Jaunissement, nanisme, flétrissement, racines brunes",
                    "Aucun traitement curatif. Arracher et détruire.",
                    "Variétés résistantes. Rotation 5-6 ans. Sol drainant.",
                ),
                (
                    "maladie",
                    "Rouille (Puccinia spinaciae)",
                    "Pustules brun-rouge sur les feuilles, jaunissement",
                    "Bouillie bordelaise ou purin de prêle.",
                    "Rotation. Espacement. Arrosage sans mouiller le feuillage.",
                ),
                (
                    "ravageur",
                    "Puceron vert (Myzus persicae)",
                    "Feuilles enroulées, décolorées, miellat",
                    "Savon noir (5 cL/L). Purin d'ortie. Chrysopes.",
                    "Fleurs compagnes. Favoriser les auxiliaires.",
                ),
                (
                    "ravageur",
                    "Limaces (Deroceras reticulatum)",
                    "Feuilles perforées, jeunes plantules dévorées",
                    "Pièges à bière. Cendres de bois. Voile anti-limaces.",
                    "Arroser le matin. Paillage de lin.",
                ),
                (
                    "ravageur",
                    "Mineuse de l'épinard (Pegomya hyoscyami)",
                    "Galeries blanches sinueuses dans les feuilles",
                    "Supprimer les feuilles atteintes. Voile anti-insectes.",
                    "Rotation. Désherbage. Voile insect-proof.",
                ),
            ],
        },
    ]

    familles = {}
    for fdata in familles_data:
        famille = Famille(**fdata)
        db.add(famille)
        db.flush()
        familles[fdata["nom"]] = famille

    for ldata in legumes_data:
        vlist = ldata.pop("varietes", [])
        clist = ldata.pop("calendrier", [])
        mlist = ldata.pop("maladies", [])
        fnom = ldata.pop("famille_nom")
        famille = familles[fnom]
        legume = Legume(famille_id=famille.id, **ldata)
        db.add(legume)
        db.flush()

        for vnom, vdesc, vpart in vlist:
            db.add(
                Variete(
                    legume_id=legume.id,
                    nom=vnom,
                    description=vdesc,
                    particularites=vpart,
                )
            )

        for c in clist:
            db.add(
                Calendrier(
                    legume_id=legume.id,
                    type=c[0],
                    mois_debut=c[1],
                    semaine_debut=c[2],
                    mois_fin=c[3],
                    semaine_fin=c[4],
                    details=c[5],
                )
            )

        for m in mlist:
            db.add(
                Maladie(
                    legume_id=legume.id,
                    type=m[0],
                    nom=m[1],
                    symptomes=m[2],
                    traitement=m[3],
                    prevention=m[4],
                )
            )

    db.commit()
    db.close()
