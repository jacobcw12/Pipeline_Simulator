"""Natural gas network: North Africa, Europe and the Levant.

Edge weight is segment length in km; capacity is nominal capacity in bcm/yr.
Figures are approximate public values and should be checked before being
relied on. "grid" edges stand in for national transmission networks that
link the import pipelines; their lengths and capacities are rough.
"""

from __future__ import annotations

import math

from flow import min_cost_flow
from graph import Graph

NA, LEV, EU, TR, RU = "North Africa", "Levant", "Europe", "Turkey", "Russia"

# id: (name, country, region, kind, lat, lon)
NODES = {
    # North Africa
    "HRM": ("Hassi R'Mel", "Algeria", NA, "hub", 32.93, 3.27),
    "ARZ": ("Arzew LNG", "Algeria", NA, "lng_export", 35.85, -0.32),
    "SKI": ("Skikda LNG", "Algeria", NA, "lng_export", 36.88, 6.95),
    "BSF": ("Beni Saf", "Algeria", NA, "landfall", 35.30, -1.38),
    "ABM": ("Ain Beni Mathar", "Morocco", NA, "border", 34.01, -2.03),
    "TNG": ("Tangier", "Morocco", NA, "landfall", 35.78, -5.90),
    "FER": ("Feriana", "Tunisia", NA, "border", 34.95, 8.57),
    "CBN": ("Cap Bon", "Tunisia", NA, "landfall", 37.05, 11.01),
    "MEL": ("Mellitah", "Libya", NA, "terminal", 32.87, 12.25),
    "GAM": ("El Gamil", "Egypt", NA, "hub", 31.27, 32.17),
    "DAM": ("Damietta LNG", "Egypt", NA, "lng_export", 31.47, 31.73),
    "IDK": ("Idku LNG", "Egypt", NA, "lng_export", 31.33, 30.27),
    "ARI": ("El Arish", "Egypt", NA, "junction", 31.13, 33.80),
    "CAI": ("Cairo (Dahshour)", "Egypt", NA, "hub", 29.80, 31.20),
    # Levant
    "DOR": ("Dor", "Israel", LEV, "landfall", 32.61, 34.92),
    "ASD": ("Ashdod", "Israel", LEV, "landfall", 31.80, 34.65),
    "ASK": ("Ashkelon", "Israel", LEV, "junction", 31.67, 34.57),
    "AQA": ("Aqaba", "Jordan", LEV, "junction", 29.53, 35.01),
    "REH": ("El Rehab", "Jordan", LEV, "junction", 32.32, 36.05),
    "HOM": ("Homs", "Syria", LEV, "junction", 34.73, 36.71),
    "DAR": ("Deir Ammar", "Lebanon", LEV, "terminal", 34.46, 35.90),
    # Turkey
    "TUR": ("Turkgozu (from Azerbaijan)", "Turkey", TR, "source", 41.53, 42.78),
    "ESK": ("Eskisehir", "Turkey", TR, "junction", 39.78, 30.52),
    "ANK": ("Ankara", "Turkey", TR, "hub", 39.93, 32.86),
    "SAM": ("Samsun", "Turkey", TR, "landfall", 41.29, 36.33),
    "KIY": ("Kiyikoy", "Turkey", TR, "landfall", 41.63, 28.09),
    "FIL": ("Filyos", "Turkey", TR, "landfall", 41.57, 32.03),
    # Russia (supply origins)
    "RUK": ("Russkaya (Anapa)", "Russia", RU, "source", 44.98, 37.40),
    "BER": ("Beregovaya", "Russia", RU, "source", 44.37, 38.53),
    "VYB": ("Portovaya (Vyborg)", "Russia", RU, "source", 60.48, 28.03),
    # Southern Europe
    "MAZ": ("Mazara del Vallo", "Italy", EU, "landfall", 37.65, 12.59),
    "ENN": ("Enna", "Italy", EU, "junction", 37.57, 14.28),
    "GEL": ("Gela", "Italy", EU, "landfall", 37.07, 14.25),
    "MES": ("Messina", "Italy", EU, "junction", 38.19, 15.55),
    "MLD": ("Melendugno", "Italy", EU, "landfall", 40.27, 18.34),
    "MIN": ("Minerbio", "Italy", EU, "hub", 44.62, 11.49),
    "PGR": ("Passo Gries", "Italy", EU, "border", 46.45, 8.38),
    "TVS": ("Tarvisio", "Italy", EU, "border", 46.50, 13.58),
    "TAR": ("Tarifa", "Spain", EU, "landfall", 36.01, -5.60),
    "COR": ("Cordoba", "Spain", EU, "junction", 37.88, -4.78),
    "ALM": ("Almeria", "Spain", EU, "landfall", 36.84, -2.46),
    "MAD": ("Madrid", "Spain", EU, "hub", 40.42, -3.70),
    "LAR": ("Larrau", "Spain", EU, "border", 43.02, -0.96),
    "LAC": ("Lacq", "France", EU, "hub", 43.41, -0.62),
    "PAR": ("Paris region", "France", EU, "hub", 48.86, 2.35),
    "KIP": ("Kipoi", "Greece", EU, "border", 40.92, 26.37),
    "KOM": ("Komotini", "Greece", EU, "junction", 41.12, 25.40),
    "FIE": ("Fier", "Albania", EU, "landfall", 40.72, 19.56),
    "STZ": ("Stara Zagora", "Bulgaria", EU, "junction", 42.43, 25.64),
    "STR": ("Strandzha 2", "Bulgaria", EU, "border", 41.97, 26.75),
    "KIR": ("Kireevo", "Bulgaria", EU, "border", 43.79, 22.58),
    "KSK": ("Kiskundorozsma", "Hungary", EU, "border", 46.28, 20.06),
    # Central and Northern Europe
    "BAU": ("Baumgarten", "Austria", EU, "hub", 48.32, 16.86),
    "VKP": ("Velke Kapusany", "Slovakia", EU, "border", 48.55, 22.08),
    "WAL": ("Wallbach", "Switzerland", EU, "border", 47.56, 7.90),
    "WAI": ("Waidhaus", "Germany", EU, "border", 49.64, 12.49),
    "GRF": ("Lubmin (Greifswald)", "Germany", EU, "landfall", 54.14, 13.66),
    "MAL": ("Mallnow", "Germany", EU, "border", 52.45, 14.48),
    "EMD": ("Emden", "Germany", EU, "landfall", 53.37, 7.21),
    "DNM": ("Dornum", "Germany", EU, "landfall", 53.65, 7.43),
    "OSZ": ("Oude Statenzijl (NL-DE)", "Germany", EU, "border", 53.20, 7.20),
    "OBK": ("Oberkappel (DE-AT)", "Austria", EU, "border", 48.55, 13.78),
    "MOS": ("Mosonmagyarovar (AT-HU)", "Hungary", EU, "border", 47.87, 17.27),
    "DRV": ("Dravaszerdahely (HR-HU)", "Hungary", EU, "border", 45.84, 17.83),
    "KON": ("Kondratki", "Poland", EU, "border", 52.93, 23.93),
    "NIE": ("Niechorze", "Poland", EU, "landfall", 54.10, 15.07),
    "ZEE": ("Zeebrugge", "Belgium", EU, "hub", 51.33, 3.20),
    "DUN": ("Dunkirk", "France", EU, "landfall", 51.03, 2.37),
    "BAC": ("Bacton", "United Kingdom", EU, "hub", 52.86, 1.46),
    "EAS": ("Easington", "United Kingdom", EU, "landfall", 53.65, 0.11),
    "TEE": ("Teesside", "United Kingdom", EU, "landfall", 54.62, -1.15),
    "STF": ("St Fergus", "United Kingdom", EU, "hub", 57.57, -1.84),
    "KAR": ("Karsto", "Norway", EU, "hub", 59.27, 5.52),
    # Netherlands and the Benelux / France / Germany border points
    "OMM": ("Ommen (Gasunie hub)", "Netherlands", EU, "hub", 52.52, 6.42),
    "BAL": ("Balgzand", "Netherlands", EU, "landfall", 52.92, 4.78),
    "ZLZ": ("Zelzate (BE-NL)", "Netherlands", EU, "border", 51.20, 3.81),
    "BOC": ("Bocholtz (NL-DE)", "Germany", EU, "border", 50.81, 6.00),
    "EYN": ("Eynatten (BE-DE)", "Germany", EU, "border", 50.69, 6.08),
    "TAI": ("Taisnieres (BE-FR)", "France", EU, "border", 50.15, 3.93),
    "OBG": ("Obergailbach (DE-FR)", "France", EU, "border", 49.12, 7.22),
    "OLT": ("Oltingue (FR-CH)", "France", EU, "border", 47.49, 7.39),
    # Czechia, Slovakia, Poland's southern border, Romania
    "BRD": ("Brandov (DE-CZ)", "Czechia", EU, "border", 50.62, 13.43),
    "PRG": ("Prague region", "Czechia", EU, "hub", 50.08, 14.44),
    "LAN": ("Lanzhot (CZ-SK)", "Czechia", EU, "border", 48.72, 16.97),
    "SKH": ("Bratislava (Eustream hub)", "Slovakia", EU, "hub", 48.15, 17.11),
    "VZL": ("Velke Zlievce (SK-HU)", "Slovakia", EU, "border", 48.20, 19.45),
    "STP": ("Strachocina (PL-SK)", "Poland", EU, "border", 49.62, 22.08),
    "BUC": ("Bucharest region", "Romania", EU, "hub", 44.43, 26.10),
    # Iran
    "BAZ": ("Bazargan (from Iran)", "Turkey", TR, "source", 39.39, 44.38),
    "NYH": ("Nyhamna", "Norway", EU, "hub", 62.85, 6.93),
    "SLP": ("Sleipner", "Norway", EU, "hub", 58.37, 1.91),
    "EKO": ("Ekofisk complex", "Norway", EU, "hub", 56.54, 3.21),
    "KOL": ("Kollsnes", "Norway", EU, "hub", 60.55, 4.84),
    "HMF": ("Hammerfest LNG", "Norway", EU, "lng_export", 70.69, 23.60),
}

