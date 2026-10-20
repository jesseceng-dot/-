"""Books 41–58 (西方现代思想家精品译丛): the ebook's pictures inside the lines, each read off its drawing and checked against
its context (the Chinese gloss, the transliteration beside it, the passage quoted).

- The publisher's name on every copyright page ('出版　⟨picture⟩') is its calligraphic logo: 中国社会科学出版社.
- The Greek words and phrases of the notes, letter for letter and mark for mark as drawn, misprints of the print included
  (χ for κ in 'χαχόν', accents out of place): what the picture shows is what the line now reads.  The variant letter forms
  of the typefaces (curled ρ, open κ, cursive θ) are set as ρ κ θ in whole words; where a picture is one letter of a word
  the ebook types in its own text (Συμπαϱανε⟨κ⟩ϱωμενοι, ⟨κ⟩ατα δυναμιν), as the letter form of that text (ϰ ϱ ϑ).
  The spaces the drawings misplace beside the open κ ('πολλουςϰ αι', 'τιϰ τει', 'σ ϰοπω') are where the words divide.
- The pictures of one letter that the ebook repeats as text right beside them (ψευδο⟨ς⟩ς, ο⟨ἱ⟩ἱτινες, ⟨ϰ⟩ϰαλο…: the
  letter typed in after the picture when the ebook was repaired) are set once: IMG_TWIN, see bk._img_text.
- One picture is the wrong one: note 〔749〕 of 非此即彼（上） shows the words of note 〔562〕 (the same file twice,
  'ἀφωρισμένος εἰς εὐαγγέλιον θεοῦ'); the note's own translation is of Marcus Aurelius VII 2, whose first words take
  its place (listed in the book's errata).
"""
_I = lambda t: (t, 'it')

IMG_TEXT = {}

for _n in ('06087', '06138', '06190', '06077', '06128', '06100', '06186', '06090', '06059', '06129', '06169', '06086',
           '06076', '06127'):
    IMG_TEXT[f'image{_n}.jpeg'] = '中国社会科学出版社'

