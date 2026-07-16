from __future__ import annotations

# Conservative product-type SEO vocabulary. Terms are suggestions only and are used
# only when the product analysis supports the corresponding product type.
KEYWORD_LIBRARY: dict[str, dict[str, list[str]]] = {
    "power button": {
        "英语": ["Power Button", "Start Button", "Power Switch"],
        "西班牙语": ["Botón de Encendido", "Botón de Inicio", "Interruptor"],
        "意大利语": ["Pulsante di Accensione", "Pulsante Start", "Interruttore"],
        "荷兰语": ["Aan-uitknop", "Startknop", "Schakelaar"],
        "日语": ["電源ボタン", "スタートボタン", "スイッチ"],
        "德语": ["Ein/Aus-Schalter", "Starttaste", "Netzschalter"],
        "法语": ["Bouton Marche Arrêt", "Bouton de Démarrage", "Interrupteur"],
        "葡萄牙语": ["Botão Liga/Desliga", "Botão de Início", "Interruptor"],
        "瑞典语": ["Strömknapp", "Startknapp", "Strömbrytare"],
    },
    "vacuum filter": {
        "英语": ["Vacuum Filter", "Replacement Filter", "Washable Filter"],
        "西班牙语": ["Filtro de Aspiradora", "Filtro de Repuesto", "Filtro Lavable"],
        "意大利语": ["Filtro Aspirapolvere", "Filtro di Ricambio", "Filtro Lavabile"],
        "荷兰语": ["Stofzuigerfilter", "Vervangingsfilter", "Wasbaar Filter"],
        "日语": ["掃除機フィルター", "交換フィルター", "洗えるフィルター"],
        "德语": ["Staubsaugerfilter", "Ersatzfilter", "Waschbarer Filter"],
        "法语": ["Filtre Aspirateur", "Filtre de Rechange", "Filtre Lavable"],
        "葡萄牙语": ["Filtro de Aspirador", "Filtro de Reposição", "Filtro Lavável"],
        "瑞典语": ["Dammsugarfilter", "Ersättningsfilter", "Tvättbart Filter"],
    },
    "roller brush": {
        "英语": ["Roller Brush", "Brush Roll", "Floor Brush"],
        "西班牙语": ["Cepillo Rodillo", "Rodillo de Cepillo", "Cepillo de Suelo"],
        "意大利语": ["Spazzola a Rullo", "Rullo Spazzola", "Spazzola Pavimenti"],
        "荷兰语": ["Borstelrol", "Roterende Borstel", "Vloerborstel"],
        "日语": ["ローラーブラシ", "回転ブラシ", "床用ブラシ"],
        "德语": ["Bürstenrolle", "Walzenbürste", "Bodenbürste"],
        "法语": ["Brosse Rotative", "Rouleau Brosse", "Brosse de Sol"],
        "葡萄牙语": ["Escova de Rolo", "Rolo de Escova", "Escova de Piso"],
        "瑞典语": ["Borstvals", "Roterande Borste", "Golvborste"],
    },
    "print head": {
        "英语": ["Print Head", "Printer Head", "Replacement Printhead"],
        "西班牙语": ["Cabezal de Impresión", "Cabezal de Impresora"],
        "意大利语": ["Testina di Stampa", "Testina Stampante"],
        "荷兰语": ["Printkop", "Printerkop"],
        "日语": ["プリントヘッド", "印刷ヘッド"],
        "德语": ["Druckkopf", "Drucker-Druckkopf"],
        "法语": ["Tête d'Impression", "Tête d'Imprimante"],
        "葡萄牙语": ["Cabeça de Impressão", "Cabeçote de Impressora"],
        "瑞典语": ["Skrivhuvud", "Skrivarhuvud"],
    },
    "shaver head": {
        "英语": ["Shaver Head", "Replacement Shaving Head", "Rotary Shaver Head"],
        "西班牙语": ["Cabezal de Afeitadora", "Cabezal de Repuesto"],
        "意大利语": ["Testina Rasoio", "Testina di Ricambio"],
        "荷兰语": ["Scheerkop", "Vervangende Scheerkop"],
        "日语": ["シェーバーヘッド", "交換用シェービングヘッド"],
        "德语": ["Scherkopf", "Ersatz-Scherkopf"],
        "法语": ["Tête de Rasoir", "Tête de Rasage de Rechange"],
        "葡萄牙语": ["Cabeça de Barbeador", "Cabeça de Reposição"],
        "瑞典语": ["Rakhuvud", "Ersättningshuvud"],
    },
    "extruder cover": {
        "英语": ["Extruder Cover", "Extruder Housing", "3D Printer Cover"],
        "西班牙语": ["Cubierta de Extrusor", "Carcasa de Extrusor"],
        "意大利语": ["Coperchio Estrusore", "Alloggiamento Estrusore"],
        "荷兰语": ["Extruderkap", "Extruderbehuizing"],
        "日语": ["エクストルーダーカバー", "押出機ハウジング"],
        "德语": ["Extruder-Abdeckung", "Extrudergehäuse"],
        "法语": ["Couvercle d'Extrudeuse", "Boîtier d'Extrudeuse"],
        "葡萄牙语": ["Tampa do Extrusor", "Carcaça do Extrusor"],
        "瑞典语": ["Extruderkåpa", "Extruderhölje"],
    },
}

ALIASES = {
    "start button": "power button",
    "power switch": "power button",
    "washing machine button": "power button",
    "filter": "vacuum filter",
    "brush roll": "roller brush",
    "printer head": "print head",
    "shaving head": "shaver head",
    "razor head": "shaver head",
    "extruder top cover": "extruder cover",
}


def keywords_for(product_type: str, language: str) -> list[str]:
    key = (product_type or "").strip().lower()
    key = ALIASES.get(key, key)
    if key in KEYWORD_LIBRARY:
        return KEYWORD_LIBRARY[key].get(language, [])
    for alias, canonical in ALIASES.items():
        if alias in key:
            return KEYWORD_LIBRARY.get(canonical, {}).get(language, [])
    for known, by_lang in KEYWORD_LIBRARY.items():
        if known in key or (key and key in known):
            return by_lang.get(language, [])
    return []