# Producing gas fields. Each feeds one hub through a field line whose flow is
# the field's output. Clusters of smaller fields are grouped into one node.
# id: (name, country, region, lat, lon, output bcm/yr, hub, line km, offshore, line name)
FIELDS = {
    # Algeria (all gathered at Hassi R'Mel)
    "HRF": ("Hassi R'Mel field", "Algeria", NA, 32.55, 2.85, 50.0, "HRM", 20, False, "Hassi R'Mel gathering"),
    "RNO": ("Rhourde Nouss", "Algeria", NA, 29.70, 6.70, 15.0, "HRM", 450, False, "Rhourde Nouss line"),
    "ISG": ("In Salah fields", "Algeria", NA, 27.80, 2.40, 9.0, "HRM", 500, False, "In Salah line"),
    "IAM": ("In Amenas", "Algeria", NA, 28.05, 9.55, 8.0, "HRM", 750, False, "In Amenas line"),
    "TFT": ("Tin Fouye Tabankort", "Algeria", NA, 28.50, 7.55, 6.0, "HRM", 600, False, "TFT line"),
    "HMD": ("Hassi Messaoud (associated gas)", "Algeria", NA, 31.68, 6.07, 4.0, "HRM", 300, False, "Hassi Messaoud line"),
    "TOU": ("Touat", "Algeria", NA, 27.40, -0.50, 4.5, "HRM", 700, False, "GR5 (Touat)"),
    "REG": ("Reggane Nord", "Algeria", NA, 26.70, 0.20, 3.0, "HRM", 760, False, "GR5 (Reggane)"),
    "TIM": ("Timimoun", "Algeria", NA, 29.30, 0.40, 1.6, "HRM", 450, False, "GR5 (Timimoun)"),
    # Libya
    "WAF": ("Wafa field", "Libya", NA, 28.90, 10.10, 3.0, "MEL", 525, False, "Wafa-Mellitah line"),
    "BES": ("Bahr Essalam", "Libya", NA, 33.55, 12.20, 7.0, "MEL", 110, True, "Bahr Essalam line"),
    "SRT": ("Sirte Basin fields (associated gas)", "Libya", NA, 29.50, 19.80, 8.0, "C_LY_TRI", 900, False, "Libyan coastal pipeline"),
    "TUF": ("Tunisian fields (Miskar, Hasdrubal, Nawara)", "Tunisia", NA, 34.20, 11.20, 2.0, "C_TN_TUN", 350, True, "Tunisian field lines"),
    # Egypt
    "ZOH": ("Zohr field", "Egypt", NA, 32.72, 32.25, 19.0, "GAM", 200, True, "Zohr export line"),
    "END": ("East Nile Delta fields (Atoll, Nooros, Baltim)", "Egypt", NA, 31.60, 31.70, 7.0, "GAM", 80, True, "East Delta lines"),
    "WND": ("West Nile Delta fields (Raven, Taurus, WDDM)", "Egypt", NA, 31.80, 30.40, 8.0, "IDK", 80, True, "West Delta lines"),
    "WDS": ("Western Desert fields", "Egypt", NA, 30.40, 27.20, 9.0, "CAI", 450, False, "Western Desert lines"),
    # Levant
    "LEV": ("Leviathan field", "Israel", LEV, 33.05, 33.65, 11.5, "DOR", 120, True, "Leviathan"),
    "TAM": ("Tamar field", "Israel", LEV, 32.85, 34.05, 10.0, "ASD", 150, True, "Tamar"),
    "KRS": ("Karish field", "Israel", LEV, 33.25, 34.15, 5.0, "DOR", 90, True, "Karish"),
    "SYR": ("Central Syria fields", "Syria", LEV, 34.55, 38.27, 3.0, "HOM", 160, False, "Central Syria line"),
    # Turkey
    "SAK": ("Sakarya field", "Turkey", TR, 42.40, 31.30, 3.5, "FIL", 170, True, "Sakarya"),
    # Norway
    "TRO": ("Troll", "Norway", EU, 60.65, 3.72, 36.0, "KOL", 65, True, "Troll"),
    "KVI": ("Kvitebjorn & Visund", "Norway", EU, 61.05, 2.50, 6.0, "KOL", 147, True, "Kvitebjorn pipeline"),
    "TPN": ("Tampen fields (Gullfaks, Statfjord, Oseberg)", "Norway", EU, 61.20, 2.20, 8.0, "KAR", 308, True, "Statpipe (Tampen)"),
    "HAL": ("Halten Bank fields (Asgard, Kristin, Heidrun)", "Norway", EU, 65.00, 6.80, 18.0, "KAR", 707, True, "Asgard Transport"),
    "ORL": ("Ormen Lange", "Norway", EU, 63.50, 5.40, 11.0, "NYH", 120, True, "Ormen Lange"),
    "AAS": ("Aasta Hansteen", "Norway", EU, 67.07, 7.00, 7.0, "NYH", 482, True, "Polarled"),
    "SLF": ("Sleipner area fields (Sleipner, Gudrun, Johan Sverdrup)", "Norway", EU, 58.70, 2.30, 8.0, "SLP", 40, True, "Sleipner area lines"),
    "EKF": ("Ekofisk area fields", "Norway", EU, 56.30, 3.35, 3.0, "EKO", 30, True, "Ekofisk area lines"),
    "SNO": ("Snohvit", "Norway", EU, 71.60, 21.00, 6.5, "HMF", 143, True, "Snohvit"),
    # United Kingdom
    "UNN": ("UK Northern North Sea & West of Shetland fields", "United Kingdom", EU, 60.30, -1.50, 8.0, "STF", 250, True, "FLAGS / SAGE / WOSP"),
    "UCN": ("UK Central North Sea fields (Culzean, Elgin-Franklin)", "United Kingdom", EU, 57.00, 1.90, 10.0, "TEE", 404, True, "CATS"),
    "USN": ("UK Southern North Sea fields", "United Kingdom", EU, 53.40, 2.00, 5.0, "BAC", 100, True, "Southern North Sea lines"),
    # Other Europe
    "ADR": ("Adriatic offshore fields (Italy)", "Italy", EU, 44.30, 12.80, 2.5, "MIN", 100, True, "Adriatic field lines"),
    "LSX": ("Lower Saxony fields (Germany)", "Germany", EU, 52.90, 9.20, 4.0, "EMD", 200, False, "Lower Saxony field lines"),
    "NLF": ("Dutch fields (North Sea & onshore; Groningen closed 2024)", "Netherlands", EU, 53.20, 4.20, 7.0, "BAL", 80, True, "Dutch field lines"),
    "ROF": ("Romanian fields (Transylvania, Oltenia)", "Romania", EU, 46.20, 24.40, 9.0, "BUC", 400, False, "Romanian field lines"),
}

