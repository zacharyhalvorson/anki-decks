# Meaning-specific Nihongo links

`nihongo-links.json` keys each reviewed link by exact Word, Reading, and Meaning. The shared answer templates expose these three existing fields in a hidden span; `dictionary_links.js` replaces the ordinary word link only when all three match. No note fields or model schema are added. `apply_templates.py` embeds the rules in both answer templates.

The N4 review checked 1,150 notes against JMdict. Fifty ambiguous headwords receive reviewed sequence-number links; seven cards intentionally spanning multiple entries/readings open dictionary search. Both arrival notes point to entry **1422970, 着く**, rather than entry 1331530, 就く. The legacy つく key remains for older exports. Words outside this reviewed set retain their normal word links.

Sources: [JMdict, EDRDG](https://www.edrdg.org/pub/Nihongo/JMdict_e.gz) and [Nihongo's official app-link documentation](https://nihongo-app.com/faq.html). `n4-link-audit.json` records candidate entries, decisions and the source hash. Dictionary excerpts are from JMdict, © EDRDG, used under its [licence](https://www.edrdg.org/edrdg/licence.html).

`python3 scripts/fix_n4_arrival.py` repairs the original N4 arrival note in place: 着く, 着きます in the plain and furigana example fields, and the existing reviewed 着 breakdown. It preserves GUIDs, cards, audio, meaning, and examples' pronunciation. It updates the sort field, checksum and modification metadata. The separate, already-correct 着く note remains to preserve existing study history.

Checks: `node scripts/tests/dictionary_links.cjs`, `python3 scripts/test_visual_senses.py`, and the export builder's identity, scheduling, media and schema checks. All headwords containing kanji were screened for absent breakdown characters; no additional gaps were found. Kana-only verbs, same-reading word groups, and kana spellings in verb/adjective examples were reviewed; ordinary kana forms such as できる and まっすぐ were retained.

Only the N4 export was rebuilt in this pass. The URL construction is tested locally; actual AnkiMobile → Nihongo routing on iPad still requires device verification.