_G = {
    # 开放社会及其敌人（第一卷）: Plato's two irrationals and Cornford's 'one and a half per mille'
    '06145.jpeg': [('√', 'rad'), ('2', '')], '06162.jpeg': [('√', 'rad'), ('3', '')], '06179.jpeg': '1½',
    # 社会主义: Epicurus, Luke 6:35
    '06219.jpeg': 'Αδιχία ού χαθ ἕαυτην χαχόν', '06041.jpeg': 'Μηδε͂ν ἀπελπίξοντεζ',
    # 论反讽概念
    '06032.gif': 'ἐποπτεία', '06107.gif': 'σωφροσύνη', '06124.gif': 'δραματικοί', '06141.gif': 'διηγηματίκοί',
    '06158.gif': 'κατὰ κρύψιν', '06175.gif': 'διασπορά', '06193.gif': 'συγχαταβασις', '06047.gif': 'τὸ δαιμόνιον',
    '06063.gif': 'ἔργον', '06079.gif': 'σημεῖον', '06096.gif': 'τὸ δαιμόνιόν μοι σημαίνει', '06113.gif': 'δαιμόνιόν τι',
    '06130.gif': 'τὸ δαιμόνιον γίγνεται', '06147.gif': 'αἰδώς', '06164.gif': 'γνῶθι σαὐτόν', '06181.gif': 'έκών—ἀκὤν',
    '06198.gif': 'χατὰχρύψιν', '06215.gif': 'χατὰ δύναμιν', '06037.gif': 'ἐπιστήμας', '06052.gif': 'λόγος',
    '06068.gif': 'πάθος', '06085.gif': 'ἠθος', '06102.gif': 'ἐποχή', '06119.gif': 'περὶ εἰρωνείας',
    '06136.gif': 'προσποίησις επι χειρον πραξεων χαὶ λόγων', '06153.gif': 'πληροφορία', '06170.gif': 'εὕρηκα',
    '06188.gif': 'εὕρηκα',
    # 非此即彼（上）
    '06075.jpeg': [_I('Τὰ εἰς ἑαυτόν')],
    '06092.jpeg': 'Δημοσθενης. ',                    # (Aristophanes, Knights 32–35: the speakers' lines, '/' between them)
    '06109.jpeg': "ποῖον βρετας; ἐτεὸν ἡγεῖ γὰρ θεούς; / Νικιας. ἔγωγε / Δημοσθενης. ποίῳ χρωμενος τεκμηρίῳ; / Νικιας. "
                  "ὁτιὴ θεοῖσιν ἐχθρὸς εἰμ'. οὐκ εἰκότως; / Δημοσθενης. 35. εὐ προσβιβάζεις με.",
    '06126.jpeg': '[Δημοσθενης. … εὐ προσβιβάζεις με.]',
    '06034.jpeg': 'συννεκροῦσθαι', '06049.jpeg': 'Συμπαρανεκρωμένοι', '06081.jpeg': 'Συμπαρανεκρωμένοι',
    '06098.jpeg': 'Πεισιθανατοι', '06115.jpeg': 'Πεισιθανατοι', '06132.jpeg': 'διανοια καὶ ἤθος',
    '06149.jpeg': 'διανοια καὶ ἤθος', '06143.jpeg': 'παρανεκροι', '06160.jpeg': 'παρανεκροι', '06177.jpeg': 'παράνεκρος',
    '06166.jpeg': 'ἁμαρτια', '06183.jpeg': 'ἁμαρτια', '06201.jpeg': 'ἁμαρτια', '06213.jpeg': 'νενεκρωμένος',
    # (Sophocles, Antigone 850–852: the verse lines, '/' between them, as the note's translation has them)
    '06217.jpeg': 'ἰὼ δύστανος', '06039.jpeg': "οὔτ' ἐν βροτοῖς οὔτ' ἐν νεκροισι / μέτοικος, οὐ ζῶσιν, οὐ θανοῦσι",
    '06055.jpeg': 'ἰὼ δύστανος', '06071.jpeg': 'ἰὼ δύστανος…οὐ ζῶσιν, οὐ θανοῦσι',
    '06088.jpeg': [('οὔτε λέγει οὔτε κρύπτει, ἀλλὰ σημαίνει', ''), ('1', 'msup')],    # (the source's note number in the drawing)
    '06105.jpeg': 'ἀφορισμενοι', '06122.jpeg': 'ἀφορισμενοι', '06156.jpeg': 'ἀφορισμενοι', '06173.jpeg': 'ἀφωρισμένοι',
    '06139.jpeg': 'ἀφωρισμένος εἰς εὐαγγέλιον θεοῦ',
    '06191.jpeg': 'πολλα μεταξυ πελει κυλικος και χειλεος ἀκρου',
    '06046.jpeg': 'πολιτικόν ζῷον',
    '06062.jpeg': 'ἀναβιῶναί σοι ἔξεστιν· ἴδε πάλιν τὰ πράγματα ',      # (the wrong picture: see above)
    '06078.jpeg': 'ὡς ἑώρας· ἐν τούτῳ γαρ τὸ ἀναβιῶναι.',
    # (Aristophanes, Plutus 189–192: the speakers in italics, their turns divided by '/', the line numbers kept)
    '06208.jpeg': [_I('Χρεμυλος.')],
    '06031.jpeg': [(' 189. …… ἐστὶ πάντων πλησμονή. 190. ἔρωτος. / ', ''), _I('Καριων.'), (' ἄρτων. / ', ''),
                   _I('Χρεμυλος.'), (' μουσικῆς. / ', ''), _I('Καριων.'), (' τραγημάτων. / ', ''), _I('Χρεμυλος.'),
                   (' 191. τιμῆς. / ', ''), _I('Καριων.'), (' πλακούντων. / ', ''), _I('Χρεμυλος.'), (' ἀνδραγαθίας. / ', ''),
                   _I('Καριων.'), (' ἰσχάδων. / ', ''), _I('Χρεμυλος.'), (' 192. φιλοτιμίας. / ', ''), _I('Καριων.'),
                   (' μάζης. / ', ''), _I('Χρεμυλος.'), (' στρατηγίας. / ', ''), _I('Καριων.'), (' φακῆς.', ''), ('i', 'msup')],
    # 非此即彼（下）: single letters of words the ebook types with ϰ ϱ
    '06036.jpeg': 'Ιδοὺ Ρόδος, ἰδοὺ καὶ τό πήδημα', '06146.jpeg': 'ϰ', '06163.jpeg': 'ϰ', '06180.jpeg': 'ϱ',
    '06197.jpeg': 'τό ἔν ἄρχη αἰτείν', '06051.jpeg': 'ς', '06067.jpeg': 'ϰ', '06084.jpeg': 'ϰ', '06101.jpeg': 'ϰ',
    '06118.jpeg': 'ϰ',
    # 哲学片断: the words with the open κ (the notes type the rest with ϑ)
    '06042.jpeg': 'ευϰαταφοια', '06187.jpeg': 'έρισιϰόν', '06204.jpeg': 'αναγϰ', '06220.jpeg': 'απεϰωλυσεν',
    '06058.jpeg': 'αϰινητος', '06074.jpeg': 'ϰινει', '06091.jpeg': 'πολλους ϰαι ϰαλους λογους ϰαι μεγαλοπρεπεις ',
    '06108.jpeg': 'τιϰτει ϰαι διανοηματα εν φιλοσοφια αφϑονω', '06125.jpeg': 'σϰοπω', '06142.jpeg': 'πολυπλοϰωτερον ϰαι',
    '06159.jpeg': 'ϰαι', '06176.jpeg': 'ϰαι', '06194.jpeg': 'σϰανδαλιζεσϑαι', '06212.jpeg': 'σϰανδαλον',
    '06033.jpeg': 'ϰινησις', '06048.jpeg': 'ϰαι', '06064.jpeg': 'ϰαι', '06080.jpeg': 'ζητηιϰη', '06097.jpeg': 'απορητιϰη',
    '06114.jpeg': 'σϰεπτιϰη', '06131.jpeg': 'ϑετιϰως', '06148.jpeg': 'σϰεπτιϰοι', '06165.jpeg': 'ήσϰαις',
    '06182.jpeg': 'επαϰολουϑει ή αταρξια', '06199.jpeg': 'εφεϰτιϰη',
    # 畏惧与颤栗 恐惧的概念 致死的疾病: single letters (most of them typed again beside the picture: IMG_TWIN)
    '06103.jpeg': 'ῇ', '06120.jpeg': 'ς', '06137.jpeg': 'ὗ', '06154.jpeg': 'ή', '06171.jpeg': 'ϰ', '06189.jpeg': 'ῇ',
    '06206.jpeg': 'ἱ', '06222.jpeg': 'ς',
    # 陶冶性的讲演集, 克尔凯郭尔讲演集
    '06144.jpeg': 'παθος', '06161.jpeg': 'φιλοσοφιας', '06065.jpeg': 'ἐμοὶ οὐκ ὀκνηρόν', '06099.jpeg': 'οὐ μισεῖ',
    '06116.jpeg': 'Αἴκα', '06133.jpeg': 'το έξαίφνης', '06167.jpeg': 'ὅτι ', '06184.jpeg': 'ἠγάπησεν πολύ',
    '06202.jpeg': 'κατ’ εξοχην', '06218.jpeg': '½',
}
IMG_TEXT.update({f'image{k}': v for k, v in _G.items()})

IMG_TWIN = {f'image{k}' for k in ('06120.jpeg', '06137.jpeg', '06154.jpeg', '06171.jpeg', '06189.jpeg', '06206.jpeg')}