NA_EU = "North Africa to Europe"
EAST_MED = "Eastern Mediterranean"
SGC = "Southern Gas Corridor"
RUSSIAN = "Russian supply"
NORWEGIAN = "Norwegian supply"
INTRA_EU = "Intra-European"
GRIDS = "National grids"
FIELD_LINES = "Field connections"
REGIONAL = "Regional grids"
LNG_LINES = "LNG import terminals"


def pipeline(corridor, capacity, segments, status="operating", type="pipeline", reverse=0.0):
    """``reverse`` is the capacity for flowing backwards (0 = one-way), or
    "same" to match the forward capacity."""
    return {"corridor": corridor, "capacity": capacity, "status": status,
            "type": type, "segments": segments, "reverse": reverse}


def grid(segments):
    # Grid segments set their own capacity: (source, target, km, offshore, {...}).
    # National grids can move gas either way.
    return pipeline(GRIDS, None, segments, type="grid", reverse="same")


# Segment: (source, target, length km, offshore[, overrides]); overrides may set
# "capacity", "status" or "reverse" for a single segment.
PIPELINES = {
    # --- North Africa to Europe
    "Transmed": pipeline(NA_EU, 32.0, [
        ("HRM", "FER", 550, False),
        ("FER", "CBN", 370, False),
        ("CBN", "MAZ", 155, True),
        ("MAZ", "ENN", 200, False),
        ("ENN", "MES", 140, False),
        ("MES", "MIN", 1070, False),  # includes 15 km Strait of Messina crossing
    ]),
    "Maghreb-Europe (GME)": pipeline(NA_EU, 12.0, [  # Algerian flows stopped Nov 2021
        ("HRM", "ABM", 515, False),
        ("ABM", "TNG", 522, False),
        ("TNG", "TAR", 45, True),
        ("TAR", "COR", 270, False),
    ], status="suspended"),
    "Medgaz": pipeline(NA_EU, 10.5, [
        ("HRM", "BSF", 550, False),
        ("BSF", "ALM", 210, True),
    ]),
    "Greenstream": pipeline(NA_EU, 8.0, [
        ("MEL", "GEL", 520, True),
    ]),
    # --- Eastern Mediterranean
    "Arab Gas Pipeline": pipeline(EAST_MED, 10.0, [
        ("ARI", "AQA", 265, False, {"reverse": 5.0}),  # includes Gulf of Aqaba crossing; reversed flows carry Israeli gas via Jordan
        ("AQA", "REH", 390, False),
        ("REH", "HOM", 320, False, {"status": "suspended"}),
        ("HOM", "DAR", 90, False, {"status": "suspended"}),
    ]),
    "EMG (Ashkelon-Arish)": pipeline(EAST_MED, 7.0, [  # reversed to Israel->Egypt in 2020
        ("ASK", "ARI", 90, True),
    ]),
    "Israel-Jordan": pipeline(EAST_MED, 3.0, [
        ("DOR", "REH", 130, False),
    ]),
    # --- Southern Gas Corridor (gas from Azerbaijan enters at Turkgozu)
    "Tabriz-Ankara pipeline": pipeline(SGC, 14.0, [("BAZ", "ANK", 1500, False)]),
    "TANAP": pipeline(SGC, 16.0, [
        ("TUR", "ESK", 1330, False),
        ("ESK", "KIP", 520, False),  # includes Sea of Marmara crossing
    ]),
    "TAP": pipeline(SGC, 10.0, [
        ("KIP", "KOM", 90, False),
        ("KOM", "FIE", 675, False),
        ("FIE", "MLD", 105, True),
    ]),
    "IGB": pipeline(SGC, 3.0, reverse="same", segments=[
        ("KOM", "STZ", 182, False),
    ]),
    # --- Russian supply
    "TurkStream": pipeline(RUSSIAN, 31.5, [
        ("RUK", "KIY", 930, True),
        ("KIY", "STR", 140, False, {"capacity": 15.75}),  # European string
    ]),
    "Balkan Stream": pipeline(RUSSIAN, 12.0, [
        ("STR", "KIR", 474, False),
        ("KIR", "KSK", 403, False),
    ]),
    "Blue Stream": pipeline(RUSSIAN, 16.0, [
        ("BER", "SAM", 396, True),
        ("SAM", "ANK", 444, False),
    ]),
    "Nord Stream 1": pipeline(RUSSIAN, 55.0, [  # damaged Sep 2022
        ("VYB", "GRF", 1224, True),
    ], status="out of service"),
    "Yamal-Europe": pipeline(RUSSIAN, 33.0, [  # Russian flows stopped 2022
        ("KON", "MAL", 680, False),
    ], status="suspended"),
    "Ukraine transit (Brotherhood)": pipeline(RUSSIAN, 40.0, [  # transit ended Jan 2025
        ("VKP", "BAU", 450, False),
    ], status="suspended"),
    # --- Norwegian supply
    "Europipe I": pipeline(NORWEGIAN, 18.0, [("SLP", "EMD", 660, True)]),
    "Europipe II": pipeline(NORWEGIAN, 24.0, [("KAR", "DNM", 658, True)]),
    "Norpipe": pipeline(NORWEGIAN, 16.0, [("EKO", "EMD", 440, True)]),
    "Zeepipe": pipeline(NORWEGIAN, 15.0, [("SLP", "ZEE", 814, True)]),
    "Franpipe": pipeline(NORWEGIAN, 19.6, [("SLP", "DUN", 840, True)]),
    "Langeled": pipeline(NORWEGIAN, 25.5, [
        ("NYH", "SLP", 627, True),
        ("SLP", "EAS", 543, True),
    ]),
    "Baltic Pipe": pipeline(NORWEGIAN, 10.0, [("KAR", "NIE", 900, True)]),
    "Zeepipe II": pipeline(NORWEGIAN, 50.0, [("KOL", "SLP", 300, True)]),
    "Statpipe": pipeline(NORWEGIAN, 20.0, [("KAR", "EKO", 440, True)]),
    # --- Intra-European interconnectors
    "TAG": pipeline(INTRA_EU, 37.0, [("BAU", "TVS", 380, False)], reverse=10.0),
    "Transitgas": pipeline(INTRA_EU, 18.0, [("WAL", "PGR", 290, False)], reverse=10.0),
    "VTN": pipeline(INTRA_EU, 15.0, [("ZEE", "EYN", 200, False)]),
    "TENP": pipeline(INTRA_EU, 15.0, [("BOC", "WAL", 500, False)]),
    "OPAL": pipeline(INTRA_EU, 36.0, [("GRF", "BRD", 470, False)]),
    "Gazelle": pipeline(INTRA_EU, 30.0, [("BRD", "WAI", 170, False)]),
    "MEGAL": pipeline(INTRA_EU, 20.0, [("WAI", "OBG", 460, False)], reverse=3.0),
    "BBL": pipeline(INTRA_EU, 15.0, [("BAL", "BAC", 235, True)], reverse=6.0),
    "Poland-Slovakia interconnector": pipeline(INTRA_EU, 5.7, [("STP", "SKH", 160, False)], reverse=4.7),
    "Slovakia-Hungary interconnector": pipeline(INTRA_EU, 2.6, [("SKH", "VZL", 150, False)], reverse="same"),
    "Romania-Hungary (BRUA)": pipeline(INTRA_EU, 2.6, [("BUC", "KSK", 600, False)], reverse="same"),
    "Giurgiu-Ruse interconnector": pipeline(INTRA_EU, 1.5, [("BUC", "STZ", 330, False)], reverse="same"),
    # Built for Russian gas to Turkey; now runs north as the "Vertical Corridor".
    "Trans-Balkan pipeline": pipeline(INTRA_EU, 5.0, [("STR", "BUC", 600, False)]),
    "Interconnector (IUK)": pipeline(INTRA_EU, 20.0, [("BAC", "ZEE", 235, True)], reverse=25.5),
    "Croatia-Hungary interconnector": pipeline(INTRA_EU, 2.6, [("LKR", "DRV", 300, False)], reverse="same"),
    "IBS (Bulgaria-Serbia)": pipeline(INTRA_EU, 1.8, [("C_BG_SOF", "C_RS_BEG", 450, False)], reverse="same"),
    "Spain-France (Larrau)": pipeline(INTRA_EU, 5.5, [("LAR", "LAC", 70, False)], reverse="same"),
    # --- National grids (approximate links between the pipelines above)
    "Algerian grid": grid([
        ("HRM", "ARZ", 510, False, {"capacity": 40.0}),
        ("HRM", "SKI", 575, False, {"capacity": 15.0}),
        # Approximate stand-in for eastern links that bypass the Hassi R'Mel complex.
        ("HMD", "SKI", 600, False, {"capacity": 10.0}),
    ]),
    "Egyptian grid": grid([
        ("GAM", "DAM", 60, False, {"capacity": 7.0}),
        ("IDK", "CAI", 200, False, {"capacity": 10.0}),  # West Delta gas into the grid
        ("ARI", "GAM", 190, False, {"capacity": 10.0}),  # Israeli gas from El Arish
        ("GAM", "CAI", 180, False, {"capacity": 20.0}),
    ]),
    "Israeli grid": grid([
        ("DOR", "ASK", 130, False, {"capacity": 12.0}),
        ("ASD", "ASK", 20, False, {"capacity": 11.0}),
    ]),
    "Turkish grid": grid([
        ("ANK", "ESK", 230, False, {"capacity": 16.0}),
        ("KIY", "ESK", 380, False, {"capacity": 15.75}),
        ("FIL", "ANK", 250, False, {"capacity": 10.0}),
    ]),
    "Italian grid": grid([
        ("GEL", "ENN", 65, False, {"capacity": 8.0}),
        ("MLD", "MIN", 720, False, {"capacity": 10.0}),
        ("TVS", "MIN", 330, False, {"capacity": 37.0}),
        ("PGR", "MIN", 330, False, {"capacity": 18.0}),
    ]),
    "Spanish grid": grid([
        ("COR", "MAD", 400, False, {"capacity": 12.0}),
        ("ALM", "MAD", 550, False, {"capacity": 10.5}),
        ("MAD", "LAR", 400, False, {"capacity": 5.5}),
    ]),
    "French grid": grid([
        ("DUN", "PAR", 280, False, {"capacity": 25.0}),
        ("PAR", "LAC", 700, False, {"capacity": 15.0}),
        ("TAI", "PAR", 230, False, {"capacity": 20.0}),
        ("OBG", "PAR", 380, False, {"capacity": 20.0}),
        ("OBG", "OLT", 220, False, {"capacity": 8.0}),
    ]),
    "Dutch grid": grid([
        ("OMM", "OSZ", 130, False, {"capacity": 30.0}),
        ("OMM", "BOC", 220, False, {"capacity": 20.0}),
        ("OMM", "BAL", 170, False, {"capacity": 20.0}),
        ("OMM", "ZLZ", 260, False, {"capacity": 15.0}),
    ]),
    "Belgian grid": grid([
        ("ZEE", "TAI", 160, False, {"capacity": 20.0}),
        ("ZEE", "ZLZ", 50, False, {"capacity": 15.0}),
    ]),
    "Swiss grid": grid([
        ("OLT", "WAL", 100, False, {"capacity": 8.0}),  # Oltingue-Rodersdorf branch of Transitgas
    ]),
    "Czech grid": grid([
        ("BRD", "PRG", 120, False, {"capacity": 15.0}),
        ("PRG", "LAN", 280, False, {"capacity": 15.0}),
        ("WAI", "PRG", 200, False, {"capacity": 10.0}),
    ]),
    "Slovak grid": grid([
        ("BAU", "SKH", 30, False, {"capacity": 15.0}),
        ("LAN", "SKH", 80, False, {"capacity": 20.0}),
    ]),
    "Polish grid": grid([
        ("NIE", "STP", 700, False, {"capacity": 6.0}),
    ]),
    "German grid": grid([
        ("EMD", "WAI", 600, False, {"capacity": 35.0}),
        ("DNM", "WAI", 620, False, {"capacity": 30.0}),
        ("OSZ", "WAI", 580, False, {"capacity": 25.0}),
        ("MAL", "WAI", 400, False, {"capacity": 33.0}),
        ("WAI", "OBK", 200, False, {"capacity": 25.0}),  # WAG / Penta West into Austria
        ("EYN", "BOC", 20, False, {"capacity": 15.0}),
    ]),
    "Austrian grid (WAG)": grid([
        ("OBK", "BAU", 250, False, {"capacity": 25.0}),
    ]),
    "Hungarian grid / HAG": grid([
        ("KSK", "MOS", 300, False, {"capacity": 6.0}),
        ("MOS", "BAU", 60, False, {"capacity": 4.4}),
        ("KSK", "DRV", 250, False, {"capacity": 2.6}),
    ]),
    "UK grid": grid([
        ("EAS", "BAC", 200, False, {"capacity": 25.5}),
        ("STF", "TEE", 300, False, {"capacity": 30.0}),
        ("TEE", "EAS", 130, False, {"capacity": 30.0}),
    ]),
}

# LNG import (regasification) terminals. Each supplies up to its send-out
# capacity; floating terminals (FSRUs) count. A terminal sends into the
# nearest demand region of its country; hub and km are used only where the
# country has no demand regions (e.g. Dutch LNG entering Germany).
# id: (name, country, region, lat, lon, send-out bcm/yr, hub, line km)
LNG_TERMINALS = {
    # Spain
    "LBC": ("Barcelona LNG", "Spain", EU, 41.34, 2.16, 17.0, "MAD", 600),
    "LCT": ("Cartagena LNG", "Spain", EU, 37.58, -0.97, 11.8, "MAD", 400),
    "LHU": ("Huelva LNG", "Spain", EU, 37.15, -6.88, 11.8, "MAD", 600),
    "LSG": ("Sagunto LNG", "Spain", EU, 39.63, -0.22, 8.8, "MAD", 350),
    "LBI": ("Bilbao LNG", "Spain", EU, 43.36, -3.09, 7.0, "MAD", 400),
    "LMU": ("Mugardos LNG", "Spain", EU, 43.46, -8.25, 3.6, "MAD", 600),
    # France
    "LDK": ("Dunkirk LNG", "France", EU, 51.03, 2.30, 13.0, "DUN", 5),
    "LMO": ("Montoir LNG", "France", EU, 47.31, -2.15, 10.0, "PAR", 450),
    "LFO": ("Fos-sur-Mer LNG", "France", EU, 43.42, 4.86, 10.0, "LAC", 450),
    "LLH": ("Le Havre FSRU", "France", EU, 49.48, 0.12, 5.0, "PAR", 200),
    # Italy
    "LPA": ("Panigaglia LNG", "Italy", EU, 44.07, 9.85, 3.5, "MIN", 200),
    "LAD": ("Adriatic LNG (Rovigo)", "Italy", EU, 45.09, 12.58, 9.0, "MIN", 100),
    "LOL": ("OLT Livorno FSRU", "Italy", EU, 43.64, 9.99, 5.0, "MIN", 250),
    "LPI": ("Piombino FSRU", "Italy", EU, 42.93, 10.53, 5.0, "MIN", 300),
    "LRA": ("Ravenna FSRU", "Italy", EU, 44.42, 12.28, 5.0, "MIN", 80),
    # Greece and Turkey
    "LRE": ("Revithoussa LNG", "Greece", EU, 37.96, 23.40, 7.0, "KOM", 600),
    "LAX": ("Alexandroupolis FSRU", "Greece", EU, 40.85, 25.87, 5.5, "KOM", 70),
    "LME": ("Marmara Ereglisi LNG", "Turkey", TR, 40.97, 27.95, 8.0, "ESK", 300),
    "LAL": ("Aliaga LNG (Egegaz, Etki)", "Turkey", TR, 38.82, 26.95, 15.0, "ESK", 350),
    "LDO": ("Dortyol FSRU", "Turkey", TR, 36.85, 36.20, 7.0, "ANK", 600),
    "LSA": ("Saros FSRU", "Turkey", TR, 40.60, 26.70, 7.0, "ESK", 350),
    # North-west Europe
    "LGR": ("Isle of Grain LNG", "United Kingdom", EU, 51.45, 0.71, 20.0, "BAC", 200),
    "LMH": ("Milford Haven LNG (South Hook, Dragon)", "United Kingdom", EU, 51.70, -5.05, 29.0, "BAC", 450),
    "LZE": ("Zeebrugge LNG", "Belgium", EU, 51.34, 3.20, 9.0, "ZEE", 5),
    "LGA": ("Gate LNG (Rotterdam)", "Netherlands", EU, 51.97, 4.05, 12.0, "OSZ", 280),
    "LEE": ("Eemshaven FSRU", "Netherlands", EU, 53.45, 6.83, 8.0, "OSZ", 40),
    "LWH": ("Wilhelmshaven FSRU", "Germany", EU, 53.58, 8.15, 5.0, "EMD", 100),
    "LBR": ("Brunsbuttel FSRU", "Germany", EU, 53.89, 9.20, 5.0, "EMD", 200),
    "LMK": ("Mukran FSRU", "Germany", EU, 54.51, 13.63, 5.0, "GRF", 50),
    "LSW": ("Swinoujscie LNG", "Poland", EU, 53.91, 14.25, 8.3, "NIE", 60),
    "LKR": ("Krk LNG", "Croatia", EU, 45.22, 14.55, 6.1, "C_HR_ZAG", 150),
    # Eastern Mediterranean
    "LSO": ("Ain Sokhna FSRUs", "Egypt", NA, 29.60, 32.35, 15.0, "CAI", 120),
    "LAQ": ("Aqaba FSRU", "Jordan", LEV, 29.45, 34.98, 5.0, "AQA", 10),
}

# Demand by city or region. Each country's demand is split across its main
# consuming regions, linked by an approximate regional grid, so gas has to
# travel to where it's used and one hub failing only cuts what depends on it.
# Where a hub already sits in a city (Madrid, Paris, Cairo, Ankara, Enna) that
# hub carries the region's demand itself.
# id: (country, demand bcm/yr[, name, lat, lon])  -- name/lat/lon for new nodes
REGIONS = {
    # North Africa
    "C_DZ_ALG": ("Algeria", 18.0, "Algiers", 36.75, 3.06),
    "C_DZ_ORA": ("Algeria", 14.0, "Oran", 35.70, -0.63),
    "C_DZ_CON": ("Algeria", 13.0, "Constantine & Annaba", 36.36, 6.61),
    "C_TN_TUN": ("Tunisia", 5.0, "Tunis", 36.80, 10.18),
    "C_LY_TRI": ("Libya", 14.0, "Tripoli", 32.89, 13.19),
    "CAI": ("Egypt", 30.0),
    "C_EG_ALX": ("Egypt", 15.0, "Alexandria & West Delta", 31.20, 29.92),
    "C_EG_CAN": ("Egypt", 10.0, "Suez Canal & Sinai", 30.60, 32.27),
    # Levant
    "C_IL_TLV": ("Israel", 9.0, "Tel Aviv", 32.08, 34.78),
    "C_IL_HFA": ("Israel", 4.0, "Haifa", 32.79, 34.99),
    "C_JO_AMM": ("Jordan", 4.0, "Amman", 31.95, 35.93),
    "C_SY_DAM": ("Syria", 3.0, "Damascus", 33.51, 36.29),
    # Turkey
    "C_TR_MAR": ("Turkey", 22.0, "Istanbul & Marmara", 41.01, 28.98),
    "ANK": ("Turkey", 14.0),
    "C_TR_AEG": ("Turkey", 8.0, "Izmir & Aegean", 38.42, 27.14),
    "C_TR_SOU": ("Turkey", 6.0, "Adana & South", 37.00, 35.32),
    # Southern Europe
    "C_GR_ATH": ("Greece", 4.0, "Athens", 37.98, 23.73),
    "C_GR_THE": ("Greece", 2.0, "Thessaloniki", 40.64, 22.94),
    "C_BG_SOF": ("Bulgaria", 3.0, "Sofia", 42.70, 23.32),
    "C_RS_BEG": ("Serbia", 3.0, "Belgrade", 44.79, 20.45),
    "C_HU_BUD": ("Hungary", 10.0, "Budapest", 47.50, 19.04),
    "C_HR_ZAG": ("Croatia", 3.0, "Zagreb", 45.81, 15.98),
    "C_IT_NOR": ("Italy", 35.0, "Milan & North", 45.46, 9.19),
    "C_IT_CEN": ("Italy", 12.0, "Rome & Centre", 41.90, 12.50),
    "C_IT_SOU": ("Italy", 8.0, "Naples & South", 40.85, 14.27),
    "ENN": ("Italy", 3.0),  # Sicily
    "MAD": ("Spain", 6.0),
    "C_ES_CAT": ("Spain", 7.0, "Barcelona & Catalonia", 41.39, 2.17),
    "C_ES_VAL": ("Spain", 5.0, "Valencia & Murcia", 39.47, -0.38),
    "C_ES_AND": ("Spain", 4.0, "Seville & Andalusia", 37.39, -5.98),
    "C_ES_NOR": ("Spain", 3.0, "Bilbao & North", 43.26, -2.93),
    "PAR": ("France", 15.0),
    "C_FR_WES": ("France", 6.0, "Nantes & West", 47.22, -1.55),
    "C_FR_SEA": ("France", 9.0, "Lyon & South-East", 45.76, 4.84),
    "C_FR_SWE": ("France", 5.0, "Toulouse & South-West", 43.60, 1.44),
    # Central and Northern Europe
    "C_AT_VIE": ("Austria", 8.0, "Vienna", 48.21, 16.37),
    "SKH": ("Slovakia", 4.5),
    "PRG": ("Czechia", 7.0),
    "BUC": ("Romania", 10.0),
    "OMM": ("Netherlands", 10.0),
    "C_NL_RAN": ("Netherlands", 18.0, "Randstad (Amsterdam, Rotterdam)", 52.05, 4.55),
    "C_CH_ZRH": ("Switzerland", 5.0, "Zurich", 47.37, 8.54),
    "C_BE_BRU": ("Belgium", 13.0, "Brussels", 50.85, 4.35),
    "C_DE_NOR": ("Germany", 15.0, "Hamburg & North", 53.55, 9.99),
    "C_DE_WES": ("Germany", 25.0, "Rhine-Ruhr", 51.45, 7.01),
    "C_DE_SOU": ("Germany", 20.0, "Munich & South", 48.14, 11.58),
    "C_DE_EAS": ("Germany", 15.0, "Berlin & East", 52.52, 13.40),
    "C_PL_WAW": ("Poland", 12.0, "Warsaw", 52.23, 21.01),
    "C_GB_LON": ("United Kingdom", 25.0, "London & South-East", 51.51, -0.13),
    "C_GB_MID": ("United Kingdom", 15.0, "Midlands", 52.49, -1.89),
    "C_GB_NOR": ("United Kingdom", 15.0, "North of England", 53.80, -1.55),
    "C_GB_SCO": ("United Kingdom", 7.0, "Scotland", 55.86, -4.25),
    "C_GB_WAL": ("United Kingdom", 3.0, "Wales & South-West", 51.48, -3.18),
}

# Regional grid links (approximate): (from, to, capacity bcm/yr). They carry
# gas from entry points and hubs to the regions, and between regions; all can
# run in either direction. Lengths are worked out from the map.
REGIONAL_GRIDS = {
    "Algeria": [("HRM", "C_DZ_ALG", 30), ("ARZ", "C_DZ_ORA", 20), ("SKI", "C_DZ_CON", 15),
                ("C_DZ_ALG", "C_DZ_ORA", 10), ("C_DZ_ALG", "C_DZ_CON", 10)],
    "Tunisia": [("FER", "C_TN_TUN", 5), ("CBN", "C_TN_TUN", 5)],
    "Libya": [("MEL", "C_LY_TRI", 14)],
    "Egypt": [("CAI", "C_EG_ALX", 15), ("CAI", "C_EG_CAN", 15), ("IDK", "C_EG_ALX", 15),
              ("GAM", "C_EG_CAN", 20), ("ARI", "C_EG_CAN", 10)],
    "Israel": [("DOR", "C_IL_HFA", 10), ("ASK", "C_IL_TLV", 13), ("ASD", "C_IL_TLV", 11),
               ("C_IL_HFA", "C_IL_TLV", 8)],
    "Jordan": [("REH", "C_JO_AMM", 4), ("AQA", "C_JO_AMM", 4)],
    "Syria": [("HOM", "C_SY_DAM", 3)],
    "Turkey": [("KIY", "C_TR_MAR", 16), ("ESK", "C_TR_MAR", 16), ("ESK", "C_TR_AEG", 10),
               ("ANK", "C_TR_SOU", 10), ("C_TR_MAR", "C_TR_AEG", 8)],
    "Greece": [("KOM", "C_GR_THE", 6), ("C_GR_THE", "C_GR_ATH", 5)],
    "Bulgaria": [("STR", "STZ", 3), ("STZ", "C_BG_SOF", 3), ("KIR", "C_BG_SOF", 3)],
    "Serbia": [("KIR", "C_RS_BEG", 4)],
    "Hungary": [("KSK", "C_HU_BUD", 10), ("MOS", "C_HU_BUD", 6), ("DRV", "C_HU_BUD", 3),
                ("VZL", "C_HU_BUD", 2.6)],
    "Netherlands": [("OMM", "C_NL_RAN", 20), ("BAL", "C_NL_RAN", 10), ("ZLZ", "C_NL_RAN", 10)],
    "Croatia": [("DRV", "C_HR_ZAG", 3)],
    "Austria": [("BAU", "C_AT_VIE", 15), ("OBK", "C_AT_VIE", 10)],
    "Switzerland": [("WAL", "C_CH_ZRH", 5), ("PGR", "C_CH_ZRH", 3)],
    "Italy": [("MIN", "C_IT_NOR", 50), ("TVS", "C_IT_NOR", 20), ("PGR", "C_IT_NOR", 18),
              ("MIN", "C_IT_CEN", 20), ("C_IT_NOR", "C_IT_CEN", 20), ("C_IT_CEN", "C_IT_SOU", 15),
              ("MES", "C_IT_SOU", 32), ("MLD", "C_IT_SOU", 10)],
    "Spain": [("MAD", "C_ES_CAT", 10), ("MAD", "C_ES_VAL", 8), ("MAD", "C_ES_AND", 8),
              ("MAD", "C_ES_NOR", 6), ("C_ES_CAT", "C_ES_VAL", 6), ("COR", "C_ES_AND", 12),
              ("ALM", "C_ES_AND", 10.5), ("LAR", "C_ES_NOR", 5.5)],
    "France": [("PAR", "C_FR_WES", 8), ("PAR", "C_FR_SEA", 12), ("LAC", "C_FR_SWE", 8),
               ("C_FR_SWE", "C_FR_SEA", 5)],
    "Belgium": [("ZEE", "C_BE_BRU", 15)],
    "Germany": [("EMD", "C_DE_NOR", 20), ("DNM", "C_DE_NOR", 20), ("EMD", "C_DE_WES", 30),
                ("BOC", "C_DE_WES", 20), ("EYN", "C_DE_WES", 15),
                ("OSZ", "C_DE_WES", 25), ("WAI", "C_DE_SOU", 30), ("GRF", "C_DE_EAS", 20),
                ("MAL", "C_DE_EAS", 15), ("C_DE_NOR", "C_DE_WES", 15), ("C_DE_WES", "C_DE_SOU", 20),
                ("C_DE_NOR", "C_DE_EAS", 10), ("C_DE_EAS", "C_DE_SOU", 10)],
    "Poland": [("NIE", "C_PL_WAW", 12)],
    "United Kingdom": [("BAC", "C_GB_LON", 25), ("EAS", "C_GB_NOR", 20), ("TEE", "C_GB_NOR", 15),
                       ("STF", "C_GB_SCO", 10), ("C_GB_SCO", "C_GB_NOR", 10), ("C_GB_NOR", "C_GB_MID", 20),
                       ("C_GB_MID", "C_GB_LON", 20), ("C_GB_MID", "C_GB_WAL", 10), ("C_GB_LON", "C_GB_WAL", 5)],
}

# Gas shipped out of LNG export terminals (bcm/yr).
LNG_EXPORTS = {"ARZ": 12.0, "SKI": 5.0, "DAM": 2.0, "IDK": 2.0, "HMF": 6.5}

# Costs in km-equivalents, so the solver uses the cheapest options first:
# pipeline gas, then extra field output, then LNG, then demand reduction.
SWING_SHARE = 0.10           # fields can produce this much extra in a pinch...
SWING_PREMIUM_KM = 5_000     # ...at a higher cost
LNG_COST_PREMIUM_KM = 10_000  # liquefaction and shipping make LNG pricier
DEMAND_RESPONSE_SHARE = 0.15  # industry, power and households can cut this much...
DEMAND_RESPONSE_COST_KM = 20_000  # ...as a last resort before going short
# In a shortage, governments keep gas at home before honouring LNG exports
# (as Egypt did in 2023-24), so exports are served at the lowest priority.
EXPORT_TIERS = ((1.0, 0.5),)


def _coords(node_id: str) -> tuple[float, float]:
    if node_id in REGIONS and len(REGIONS[node_id]) == 5:
        return REGIONS[node_id][3], REGIONS[node_id][4]
    for table, (lat_i, lon_i) in ((NODES, (4, 5)), (FIELDS, (3, 4)), (LNG_TERMINALS, (3, 4))):
        if node_id in table:
            return table[node_id][lat_i], table[node_id][lon_i]
    raise KeyError(node_id)


def _route_km(a: str, b: str) -> int:
    """Great-circle distance with a 20% allowance for real routing."""
    (lat1, lon1), (lat2, lon2) = map(lambda n: map(math.radians, _coords(n)), (a, b))
    h = (math.sin((lat2 - lat1) / 2) ** 2
         + math.cos(lat1) * math.cos(lat2) * math.sin((lon2 - lon1) / 2) ** 2)
    return max(5, round(1.2 * 2 * 6371 * math.asin(math.sqrt(h))))


def _region_of(country: str) -> str:
    rows = [*((spec[1], spec[2]) for spec in NODES.values()),
            *((spec[1], spec[2]) for spec in LNG_TERMINALS.values())]
    return next((region for c, region in rows if c == country), EU)  # e.g. Serbia, Croatia


def _nearest_region(node_id: str, country: str) -> str | None:
    regions = [r for r, spec in REGIONS.items() if spec[0] == country]
    return min(regions, key=lambda r: _route_km(node_id, r), default=None)


for _id, (_name, _c, _r, _lat, _lon, _cap, _hub, _km) in LNG_TERMINALS.items():
    _target = _nearest_region(_id, _c)
    _segment = (_id, _target, _route_km(_id, _target), False) if _target else (_id, _hub, _km, False)
    PIPELINES[f"{_name} send-out"] = pipeline(LNG_LINES, _cap, [_segment], type="lng")

# A field line can carry the field's full output, including its swing.
for _id, (_name, _c, _r, _lat, _lon, _out, _hub, _km, _off, _line) in FIELDS.items():
    PIPELINES[_line] = pipeline(FIELD_LINES, round(_out * (1 + SWING_SHARE), 2),
                                [(_id, _hub, _km, _off)], type="gathering")

for _country, _links in REGIONAL_GRIDS.items():
    PIPELINES[f"{_country} regional grid"] = pipeline(
        REGIONAL, None, [(a, b, _route_km(a, b), False, {"capacity": float(c)}) for a, b, c in _links],
        type="regional", reverse="same")


# --- Supply and demand -----------------------------------------------------
# Flows are solved, not assumed: gas from fields and import entry points is
# routed to demand by min-cost max-flow (flow.py), within pipeline capacities,
# cheapest first. Pipelines that are not "operating" carry nothing.

# Gas entering the network from outside the region (bcm/yr the supplier would
# send if the route were open). Fields supply their output from FIELDS.
SOURCE_SUPPLY = {
    "RUK": 31.5,  # Russia via TurkStream
    "BER": 16.0,  # Russia via Blue Stream
    "VYB": 55.0,  # Russia via Nord Stream 1 (pipeline out of service)
    "KON": 33.0,  # Russia via Yamal-Europe (suspended)
    "VKP": 40.0,  # Russia via Ukraine (suspended)
    "TUR": 16.0,  # Azerbaijan (Shah Deniz) via the South Caucasus Pipeline
    "BAZ": 9.6,   # Iran via the Tabriz-Ankara pipeline (contract volume)
}

DEMAND = ({r: (spec[1], spec[0]) for r, spec in REGIONS.items()}
          | {t: (bcm, f"{NODES[t][1]} LNG exports") for t, bcm in LNG_EXPORTS.items()})


# --- Economics -------------------------------------------------------------
# Value of gas moved = flow (bcm) x energy content x price. Prices are rough
# assumptions meant to be tuned, not observed data.

MWH_PER_BCM = 10.55e6  # ~10.55 TWh of energy per bcm of natural gas

# Gas price in EUR/MWh by pipeline name or corridor. Europe uses a TTF-like hub
# price; Eastern Mediterranean flows are priced lower, closer to regional
# contract prices.
DEFAULT_PRICE_EUR_MWH = 35.0
PRICE_EUR_MWH = {EAST_MED: 22.0, "Egyptian grid": 22.0, "Israeli grid": 22.0}
# Field lines are priced by the field's country.
PRICE_EUR_MWH_BY_COUNTRY = {c: 22.0 for c in ("Egypt", "Israel", "Jordan", "Syria", "Lebanon")}


def gas_value_eur(bcm: float, price_eur_mwh: float) -> float:
    return bcm * MWH_PER_BCM * price_eur_mwh


def build_gas_network(supply: dict[str, float] | None = None,
                      demand: dict[str, float] | None = None,
                      disabled_nodes: set[str] = frozenset(),
                      disabled_edges: set[tuple[str, str]] = frozenset()) -> Graph:
    """Build the network and solve its flows.

    ``supply`` and ``demand`` override entries of SOURCE_SUPPLY / field output
    and DEMAND, which makes scenarios easy, e.g. ``supply={"RUK": 0}``.
    A disabled node or edge carries no gas: a disabled node's edges are all
    shut, so it neither supplies nor receives, and its demand goes unmet.
    """
    g = Graph(directed=True)
    for node_id, (name, country, region, kind, lat, lon) in NODES.items():
        g.add_node(node_id, name=name, region=region,
                   attributes={"country": country, "kind": kind,
                               "lat": lat, "lon": lon})
    for node_id, (name, country, region, lat, lon, output, *_) in FIELDS.items():
        g.add_node(node_id, name=name, region=region,
                   attributes={"country": country, "kind": "field", "lat": lat, "lon": lon,
                               "production_bcm_year": output})
    for node_id, (name, country, region, lat, lon, *_) in LNG_TERMINALS.items():
        g.add_node(node_id, name=name, region=region,
                   attributes={"country": country, "kind": "lng_import", "lat": lat, "lon": lon})
    for node_id, (country, _, *new) in REGIONS.items():
        if new:  # a city node; otherwise the region's demand sits at an existing hub
            name, lat, lon = new
            g.add_node(node_id, name=name, region=_region_of(country),
                       attributes={"country": country, "kind": "city", "lat": lat, "lon": lon})
    for name, p in PIPELINES.items():
        price = PRICE_EUR_MWH.get(name, PRICE_EUR_MWH.get(p["corridor"], DEFAULT_PRICE_EUR_MWH))
        if p["type"] == "gathering":
            country = FIELDS[p["segments"][0][0]][1]
            price = PRICE_EUR_MWH_BY_COUNTRY.get(country, DEFAULT_PRICE_EUR_MWH)
        for source, target, length_km, offshore, *rest in p["segments"]:
            overrides = rest[0] if rest else {}
            capacity = overrides.get("capacity", p["capacity"])
            reverse = overrides.get("reverse", p["reverse"])
            g.add_edge(source, target, weight=length_km, capacity=capacity,
                       attributes={"pipeline": name, "corridor": p["corridor"],
                                   "type": p["type"], "offshore": offshore,
                                   "status": overrides.get("status", p["status"]),
                                   "reverse_capacity": capacity if reverse == "same" else reverse,
                                   "price_eur_mwh": price})

    for node in g.nodes:
        node.attributes["disabled"] = node.id in disabled_nodes
    for e in g.edges:
        e.attributes["disabled"] = ("edge" if (e.source, e.target) in disabled_edges
                                    else "node" if {e.source, e.target} & disabled_nodes
                                    else None)

    supply_bcm = ({f: spec[5] for f, spec in FIELDS.items()} | SOURCE_SUPPLY
                  | {t: spec[5] for t, spec in LNG_TERMINALS.items()} | (supply or {}))
    demand_bcm = {n: bcm for n, (bcm, _) in DEMAND.items()} | (demand or {})
    # Priced tranches: fields can swing up, LNG costs extra, and markets can
    # cut demand as a last resort (that "supply" is demand reduction, not gas).
    tranches = {}
    for node_id, amount in supply_bcm.items():
        if node_id in FIELDS:
            tranches[node_id] = [(amount, 0.0), (amount * SWING_SHARE, SWING_PREMIUM_KM)]
        elif node_id in LNG_TERMINALS:
            tranches[node_id] = [(amount, LNG_COST_PREMIUM_KM)]
        else:
            tranches[node_id] = [(amount, 0.0)]
    for r in REGIONS:
        if r not in disabled_nodes:
            tranches[r] = [(demand_bcm.get(r, 0.0) * DEMAND_RESPONSE_SHARE, DEMAND_RESPONSE_COST_KM)]
    _solve_flows(g, tranches, supply_bcm, demand_bcm)
    _add_node_economics(g)
    return g


def _solve_flows(g: Graph, tranches: dict, supply: dict[str, float],
                 demand: dict[str, float]) -> None:
    def usable(e, c):
        return c if e.attributes["status"] == "operating" and not e.attributes["disabled"] else 0.0

    result = min_cost_flow(
        g, tranches, demand,
        capacity=lambda e: usable(e, e.capacity),
        reverse_capacity=lambda e: usable(e, e.attributes["reverse_capacity"]),
        node_tiers={t: EXPORT_TIERS for t in LNG_EXPORTS},
    )
    for e in g.edges:
        flow = result.edge_flow.get((e.source, e.target), 0.0)  # negative = reversed
        value_year = gas_value_eur(abs(flow), e.attributes["price_eur_mwh"])
        e.attributes.update({
            "flow_bcm_year": round(flow, 3),
            "utilization": round(abs(flow) / (e.capacity if flow >= 0 else e.attributes["reverse_capacity"]), 3)
                           if flow else 0.0,
            "value_eur_year": round(value_year),
            "value_eur_day": round(value_year / 365),
        })
    for node in g.nodes:
        a = node.attributes
        if node.id in supply:
            a["supply_bcm_year"] = supply[node.id]
            if node.id in FIELDS:
                a["swing_bcm_year"] = round(supply[node.id] * SWING_SHARE, 3)
            a["supplied_bcm_year"] = round(result.supplied.get(node.id, 0.0), 3)
        if node.id in demand:
            # A region's "supply" is demand reduction; the rest arrived as gas.
            reduced = result.supplied.get(node.id, 0.0) if node.id in REGIONS else 0.0
            met = result.delivered.get(node.id, 0.0)
            a["demand_bcm_year"] = demand[node.id]
            a["market"] = DEMAND.get(node.id, (0, a["country"]))[1]
            a["delivered_bcm_year"] = round(met - reduced, 3)
            a["demand_reduced_bcm_year"] = round(reduced, 3)
            a["unmet_bcm_year"] = round(demand[node.id] - met, 3)


def _add_node_economics(g: Graph) -> None:
    """Give each node the flow and value of gas passing through it.

    Throughput is the larger of inflow and outflow, so a field counts what it
    sends out and a terminal counts what it receives. Node values overlap with
    the edges and each other, so they should not be summed across the network.
    """
    inflow = {n.id: [0.0, 0.0] for n in g.nodes}   # [bcm, EUR]
    outflow = {n.id: [0.0, 0.0] for n in g.nodes}
    for e in g.edges:
        flow = e.attributes["flow_bcm_year"]
        sender, receiver = (e.source, e.target) if flow >= 0 else (e.target, e.source)
        for totals, node_id in ((outflow, sender), (inflow, receiver)):
            totals[node_id][0] += abs(flow)
            totals[node_id][1] += e.attributes["value_eur_year"]
    for node in g.nodes:
        (in_bcm, in_eur), (out_bcm, out_eur) = inflow[node.id], outflow[node.id]
        value_year = max(in_eur, out_eur)
        node.attributes.update({
            "inflow_bcm_year": round(in_bcm, 3),
            "outflow_bcm_year": round(out_bcm, 3),
            "throughput_bcm_year": round(max(in_bcm, out_bcm), 3),
            "value_eur_year": round(value_year),
            "value_eur_day": round(value_year / 365),
        })


def format_eur(amount: float) -> str:
    for size, suffix in ((1e9, "bn"), (1e6, "m"), (1e3, "k")):
        if abs(amount) >= size:
            return f"EUR {amount / size:.1f}{suffix}"
    return f"EUR {amount:.0f}"


if __name__ == "__main__":
    g = build_gas_network()
    print(g)
    print("\nEdges")
    for e in g.edges:
        a = e.attributes
        print(f"  {g.get_node(e.source).name:>20} -> {g.get_node(e.target).name:<20}"
              f" {a['flow_bcm_year']:>6.2f} bcm/yr  {format_eur(a['value_eur_year']):>13}/yr"
              f"  {format_eur(a['value_eur_day']):>12}/day  {a['pipeline']}"
              f"{'' if a['status'] == 'operating' else ' [' + a['status'] + ']'}")
    print("\nNodes")
    for n in sorted(g.nodes, key=lambda n: -n.attributes["value_eur_year"]):
        a = n.attributes
        print(f"  {n.name:>20} ({a['country']:<14}) {a['throughput_bcm_year']:>6.2f} bcm/yr"
              f"  {format_eur(a['value_eur_year']):>13}/yr  {format_eur(a['value_eur_day']):>12}/day")

    print("\nDemand by market (bcm/yr)")
    by_country: dict[str, list[float]] = {}
    for n in g.nodes:
        if "demand_bcm_year" in n.attributes:
            row = by_country.setdefault(n.attributes["market"].split(" (")[0], [0.0, 0.0])
            row[0] += n.attributes["demand_bcm_year"]
            row[1] += n.attributes["delivered_bcm_year"]
    for country, (want, got) in sorted(by_country.items(), key=lambda kv: -kv[1][0]):
        print(f"  {country:<20} demand {want:6.1f}  delivered {got:6.1f}  unmet {want - got:6.1f}")
    lng = [n.attributes for n in g.nodes if n.attributes["kind"] == "lng_import"]
    print(f"\nLNG imports: {sum(a['supplied_bcm_year'] for a in lng):.1f} bcm/yr"
          f" of {sum(a['supply_bcm_year'] for a in lng):.1f} send-out capacity")
    print("\nPipeline and field supply left unused (bcm/yr)")
    for n in g.nodes:
        a = n.attributes
        if (a["kind"] != "lng_import" and "supply_bcm_year" in a
                and a["supply_bcm_year"] - a["supplied_bcm_year"] > 0.01):
            print(f"  {n.name:<40} {a['supply_bcm_year'] - a['supplied_bcm_year']:6.1f} of {a['supply_bcm_year']:.1f}")
