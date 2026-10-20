"""四本书的模块配置：巴菲特致股东的信·投资原则篇 / 财富、贫穷与政治 / 工作、消费主义和新穷人 / 股票大作手回忆录。

`book(b)` 返回 build.build 需要的 cfg（同黑格尔、康德、杜威各册）；页面为 16 开（BOOK_GEOM=k16）。
四本书各有一个工作目录（BOOK_SCRATCH），bk_make_all.py 逐本设置。
"""
import math
import os
import re
import shutil
from . import bk_extract as BE, bk_text as BT, kant_struct as KS, normalize, special, style
from .book import Mod, title_text, toc_runs
from .kant import finish_blocks, balance_headings, wrap_lines, repair_link
from .dewey import make_toc as toc_blocks
from .model import run, merge_runs, runs_text, BR
from .books import page_module

P = lambda n: f'part{n:04d}'
NOTE_MIN = 2400          # notes of consecutive short chapters are gathered until they fill about two small-print pages

# 《哥德尔、艾舍尔、巴赫》: paragraph classes of the ebook -> (style, first, left, run classes); indents in em as in its CSS
GEB_STYLE = {
    'calibre6': ('body', 2, 0, ''), 'calibre21': ('body', 2, 0, ''), 'text_indent': ('noindent', 0, 0, ''),
    'text_indent5': ('noindent', 0, 0, ''), 'hanging_indent': ('noindent', -2, 2, ''), 'dialog_h-indent': ('noindent', -2, 2, ''),
    'hanging_indent_1': ('noindent', -2, 4, ''), 'hanging_indent2': ('noindent', -4, 4, ''), 'hanging_indent_2': ('noindent', -3, 5, ''),
    'hanging_indent_3': ('noindent', -4, 6, ''), 'hanging_indent_4': ('noindent', -1, 2, ''), 'hanging_indent_5': ('noindent', -1, 3, ''),
    'hanging_indent_6': ('noindent', -1, 4, ''), 'hanging_indent_7': ('noindent', -1, 5, ''), 'hanging_indent_8': ('noindent', -1, 6, ''),
    'duiweicangtou': ('noindent', -6, 6, ''), 'question': ('noindent', -3, 3, ''), 'speculation': ('noindent', -2, 3, ''),
    'text_indent1': ('body', 2, 2, ''), 'text_indent2': ('body', 2, 2, ''), 'text_indent3': ('body', 2, 4, ''),
    'text_indent6': ('body', 2, 4, ''), 'text_indent4': ('body', 2, 6, ''), 'text_indent-left': ('noindent', 0, 2, ''),
    'd_indent_': ('noindent', 0, 2, ''), 'd_indent_1': ('noindent', 0, 2, ''), 'd_indent_2': ('noindent', 0, 4, ''),
    'd_indent_4': ('noindent', 0, 6, ''), 'reference': ('noindent', -2, 2, ''), 'reference1': ('noindent', -2, 4, ''),
    'reference-note': ('small', 2, 2, ''), 'preface_quote': ('small', 0, 2, ''), 'd_indent_3': ('smalll', 0, 0, ''),
    'hanging_2_2-small': ('small', -2, 4, ''), 'text_indent-small': ('small', 2, 2, ''), 'centersmalltext': ('smallc', 0, 0, ''),
    'dialog_kaiti': ('smallkai', 0, 2, ''), 'center': ('center', 0, 0, ''), 'right1': ('right', 0, 0, ''),
    'quote_text': ('quote', 2, 2, ''), 'quote_text1': ('quote', 2, 2, ''), 'view_text': ('quote', 2, 2, ''),
    'dialog_guided': ('quote', 2, 2, ''), 'quote_text-indent': ('quote', 0, 2, ''), 'quote_text-hanging': ('quote', -2, 4, ''),
    'quote_text_hanging_1': ('quote', -3, 5, ''), 'quote_text_hanging_': ('quote', -4, 6, ''), 'quote_text_': ('quote', -2, 6, ''),
    'hanging_indent_': ('quote', -4, 5, ''), 'zen_koan': ('quote', 0, 2, ''), 'zen_koan1': ('quote', 0, 3, ''),
    'quote_text_kaiti': ('quote', 0, 2, ''), 't_indent_0-5-kaiti': ('quote', 0, 5, ''),
    'zen_koan-poem': ('ck', 0, 0, ''), 'dialog_poem_title': ('ck', 0, 0, ''),
    'dialog_poem': ('verse', 0, 2, ''), 'dialog_poem1': ('verse', 0, 3, ''), 'dialog_poem2': ('verse', 0, 4, ''),
    'hanging_indent_rule': ('noindent', -5, 5, 'hei'), 'h_indent_3_rule': ('noindent', -3, 3, 'hei'),
    'hanging_indent-2_rule': ('noindent', -2, 2, 'hei'), 'h_indent_4_rule': ('noindent', -4, 4, 'hei'),
    'hanging_indent_rule_': ('noindent', -3, 5, 'hei'), 'hanging_indent_rule_1': ('noindent', -2, 6, 'hei'),
    'hanging_indent1': ('noindent', -6, 6, 'hei'), 'rule_hanging_5_p': ('noindent', 2, 3, 'hei'),
    'text_indent-bold': ('noindent', 0, 0, 'hei'), 'heiti1': ('body', 2, 0, 'hei'),
    'signature': ('right', 0, 0, 'kai'), 'quote_text_signature1': ('right', 0, 0, 'kai'), 'quote_text_honorific': ('right', 0, 0, 'kai'),
    'dedicate_sub': ('right', 0, 0, 'kai'), 'geb-byline': ('right', 0, 0, 'kai'),
    'dialog_sub_or': ('center', 0, 0, ''), 'dialog_sub': ('center', 0, 0, 'kai'), 'geb-multilingual-byline': ('noindent', 0, 0, ''),
}

CFG = {
    1: dict(scratch='q1', file='巴菲特致股东的信', title='巴菲特致股东的信', sub='投资原则篇', author='〔美〕杰里米·米勒 著',
            credits=['郝旭奇　译'], publisher='中信出版集团', pdf_author='〔美〕杰里米·米勒', cover='cover00196.jpeg', title_img=None,
            copyright=27, marker='sq',
            front=[(2, 'dedication'), (3, 'kaitext'), (4, 'kaitext'), (5, 'text')], body=list(range(6, 20)),
            back=list(range(20, 27)), tail=[],
            inplace={'image00191.jpeg', 'image00192.jpeg', 'image00193.jpeg', 'image00194.jpeg', 'image00195.jpeg'}),
    2: dict(scratch='q2', file='财富、贫穷与政治', title='财富、贫穷与政治', sub='', author='〔美〕托马斯·索维尔 著',
            credits=['孙志杰　译'], publisher='浙江教育出版社', pdf_author='〔美〕托马斯·索维尔', cover='cover00223.jpeg', title_img=None,
            copyright=1, marker='plain', front=[], body=list(range(3, 9)), back=[9], tail=[], inplace=set()),
    3: dict(scratch='q3', file='工作、消费主义和新穷人', title='工作、消费主义和新穷人', sub='', author='〔英〕齐格蒙特·鲍曼 著',
            credits=['郭　楠　译'], publisher='上海社会科学院出版社', pdf_author='〔英〕齐格蒙特·鲍曼', cover='cover00111.jpeg',
            title_img='image00108.jpeg', copyright=1, marker='sq', front=[(2, 'text')], body=[4, 5, 6, 7, 8, 9, 10, 11, 12], back=[],
            tail=['image00109.jpeg', 'image00110.jpeg'], inplace=set()),
    4: dict(scratch='q4', file='股票大作手回忆录', title='股票大作手回忆录', sub='', author='〔美〕埃德温·勒菲弗 著',
            credits=['丁圣元　译'], publisher='凤凰出版社', pdf_author='〔美〕埃德温·勒菲弗', cover='cover00221.jpeg',
            title_img='image00200.jpeg', copyright=1, marker='paren', front=[(3, 'text'), (4, 'text')], body=list(range(5, 29)),
            back=[29, 30], tail=[], inplace={'image00219.jpeg', 'image00220.jpeg'}),
    # ---- books 5-10: two EPUBs (5, 6) and four AZW3 (7-10)
    5: dict(scratch='q5', file='叫魂', title='叫魂', sub='1768年中国妖术大恐慌', author='〔美〕孔飞力 著', credits=['陈兼　刘昶　译'],
            publisher='上海三联书店', pdf_author='〔美〕孔飞力', cover='cover.jpg', cover_file='source/covers/05-叫魂.png', title_img=None, copyright=None, marker='sq', renum=True,
            head_clean=True, merge_dash_head=True, cls_cap=('caption',), cls_right=('year', 'year1', 'year2'), cls_quote=('call',),
            img_text={'char01.png': '饘'},
            front=[(2, 'text'), (3, 'text')],
            body=[[4, 5, 6, 7, 8, 9], [10, 11, 12], [13, 14, 15], [16, 17, 18, 19], [20, 21, 22, 23], [24, 25, 26, 27],
                  [28, 29, 30, 31, 32, 33], [34, 35, 36, 37, 38, 39], [40, 41, 42, 43, 44, 45, 46, 47], [48, 49, 50, 51, 52]],
            back=[53, 54, 55, 56], tail=[], inplace=set()),
    6: dict(scratch='q6', file='狂热分子', title='狂热分子', sub='码头工人哲学家的沉思录', author='〔美〕埃里克·霍弗 著', credits=['梁永安　译'],
            publisher='广西师范大学出版社', pdf_author='〔美〕埃里克·霍弗', cover='cover1.jpeg', cover_file='source/covers/06-狂热分子.png', title_img=None, copyright=50, marker='sq',
            head_clean=True, merge_dash_head=True, strip_indent=True, skip_text=('【注释】',), renum=True,
            head_cls={'prefacetitle': 1, 'h2sub': 1}, head_sub=[(r'^0*(\d{1,3})(?=\D)', '\\1　')],
            cls_quote=('editornote',), cls_right=('signature', 'author'),
            part_split=r'^(第[一二三四五六七八九十]+部分)[\s　]*(.*)$', part_sub_cls=('h1note',),
            front=[(2, 'dedication'), (3, 'dedication'), (4, 'text'), (6, 'text'), (7, 'text')],
            body=[8, [9, 10], [11, 12], [13, 14], 15, [16, 17], [18, 19], [20, 21], [22, 23], [24, 25], [26, 27], [28, 29], [30, 31],
                  32, [33, 34], [35, 36], [37, 38], 39, [40, 41], [42, 43], [44, 45], [46, 47]],
            back=[(48, 'noindent')], tail=[], backcover='00001.jpeg', inplace=set()),
    7: dict(scratch='q7', file='漫步华尔街', title='漫步华尔街', sub='（原书第12版）', author='〔美〕伯顿·G.马尔基尔 著', credits=['张　伟　译'],
            publisher='机械工业出版社', pdf_author='〔美〕伯顿·G.马尔基尔', cover='cover00359.jpeg', title_img=None, copyright=0, copyright_skip=5,
            marker='sq', renum=True, img_text={'image00280.jpeg': ('R', 'it ov'), 'image00281.jpeg': ('U', 'it ov')},
            head_cls={'p6': (5, r'^\d+[.．]\s')}, cls_cap=('middle-img',), cls_right=('you1',), cls_quote=('ziti1',),
            cls_center=('p6',), cap_mode='tabfig', cap_after_re=r'^(①|②|③|资料来源|数据来源|注[：:])', label_re=r'^([图表][^\s　]+)',
            part_re=r'^第[一二三四]部分', part_split=r'^(第[一二三四]部分)[\s　]*(.*)$',
            front=[(2, 'text'), (3, 'dedication'), (4, 'text'), (5, 'text')],
            body=[list(range(6, 13)), list(range(13, 18)), list(range(18, 24)), list(range(24, 29)), list(range(29, 39)),
                  list(range(39, 47)), list(range(47, 53)), list(range(53, 59)), list(range(59, 67)), list(range(67, 73)),
                  list(range(73, 80)), list(range(80, 92)), list(range(92, 97)), list(range(97, 105)), list(range(105, 112))],
            back=[112, 113, 114, 115], tail=[], inplace=set()),
    8: dict(scratch='q8', file='失控', title='失控', sub='机器、社会与经济的新生物学', author='〔美〕凯文·凯利 著',
            credits=['陈新武　陈之宇　顾珮嵚　郝宜平', '卢蔚然　陆丁　王钦　小青', '袁璐　张鹃　张行舟　译', '赵嘉敏　审校'],
            publisher='新星出版社', pdf_author='〔美〕凯文·凯利', cover='cover00466.jpeg', title_img=None, copyright=2, marker='sq',
            head_clean=True, table_head=False, head_cls={'title1': 1, 'title2': 2}, head_keep={'title1': 'middle'},
            cls_right=('normaltext1',), cls_quote=('normaltext2',), cls_center=('title5', 'subtitle1'), cls_refhead=('subtitle2',),
            skip_text=('注释',), img_text={'image00464.jpeg': '‰'}, img_max_scale=0.6,
            orn={f'image{n:05d}.jpeg' for n in range(442, 466) if n != 464}, orn_size=(38.0, 38.0),
            front=[(3, 'text'), (4, 'text'), (5, 'dedication'), (6, 'text')], body=list(range(7, 31)),
            back=[31, 32, 33, 34], tail=[], inplace={'image00441.jpeg'}),
    9: dict(scratch='q9', file='血酬定律', title='血酬定律', sub='中国历史中的生存游戏', author='吴思 著', credits=[],
            publisher='', pdf_author='吴思', cover='cover00255.jpeg', cover_file='source/covers/09-血酬定律.png', title_img='image00191.jpeg', copyright_img='image00192.jpeg',
            marker='sq', note_by_marker=True, head_clean=True, strip_indent=True, head_sub=[(r'^\[\s*', '【')],
            part_re=r'^【[正杂]编】', part_split=r'^【([正杂]编)】()$',
            front=[(3, 'text'), (4, 'text')], body=list(range(5, 24)), back=[24, 25], endnotes=[26], endnotes_title='脚注',
            tail=[], inplace=set()),
    10: dict(scratch='q10', file='政治学通识', title='政治学通识', sub='', author='包刚升 著', credits=[],
             publisher='北京大学出版社', pdf_author='包刚升', cover='cover00344.jpeg', title_img=None, copyright=1, marker='sq',
             note_by_marker=True, head_clean=True, cls_quote=('kindle-cn-ref',), cls_right=('kindle-cn-signature',),
             cap_mode='tabfig', cap_after_re=r'^(备注|资料来源|注[：:]|数据来源)', label_re=r'^([图表][^\s　]+)',
             img_para={'image00316.jpeg': [
                 [run('N', c='it'), run('v', c='it msub'), run(' = 1 / Σ'), run('V', c='it'), run('i', c='it msub'), run('2', c='msup')],
                 [run('N', c='it'), run('s', c='it msub'), run(' = 1 / Σ'), run('S', c='it'), run('i', c='it msub'), run('2', c='msup')]]},
             front=[(2, 'kaibody')], body=list(range(3, 17)), back=[17], tail=[], inplace=set()),
    # ---- books 11-15: proof-read (corrections in bk_fixes.py), three AZW3 (11, 13, 14) and two EPUBs (12, 15)
    11: dict(scratch='q11', exp_sup=True, file='大国政治的悲剧', title='大国政治的悲剧', sub='（修订版）', author='〔美〕约翰·米尔斯海默 著',
             credits=['王义桅　唐小松　译'], publisher='上海人民出版社', pdf_author='〔美〕约翰·米尔斯海默', series='东方编译所译丛',
             cover='cover00437.jpeg', title_img=None, copyright=0, marker='sqcirc', note_cls=('kindle-cn-footnote',), head_clean=True,
             head_sub=[(r'^附[\s\u3000]*录[\s\u3000]*', '附录\u3000')], cls_cap=('kindle-cn-caption', 'kindle-cn-caption1'),
             cap_mode='tabfig', cap_after_re=r'^(注[：:]|资料来源)', label_re=r'^([图表][^\s　]+)', cls_hang=('kindle-cn-para-hang',),
             join_cont=r'（续表）', img_max_scale=0.3,
             front=[(1, 'kaibody'), (2, 'kaibody'), (3, 'kaibody'), (4, 'kaibody'), (5, 'kaibody')], body=list(range(7, 17)), back=[17, 18],
             tail=[], inplace={'image00403.jpeg'}),
    12: dict(scratch='q12', exp_sup=True, file='法律的概念', title='法律的概念', sub='（增訂三版）', author='H. L. A. 哈特 著',
             credits=['許家馨　李冠宜　譯'], publisher='商周出版', pdf_author='H. L. A. 哈特', cover='cover.jpg', title_img=None,
             copyright=None, marker='zhu', tc=True, cjk='TC', notes_title='註　釋', notes_toc='註釋', pgno_cls=('ta_c',),
             head_clean=True, head_demote={'李冠宜、許家馨': 'right'},
             front=[(1, 'text'), (2, 'text'), (3, 'text'), (4, 'text'), (5, 'text'), (list(range(6, 13)), 'text')],
             body=[list(range(13, 17)), list(range(17, 20)), list(range(20, 24)), list(range(24, 29)), list(range(29, 33)),
                   list(range(33, 37)), list(range(37, 42)), list(range(42, 46)), list(range(46, 50)), list(range(50, 56)),
                   list(range(56, 63))],
             back=[63, 64, 65], tail=[], inplace=set()),
    13: dict(scratch='q13', exp_sup=True, file='公正：该如何做是好？', title='公正', sub='该如何做是好？', author='〔美〕迈克尔·桑德尔 著',
             credits=['朱慧玲　译'], publisher='中信出版社', pdf_author='〔美〕迈克尔·桑德尔', cover='cover00199.jpeg', title_img=None,
             copyright=1, marker='keep', head_clean=True, head_split='／', front=[], body=list(range(3, 13)), back=[13], tail=[], inplace=set()),
    14: dict(scratch='q14', exp_sup=True, file='牛津通识读本：气候', title='气候', sub='', series='牛津通识读本', author='〔英〕马克·马斯林 著',
             credits=['朱邦芊　译'], publisher='译林出版社', pdf_author='〔英〕马克·马斯林', cover='cover00119.jpeg', title_img=None,
             copyright=1, marker='sq', head_cls={'heiti': 2, 'xiaobiao': 3}, cls_cap=('tuzhu-center',), cls_right=('bodytext-right',),
             front=[(3, 'text'), (4, 'text')], body=list(range(5, 15)), back=[], endnotes=[15], endnotes_title='注释',
             tail=[], inplace=set()),
    15: dict(scratch='q15', exp_sup=True, file='气候赌场', title='气候赌场', sub='全球变暖的风险、不确定性与经济学', author='〔美〕威廉·诺德豪斯 著',
             credits=['梁小民　译'], publisher='东方出版中心', pdf_author='〔美〕威廉·诺德豪斯', series='威廉·诺德豪斯著作系列',
             cover='image00246.jpeg', title_img=None, copyright=2, marker='paren', head_clean=True,
             head_sub=[(r'^(第\d+章)[|｜]?[\s\u3000]*', '\\1\u3000')], note_cls=('fnContent-1', 'fnContent-2'),
             cls_cap=('tuti', 'tuzhu', 'biaoti'), cap_mode='tabfig', label_re=r'^([图表][^\s　]+)',
             cls_right=('signContent-1-kaiti',), cls_quote=('bodyContent-2-kaiti', 'bodyContent-2-kaiti-top'),
             part_re=r'^PART', part_split=r'^(PART \d+) ([^A-Za-z]+?) ([A-Z].*)$',
             part_epi_cls=('bodyContent-1-kaiti', 'signContent-1-kaiti', 'bodyContent-1'),
             front=[(3, 'text'), (4, 'text'), (5, 'dedication'), (6, 'text'), (7, 'text'), (8, 'text')],
             body=[[10, 11]] + list(range(12, 17)) + [[17, 18]] + list(range(19, 26)) + [[26, 27]] + list(range(28, 32)) + [[32, 33]]
                  + list(range(34, 41)) + [[41, 42]] + list(range(43, 46)),
             back=[], tail=[], inplace=set()),
    16: dict(scratch='q16', exp_sup=True, file='哥德尔、艾舍尔、巴赫', title='哥德尔、艾舍尔、巴赫', sub='集异璧之大成',
             author='〔美〕侯世达 著', credits=['本书翻译组　译'], publisher='商务印书馆', pdf_author='〔美〕侯世达（Douglas R. Hofstadter）',
             cover='cover.jpeg', title_img=None, copyright=2, marker='sq', head_clean=True, backcover='01Back.jpg', toc_sections=False,
             head_num_cls=('chapter_number', 'part_number'), head_as_p={'view_title': 'refhead'},
             head_lvl={'title': 2, 'preface_title': 2, 'preface_title_zhcn': 2, 'view_title_part': 2, 'geb-index-heading': 2},
             part_re=r'^[上下]篇', part_split=r'^([上下]篇)[\s\u3000]+(.+)()$', part_img=True,
             cls_cap=('duokan-image-maintitle', 'duokan-image-maintitle1', 'duokan-image-subtitle', 'duokan-image-subtitle1',
                      'duokan-image-subtitle3'),
             fig_inline=True, q_left=2, div_left={'dialog_indent': 2, 'dialog_indent1': 1}, div_small=('smalltext3',), table2=True,
             formula_img=r'^(Formula\d|Gene-[1-578]\.|img_Chapter10_1)',
             cls_style=GEB_STYLE, front=[(3, 'dedication'), (5, 'text'), (6, 'text'), ([7, 8], 'text'), (9, 'text'), (10, 'text')],
             body=[11] + list(range(12, 27)) + [[27, 28]] + list(range(29, 47)) + [[47, 48]] + list(range(49, 57)),
             back=[57, 58], tail=[], inplace=set()),
    17: dict(scratch='q17', file='乡土中国', title='乡土中国', sub='', author='费孝通 著', credits=[], publisher='天津人民出版社',
             pdf_author='费孝通', series='果麦经典', cover='CB_3300027208_device_phone_frontcover.jpg', title_img=None, copyright=2,
             marker='sq', head_clean=True, skip_text=('注释',), lat_apos=True, li_hang=True, cls_cap=('imgdescript',), cls_right=('right-info',),
             cls_center=('subHead', 'content-c1', 'author'),
             img_text={'xtzg_math_01.svg': [('X', 'it'), '+1'], 'xtzg_math_02.svg': 'Tönnies', 'xtzg_math_03.svg': 'Émile',
                       'xtzg_math_04.svg': 'gǔ sǒu', 'xtzg_math_05.svg': 'cóng', 'xtzg_math_06.svg': 'kǔn', 'xtzg_math_07.svg': 'zé',
                       'xtzg_math_08.svg': '＊　＊　＊', 'xtzg_math_09.svg': '1+1>2'},
             front=[(3, 'text'), (4, 'figure'), (5, 'text')],
             body=list(range(6, 21)),
             back=[21, (22, 'figpages'), 23, 24], tail=[], inplace=set(),
             errata_note='底本是一份已经通读校订过的个人校订本（书末“本次校订说明”：26 处改正，7 条“校订注”与核查依据链接，均照排）。'
                         '转换时按要求只改正已经发现的明确错误，没有再全面校订；另把电子书网页式的半角空格（U+2002）和半角括号统一为中文排版规范。'),
    18: dict(scratch='q18', file='中国哲学简史', title='中国哲学简史', sub='', author='冯友兰 著', credits=['涂又光　译'],
             publisher='北京大学出版社', pdf_author='冯友兰', cover='00032.jpeg', title_img='00001.jpeg', copyright=1, marker='sq',
             note_cls=('note',), cls_quote=('block',), fig_inline=True, fig_dpi=300,
             img_text={'00002.jpeg': '𤴯', '00003.jpeg': '𢜔', '00004.jpeg': '乂', '00016.jpeg': '𬘡', '00017.jpeg': '𫍰',
                       '00018.jpeg': '𮭨', '00019.jpeg': '㑺',
                       # the eight trigrams (先天 order 乾兑离震巽坎艮坤), hexagrams and yao signs, read off line by line
                       '00005.jpeg': ('☰', 'gua'), '00006.jpeg': ('☱', 'gua'), '00007.jpeg': ('☲', 'gua'), '00008.jpeg': ('☳', 'gua'),
                       '00009.jpeg': ('☴', 'gua'), '00010.jpeg': ('☵', 'gua'), '00011.jpeg': ('☶', 'gua'), '00012.jpeg': ('☷', 'gua'),
                       'dui_latex.svg': ('☱', 'gua'), '00013.jpeg': ('䷀', 'gua'), '00014.jpeg': ('䷁', 'gua'), '00015.jpeg': ('䷂', 'gua'),
                       '00020.jpeg': ('䷗', 'gua'), '00021.jpeg': ('䷒', 'gua'), '00022.jpeg': ('䷊', 'gua'), '00023.jpeg': ('䷡', 'gua'),
                       '00024.jpeg': ('䷪', 'gua'), '00025.jpeg': ('䷫', 'gua'), '00026.jpeg': ('䷠', 'gua'), '00027.jpeg': ('䷋', 'gua'),
                       '00028.jpeg': ('䷓', 'gua'), '00029.jpeg': ('䷖', 'gua'),
                       'yang_latex.svg': ('⚊', 'gua'), 'yin_latex.svg': ('⚋', 'gua'), 'yang_emblem_latex.svg': ('⚌', 'gua'),
                       'yin_emblem_latex.svg': ('⚍', 'gua')},
             front=[(2, 'text')], body=list(range(4, 32)), back=[], tail=[], inplace=set(),
             errata_note='按要求没有通读校订：这里只有转换时发现的排版问题（标点的全角半角、西文姓名缩写里的全角句点、漏掉的空格），'
                         '以及一处排成正文的小标题和一幅排错位置的插图。'),
    19: dict(scratch='q19', file='退出、呼吁与忠诚', title='退出、呼吁与忠诚', sub='对企业、组织和国家衰退的回应',
             author='〔美〕艾伯特·O.赫希曼 著', credits=['卢昌崇　译'], publisher='格致出版社　上海人民出版社',
             pdf_author='〔美〕艾伯特·O.赫希曼', series='世纪人文系列丛书　世纪前沿',
             cover=None, cover_file='source/covers/19-退出、呼吁与忠诚.png', title_img=None, copyright=2, marker='sq', lat_apos=True,
             note_cls=('divcontent-text_yinwen2', 'zhusi'), circ_link=r'#zs-bz\d+$', skip_text=('注释',),
             cls_quote=('divcontent-text_yinwen',), cls_right=('divcontent-text_right',),
             cls_center=('divcontent-text_center1', 'divcontent-text_center2'), cls_cap=('divcontent-text-tushuo', 'table-caption'),
             head_cls={'divcontent-text1': 2, 'divcontent-text_yinwen1': (3, r'^(?!注释$)')},
             fig_inline=True, fig_dpi=63, table2=True, table_keep=12, fig_join=[('ev_fig_13.svg', 'ev_fig_14.svg')], front_notes_each=True,
             # the reviser's LaTeX pictures of formulas and of words with accents, read off one by one (italic variables,
             # upright labels XAL ...; sub-scripts small and low; primes)
             img_text={'ev_math_001.svg': '635×965', 'ev_math_002.svg': '1/16', 'ev_math_003.svg': '1/2', 'ev_math_004.svg': '1/4',
                       'ev_math_005.svg': '3/4', 'ev_math_006.svg': '3×2', 'ev_math_007.svg': [('x', 'it'), '/5'],
                       'ev_math_008.svg': 'Café', 'ev_math_009.svg': 'Bogotá', 'ev_math_010.svg': 'orientación',
                       'ev_math_011.svg': 'Educação', 'ev_math_012.svg': 'François', 'ev_math_013.svg': 'Lainé',
                       'ev_math_014.svg': 'réforme', 'ev_math_015.svg': 'glücklich', 'ev_math_016.svg': 'già',
                       'ev_math_017.svg': 'XAL', 'ev_math_018.svg': 'XWL', 'ev_math_019.svg': 'XSI', 'ev_math_020.svg': 'ULB',
                       'ev_math_021.svg': 'TX', 'ev_math_022.svg': '50%', 'ev_math_023.svg': '100%',
                       'ev_math_024.svg': ['≥', ('Q', 'it'), ('x', 'it msub')], 'ev_math_025.svg': ['<', ('Q', 'it'), ('x', 'it msub')],
                       'ev_math_031.svg': [('A–B', 'it')],
                       'ev_math_032.svg': [('Q', 'it'), ('1', 'msub')], 'ev_math_033.svg': [('Q', 'it'), ('3', 'msub')],
                       'ev_math_034.svg': [('Q', 'it'), ('2', 'msub')], 'ev_math_035.svg': [('Q', 'it'), ('n', 'it msub')],
                       'ev_math_036.svg': [('Q', 'it'), ('0', 'msub')], 'ev_math_037.svg': [('Q', 'it'), ('E', 'it msub')],
                       'ev_math_038.svg': [('Q', 'it'), ('L', 'it msub')], 'ev_math_039.svg': [('Q', 'it'), ('C', 'it msub')],
                       'ev_math_043.svg': [('L', 'it'), ('0', 'msub')], 'ev_math_044.svg': [('L', 'it'), ('1', 'msub')],
                       'ev_math_045.svg': [('V', 'it'), ('1', 'msub')], 'ev_math_046.svg': [('V', 'it'), ('2', 'msub')],
                       'ev_math_047.svg': [('V', 'it'), ('3', 'msub')], 'ev_math_048.svg': [('P', 'it'), ('1', 'msub')],
                       'ev_math_049.svg': [('P', 'it'), ('2', 'msub')], 'ev_math_050.svg': [('P', 'it'), ('a', 'it msub')],
                       'ev_math_051.svg': [('P', 'it'), ('b', 'it msub')], 'ev_math_052.svg': [('P', 'it'), ('c', 'it msub')],
                       'ev_math_053.svg': [('E', 'it'), ('A', 'it msub')], 'ev_math_054.svg': [('E', 'it'), ('B', 'it msub')],
                       'ev_math_055.svg': [('P′', 'it')], 'ev_math_056.svg': [('P″', 'it')], 'ev_math_057.svg': [('Q′', 'it')],
                       'ev_math_058.svg': [('AA′', 'it')], 'ev_math_059.svg': [('BB′', 'it')], 'ev_math_060.svg': [('ABC', 'it')],
                       'ev_math_061.svg': [('CDA', 'it')], 'ev_math_062.svg': [('Q', 'it'), ('2', 'msub'), ('B', 'it')],
                       'ev_math_063.svg': [('Q', 'it'), ('2', 'msub'), ('D', 'it')],
                       'ev_math_064.svg': [('Q', 'it'), ('1', 'msub'), ('Q', 'it'), ('0', 'msub'), ('P′', 'it'), ('0', 'msub'), ('T′', 'it')],
                       'ev_math_065.svg': [('OQ', 'it'), ('1', 'msub')],
                       'ev_math_066.svg': [('L', 'it'), ('0', 'msub'), ('L', 'it'), ('1', 'msub')],
                       'ev_math_067.svg': [('L', 'it'), ('0', 'msub'), ('TP', 'it'), ('1', 'msub'), ('L', 'it'), ('1', 'msub')],
                       'ev_math_068.svg': [('ORT′Q', 'it'), ('1', 'msub')],
                       'ev_math_069.svg': [('OQ', 'it'), ('0', 'msub'), ('Q', 'it'), ('n', 'it msub'), ('Q′', 'it'), ('n', 'it msub')],
                       'ev_math_070.svg': [('Q', 'it'), ('E', 'it msub'), ('V', 'it'), ('2', 'msub')],
                       'ev_math_071.svg': [('Q', 'it'), ('0', 'msub'), ('V', 'it'), ('1', 'msub')],
                       'ev_math_072.svg': [('Q', 'it'), ('n', 'it msub'), ('Q′', 'it'), ('n', 'it msub')],
                       'ev_math_073.svg': [('Q', 'it'), ('E', 'it msub'), ('Q', 'it'), ('C', 'it msub')],
                       'ev_math_074.svg': [('A', 'it')], 'ev_math_075.svg': [('B', 'it')], 'ev_math_076.svg': [('C', 'it')],
                       'ev_math_077.svg': [('D', 'it')], 'ev_math_078.svg': [('E', 'it')], 'ev_math_079.svg': [('V', 'it')],
                       'ev_math_080.svg': [('P', 'it')], 'ev_math_084.svg': [('S', 'it')], 'ev_math_085.svg': [('x', 'it')]},
             img_text_plain=[(r'附录', r''), (r'“', r' Mathematical')],      # '附录A', the article 'A' of an English title: upright
             front=[(3, 'text'), (4, 'text'), (5, 'text'), (6, 'dedication'), (7, 'text')], body=list(range(8, 17)),
             back=[17, 18, 19, 20, 21, 22, (23, 'notes'), 24], tail=[], inplace=set(),
             errata_note='底本是一份已经通读修订过的个人校订本（书末“本次校订说明”：408 条文字修订，9 条“校订注”与核查依据链接，均照排）。'
                         '按要求没有再全面校订；这里只有转换时发现的排版问题。'),
    20: dict(scratch='q20', file='论证是一门学问', title='论证是一门学问', sub='', author='〔美〕安东尼·韦斯顿 著',
             credits=['姜昊骞　译'], publisher='天地出版社', pdf_author='〔美〕安东尼·韦斯顿', cover='cover00070.jpeg',
             title_img=None, copyright=1, marker='sq', lat_apos=True, cls_kai=('bodycontent-text_yinwen',),
             cls_right=('bodycontent-text_right',), cls_center=('bodycontent-text_center',),
             # the LaTeX pictures of the ebook: roman numerals and circled numbers of the CIP line, logic letters (italic),
             # E₁–E₃, the numerals I–IV that label conclusions (upright)
             img_text={'arg33-math-001.svg': 'Ⅰ', 'arg33-math-002.svg': '①', 'arg33-math-003.svg': 'Ⅱ', 'arg33-math-004.svg': '②',
                       'arg33-math-005.svg': 'Ⅲ', 'arg33-math-006.svg': 'Ⅳ', 'arg33-math-007.svg': ' © ',
                       'arg33-math-008.svg': '145mm×210mm', 'arg33-math-009.svg': '1/32', 'arg33-math-010.svg': '◆',
                       'arg33-math-011.svg': [('X', 'it')], 'arg33-math-012.svg': [('Y', 'it')], 'arg33-math-013.svg': '88%',
                       'arg33-math-014.svg': '50%', 'arg33-math-015.svg': [('E', 'it'), ('1', 'msub')],
                       'arg33-math-016.svg': [('E', 'it'), ('2', 'msub')], 'arg33-math-017.svg': [('E', 'it'), ('3', 'msub')],
                       'arg33-math-018.svg': [('p', 'it')], 'arg33-math-019.svg': [('q', 'it')], 'arg33-math-020.svg': [('s', 'it')],
                       'arg33-math-021.svg': [('b', 'it')], 'arg33-math-022.svg': [('r', 'it')], 'arg33-math-023.svg': [('c', 'it')],
                       'arg33-math-024.svg': [('a', 'it')], 'arg33-math-025.svg': [('d', 'it')], 'arg33-math-026.svg': [('f', 'it')],
                       'arg33-math-027.svg': [('l', 'it')], 'arg33-math-028.svg': 'I', 'arg33-math-029.svg': 'II',
                       'arg33-math-030.svg': 'III', 'arg33-math-031.svg': 'IV', 'arg33-math-032.svg': '25%'},
             front=[(3, 'text'), (4, 'text')], body=list(range(5, 16)), back=[16, 17], endnotes=[18], endnotes_title='注释',
             tail=[], inplace=set(),
             errata_note='按要求没有通读校订：这里只有转换时发现的排版问题（西文逗号后漏空格、西文里的全角冒号、套用的书名号）。'),
    21: dict(scratch='q21', file='这才是心理学', title='这才是心理学', sub='看穿伪心理学的本质（第10版）',
             author='〔加〕基思·斯坦诺维奇 著', credits=['窦东徽　刘肖岑　译'], publisher='中国人民大学出版社',
             pdf_author='〔加〕基思·斯坦诺维奇', cover='00004.jpeg', title_img=None, copyright=1, marker='sq', renum=True,
             lat_apos=True, li_hang=True, note_cls=('noteContent',), skip_text=('注释',),
             cls_quote=('yinwen',), cls_center=('yinwen1',), cls_right=('bodytext-right',), cls_cap=('tuzhu-center', 'page-label'),
             cls_map={'proof-note': ('smallkai', 0, 2), 'di': ('noindent', 0, 2)},     # the reviser's notes; the list of APA divisions
             head_sub=[(r'^(Chapter \d+)[\s\u2028]+', r'\1／'), (r'^推荐序 ', '推荐序\u3000')], head_split='／',
             head_split_balance=True, head_split_join='\u3000', head_demote={'表1-1 美国心理学会（APA）的分支机构': 'cap'},
             fig_inline=True, figpage_each=True, open_air=True,
             # the reviser's LaTeX pictures of numbers (each carries its LaTeX source; checked against the drawing): times 7:45,
             # ratios 16∶1, ranges 80～110, fractions a/b
             img_text={
                       'psy-math-002769163017.svg': '7:45', 'psy-math-0602d7c813c1.svg': '0.05', 'psy-math-071d4531b1c7.svg': '90%',
                       'psy-math-08985ebeaf12.svg': '20%', 'psy-math-0cfd86153ae2.svg': '36%', 'psy-math-1190e5399884.svg': '7:55',
                       'psy-math-124844a94058.svg': '609.6', 'psy-math-1d464f4ecc27.svg': '0.80',
                       'psy-math-1db007921411.svg': '58%', 'psy-math-268b204a015c.svg': '≈', 'psy-math-28d6d2a47fca.svg': '8%',
                       'psy-math-2b6b8c86778a.svg': '1%', 'psy-math-2d0ffa76cefe.svg': '80～110',
                       'psy-math-2eac8a7139ff.svg': '7:05', 'psy-math-2f93767b72dd.svg': '16∶1',
                       'psy-math-323665401a33.svg': '0.305', 'psy-math-380918b946a5.svg': '＝', 'psy-math-385223d01d09.svg': '2%',
                       'psy-math-3985b83ab29f.svg': '7:35', 'psy-math-39ef8fa9c9d8.svg': '0.00000033',
                       'psy-math-3ad2d7cc2c3f.svg': '1/600000', 'psy-math-3bb60d45ab44.svg': '600～800',
                       'psy-math-4075fa87d10c.svg': '10%', 'psy-math-40e4098702d3.svg': '100∶1',
                       'psy-math-41a94e154d3e.svg': '86.7%', 'psy-math-4387108b67da.svg': '69%',
                       'psy-math-441a04df7ce4.svg': '7.973', 'psy-math-4510b7bcd95a.svg': '77.5',
                       'psy-math-45aded9a043f.svg': '125～150', 'psy-math-46e32115bc24.svg': '60%', 'psy-math-4893e9df8b54.svg': 'α',
                       'psy-math-494cce58d2c6.svg': '105.6', 'psy-math-5055a2cf5dca.svg': '1/10',
                       'psy-math-51127aefe2e5.svg': '49.00', 'psy-math-52524a6cc469.svg': '27%', 'psy-math-552230819632.svg': '50%',
                       'psy-math-586b30cdcb5a.svg': '1/100', 'psy-math-58a44ef59594.svg': '75%',
                       'psy-math-5b25f56c05d1.svg': '64.3', 'psy-math-5e061ba9d1d9.svg': '____分之____',
                       'psy-math-6133ba955336.svg': '47%', 'psy-math-6165ec595070.svg': '21%',
                       'psy-math-6294b0aa1a92.svg': '0.000126', 'psy-math-63bec9cedbf3.svg': '7:21',
                       'psy-math-6bb65766f903.svg': '76.9%', 'psy-math-72898fffd9d8.svg': '4%', 'psy-math-72b8c71a2884.svg': '25%',
                       'psy-math-7306a5d2435e.svg': '0～0.000126', 'psy-math-773a15ec53a8.svg': '0.03',
                       'psy-math-7a53bd4744c5.svg': '101.9', 'psy-math-7b1bd53949b7.svg': '8.0',
                       'psy-math-7e88bc95b587.svg': '2.54', 'psy-math-81d93f7d474b.svg': '5～6',
                       'psy-math-833d2652d626.svg': '1/101', 'psy-math-85c0e583a6b5.svg': '44%', 'psy-math-870327446d5a.svg': '55%',
                       'psy-math-8b084868aad0.svg': '→', 'psy-math-8ea3355aee43.svg': '29%', 'psy-math-911acc3ad146.svg': '70∶30',
                       'psy-math-9153d7a11972.svg': '12.5%', 'psy-math-93f432a7d292.svg': '6%', 'psy-math-943b5cbdc716.svg': '7%',
                       'psy-math-96cb56f579cf.svg': '8∶1', 'psy-math-976333852323.svg': '7:19', 'psy-math-9bde70798669.svg': '100%',
                       'psy-math-a8426aab51ee.svg': '43%', 'psy-math-a881c898486d.svg': '33%', 'psy-math-a9c3e0de9a5b.svg': '29.95',
                       'psy-math-ad283dbc1440.svg': '57%', 'psy-math-ad716a1a87e6.svg': '7:10', 'psy-math-ad722b5464b8.svg': '80%',
                       'psy-math-b03f309488a7.svg': '10.95', 'psy-math-b0c17c0e1187.svg': '70%',
                       'psy-math-b59eab6a1f9f.svg': '20～25', 'psy-math-b8736b999909.svg': '2.5',
                       'psy-math-b8d3c4b69a55.svg': '72.7%', 'psy-math-bdd751395eb4.svg': '8.027',
                       'psy-math-beaac16687f2.svg': '0.0144', 'psy-math-bf1d4c38465b.svg': '30%',
                       'psy-math-bf5fac6e3a72.svg': '0.96', 'psy-math-c1bb1ff3063d.svg': '2×2', 'psy-math-c45cbf80cde9.svg': '1/3',
                       'psy-math-c559959ed440.svg': [('G', 'it'), ('f', 'it msub'), '-', ('G', 'it'), ('c', 'it msub')],
                       'psy-math-c95d9419b96b.svg': '16/17', 'psy-math-cd06d2d11645.svg': '5%', 'psy-math-cd7603e86d09.svg': '7:20',
                       'psy-math-cf51bd76819a.svg': '40%', 'psy-math-d103bbf440f1.svg': '2/3', 'psy-math-d1a841c056a4.svg': '58.2',
                       'psy-math-d1effb5e1f4b.svg': '76%', 'psy-math-d2cbad71ff33.svg': '0.5', 'psy-math-d84ccfc4e559.svg': '63%',
                       'psy-math-da5cbc320029.svg': '6～9', 'psy-math-df15459dcbf2.svg': '8/9',
                       'psy-math-e7019f188ff7.svg': '70×0.70', 'psy-math-ec8e07ba9e2f.svg': '95%',
                       'psy-math-f090366ee5cc.svg': '30×0.3', 'psy-math-f870c5a7e0e9.svg': '96.9%',
                       'psy-math-f88afaea4207.svg': '0.50', 'psy-math-f97844def35e.svg': '6.25%',
                       'psy-math-fbc32f5d6148.svg': '110～125', 'psy-math-fd2f3b661ba6.svg': '1/32',},
             front=[(3, 'text'), (4, 'text'), (5, 'text')],
             body=[[6, 7, 8, 9, 10, 11, 12], [13, 14, 15, 16], [17, 18, 19, 20], [21, 22, 23, 24, 25, 26], [27, 28, 29, 30, 31], [32, 33, 34, 35], [36, 37, 38, 39], [40, 41, 42, 43, 44], [45, 46, 47, 48], [49, 50, 51, 52, 53], [54, 55, 56, 57, 58], [59, 60, 61, 62, 63, 64, 65]],
             back=[66, (list(range(67, 99)), 'figpages')], tail=[], inplace=set(),
             errata_note='底本是一份已经通读校订过的个人校订本（21 条“校订注”排在相关段落之后，注释里的校订也照排）。'
                         '按要求没有再全面校订；这里只有转换时发现的排版问题。'),
    22: dict(scratch='q22', file='心智社会', title='心智社会', sub='从细胞到人工智能，人类思维的优雅解读',
             author='〔美〕马文·明斯基 著', credits=['任楠　译'], publisher='机械工业出版社', pdf_author='〔美〕马文·明斯基',
             cover='00170.jpeg', title_img=None, copyright=0, marker='sq', renum=True, lat_apos=True, toc_even=True,
             note_cls=('fnote',), cls_quote=('ziti1',), cls_right=('you1',), cls_cap=('middle-img',),
             cls_map={'yanse': ('body', 2, 0, 'hei'), 'manual-proofreading-note': ('small', 0, 2)},   # the ebook's coloured lines; the reviser's notes
             text_map=[(r'(校注|图示)', ('small', 0, 2))],         # (four reviser's notes set as quotations in the ebook)
             fig_inline=True, open_air=True,
             # formulas the ebook draws as <svg> in the text, keyed by their LaTeX (<title>): Minsky's agents A, B, K ... upright
             img_text={r'svg:A\,\text{引起}\,B\quad\text{（A causes B）}': [('A', 'it'), '引起', ('B', 'it'), '（A causes B）'],
                       r'svg:B\,\text{引起}\,A\quad\text{（B causes A）}': [('B', 'it'), '引起', ('A', 'it'), '（B causes A）'],
                       r'svg:A\to B,\quad A\to C,\quad A\to D': [('A', 'it'), '→', ('B', 'it'), '、', ('A', 'it'), '→', ('C', 'it'), '、',
                                                                ('A', 'it'), '→', ('D', 'it')],
                       r'svg:4\,\text{在}\,3\,\text{之后}': '4在3之后', r'svg:0\,\text{美元}': '0美元',
                       r'svg:\frac{2}{3},\quad\frac{4}{9},\quad\frac{8}{27}': '2/3、4/9、8/27', r'svg:\texttt{-{}-{}-{}o}': '---o',
                       r'svg:1\,\text{英尺}=0.3048\,\text{米}': '1英尺=0.3048米', r'svg:1\,\text{英寸}=0.0254\,\text{米}': '1英寸=0.0254米',
                       r'svg:\mathrm{M}\text{-}1': 'M-1', r'svg:\mathrm{M}\text{-}2': 'M-2', r'svg:\frac{1}{4}': '1/4',
                       r'svg:\frac{1}{1000}': '1/1000', r'svg:\frac{1}{10^{12}}': ['1/10', ('12', 'msup')],
                       r'svg:\left(3,3,5,7,1,1,-15\right)': '(3, 3, 5, 7, 1, 1, −15)',
                       r'svg:\mathrm{A},\mathrm{B},\mathrm{C}': 'A、B、C',
                       r'svg:(\mathrm{A}),(\mathrm{B}),(\mathrm{C}),(\mathrm{B})': '(A)、(B)、(C)、(B)',
                       r'svg:p': [('p', 'it')], r'svg:q': [('q', 'it')], r'svg:5+8=13': '5+8=13',
                       **{'svg:\\mathrm{%s}' % x: x for x in ('A', 'B', 'C', 'D', 'K', 'L', 'M', 'P', 'Q', 'S', 'U', 'V', 'W', 'X', 'Y', 'Z',
                                                         'IT', 'AND', 'kP')},
                       **{'svg:%s' % x: x for x in ('0', '1', '2', '3', '4', '5', '6', '8', '10', '11', '12', '13', '40', '50', '100')}},
             front=[(2, 'text')], body=[list(range(3, 10)), list(range(10, 17)), list(range(17, 23)), list(range(23, 32)), list(range(32, 40)), list(range(40, 55)), list(range(55, 65)), list(range(65, 77)), list(range(77, 82)), list(range(82, 92)), list(range(92, 102)), list(range(102, 116)), list(range(116, 124)), list(range(124, 134)), list(range(134, 146)), list(range(146, 157)), list(range(157, 169)), list(range(169, 179)), list(range(179, 190)), list(range(190, 200)), list(range(200, 208)), list(range(208, 220)), list(range(220, 226)), list(range(226, 236)), list(range(236, 243)), list(range(243, 256)), list(range(256, 265)), list(range(265, 274)), list(range(274, 283)), list(range(283, 292))],
             back=[list(range(292, 300)), 300, 301], tail=[], inplace=set(),
             errata_note='底本有人校订过（11 条“校注”“图示”说明排在相关插图之后，注释里的校订说明也照排）。'
                         '按要求没有再全面校订；这里只有转换时发现的排版问题。'),
    23: dict(scratch='q23', file='美国大城市的死与生', title='美国大城市的死与生', sub='60周年致敬版',
             author='〔加〕简·雅各布斯 著', credits=['金衡山　译'], publisher='译林出版社', pdf_author='〔加〕简·雅各布斯',
             cover=None, cover_file='source/covers/23-美国大城市的死与生.png', title_img=None, copyright=2, marker='sq', lat_apos=True,
             cls_quote=('yinwen',), cls_center=('yinwen-c',), cls_right=('divtext-right',), cls_cap=('tuzhu-center',),
             part_re=r'^第[一二三四]部分', part_split=r'^(第[一二三四]部分)[\s\u3000]*(.*)$',
             fig_inline=True, fig_dpi=150, open_air=True, toc_sections=False, toc_even=True,
             edit_inplace=r'\[校\d+\]', edit_style=('smallkai', 0, 2),        # the reviser's 7 notes at the ends of their chapters
             note_cls=('noteContent',), note_group_cls=('heiti',), dedication_grid=True, page_anchor=r'#source-page-\d+$', index_map=r'#source-page-(\d+)$',
             pagelinks_note='〔本 PDF 说明〕下列页码都可以点击，跳到原书该页末尾在本书中的位置；书末索引的页码已据这些标记换算成本书页码。',
             # the reviser's LaTeX pictures of fractions, percentages and the multiplication sign (each carries its text as alt;
             # checked against the drawing)
             img_text={'city_math_001.svg': '1/13', 'city_math_002.svg': '1/2', 'city_math_003.svg': '1/3',
                       'city_math_004.svg': '1/4', 'city_math_005.svg': '1/6', 'city_math_006.svg': '1/7',
                       'city_math_007.svg': '1/8', 'city_math_008.svg': '1/9', 'city_math_009.svg': '10%',
                       'city_math_010.svg': '12%', 'city_math_011.svg': '15%', 'city_math_012.svg': '2/3',
                       'city_math_013.svg': '2/9', 'city_math_014.svg': '20%', 'city_math_015.svg': '22%',
                       'city_math_016.svg': '25%', 'city_math_017.svg': '36%', 'city_math_018.svg': '40%',
                       'city_math_019.svg': '43.37%', 'city_math_020.svg': '44.38%', 'city_math_021.svg': '5%',
                       'city_math_022.svg': '50%', 'city_math_023.svg': '58%', 'city_math_024.svg': '59.58%',
                       'city_math_025.svg': '60%', 'city_math_026.svg': '60.60%', 'city_math_027.svg': '66%',
                       'city_math_028.svg': '7%', 'city_math_029.svg': '7.86%', 'city_math_030.svg': '7.9%',
                       'city_math_031.svg': '70%', 'city_math_032.svg': '75%', 'city_math_033.svg': '80%',
                       'city_math_034.svg': '83%', 'city_math_035.svg': '85%', 'city_math_036.svg': '90%',
                       'city_math_037.svg': '92%', 'city_math_038.svg': '95%', 'city_math_039.svg': '97%',
                       'city_math_040.svg': '×', 'city_math_041.svg': '××'},
             front=[(3, 'kaibody'), (4, 'kaibody'), (5, 'kaibody'), (6, 'dedication'), (7, 'text')], body=list(range(8, 30)),
             back=[(30, 'index'), (31, 'kaibody'), (32, 'kaibody'), (33, 'notes'), (34, 'pagelinks'), 35], tail=[], inplace=set(),
             errata_note='底本是一份已经通读修订过的个人校订本（书末“本次校订说明”：1050 条文字修订，7 条“校订注”附核查来源，均照排）。'
                         '按要求没有再全面校订；这里只有转换时发现的排版问题和一处校订说明里的人名错误。'),
    24: dict(scratch='q24', file='理性之谜', title='理性之谜', sub='', author='〔法〕雨果·梅西耶　〔法〕丹·斯珀伯 著', credits=[],
             publisher='中信出版集团', pdf_author='〔法〕雨果·梅西耶　〔法〕丹·斯珀伯', cover='cover.jpg', title_img=None,
             copyright=1, copyright_skip=2, marker='sq', lat_apos=True, toc_even=True, open_air=True, url_break=True,
             note_cls=('zhusi',), cls_quote=('bodycontent-text_yinwen',), cls_right=('bodycontent-text_right',),
             cls_cap=('tuti', 'bodycontent-text-tushuo'), text_map=[(r'^反射比=', ('center', 0, 0))],   # (a formula line under a figure)
             head_sub=[(r'^推荐序\s+', '推荐序／'), (r'^(序言|结论)\s+', '\\1\u3000')], head_split='／', head_split_balance=True,
             head_split_join='\u3000', head_split_width=340,      # ('推荐序' above its long title, as in the ebook)
             part_re=r'^第[一二三四五]部分', part_split=r'^(第[一二三四五]部分)[\s\u3000]*(.*)$',
             part_epi_cls=('bodycontent-text_yinwen',), part_epi_para=True,     # the introduction of each part, on the part page
             fig_inline=True, fig_dpi=180, table2=True, table_keep=12,
             # the reviser's one LaTeX picture: drawn "185.014 m", its text (alt) "185.014米", as the context ("607英尺")
             img_text={'book03-repair-01.svg': '185.014米'},
             front=[(2, 'text')], body=list(range(3, 28)), back=[28], tail=[], inplace=set(),
             errata_note='按要求没有通读校订：这里只有转换时发现的排版问题（中文里的半角括号和分号、西文逗号后漏空格、西文里的全角冒号、多余的空格）。'),
    25: dict(scratch='q25', file='国家的视角', title='国家的视角', sub='那些试图改善人类状况的项目是如何失败的',
             author='〔美〕詹姆斯·C.斯科特 著', credits=['王晓毅　译', '胡　搏　校'], publisher='社会科学文献出版社', series='思想会',
             pdf_author='〔美〕詹姆斯·C.斯科特', cover='00052.jpeg', front_flaps=['00001.jpeg'], title_img='00003.jpeg',
             back_flaps=['00050.jpeg'], backcover='00051.jpeg',
             copyright=[24, 2], copyright_imgs={'00002.jpeg': 26.0}, copyright_top=1,   # the CIP page (last in the ebook) and the original's rights + fund mark
             marker='sq', lat_apos=True, toc_even=True, open_air=2, note_cls=('note',),
             cls_quote=('block',), cls_right=('lk',), cls_center=('center1',), cls_cap=('img',),
             text_map=[(r'^(A\.三权广场|在这张图上可以看到：|这个布局显示出：|图片描述了21世纪|图8-3中右侧|环状图表示)', ('cap', 0, 0))],   # (the legends under six figures)
             part_re=r'^第[一二三四]部分', part_split=r'^(第[一二三四]部分)[\s\u3000]*(.*)$',
             fig_inline=True, fig_dpi=150, table2=True, table_keep=12,
             # the ebook's pictures of a word and a character, and the reviser's one LaTeX picture: maître; 𮝴 (U+2E774, the
             # simplified 軱 the picture shows, 车 + 瓜; composed from the face's own strokes, fonts.compose_gu); the formula
             # drawn as "4264 (°C)²", its text (alt) "4264平方摄氏度"
             img_text={'00011.jpeg': 'maître', '00049.jpeg': '\U0002E774', 'book02-repair-01.svg': '4264平方摄氏度'},
             front=[(4, 'figure'), (5, 'text'), (6, 'text')], body=list(range(8, 20)),
             back=[20, 21, (22, 'index'), 23], tail=[], inplace=set(),
             errata_note='按要求没有通读校订：这里只有转换时发现的排版问题。'),
    26: dict(scratch='q26', file='第三个千年思维', title='第三个千年思维', sub='重新理解世界的思想、工具和方法',
             author='〔美〕索尔·珀尔马特　〔美〕约翰·坎贝尔　〔美〕罗伯特·麦考恩 著', credits=['彭相珍　译'], publisher='中信出版集团',
             pdf_author='〔美〕索尔·珀尔马特、约翰·坎贝尔、罗伯特·麦考恩', cover='cover.jpeg', title_img=None,
             copyright=2, copyright_skip=2, marker='sq', renum=True, note_by_marker=True, lat_apos=True, toc_even=True,
             open_air=3, url_break=True, dedication_grid=True,   # (open_air: chapter 13 has three rigid paragraphs under its title)
             # the section titles are bold paragraphs; '第3章' + its title, '1' + the part's title, '推荐序一' + its title: one heading
             bold_head=(3, 40), head_join=[(r'推荐序[一二三]', '／'), (r'第\d+章', '\u3000'), (r'\d', '\u3000')],
             head_relevel={'证真偏差': 3, '事实与价值观': 3},       # (two section titles tagged like chapter titles)
             head_split='／', head_split_balance=True, head_split_join='\u3000', head_split_width=340,
             part_re=r'^\d\s', part_split=r'^(\d)\s+(.*)$',
             short_right={4: 40, 5: 40, 6: 40, 7: 40}, cls_right=('short_right',),
             text_map=[(r'^[图表]\d+-\d+\s', ('cap', 0, 0))], cap_mode='tabfig', cap_top_re=r'^表',
             fig_inline=True, table2=True, table_keep=12, table_head_keep=True,
             # the reviser's four formula pictures: their LaTeX / alt text
             img_text={'book01-repair-01.svg': '229733±9', 'book01-repair-02.svg': '1英尺=0.3048米',
                       'book01-repair-03.svg': '1英寸=0.0254米', 'book01-repair-04.svg': 'f′′(a)(x-a)²/2'},
             front=[(3, 'dedication'), (4, 'text'), (5, 'text'), (6, 'text'), (7, 'text')], body=list(range(8, 32)),
             back=[32], tail=[], inplace=set(),
             errata_note='按要求没有通读校订：这里只有转换时发现的排版问题。'),
    27: dict(scratch='q27', file='置身事内', title='置身事内', sub='中国政府与经济发展', author='兰小欢 著', credits=[],
             publisher='上海人民出版社', pdf_author='兰小欢', cover='00030.jpeg', title_img='00001.jpeg',
             copyright=2, copyright_imgs={'00002.jpeg': 26.0}, tail=['00003.jpeg'], tail_w=320.0,   # (the publisher's page of QR codes: the last page)
             marker='paren', note_cls=('fnContent-1',), lat_apos=True, toc_even=True, open_air=True, dedication_grid=True,
             cls_cap=('tuti', 'tuzhu-8'), cls_right=('signContent-1-kaiti',), cls_quote=('bodyContent-2-kaiti', 'bodyContent-2-kaiti-top'),
             cls_kai=('bodyContent-1-kaiti', 'bodyContent-1-kaiti-top-1', 'bodyContent-1-kaiti-top-6'),
             cls_map={'hang-bodyContent-1': ('noindent', -2, 2)},          # (the references: hanging indent)
             part_re=r'^[上下]篇', part_split=r'^([上下]篇)\s+(.*)$', part_epi_cls=('bodyContent-1-kaiti',), part_epi_para=True,
             fig_inline=True, fig_dpi=300, table2=True, table_keep=12, table_head_keep=True,
             front=[(4, 'dedication'), (5, 'text'), (6, 'text')], body=list(range(7, 17)), back=[17, 18], inplace=set(),
             errata_note='按要求没有通读校订：这里只有转换时发现的排版问题。'),
    28: dict(scratch='q28', file='风险认知', title='风险认知', sub='如何精准决策', author='〔德〕格尔德·吉仁泽 著', credits=['王晋　译'],
             publisher='中信出版集团', pdf_author='〔德〕格尔德·吉仁泽', cover='00050.jpeg', title_img=None, copyright=88,
             marker='sq', renum=True, lat_apos=True, toc_even=True, open_air=True, dedication_grid=True,
             cls_quote=('kaiti',), cls_cap=('tushuo', 'tushuo1'), part_epi_cls=('kaiti',),
             part_re=r'^第[一二三]部分', part_split=r'^(第[一二三]部分)\s+(.*)$', part_grid=True,
             fig_inline=True, fig_dpi=150, table2=True, table_keep=12, table_head_keep=True,
             img_text={'svg:20³': '20³'},                       # (the reviser's formula picture in the text: 8000（20³）种组合)
             # one chapter = its title part and its section parts (the ebook has a file for every section)
             front=[(3, 'dedication')],
             body=[4, list(range(5, 11)), list(range(11, 20)), list(range(20, 28)), list(range(28, 32)), 32, list(range(33, 41)),
                   list(range(41, 48)), list(range(48, 52)), list(range(52, 60)), list(range(60, 69)), list(range(69, 79)),
                   list(range(79, 82)), 82, list(range(83, 88))],
             back=[], tail=[], inplace=set(),
             errata_note='按要求没有通读校订：这里只有转换时发现的排版问题。'),
    29: dict(scratch='q29', file='超越智商', title='超越智商', sub='为什么聪明人也会做蠢事', author='〔加〕基思·斯坦诺维奇 著',
             credits=['张斌　译'], publisher='机械工业出版社', pdf_author='〔加〕基思·斯坦诺维奇', cover='00078.jpeg', title_img=None,
             copyright=1, marker='sq', renum=True, lat_apos=True, toc_even=True, open_air=True, url_break=True,
             cls_right=('you1',), epi_quote=True, cls_cap=('middle-img',), cap_mode='tabfig', cap_top_re=r'^表',
             part_epi_cls=('ziti1',), part_epi_para=True, part_re=r'^第[一二三四]部分', part_split=r'^(第[一二三四]部分)\s+(.*)$',
             fig_inline=True, fig_dpi=120, table2=True, table_keep=12, table_head_keep=True,
             img_text={'00003.jpeg': '⑪', '00004.jpeg': '⑫', '00005.jpeg': '⑬'},   # (the guide's list: ⑩ is a character, ⑪–⑬ pictures)
             front=[(3, 'text'), (4, 'text'), (5, 'text'), (6, 'text')],
             body=[7, [8, 9, 10], list(range(11, 16)), list(range(16, 24)), list(range(24, 31)), list(range(31, 36)), 36,
                   list(range(37, 44)), list(range(44, 48)), list(range(48, 52)), list(range(52, 56)), 56, list(range(57, 66)),
                   list(range(66, 73)), list(range(73, 80)), 80, list(range(81, 85))],
             back=[(85, 'figpages')], tail=[], inplace=set(),
             errata_note='按要求没有通读校订：这里只有转换时发现的排版问题。'),
    30: dict(scratch='q30', file='病毒星球', title='病毒星球', sub='', author='〔美〕卡尔·齐默 著', credits=['刘旸　译'],
             publisher='广西师范大学出版社', pdf_author='〔美〕卡尔·齐默', cover='00017.jpeg', title_img=None,
             front_flaps=['00001.jpeg', '00002.jpeg'], backcover='00016.jpeg', tail=['00015.jpeg'], tail_w=300.0,   # (the imprint's two pages; its QR page last)
             copyright=2, marker='sq', renum=True, note_cls=('noteContent',), notes_end=True,   # (10 notes in all: one module after the text)
             lat_apos=True, toc_even=True, open_air=True, dedication_grid=True, url_break=True, cls_refhead=('zh',),
             cls_map={'center': ('center', 0, 0, 'kai'), 'yinwen0': ('noindent', -2, 2), 'yinwen': ('noindent', 0, 0, 'kai')},
             part_re=r'^(老朋友|无处不在|与病毒共赴未来)$', cls_cap=('tuzhu-center',), fig_inline=True, fig_dpi=110,
             # the reviser's LaTeX pictures (names with accents, percentages, fractions, ranges, the CIP's numbering), each drawn as
             # its alt text says (checked against the drawings); ranges with '～' throughout, the 32-digit number without the stray gap
             img_text={'b24_abrahao.svg': 'Abrahão', 'b24_alonso.svg': 'Á.', 'b24_andre.svg': 'André',
                       'b24_bookformat.svg': '850mm×1168mm　1/32', 'b24_brussow.svg': 'Brüssow', 'b24_bullet.svg': '•',
                       'b24_circle1.svg': '①', 'b24_circle2.svg': '②', 'b24_copyright.svg': '©', 'b24_delbruck.svg': 'Delbrück',
                       'b24_felix.svg': 'Félix', 'b24_frac13.svg': '1/3', 'b24_frac14.svg': '1/4', 'b24_frac23.svg': '2/3',
                       'b24_garciaruiz.svg': 'García-Ruiz', 'b24_garciavallve.svg': 'García-Vallvé', 'b24_genecount.svg': '1×10²⁴',
                       'b24_lopezgarcia.svg': 'López-García', 'b24_marinecount.svg': '1×10³¹',
                       'b24_marineinteger.svg': '1' + '0' * 31, 'b24_menage.svg': 'Ménage à trois', 'b24_onehundredth.svg': '1/100',
                       'b24_percent10.svg': '10%', 'b24_percent1_2.svg': '1.2%', 'b24_percent2.svg': '2%', 'b24_percent25.svg': '25%',
                       'b24_percent26_3.svg': '26.3%', 'b24_percent30.svg': '30%', 'b24_percent35.svg': '35%', 'b24_percent40.svg': '40%',
                       'b24_percent43.svg': '43%', 'b24_percent5.svg': '5%', 'b24_percent57.svg': '57%', 'b24_percent69.svg': '69%',
                       'b24_percent70.svg': '70%', 'b24_percent8.svg': '8%', 'b24_percent90.svg': '90%', 'b24_percent95.svg': '95%',
                       'b24_percent99_975.svg': '99.975%', 'b24_percent99_997.svg': '99.997%', 'b24_permil1_8.svg': '1.8‰',
                       'b24_permil6_7.svg': '6.7‰', 'b24_philomene.svg': 'Philomène', 'b24_range10_20.svg': '10%～20%',
                       'b24_range15_40.svg': '15%～40%', 'b24_range20_30.svg': '20%～30%', 'b24_range5_10.svg': '5%～10%',
                       'b24_roman1.svg': 'Ⅰ', 'b24_roman2.svg': 'Ⅱ', 'b24_roman3.svg': 'Ⅲ', 'b24_roman4.svg': 'Ⅳ',
                       'b24_tilderange.svg': '～'},
             front=[(4, 'figure'), (5, 'text'), (6, 'dedication'), (7, 'text')], body=list(range(8, 20)),   # (彩插: a plate a page)
             back=[20, (21, 'hang')], inplace=set(),
             errata_note='按要求没有通读校订：这里只有转换时发现的排版问题。'),
    31: dict(scratch='q31', file='知识的错觉', title='知识的错觉', sub='', author='〔美〕史蒂文·斯洛曼　〔美〕菲利普·费恩巴赫 著',
             credits=['祝常悦　译'], publisher='中信出版社', pdf_author='〔美〕史蒂文·斯洛曼、菲利普·费恩巴赫', cover='00008.jpeg',
             title_img=None, copyright=20, marker='sq', renum=True, lat_apos=True, toc_even=True, open_air=True, url_break=True,
             # two series: the editor's footnotes ([n] in the ebook, the notes in <div.fnote> at the end of each chapter) as ①②③
             # in a 编者注 section at the end, one group per chapter; the authors' notes (bare numbers, the chapter's own
             # numbering) in the ebook's 注释 after it, one group per chapter (its <h3> headings)
             circ_link=r'#note\d+n?$', notes_title='编者注', notes_toc='编者注', note_group_h=True,
             head_sub=[(r'^(第[一二三四五六七八九十]+章|前言|结语|推荐序)[\s\u3000]+', '\\1\u3000')],
             cls_right=('right',), fig_inline=True, fig_dpi=150,
             front=[(3, 'text')], body=list(range(4, 18)), back=[18, (19, 'notes')], tail=[], inplace=set(),
             errata_note='按要求没有通读校订：这里只有转换时发现的排版问题。'),
    # the book once planned as 15 (CFG[15], an earlier ebook, dropped with 11–15); now from the revised ebook (the reviser's
    # 263 LaTeX pictures of quantities, chemical formulas and equations, tools/bk_img32.py)
    32: dict(scratch='q32', file='气候赌场', title='气候赌场', sub='全球变暖的风险、不确定性与经济学', author='〔美〕威廉·诺德豪斯 著',
             credits=['梁小民　译'], publisher='东方出版中心', pdf_author='〔美〕威廉·诺德豪斯', series='威廉·诺德豪斯著作系列',
             cover='cover00313.jpeg', title_img='image00246.jpeg', copyright=2, marker='paren', renum=True, lat_apos=True,
             toc_even=True, open_air=True, dedication_grid=True, url_break=True, head_clean=True,
             head_sub=[(r'^(第\d+章)[|｜]?[\s\u3000]*', '\\1\u3000')],
             note_cls=('fnContent-1', 'fnContent-2', 'noindent-fnContent-2-c'), notel_vary=True,
             cls_cap=('tuti', 'tuzhu', 'biaoti', 'biaozhu'), cap_mode='tabfig', cap_top_re=r'^表', label_re=r'^([图表][^\s　]+)',
             cls_right=('signContent-1-kaiti', 'signContent-1-kaiti-top'), cls_quote=('bodyContent-2-kaiti', 'bodyContent-2-kaiti-top'),
             cls_center=('bodyContent-1-c-3',), cls_map={'noindent-bodyContent-1': ('noindent', 0, 0),
                                                       'noindent-bodyContent-1-top': ('noindent', 0, 0)},
             part_re=r'^PART', part_split=r'^(PART \d+) ([^A-Za-z]+?) ([A-Z].*)$',
             part_epi_cls=('bodyContent-1-kaiti', 'signContent-1-kaiti', 'bodyContent-1'), part_grid=True,
             fig_inline=True, fig_dpi=300, table_keep=12,
             img_text=__import__('tools.bk_img32', fromlist=['IMG_TEXT']).IMG_TEXT,
             front=[(3, 'text'), (4, 'text'), (5, 'dedication'), (6, 'text'), (7, 'text'), (8, 'text')],
             body=[[10, 11]] + list(range(12, 17)) + [[17, 18]] + list(range(19, 26)) + [[26, 27]] + list(range(28, 32)) + [[32, 33]]
                  + list(range(34, 41)) + [[41, 42]] + list(range(43, 46)),
             back=[], tail=[], inplace=set(),
             errata_note='按要求没有通读校订：这里只有转换时发现的排版问题。'),
    # two series of notes: the author's and the translator's footnotes ([n] linked, at the end of each chapter in the ebook)
    # as ①②③ after the chapters; the sources (the chapters' plain superscript [n], linked here to the entries of 注释及出处,
    # one group per chapter: bk_fixes XNOTELINK) in the ebook's place at the end.  The two plate sections the ebook binds
    # inside chapters 7 and 18 (插图列表 calls them 第一部分 and 第二部分) follow those chapters, a picture a page.
    33: dict(scratch='q33', file='人体简史', title='人体简史', sub='你的身体30亿岁了', author='〔英〕比尔·布莱森 著',
             credits=['闾　佳　译'], publisher='文汇出版社', pdf_author='〔英〕比尔·布莱森', cover='00070.jpeg',
             title_img='00001.jpeg', copyright_img='00069.jpeg', tail=['00068.jpeg'], tail_w=300.0,
             marker='sq', renum=True, note_cls=('noteContent',), circ_link=r'#note(Back)?_\d+$', note_group_re=r'^第[一二三四五六七八九十]+章',
             lat_apos=True, toc_even=True, open_air=True, dedication_grid=True, url_break=True, table2=True, table_keep=12,
             head_sub=[(r'^(第[一二三四五六七八九十]+章)[\s\u3000]+', '\\1\u3000')],
             cls_quote=('conQuot',), cls_cap=('imgDescript',), cls_sep=('center',), fig_inline=True, fig_dpi=300,
             insert_plates={9: '插图　第一部分', 20: '插图　第二部分'},
             img_text=__import__('tools.bk_img33', fromlist=['IMG_TEXT']).IMG_TEXT,
             front=[(1, 'dedication')], body=list(range(3, 26)), back=[(26, 'notes'), (27, 'hang')], inplace=set(),
             errata_note='按要求没有通读校订：这里只有转换时发现的排版问题。'),
    # the notes of the print edition (编者注、译者注, icons as marks in the ebook) and the reviser's three 校订注, both at the
    # end of the ebook (notes.xhtml): one 注释 section at the end, a group each; the reviser's marks '〔校订注1〕' raised as
    # the ebook sets them.  The 系统之思 / THINKING IN SYSTEMS labels close the key-point paragraphs (Hei) they follow.
    34: dict(scratch='q34', file='系统之美', title='系统之美', sub='决策者的系统思考（全新升级版）', author='〔美〕德内拉·梅多斯 著',
             credits=['邱昭良　译'], publisher='浙江教育出版社', pdf_author='〔美〕德内拉·梅多斯', cover='img001.jpg', title_img=None,
             copyright=1, marker='sq', note_group_h='all', endnotes_title='注　释',
             lat_apos=True, toc_even=True, open_air=3, epi_name_air=True, url_break=True, table2=True, table_keep=12,
             part_re=r'^第[一二三]部分', part_split=r'^(第[一二三]部分)[\s\u3000]+(.+)$',
             head_cls={'content-b': (5, r'^(?!系统之思$|THINKING IN SYSTEMS$)')},
             cls_kai=('quotation',), cls_right=('content-right',), cls_cap=('imgtitle', 'imgdescript'),
             cls_map={'quotation-right': ('right', 0, 0, 'kai'), 'content-noindent': ('noindent', 0, 0, 'hei'),
                      'formula-block': ('left', -2, 2)},
             text_map=[(r'^(系统之思|THINKING IN SYSTEMS)$', ('right', 0, 0, 'hei'))],
             fig_inline=True, fig_dpi=300, fig_scale={'img002.jpg': 0.6, 'img034.jpg': 0.92}, fig_air={'img003.jpg': 3},   # (the author's card under its heading)
             img_text=__import__('tools.bk_img34', fromlist=['IMG_TEXT']).IMG_TEXT,
             front=[(n, 'text') for n in range(2, 8)], body=list(range(8, 16)), back=[16, 17, (18, 'notes')], tail=[], inplace=set(),
             errata_note='按要求没有通读校订：这里只有转换时发现的排版问题。'),
    35: dict(scratch='q35', file='卓有成效的管理者', title='卓有成效的管理者', sub='珍藏版', author='〔美〕彼得·德鲁克 著',
             credits=['许是祥　译', '那国毅　审订'], publisher='机械工业出版社', pdf_author='〔美〕彼得·德鲁克', series='德鲁克管理经典',
             cover='00041.jpeg', title_img=None, copyright=3, marker='sq', renum=True, notes_end=True, note_li=True,
             lat_apos=True, toc_even=True, open_air=True, url_break=True,
             # the series banner at the head of every section is the ebook's decoration, not the book's
             img_drop={'00004.jpeg'}, head_cls={'p2': 3, 'p3': 3}, cls_quote=('ziti1',), cls_right=('you',), cls_center=('middle-img',),
             cls_map={'yanse': ('noindent', 0, 0, 'hei'), 'nrjj1': ('center', 0, 0, 'hei')}, fig_inline=True, fig_dpi=150,
             fig_right={'00006.jpeg'},
             # the catalogue at the end ('精品推荐' in the ebook's contents): the series banners as pictures, each cover small
             orn={f'{n:05d}.jpeg' for n in list(range(9, 25)) + list(range(26, 33)) + list(range(34, 41))}, orn_size=(60.0, 80.0),
             orn_air=True, insert_head={43: '精品推荐'}, text_map=[(r'^978-', ('center', 0, 0))],
             img_text={'latex_b09_commutative_example.svg': '4×6=6×4', 'latex_b09_one_fifth.svg': '1/5',
                       'latex_b09_one_fourth.svg': '1/4', 'latex_b09_one_tenth.svg': '1/10', 'latex_b09_one_third.svg': '1/3',
                       'latex_b09_three_fourths.svg': '3/4'},
             # the ebook's own pages before the title (a promotion page, Drucker's letter to Chinese readers, the centenary page)
             front_flaps=['00001.jpeg', '00002.jpeg', '00003.jpeg'], front=[(n, 'text') for n in range(5, 15)],
             body=[list(range(15, 20)), list(range(20, 25)), list(range(25, 30)), list(range(30, 33)), list(range(33, 36)),
                   list(range(36, 39)), list(range(39, 42)), 42],
             back=[list(range(43, 74))], tail=[], inplace=set(),
             errata_note='按要求没有通读校订：这里只有转换时发现的排版问题。'),
    # 认知三部曲（全三册）: one ebook, three books (36–38), each its own PDF (its cover from the ebook, the set's ebook colophon
    # as the copyright page) and a collection of the three (tools/bk_collection.py).  The scratch directories q36–q38 hold
    # the same unpacked ebook.
    36: dict(scratch='q36', file='思维版图', title='思维版图', sub='', author='〔美〕理查德·尼斯贝特 著', credits=['李秀霞　译'],
             publisher='中信出版社', pdf_author='〔美〕理查德·尼斯贝特', series='认知三部曲', cover='image00418.jpeg', title_img=None,
             copyright=90, marker='sq', note_cls=('calibre14',), notes_end='all', lat_apos=True, toc_even=True, open_air=True, url_break=True, name_dot=True,
             head_sub=[(r'^(第\d+章)[\s\u3000]+', '\\1\u3000')], head_cls={'jz': 3},       # (a chapter: its opening part and a part per section)
             cls_kai=('kaiti2',), cls_map={'kaiti3': ('right', 0, 0, 'kai')}, cls_cap=('tushuo', 'tushuo1', 'tushuo2'),
             label_re=r'^(图\d+[–-]\d+)', fig_inline=True, fig_dpi=150,
             front=[(4, 'text')], body=[list(range(5, 10)), list(range(10, 14)), list(range(14, 19)), list(range(19, 24)),
                                       list(range(24, 29)), list(range(29, 34)), list(range(34, 38)), list(range(38, 42)),
                                       list(range(42, 46))], back=[46], tail=[], inplace=set(),
             errata_note='按要求没有通读校订：这里只有转换时发现的排版问题。'),
    # the chapter's opening picture (the ebook's decoration, ten times the same) is not set; the epigraph under each title
    # (div.block: Kai quotation, bold Hei name) as the ebook has it
    37: dict(scratch='q37', file='认知升级', title='认知升级', sub='', author='〔美〕理查德·尼斯贝特 著', credits=['仲田甜　译'],
             publisher='中信出版社', pdf_author='〔美〕理查德·尼斯贝特', series='认知三部曲', cover='image00410.jpeg', title_img=None,
             copyright=90, marker='sq', note_cls=('calibre14',), notes_end='all', lat_apos=True, toc_even=True, open_air=True, url_break=True, name_dot=True,
             img_drop={'image00426.jpeg'},
             head_sub=[(r'^(第\d+章|结语|附录[一二])[\s\u3000]+', '\\1\u3000')], head_as_p={'calibre22': 'cap', 'calibre23': 'cap'},
             cls_quote=('calibre16',), cls_kai=('calibre19',), cls_right=('right', 'right1'), cls_cap=('tushuo', 'tushuo1', 'tushuo2'),
             cap_top_re=r'^表', cap_after_re=r'^资料来源', label_re=r'^([图表]\d+[–-]\d+)', fig_inline=True, fig_dpi=150,
             front=[], body=list(range(49, 60)), back=[60, 61, 62], tail=[], inplace=set(),
             errata_note='按要求没有通读校订：这里只有转换时发现的排版问题。'),
    38: dict(scratch='q38', file='逻辑思维', title='逻辑思维', sub='拥有智慧思考的工具', author='〔美〕理查德·尼斯贝特 著',
             credits=['张　媚　译'], publisher='中信出版社', pdf_author='〔美〕理查德·尼斯贝特', series='认知三部曲',
             cover='image00385.jpeg', title_img=None, copyright=90, marker='sq', note_cls=('calibre14',), notes_end='all', lat_apos=True, toc_even=True,
             open_air=True, url_break=True, name_dot=True, head_sub=[(r'^(第\d+章|总结)[\s\u3000]+', '\\1\u3000')],
             part_re=r'^第[一二三四五六]部分', part_split=r'^(第[一二三四五六]部分)[\s\u3000]+(.+)$', part_intro=True,
             cls_kai=('kaiti2',), cls_map={'kaiti3': ('right', 0, 0, 'kai')}, cls_cap=('tushuo', 'tushuo1', 'tushuo2'),
             fig_inline=True, fig_dpi=150,
             front=[(65, 'text')], body=list(range(66, 88)), back=[88, 89], tail=[], inplace=set(),
             errata_note='按要求没有通读校订：这里只有转换时发现的排版问题。'),
    # the formulas set as pictures (tools/bk_img39.py): the relativity chapter's fractions and roots in the lines, nine display
    # formulas as centred lines; the examples, numbered theses and syllogisms in Kai (ziti4); the terms the ebook colours in Hei
    39: dict(scratch='q39', file='世界观', title='世界观', sub='现代人必须要懂的科学哲学和科学史（原书第3版）',
             author='〔美〕理查德·德威特 著', credits=['孙天　译'], publisher='机械工业出版社', pdf_author='〔美〕理查德·德威特',
             cover='cover00295.jpeg', title_img=None, copyright=0, marker='sq', notes_end='all', lat_apos=True, toc_even=True,
             open_air=2, open_air_cost=(30.0, 45.0),                   # (6 notes, one in 前言: one module at the end)
             url_break=True, name_dot=True, head_sub=[(r'^(第\d+章)[\s\u3000]+', '\\1\u3000')], head_cls={'p4': 4},
             part_re=r'^第[一二三]部分', part_split=r'^(第[一二三]部分)[\s\u3000]+(.+)$', part_epi_cls=('ziti4',), part_epi_para=True,
             cls_kai=('ziti4',), cls_map={'you': ('right', 0, 0, 'kai')}, cls_cap=('middle-img',), label_re=r'^(图\d+-\d+)',
             fig_inline=True, fig_dpi=150,
             img_text=__import__('tools.bk_img39', fromlist=['IMG_TEXT']).IMG_TEXT,
             img_para=__import__('tools.bk_img39', fromlist=['IMG_PARA']).IMG_PARA,
             front=[(2, 'text'), (3, 'text')], body=list(range(4, 38)), back=[38], tail=[], inplace=set(),
             errata_note='按要求没有通读校订：这里只有转换时发现的排版问题。'),
    # the headings carry the original title in grey (‘Fooled by Randomness’, the ebook's decoration) and a forced break
    # between the label and the title; the 篇 pages open with an epigraph and a few paragraphs (modules of their own).
    # heiti1: the titles under the sections, but for the few sentences (ending in 。) the ebook sets in Hei
    40: dict(scratch='q40', file='随机漫步的傻瓜', title='随机漫步的傻瓜', sub='发现市场和人生中的隐藏机遇',
             author='〔美〕纳西姆·尼古拉斯·塔勒布 著', credits=['盛逢时　译'], publisher='中信出版社',
             pdf_author='〔美〕纳西姆·尼古拉斯·塔勒布', cover='cover00117.jpeg', title_img=None, copyright=[1, 2],
             marker='sq', renum=True, lat_apos=True, toc_even=True, open_air=True, url_break=True, name_dot=True,
             head_sub=[(r'[\s\u3000]*Fooled by Randomness$', ''), (r'太多[\s\u3000]+“', '太多“'),     # (第八章: a break in the title)
                       (r'^(第[一二三四五六七八九十]+[篇章]|各方赞誉|专家推荐|自序|前言|后记)[\s\u3000]+', '\\1\u3000')],
             part_re=r'^第[一二三]篇', part_split=r'^(第[一二三]篇)[\s\u3000]+(.+)$', part_sub_cls=('center',),
             part_epi_cls=('calibre9',), part_epi_para=True, part_intro=True,   # (the part page: title, sub-title, epigraph; its introduction follows)
             head_cls={'heiti1': (4, r'^(?!.*。$)')}, head_as_p={'sigil_not_in_toc': 'cap'},
             cls_center=('center',), notes_end='all',                      # (4 notes in all, one in 前言: one module after the text)
             cls_map={'heiti1': ('body', 2, 0, 'hei'), 'btx': ('body', 2, 0, 'hei'), 'right': ('right', 0, 0, 'kai'),
                      'right2': ('right', 0, 0, 'kai'), 'right1': ('right', 0, 0, 'hei')},   # (the names in the signatures: Hei)
             cap_mode='tabfig', cap_top_re=r'^表', label_re=r'^([图表][\d–-]+)', fig_inline=True, fig_dpi=150,
             front=[(n, 'text') for n in range(4, 8)], body=list(range(8, 25)), back=[25], tail=[], inplace=set(),
             errata_note='按要求没有通读校订：这里只有转换时发现的排版问题。'),
    # a repaired ebook: three series of notes, each with the label the ebook prints ([n] the translator's and editor's,
    # [原注n] the author's footnotes and [资料n] his source notes, both added by the repairer); the first two after each
    # chapter (the label '原作者注释' over the author's dropped), the source notes at the end in their place, by chapter.
    # The formulas inside the lines are pictures (tools/bk_img59.py); display formulas and tables are pictures too and stay.
    59: dict(scratch='q59', file='魔鬼数学', title='魔鬼数学', sub='大数据时代，数学思维的力量', author='〔美〕乔丹·艾伦伯格 著',
             credits=['胡小锐　译'], publisher='中信出版社', pdf_author='〔美〕乔丹·艾伦伯格', cover='cover00387.jpeg', title_img=None,
             copyright=30, marker='sq', mark_label='原注|资料', note_cls=('calibre18',), note_by_marker=True, note_group_h=True,
             head_drop=('原作者注释',), uni_sup=True, sup_join=True, sup_plain=r'[…“]+', lat_apos=True, toc_even=True, open_air=True,
             url_break=True, url_break_back=True, name_dot=True,
             head_sub=[(r'^(第\d+章|第[一二三四五]部分|引言|结语)[\s\u3000]+', '\\1\u3000')],
             part_re=r'^第[一二三四五]部分', part_split=r'^(第[一二三四五]部分)[\s\u3000]+(.+)$', part_list=r'^精彩内容',
             cls_quote=('calibre13', 'calibre22'), cls_right=('kaiti2',), cls_cap=('tushuo',),
             head_as_p={'calibre27': 'cap', 'calibre28': 'cap'}, cls_map={'sequence-row': ('center', 0, 0, '')},
             text_map=[(r'^……$', ('center', 0, 0, ''))],                # (the lottery tickets listed as a picture: '……' under it)
             img_mark={'image00322.jpeg': ('[3]', 'part0004#note3n')},   # (the table of the bullet holes: the mark of the editor's note [3])
             fig_scale={'image00431.jpeg': 0.75,                     # (chapter 1: two charts in a row; the first one fits on the first page)
                        'image00422.jpeg': 0.5},                     # (Wald's report: its Chinese about the size of the text)
             plate_figs={'image00375.jpeg'},                         # (chapter 3: 24 lines before it, '上图表明' after it: a blank foot otherwise)
             fig_inline=True, fig_dpi=220, formula_img=r'image00(325|351|379|381|422|426|429|440|443)\.jpeg$',
             img_text=__import__('tools.bk_img59', fromlist=['IMG_TEXT']).IMG_TEXT,
             front=[(1, 'dedication'), (2, 'kaitext')], body=list(range(4, 28)), back=[28, 29, (31, 'notes')], tail=[], inplace=set(),
             errata_note='按要求没有通读校订：这里只有转换时发现的排版问题。另有两处不在下面的规则里，是配置项：电子书误标成上标的“（24 处）'
                         '和“……”（5 处）恢复为正常文字（`sup_plain`）；编者注 [3] 的角标在电子书里是整张表格图片的链接，补在表格前一段的末尾'
                         '（`img_mark`）。'),
}
# 西方现代思想家精品译丛（18卷）·续校本: one ebook, eighteen books (41–58), each its own PDF and a collection of all
# (tools/bk_collection.py).  The scratch directories q41–q58 hold the same unpacked ebook; one font directory serves all
# (BOOK_FONT_KEYS).  Each book has its cover, its title page (a picture), its CIP page and the original's rights page.
_IMG41 = __import__('tools.bk_img41', fromlist=['IMG_TEXT']).IMG_TEXT
_XF = dict(publisher='中国社会科学出版社', title_img=None, marker='sq', lat_apos=True, toc_even=True, open_air=True, url_break=True,
           name_dot=True, tail_join=True, fig_inline=True, fig_dpi=220, note_cls=('note', 'note1', 'footnote_content'), img_text=_IMG41, img_twin=__import__('tools.bk_img41', fromlist=['IMG_TWIN']).IMG_TWIN,
           tail=[], inplace=set(),
           errata_note='按要求没有通读校订：这里只有转换时发现的排版问题。')


def _xf(**kw):
    return dict(_XF, **kw)


CFG[41] = _xf(scratch='q41', file='自由与繁荣的国度', title='自由与繁荣的国度', sub='', author='〔奥〕路德维希·冯·米瑟斯 著',
              credits=['韩光明　潘琪昌　李百吉　等译'], pdf_author='〔奥〕路德维希·冯·米瑟斯', series='西方现代思想丛书',
              cover='image06054.jpeg', title_img='image06070.jpeg', copyright=[4, 5], cls_center=('center1',),
              front=[(6, 'board'), (7, 'text'), (9, 'text'), (10, 'text')], body=list(range(11, 16)), back=[16])
CFG[42] = _xf(scratch='q42', file='通往奴役之路', title='通往奴役之路', sub='修订版', author='〔英〕弗里德里希·奥古斯特·哈耶克 著',
              credits=['王明毅　冯兴元　等译', '冯兴元　毛寿龙　王明毅　等校'], pdf_author='〔英〕F. A. 哈耶克', series='西方现代思想丛书',
              cover='image06104.jpeg', title_img='image06121.jpeg', copyright=[19, 21],
              cls_quote=('content_reference',), cls_right=('content_reference_right', 'content_right'), cls_center=('content_center',),
              cls_noindent=('content_left',),
              front=[(20, 'text'), (22, 'board'), (23, 'text'), (25, 'text'), (26, 'text'), (27, 'text'), (28, 'text')],
              body=list(range(29, 45)), back=[45, 46])
# (the part pages: the title, the part's epigraph and its author, the epigraph's note mark linked; tables inside notes)
CFG[43] = _xf(scratch='q43', file='自由宪章', title='自由宪章', sub='', author='〔英〕弗里德里希·奥古斯特·冯·哈耶克 著',
              credits=['杨玉生　冯兴元　陈茅　等译', '杨玉生　陆衡　伊虹　统校'], pdf_author='〔英〕F. A. 冯·哈耶克', series='西方现代思想丛书',
              cover='image06155.jpeg', title_img='image06172.jpeg', copyright=[49, 50], cls_quote=('content_reference',),
              cls_center=('center1',), cls_noindent=('left',), notes_tail=True,
              notel_vary=True,                        # (references in Latin, set ragged: their lines may be spaced too)
              note_plates={'image06030.jpeg'},        # (chapter 21, note 8: its table at the back, else a page foot stays empty)
              part_re=r'^第[一二三]篇', part_split=r'^(第[一二三]篇)[\s\u3000]+(.+)$', part_epi_cls=('content_reference', 'right'),
              part_epi_right=('right',), part_epi_para=True,
              front=[(51, 'board'), (52, 'dedication'), (53, 'text'), (55, 'text'), (56, 'text'), (57, 'text'), (58, 'text')],
              body=list(range(59, 83)), back=[83, 84])
CFG[44] = _xf(scratch='q44', file='历史主义贫困论', title='历史主义贫困论', sub='', author='〔英〕卡尔·波普尔 著', credits=['何林　赵平　译'],
              pdf_author='〔英〕卡尔·波普尔', series='西方现代思想丛书', cover='image06045.jpeg', title_img='image06061.jpeg',
              copyright=87, cls_center=('content_center',), cls_right=('content_right',), cls_noindent=('content_left',),
              front=[(89, 'text')], body=list(range(90, 94)), back=[94, 95])
# 开放社会及其敌人: the parts have titles of their own, no numbers ('柏拉图的描述社会学'); a figure and its caption inside a note
_OS1 = r'^(起源和命运的神话|柏拉图的描述社会学|柏拉图的政治纲领|柏拉图攻击的背景)$'
_OS2 = r'^(神谕哲学的兴起|马克思的方法|马克思的预言|马克思的伦理学|余波|结论)$'
CFG[45] = _xf(scratch='q45', file='开放社会及其敌人（第一卷）', title='开放社会及其敌人', sub='第一卷　柏拉图的符咒',
              author='〔英〕卡尔·波普尔 著', credits=['陆衡　张群群　杨光明　李少平　等译'], pdf_author='〔英〕卡尔·波普尔',
              series='西方现代思想丛书', cover='image06094.jpeg', title_img='image06111.jpeg', copyright=98,
              cls_quote=('content_reference',), cls_center=('center1',), cls_noindent=('left',), cls_cap=('img',), notes_tail=True,
              part_re=_OS1, front=[(99, 'board'), (100, 'text'), (101, 'kaitext'), (102, 'text'), (103, 'text'), (104, 'text'),
                                   (105, 'text'), (107, 'text')], body=list(range(108, 118)), back=[118])
CFG[46] = _xf(scratch='q46', file='开放社会及其敌人（第二卷）', title='开放社会及其敌人', sub='第二卷　预言的高潮：黑格尔、马克思及余波',
              author='〔英〕卡尔·波普尔 著', credits=['郑一明　李惠斌　陆俊　黄书进　等译'], pdf_author='〔英〕卡尔·波普尔',
              series='西方现代思想丛书', cover='image06066.jpeg', title_img='image06083.jpeg', copyright=121,
              cls_quote=('content_reference',), cls_center=('center1',), cls_noindent=('left',), part_re=_OS2,
              front=[], body=list(range(123, 138)), back=[138])
CFG[47] = _xf(scratch='q47', file='致命的自负', title='致命的自负', sub='', author='〔英〕弗里德里希·奥古斯特·冯·哈耶克 著',
              credits=['冯克利　胡晋华　等译', '冯克利　统校'], pdf_author='〔英〕F. A. 哈耶克', series='西方现代思想丛书',
              cover='image06117.jpeg', title_img='image06134.jpeg', copyright=141, cls_quote=('content_reference',),
              cls_right=('content_reference_right',), cls_center=('content_center',), cls_noindent=('content_left',),
              front=[(142, 'board'), (144, 'text'), (145, 'text'), (146, 'text'), (147, 'text'), (148, 'text')],
              body=list(range(149, 158)), back=[158])
# 社会主义: 卷 > 部分 > 章 > 节; both the 卷 and the 部分 get a page (part_re, part_re2); the index of the English edition's
# pages (its numbers refer to the printed book's margins, which the ebook does not have) in two columns as it is
CFG[48] = _xf(scratch='q48', file='社会主义', title='社会主义', sub='经济与社会学的分析', author='〔奥〕路德维希·冯·米瑟斯 著',
              credits=['王建民　冯克利　崔树义　译'], pdf_author='〔奥〕路德维希·冯·米瑟斯', series='西方现代思想丛书',
              cover='image06151.jpeg', title_img='image06168.jpeg', copyright=[161, 162], cls_quote=('content_reference',),
              cls_center=('center1',), notes_tail=True, notel_vary=True,
              part_re=r'^第[一二三四五]卷', part_split=r'^(第[一二三四五]卷)[\s\u3000]+(.+)$',
              part_re2=r'^第[一二三]部分', part_split2=r'^(第[一二三]部分)[\s\u3000]+(.+)$',
              front=[(163, 'board'), (164, 'text'), (165, 'text'), (166, 'text'), (167, 'text'), (168, 'text'), (169, 'text'),
                     (170, 'text'), (171, 'text')], body=list(range(173, 209)), back=[209, (210, 'index'), 211])
# 克尔凯郭尔文集 (books 49–58): each volume has the edition's statement, its editorial board, the general preface (汝信) and
# the introduction to Kierkegaard (天才释放出的尖利的闪电), the same in every volume, as the ebook has them
_KG = dict(author='〔丹〕索伦·克尔凯郭尔 著', pdf_author='〔丹〕索伦·克尔凯郭尔', series='克尔凯郭尔文集')
CFG[49] = _xf(scratch='q49', file='论反讽概念', title='论反讽概念', sub='以苏格拉底为主线', credits=['汤晨溪　译'], **_KG,
              cover='image06057.jpeg', title_img='image06073.jpeg', copyright=214, cls_quote=('content_reference',),
              notes_tail=True,                         # (note 10 of chapter 1 is a picture: Napoleon's grave,
              note_plates={'image06211.jpeg'},         #  at the back: in the note it would leave a page foot empty)
              cls_center=('center1', 'block_center'), cls_right=('block_right',),
              part_re=r'^[上下]卷', part_split=r'^([上下]卷)[\s\u3000]+(.+)$',
              front=[(215, 'text'), (216, 'board'), (217, 'plain'), (218, 'text'), (219, 'text'), (220, 'text'), (221, 'text'),
                     (222, 'text')], body=list(range(224, 234)), back=[(234, 'index'), (235, 'index'), 236])
_EE = dict(cls_quote=('content_reference',), cls_center=('content_center',), cls_right=('content_right', 'content_reference_right1'),
           cls_noindent=('content_left',))
CFG[50] = _xf(scratch='q50', file='非此即彼（上）', title='非此即彼', sub='一个生命的残片（上）', credits=['京不特　译'], **_KG, **_EE,
              cover='image06221.jpeg', title_img='image06043.jpeg', copyright=239,
              part_re=r'^(那些直接的爱欲的阶段或者那音乐性的—爱欲的|剪影)$', part_intro=True, part_top={251, 254},
              front=[(240, 'text'), (241, 'text'), (242, 'board'), (243, 'text'), (244, 'text'), (246, 'text')],
              body=list(range(247, 258)), back=[(258, 'index'), (259, 'index')])
CFG[51] = _xf(scratch='q51', file='非此即彼（下）', title='非此即彼', sub='一个生命的残片（下）', credits=['京不特　译'], **_KG, **_EE,
              cover='image06095.jpeg', title_img='image06112.jpeg', copyright=262,
              front=[(263, 'text'), (264, 'board'), (265, 'text'), (266, 'text'), (267, 'text')],
              body=[269, 270, 271], back=[(272, 'index'), (273, 'index')])
CFG[52] = _xf(scratch='q52', file='哲学片断', title='哲学片断', sub='或片断的哲学', credits=['王齐　译'], **_KG,
              cover='image06135.jpeg', title_img='image06152.jpeg', copyright=276, mark_label='原译注',
              cls_quote=('content_reference',), cls_center=('center1', 'block_center'), cls_right=('block_right',),
              cls_noindent=('left',),
              front=[(277, 'text'), (278, 'text'), (279, 'board'), (280, 'dedication'), (281, 'text'), (282, 'text'), (283, 'text'),
                     (284, 'dedication'), (285, 'text')], body=list(range(287, 296)), back=[296, 297])
# 最后的、非科学性的附言: another ebook's markup; the translator's notes unlinked (bk_fixes PNOTES), the author's notes '[n]' at
# the end of each part; the two parts of the book are two very long files: one unit per chapter (split_heads)
CFG[53] = _xf(scratch='q53', file='最后的、非科学性的附言', title='对《哲学片断》所做的最后的、非科学性的附言', sub='',
              credits=['王齐　译'], **_KG, cover='image06216.jpeg', title_img=None, copyright=300, marker='keep',
              head_drop=('其他',), cls_center=('content_', 'tg-title'),
              cls_map={'content_1': ('body', 2, 0, 'hei'), 'content_2': ('center', 0, 0, 'hei'), 'content_3': ('right', 0, 0, 'hei'),
                       'content_4': ('body', 2, 6), 'content_5': ('right', 0, 0), 'content_6': ('body', 2, 3)},
              part_re=r'^第[一二]部(?!分)', part_split=r'^(第[一二]部)[\s\u3000]+(.+)$', part_intro=True,
              part_re2=r'^第[一二]册', part_split2=r'^(第[一二]册)[\s\u3000]+(.+)$',
              split_heads={309: r'^第[一二三四五六]章', 310: r'^(第[一二三四五六]章|第[一二]册|附录)'},
              front=[(299, 'board'), (302, 'text'), (303, 'board'), (304, 'text'), (305, 'text'), (306, 'text'), (307, 'text'),
                     (308, 'text')], body=[309, 310], back=[311, 312])
# 畏惧与颤栗 恐惧的概念 致死的疾病: three works, each with a page of its own (its title and the lines under it); the works'
# own contents pages are not set (the book's contents lists them all)
CFG[54] = _xf(scratch='q54', file='畏惧与颤栗 恐惧的概念 致死的疾病', title='畏惧与颤栗　恐惧的概念　致死的疾病', sub='',
              credits=['京不特　译'], **_KG, cover='image06053.jpeg', title_img='image06069.jpeg', copyright=315,
              cls_quote=('content_reference',), cls_center=('center1',), cls_noindent=('left',),
              part_re=r'^(畏惧与颤栗|恐惧的概念|致死的疾病)$', part_sub_cls=('center1',), part_sub_notoc=True,
              part_re2=r'^第[一二]部分', part_split2=r'^(第[一二]部分)[\s\u3000]+(.+)$',
              front=[(316, 'text'), (317, 'board'), (318, 'kaitext'), (319, 'text'), (320, 'text'), (321, 'text')],
              body=[323] + list(range(325, 333)) + list(range(334, 343)) + list(range(344, 351)),
              back=[(351, 'index'), (352, 'index')])
CFG[55] = _xf(scratch='q55', file='爱的作为', title='爱的作为', sub='', credits=['京不特　译'], **_KG,
              cover='image06044.jpeg', title_img='image06060.jpeg', copyright=355, cls_center=('center1',),
              part_re=r'^爱的作为$', part_sub_cls=('center1',), part_sub_toc=r'^第[一二]系列',
              front=[(356, 'text'), (357, 'board'), (358, 'text'), (359, 'text')],
              body=[361] + list(range(363, 374)) + list(range(375, 387)), back=[])
# 陶冶性的讲演集: four collections, each a page of its own; one unit per discourse (the <h2>), its notes after it
CFG[56] = _xf(scratch='q56', file='陶冶性的讲演集', title='陶冶性的讲演集', sub='', credits=['京不特　译'], **_KG,
              cover='image06093.jpeg', title_img='image06110.jpeg', copyright=389, note_by_marker=True, notes_tail=True,
              skip_text=('注释：',), cls_quote=('content_reference',), cls_center=('block_center', 'center1'),
              part_re=r'^(两个陶冶性的讲演|四个陶冶性的讲演|三个想象出的场合讲演|原野里的百合和天空下的飞鸟)', part_intro=True,
              split_heads={396: 2, 397: 2, 398: 2, 399: 2},
              front=[(390, 'text'), (391, 'board'), (392, 'text'), (393, 'text'), (394, 'text')], body=[396, 397, 398, 399], back=[])
_KS = dict(cls_center=('content_', 'tg-title'),
           cls_map={'content_1': ('body', 2, 0, 'hei'), 'content_2': ('center', 0, 0, 'hei'), 'content_3': ('right', 0, 0, 'hei'),
                    'content_4': ('body', 2, 6), 'content_5': ('right', 0, 0), 'content_6': ('body', 2, 3)})
CFG[57] = _xf(scratch='q57', file='克尔凯郭尔讲演集（1848—1855）', title='克尔凯郭尔讲演集', sub='1848—1855', credits=['京不特　译'],
              **_KG, **_KS, cover='image06214.jpeg', title_img=None, copyright=402, head_drop=('其他',),
              part_re2=r'^第[一二三四]部分', part_split2=r'^(第[一二三四]部分)(?:\[\d+\])?[\s\u3000]+(.+)$',
              split_heads={409: r'^第[一二三四]部分'},
              front=[(401, 'board'), (404, 'text'), (405, 'board'), (406, 'text'), (407, 'text'), (408, 'text')],
              body=list(range(409, 414)), back=[])
CFG[58] = _xf(scratch='q58', file='克尔凯郭尔日记选（1842—1846）', title='克尔凯郭尔日记选', sub='1842—1846', credits=['王齐　译'],
              **_KG, **_KS, cover='image06040.jpeg', title_img=None, copyright=416, marker='keep', head_drop=('其他',),
              orn={'image06072.jpeg', 'image06106.jpeg', 'image06123.jpeg', 'image06140.jpeg'}, orn_size=(60.0, 16.0),
              cls_cap=('imgtitle',),
              front=[(415, 'board'), (418, 'text'), (419, 'board'), (420, 'text'), (421, 'text'), (422, 'text')],
              body=[423, 424, 425], back=[])
FILES = {b: f'{b:02d}-{CFG[b]["file"]}.pdf' for b in CFG}
TITLES = {b: CFG[b]['file'] for b in CFG}


def meta(b):
    C = CFG[b]
    return dict(title=C['title'], sub=C['sub'], author=C['author'], credits=C['credits'], series=C.get('series', ''),
                publisher=C['publisher'], subject=C['file'])


# ---------------------------------------------------------------------------------------------- headings
CN = '一二三四五六七八九十百'
ORD_ONLY = re.compile(r'^第[%s\d]+[部章节篇讲]分?$' % CN)
BARE = re.compile(r'^(第[%s\d]+[部章节篇讲]分?|§\s*\d+[.．]?|[%s]+|\d+[.．]?|[IVX]+[.．]?)$' % (CN, CN))
NUM_PATTERNS = [
    (re.compile(r'^(第[%s\d]+[部章节篇讲]分?)(?![的分])[\s　 ]*(?=\S)' % CN), '　'),
    (re.compile(r'^(附录[%sA-Z]+)[\s　 ]*(?=\S)' % CN), '　'),
    (re.compile(r'^([一二三四五六七八九十]+)[\s　 ]+(?=\S)'), '　'),
    (re.compile(r'^(§\s*\d+[.．])[\s　]*(?=\S)'), ' '),
    (re.compile(r'^(\d+[.．])[\s　]*(?=\S)'), ' '),
]
NUM_PATTERNS.insert(3, (re.compile(r'^(\d+(?:\.\d+)+)[\s\u3000\xa0]*(?=\S)'), '\u3000'))       # '1.1　Title' (before the plain '1. Title' rule)
MARK_TAIL = re.compile(r'(?:⁠?[\[［(（]\d+[\]］)）])+$')
PART_RE = re.compile(r'^第[一二三四五六七八九十]+部分$')


def plain(runs):
    return re.sub(r'\s+', ' ', runs_text(runs)).strip()


def regap_heading(runs):
    """One solid gap between an ordinal and the title text; source line breaks inside a title removed."""
    if not runs:
        return runs
    first = runs[0]
    t = first['t']
    if len(runs) == 1 and ORD_ONLY.match(t.strip()):
        return [dict(first, t=t.strip())]
    head, body = '', t
    for pat, gap in NUM_PATTERNS:
        m = pat.match(t)
        if m:
            head, body = m.group(1) + gap, t[m.end():]
            if body.lstrip(' \u3000')[:1] in ('：', ':', '、', '．'):
                head, body = m.group(1), body.lstrip(' \u3000')     # ('第1章：世界观': the colon is the separator, no gap)
            break
    body = re.sub(' +', ' ', body)
    body = re.sub(r'\s+(?=——)', '', body)
    return [dict(first, t=head + body)] + [dict(r, t=re.sub(' +', ' ', r['t'])) if not r.get('i') else dict(r) for r in runs[1:]]


# ---------------------------------------------------------------------------------------------- markers
CIRC_LINK = None          # (set per book from C['circ_link']) marks and entries of a second series of notes, set as ①②③
PAGE_ANCHOR = None        # (set per book from C['page_anchor']) anchors of the ends of printed pages, kept in the text
MARK_LABEL = None         # (set per book from C['mark_label']) marks that carry a label before their number ('[原注3]', '[资料12]')


def circ_number(n):
    n = int(n)
    if 1 <= n <= 20:
        return chr(0x2460 + n - 1)
    if 21 <= n <= 35:
        return chr(0x3251 + n - 21)
    if 36 <= n <= 50:
        return chr(0x32b1 + n - 36)
    return f'({n})'


def _marker(r, fmt):
    """The printed note number of a mark or of a note entry's label: C['circ_link'] (a pattern of the link or anchor)
    picks out the translator's notes of a book whose two series are both '[n]' in the ebook."""
    if MARK_LABEL and re.fullmatch(r'\u2060?\[(?:%s)[\dA-Z]+\]' % MARK_LABEL, r['t'].strip()):
        return '\u2060'.join(r['t'].strip().lstrip('\u2060'))   # (book 59) a labelled mark as the ebook prints it, never broken
    mt = BT.marker_text(r['t'], fmt)
    if mt and CIRC_LINK and mt.startswith('[') and '校' not in mt \
            and any(re.search(CIRC_LINK, r.get(k) or '') for k in ('h', 'a')):
        return circ_number(re.sub(r'\D', '', mt))
    return mt


URL_RE = re.compile(r'(?:(?:https?|ftp)://|www\.)[^\s，。；：、）】\]”]+[^\s，。；：、）】\]”.,;:]')


def url_runs(runs):
    """(C['url_break']) A web address may break at any character: a long one has no other place to break."""
    out = []
    for r in runs:
        if r.get('i') or not URL_RE.search(r['t']):
            out.append(r)
            continue
        pos = 0
        for m in URL_RE.finditer(r['t']):
            if m.start() > pos:
                out.append(dict(r, t=r['t'][pos:m.start()]))
            out.append(dict(r, t=m.group(0), c=_cls_add(r.get('c'), 'url')))
            pos = m.end()
        if pos < len(r['t']):
            out.append(dict(r, t=r['t'][pos:]))
    return out


_NAME_DOT = re.compile(r'(?<=[^\s⁠])·(?=[^\s⁠])')


def dot_runs(runs):
    """(C['name_dot']) The interpunct inside a name (卡尔·皮尔逊, 《论语·子路》) neither starts nor ends a line: word joiners on
    both sides.  (A '·' at the start of a paragraph, a list item's bullet, is left alone.)"""
    return [r if r.get('i') or '·' not in r['t'] else dict(r, t=_NAME_DOT.sub('⁠·⁠', r['t'])) for r in runs]


_TAIL = re.compile(r'([，、,；;：:])\s?(?=(?:\d{1,4}[)）\]］]|[（(]\d{1,2}[)）])[)）\]］]*[。.，；]?$)')   # (and a verse: '（4：17）］。')


def tail_runs(runs):
    """(C['tail_join'], books 41–58) A paragraph that ends in a number after a comma ('……，II，270）。', '……，（2）。'): the
    number is not alone on the last line, where it would read as a stray note mark (a word joiner after the comma)."""
    k = len(runs) - 1
    while k >= 0 and (runs[k].get('i') or runs[k].get('s')):
        k -= 1                                             # (a note mark at the very end: the text before it)
    if k < 0 or k < len(runs) - 1:
        return runs
    t = runs[k]['t']
    t2 = _TAIL.sub('\\1\u2060', t)
    return runs if t2 == t else runs[:k] + [dict(runs[k], t=t2)]


def sup_runs(runs):
    """(C['sup_join']) An exponent or index (msup / msub runs: L², q_i) never starts a line: a word joiner before it."""
    return [dict(r, t='\u2060' + r['t']) if not r.get('i') and set((r.get('c') or '').split()) & {'msup', 'msub'}
            and r['t'] and not r['t'].startswith('\u2060') else r for r in runs]


def mark_runs(runs, fmt):
    """Note markers (linked runs whose text is a bare note number) -> superscript '[n]' / '(n)', never at the start of a line."""
    out = []
    for r in runs:
        if PAGE_ANCHOR and not r.get('h') and re.search(PAGE_ANCHOR, r.get('a') or ''):
            out.append(r)                                         # (the anchor of a printed page's end on a run of digits)
            continue
        if (r.get('h') or r.get('a')) and not r.get('i') and 'nomark' not in (r.get('c') or ''):
            mt = _marker(r, fmt)
            if mt:
                r = repair_link(dict(r, t='⁠' + mt, s=1))
        out.append(r)
    return out


LAT_APOS = re.compile(r"(?<=[A-Za-z\u00c0-\u024f])[’'](?=[A-Za-z\u00c0-\u024f])|(?:(?<=[\s(“\"])|^)[’‘'](?=[A-Za-z])")


def latin_runs(runs, whole=True):
    """(book 16) Latin text in a Latin face: whole paragraphs that are mostly Latin (the French and German Jabberwocky,
    English quotations), and apostrophes inside Latin words elsewhere (the CJK faces set ’ full width: “l’ oiseau”).
    whole=False: only the apostrophes (C['lat_apos'])."""
    add = lambda r: dict(r, c=((r.get('c') or '') + ' lat').strip())
    if whole and latin_ratio(runs) > 0.5:
        return [add(r) if not r.get('i') else r for r in runs]
    out = []
    for r in runs:
        if r.get('i') or not LAT_APOS.search(r['t']):
            out.append(r)
            continue
        pos = 0
        for m in LAT_APOS.finditer(r['t']):
            if m.start() > pos:
                out.append(dict(r, t=r['t'][pos:m.start()]))
            out.append(add(dict(r, t=m.group(0))))
            pos = m.end()
        if pos < len(r['t']):
            out.append(dict(r, t=r['t'][pos:]))
    return out


def latin_ratio(runs):
    t = plain(runs)
    return sum(1 for ch in t if ch.isascii() and ch.isalpha()) / max(1, len(t))


# ---------------------------------------------------------------------------------------------- elements
def _kai_only(runs):
    return bool(runs) and all('kai' in (r.get('c') or '').split() or not r['t'].strip() for r in runs)


def _cs(C, key):
    return set(C.get(key, ()))


_UNI_SUP = dict(zip('⁰⁴⁵⁶⁷⁸⁹⁺⁻ⁿⁱˣ', '0456789+−nix'))


def uni_scripts(runs):
    """(C['uni_sup'], book 59) The Unicode superscripts that the text faces lack (eˣ, 2⁵): raised digits and letters as the
    ebook's own exponents are (msup)."""
    out = []
    for r in runs:
        if r.get('i') or not any(ch in _UNI_SUP for ch in r['t']):
            out.append(r)
            continue
        for m in re.finditer('([%s]+)|([^%s]+)' % ((''.join(_UNI_SUP),) * 2), r['t']):
            if m.group(1):
                out.append(dict(r, t=''.join(_UNI_SUP[ch] for ch in m.group(1)), c=_cls_add(r.get('c'), 'msup')))
            else:
                out.append(dict(r, t=m.group(2)))
    return out


def _img_text(C, runs):
    """Inline images: those with a transcription (C['img_text']) become text, all others are dropped.  C['img_text_plain']
    lists (text before, text after) patterns where a transcription is plain upright text instead (the letter of
    '附录A', the article of an English title, set by the ebook with the same italic formula picture as a variable)."""
    if C.get('uni_sup'):
        runs = uni_scripts(runs)
    if C.get('sup_plain'):                                         # (book 59) text the ebook marks as an exponent by mistake
        runs = [dict(r, c=' '.join(x for x in r['c'].split() if x != 'msup')) if 'msup' in (r.get('c') or '').split()
                and re.fullmatch(C['sup_plain'], r['t']) else r for r in runs]
    m = C.get('img_text')
    if m is None or not any(r.get('i') for r in runs):
        return runs
    if C.get('img_twin'):                                          # (books 41–58) a picture of a letter that the ebook types again
        tw = C['img_twin']                                         # right beside it (the repair of the ebook): the letter once
        txt = lambda rs: ''.join(x['t'] for x in rs if not x.get('i'))
        drop, k = set(), 0
        while k < len(runs):
            if runs[k].get('i') in tw:
                j = k
                while j < len(runs) and runs[j].get('i') in tw:
                    j += 1
                word = ''.join(m[runs[x]['i']] for x in range(k, j))
                after = re.sub(r'\s', '', txt(runs[j:j + 3]))
                before = txt(runs[max(0, k - 3):k]).rstrip()
                if after.startswith(word) or before.endswith(word):
                    drop |= set(range(k, j))
                k = j
            else:
                k += 1
        runs = [r for x, r in enumerate(runs) if x not in drop]
    def sub(r, k):
        v = m[r['i']]
        pieces = v if isinstance(v, list) else [v]                     # text, (text, run class), or a list of those
        if C.get('img_text_plain'):
            before = ''.join(x['t'] for x in runs[:k] if not x.get('i'))
            after = ''.join(x['t'] for x in runs[k + 1:] if not x.get('i'))
            if any(re.search(b + '$', before) and re.match(a, after) for b, a in C['img_text_plain']):
                pieces = [''.join(x[0] if isinstance(x, tuple) else x for x in pieces)]
        out = []
        for x in pieces:
            t, c = x if isinstance(x, tuple) else (x, '')
            out.append(dict({k: y for k, y in r.items() if k not in ('i', 'c')}, t=t, **({'c': c} if c else {})))
        return out
    return [x for k, r in enumerate(runs) if not r.get('i') or r['i'] in m for x in (sub(r, k) if r.get('i') else [r])]


def exp_sup(runs):
    """A superscript without a link is an exponent (m², 10⁶), not a note mark: black raised digits."""
    return [dict({k: v for k, v in r.items() if k != 's'}, c=((r.get('c') or '') + ' msup').strip())
            if r.get('s') and not r.get('h') and not r.get('a') and not r.get('i') else r for r in runs]


def _head_runs(C, runs, keep=None):
    """Heading text of a source paragraph/heading: line breaks -> one space; `keep='middle'` keeps only the middle line of three."""
    if keep == 'middle':
        lines, cur = [[]], []
        for r in runs:
            if r['t'] in ('\n', '\u2028'):
                lines.append([])
            else:
                lines[-1].append(r)
        if len(lines) >= 3:
            runs = lines[1]
    merged = []
    for r in runs:                                                 # plain runs of a heading are one text (a page anchor may split them)
        if merged and not any(x.get(k) for x in (r, merged[-1]) for k in ('h', 's', 'i')) \
                and (r.get('c'), r.get('b')) == (merged[-1].get('c'), merged[-1].get('b')):
            merged[-1] = dict(merged[-1], t=merged[-1]['t'] + r['t'])
        else:
            merged.append(dict(r))
    runs = merged
    out = []
    for r in runs:
        if r['t'] in ('\n',):
            out.append(dict(r, t=' '))
        else:
            t = re.sub(r'(?<=[\u3400-\u9fff，：；、])\u2028(?=[\u3400-\u9fff“《（])', '', r['t'])   # a break inside a Chinese title
            out.append(dict(r, t=t.replace('\u2028', ' ').replace('\n', ' ')))
    return BT.fix_edges(merge_runs(out))


def _head_sub(C, runs):
    for pat, repl in C.get('head_sub', ()) if runs else ():
        runs = [dict(runs[0], t=re.sub(pat, repl, runs[0]['t']))] + runs[1:]
    return runs


def _cls_add(c, x):
    return x if not c else (c if x in c.split() else c + ' ' + x)


def elements(C, items, kaitext=False):
    """Items of one part -> (elements, note items).  Headings carry 'lvl'; figures are {'k': 'fig'}; captions style 'cap'."""
    els, notes = [], []
    gap_before = False
    head_cls = C.get('head_cls', {})
    pg_pend = []
    in_box = False
    num_pend = None
    for it in items:
        k = it['k']
        if k == 'p' and set(it['cls'].split()) & _cs(C, 'head_num_cls'):
            num_pend = plain(it['runs'])                    # '第一章' set above the chapter title: prefixed to the heading
            continue
        if k == 'h' and num_pend:
            it = dict(it, runs=[run(num_pend + '\u3000')] + it['runs'])
            num_pend = None
        if k == 'h' and set(it['cls'].split()) & set(C.get('head_as_p', {})):
            key = next(c for c in it['cls'].split() if c in C['head_as_p'])
            els.append(dict(k='p', style=C['head_as_p'][key], runs=BT.fix_edges(BT.fix_runs(it['runs'])), id=it['id'],
                            src=f'h.{it["cls"]}', nomerge=True))
            continue
        if k == 'p' and it.get('runs') and it['runs'][0].get('i') in C.get('img_mark', {}) \
                and not any(r['t'].strip() for r in it['runs'][1:] if not r.get('i')):
            mt, href = C['img_mark'][it['runs'][0]['i']]   # (book 59) a picture that is the link of a note mark (a table whose
            if els and els[-1]['k'] == 'p':                 # header carried the mark): the figure stays
                els[-1]['runs'] = els[-1]['runs'] + [dict(run(mt), h=href, a=it['id'])]   # and the mark (the note's back-link
            els.append(dict(k='fig', src=it['runs'][0]['i'], id=''))                    # lands on it) ends the paragraph above it
            continue
        if k == 'p' and set(it['cls'].split()) & _cs(C, 'note_cls'):
            it = dict(it, k='note')                         # footnote paragraphs marked by their class
            k = 'note'
        if k == 'p' and set(it['cls'].split()) & _cs(C, 'pgno_cls') and re.fullmatch(r'[ivxlcdm]{1,8}|\d{1,4}', plain(it['runs'])):
            mk = run('〔%s〕' % plain(it['runs']), c='pgno')     # a page number of the original edition: small, at the end of its paragraph
            if els and els[-1]['k'] == 'p' and els[-1].get('style') not in ('cap',):
                els[-1]['runs'] = els[-1]['runs'] + [mk]
            else:
                pg_pend.append(mk)
            continue
        if k == 'p' and C.get('note_by_marker') and it['runs'] and it['runs'][0].get('h') and _marker(it['runs'][0], 'sq') \
                and len(it['runs']) > 1:
            it = dict(it, k='note')                         # a paragraph that starts with a linked note number is a note entry
            k = 'note'
        if k == 'li' and C.get('note_li') and it['runs'] and (it['runs'][0].get('h') or it['runs'][0].get('a')) \
                and BT.marker_text(it['runs'][0]['t'], 'sq'):
            it = dict(it, k='note')                         # (book 35) a note set as a list item: '1.' linking back to its mark
            k = 'note'
        if k == 'table' and it.get('innote'):
            notes.append(it)                                # a table inside a note (第 2 册注释 11): set under the note's text
            continue
        if k == 'note':
            if ''.join(r['t'] for r in it['runs']).strip('\u3000 ') in C.get('skip_text', ()):
                continue                                    # a 'notes' label that the ebook sets as a note entry
            nr = _img_text(C, it['runs'])                   # (transcribed inline pictures, as in the text)
            r0 = nr[0] if nr else {}
            m = re.match(r'\s*(\[\d+\])', r0.get('t', '')) if (r0.get('h') or r0.get('a')) and not r0.get('i') else None
            if m and r0['t'][m.end():].strip():               # the whole entry is its back-link: the number links back, the text is plain
                back = r0.get('h')
                nr = [dict(r0, t=m.group(1))] + [{k: v for k, v in x.items() if not (k == 'h' and v == back) and k != 'a'}
                                                 for x in [dict(r0, t=r0['t'][m.end():])] + nr[1:]]
            if C.get('edit_inplace') and nr and re.fullmatch(C['edit_inplace'], nr[0]['t'].strip()):
                st = C.get('edit_style', ('smallkai', 0, 2))        # a reviser's note at the end of its chapter, where the ebook has it:
                rest = BT.fix_edges(BT.fix_runs(nr[1:]))            # small type, the label linking back to its mark
                if rest and rest[0]['t'].startswith(('　', ' ')):
                    rest = [dict(rest[0], t=rest[0]['t'].lstrip('　 '))] + rest[1:]
                runs = [dict(nr[0], c=_cls_add(nr[0].get('c'), 'nomark')), run('\u3000')] + rest
                els.append(dict(k='p', style=st[0], first=st[1], left=st[2], right=0, runs=latin_runs(runs, whole=False)
                                if C.get('lat_apos') else runs, id='', src='edit_note', nomerge=True,
                                before=0 if els and els[-1].get('src') == 'edit_note' else 1))
                continue
            notes.append(dict(it, runs=latin_runs(nr, whole=False) if C.get('lat_apos') else nr))
            continue
        if C.get('notes_tail') and notes and k in ('p', 'img'):    # (book 43) after the first note of a part everything is notes:
            if k == 'img':                                  # a note's table (a picture) and its further paragraphs stay with it
                notes.append(dict(k='img', src=it['src'], id=it.get('id', ''), runs=[]))
            elif it.get('runs') and not it.get('blank'):
                notes.append(dict(it, k='note', runs=latin_runs(_img_text(C, it['runs']), whole=False) if C.get('lat_apos')
                                  else _img_text(C, it['runs']), notecap=bool(set(it['cls'].split()) & _cs(C, 'cls_cap'))))
            continue
        if k == 'img' and it['src'] in C.get('img_drop', ()):
            continue                                        # (book 35) the ebook's decoration repeated at the head of every section
        if k == 'img' and it['src'] in C.get('img_text', {}):        # a picture of a few characters standing alone: its transcription, centred
            els.append(dict(k='p', style='center', runs=_img_text(C, [dict(run('\ufffc'), i=it['src'])]), id='', src='img_text',
                            nomerge=True, novary=True))
            continue
        if k == 'img' and it['src'] in C.get('img_para', {}):
            for ln_ in C['img_para'][it['src']]:                 # a display formula set as an image: transcribed to centred text lines
                els.append(dict(k='p', style='center', runs=ln_, id='', src='img_para', nomerge=True, novary=True))
            continue
        if k == 'img':
            if it['src'] in C['tail']:
                continue                                    # the publisher's QR codes: kept as the last page of the book instead
            els.append(dict(k='orn' if (it.get('orn') or it['src'] in C.get('orn', ())) else 'fig', src=it['src'],
                            grp=it.get('grp'), snap=it.get('snap'), id=it.get('id', '')))
            continue
        if k == 'table':
            els.append(dict(k='table', rows=it['rows'], spans=it.get('spans'), heads=it.get('heads')))
            continue
        if k == 'p' and it.get('blank'):
            if els:
                gap_before = True                           # an empty paragraph = one blank line before the next paragraph
            continue
        runs = BT.fix_edges(BT.fix_runs(_img_text(C, it['runs'])))
        if C.get('exp_sup'):
            runs = exp_sup(runs)
        if not runs:
            continue
        cls = it['cls']
        if it.get('box') and not in_box:
            gap_before = True                                # a box (方框) starts: one blank line above it
        elif in_box and not it.get('box'):
            gap_before = True
        in_box = bool(it.get('box'))
        if set(cls.split()) & _cs(C, 'cls_skip') or plain(runs) in C.get('skip_text', ()):
            continue
        if k == 'p' and set(cls.split()) & set(head_cls):          # headings that the ebook sets as paragraphs
            key = next(c for c in cls.split() if c in head_cls)
            spec = head_cls[key]
            lvl, hre = spec if isinstance(spec, tuple) else (spec, None)
            if it.get('box'):                                # the title / sub-titles of a box: small bold lines, not in the contents
                els.append(dict(k='p', style='refhead', runs=_head_runs(C, runs), id=it['id'], src=f'p.{cls}', nomerge=True,
                                **({'before': 1} if gap_before else {})))
                gap_before = False
                continue
            if hre is None or re.match(hre, plain(runs)):
                hr = _head_runs(C, runs, C.get('head_keep', {}).get(key))
                if hr and C.get('merge_dash_head') and plain(hr).startswith('——') and els and els[-1]['k'] == 'h':
                    els[-1]['runs'] = merge_runs(els[-1]['runs'] + hr)
                elif hr:
                    els.append(dict(k='h', lvl=float(lvl), runs=hr, id=it['id'], src=f'p.{cls}', cls=cls))
                continue
        if k == 'p' and C.get('bold_head') and not it.get('box') and runs:     # (book 26) section titles set as bold paragraphs
            lvl_b, max_b = C['bold_head']
            t_b = plain(runs)
            if len(t_b) <= max_b and t_b[-1] not in '。！，；：…' and not any(r.get('s') for r in runs) \
                    and all(r.get('b') for r in runs if r['t'].strip()):
                els.append(dict(k='h', lvl=float(lvl_b), runs=[dict(r, b=0) for r in runs], id=it['id'], src=f'p.{cls}', cls=cls))
                continue
        if k == 'h' and C.get('head_clean'):
            runs = _head_runs(C, runs)
            if not runs:
                continue
        if k == 'h':
            runs = _head_sub(C, runs)
        if k == 'h' and plain(runs) in C.get('head_demote', {}):
            els.append(dict(k='p', style=C['head_demote'][plain(runs)], runs=runs, id=it['id'], src=f'h.{cls}', nomerge=True))
            continue
        if k == 'h':
            t = plain(runs)
            if t in ('注释', '注 释', '註釋', '註 釋', '注釋') or (els and els[-1]['k'] == 'h' and plain(els[-1]['runs']) == t) \
                    or t in C.get('head_drop', ()):
                continue                                         # (head_drop, book 59: the label over the notes at a chapter's end)
            if C.get('merge_dash_head') and t.startswith('——') and els and els[-1]['k'] == 'h':
                els[-1]['runs'] = merge_runs(els[-1]['runs'] + runs)          # 'Title' + '——sub-title' set as two headings
                continue
            sep = next((sp for pat, sp in C.get('head_join', ()) if els and els[-1]['k'] == 'h'
                        and re.fullmatch(pat, plain(els[-1]['runs']))), None)
            if sep is not None:                                  # (book 26) '第3章' and its title as two headings: one heading
                els[-1]['runs'] = merge_runs(els[-1]['runs'] + [run(sep)] + runs)
                continue
            lvl_h = C.get('head_relevel', {}).get(t, it['lvl'])     # (a section title the ebook tags like a chapter title)
            els.append(dict(k='h', lvl=float(lvl_h), runs=runs, id=it['id'], src=f'h{it["lvl"]}.{cls}', cls=cls))
            continue
        if k == 'li':
            if C.get('cls_style') is not None:            # (book 16) nested lists: one hanging level per depth, the list's own bullet
                d = it.get('depth', 0)
                bul = {'square': '▪', 'square1': '▪', 'circle': '◦', 'disc': '•'}.get(it.get('bullet'), '•')
                els.append(dict(k='p', style='noindent', runs=[run(bul + '\u3000')] + runs, id=it['id'], src='li',
                                first=-2, left=2 * (d + 2)))
                continue
            if C.get('li_hang'):                          # the bullet in a 2-em box, turned lines under the text
                els.append(dict(k='p', style='noindent', runs=[dict(run('•'), c='nb')] + runs, id=it['id'], src='li',
                                first=-2, left=2))
                continue
            els.append(dict(k='p', style='noindent', runs=[run('•　')] + runs, id=it['id'], src='li'))
            continue
        if C.get('strip_indent') and runs and not runs[0].get('i'):
            runs = [dict(runs[0], t=runs[0]['t'].lstrip('\u3000 '))] + runs[1:]
            if not runs[0]['t']:
                runs = runs[1:]
            if not runs:
                continue
        if C.get('lat_apos'):
            runs = latin_runs(runs, whole=False)
        b = dict(k='p', runs=runs, id=it['id'], src=f'p.{cls}')
        c = set(cls.split())
        t = plain(runs)
        if re.fullmatch(r'[—－-]{6,}', t):
            continue                                        # the dashed rule before the notes of book 4
        gs = C.get('cls_style')
        if gs is not None and not (c & _cs(C, 'cls_cap')):
            spec = next((gs[x] for x in cls.split() if x in gs), None) or ('body', 2, 0, '')
            stl, first, left, rc = spec
            dc = (it.get('dcls') or '').split()
            left += sum(C.get('div_left', {}).get(x, 0) for x in dc) + (C.get('q_left', 0) if it.get('q') else 0)
            if set(dc) & set(C.get('div_small', ())) and stl in ('body', 'noindent'):
                stl = 'small'
            if rc:
                runs = [dict(r, c=((r.get('c') or '') + ' ' + rc).strip()) if not r.get('i') and 'nohei' not in (r.get('c') or '') else r
                        for r in runs]
            runs = latin_runs(runs)
            b.update(runs=runs, style=stl, first=first, left=left)
            if stl in ('center', 'right', 'ck'):
                b['nomerge'] = True
            if stl in ('quote', 'smallkai', 'verse'):
                b['right'] = 0
            if gap_before and stl not in ('cap',):
                b['before'] = 1
            gap_before = False
            if pg_pend:
                b['runs'] = pg_pend + b['runs']
                pg_pend = []
            els.append(b)
            continue
        if c & ({'tushuo', 'kindle-cn-picture-txt-withmanycharactors', 'kindle-cn-picture-txt-withfewcharactors'} | _cs(C, 'cls_cap')):
            b['style'] = 'cap'
        elif c & ({'right', 'Right', 'kindle-cn-para-right', 'Inscribe'} | _cs(C, 'cls_right')):
            b.update(style='right', nomerge=True)
        elif c & ({'center', 'kindle-cn-para-center'} | _cs(C, 'cls_center')):
            b.update(style='center', nomerge=True)
            if c & _cs(C, 'cls_sep'):                       # (book 33) a section number ('I', 'II'): a blank line above and
                b.update(before=1, after=1, keep=1, minbefore=1)   # below, never the last line of a page
        elif it.get('box'):
            b['style'] = 'quote'
        elif it.get('q'):
            b['style'] = 'quotel' if latin_ratio(runs) > 0.35 else 'quote'
            if c & {'noindent'}:
                b['style'] = 'noindent'
        elif c & ({'noindent', 'kindle-cn-noindent'} | _cs(C, 'cls_noindent')):
            b['style'] = 'noindent'
        elif c & ({'kindle-cn-kai'} | _cs(C, 'cls_quote')) or (_kai_only(runs) and not C.get('no_kai_quote')):
            b['style'] = 'quote'
        elif c & _cs(C, 'cls_quotel'):
            b['style'] = 'quotel'
        elif c & _cs(C, 'cls_refhead'):
            b['style'] = 'refhead'
        elif 'kaiti' in c or kaitext or c & _cs(C, 'cls_kai'):
            b['style'] = 'kaibody'
        else:
            b['style'] = 'body'
        cm = next((C['cls_map'][x] for x in cls.split() + (it.get('dcls') or '').split() if x in C.get('cls_map', {})), None) \
            or next((v for pat, v in C.get('text_map', ()) if re.match(pat, plain(runs).replace('\u2060', ''))), None)   # (or by its first words)
        if cm:                                              # (a class of this book with a style of its own: style, first, left[, run class])
            b.update(style=cm[0], first=cm[1], left=cm[2])
            if len(cm) > 3 and cm[3]:
                b['runs'] = [dict(r, c=((r.get('c') or '') + ' ' + cm[3]).strip()) if not r.get('i') else r for r in b['runs']]
            if cm[0] in ('quote', 'smallkai', 'verse'):
                b['right'] = 0
        if c & _cs(C, 'cls_hang'):                         # '● item' paragraphs: hanging indent under the bullet
            r0 = b['runs'][0]
            b['runs'] = [dict(r0, t=re.sub(r'^([●•■◆▲○◇□])[\s\u3000]*', '\\1\u3000', r0['t']))] + b['runs'][1:]
            b.update(style='noindent', first=-2, left=2)
        if gap_before and b['style'] in ('body', 'noindent', 'quote', 'quotel', 'kaibody', 'center', 'right'):
            b['before'] = 1
        gap_before = False
        if pg_pend and b['style'] not in ('cap',):
            b['runs'] = pg_pend + b['runs']
            pg_pend = []
        els.append(b)
    if C.get('epi_quote'):                                  # (book 29) an epigraph under a title, set as plain text in the ebook:
        for k in range(2, len(els)):                       # the lines between the heading and the '——name' are a quotation
            x = els[k]
            if x['k'] == 'p' and x.get('style') == 'right' and plain(x['runs']).startswith('——'):
                j = k - 1
                while j > 0 and els[j]['k'] == 'p' and els[j].get('style') in ('body', 'noindent') and k - j <= 4:
                    j -= 1
                if els[j]['k'] == 'h' and j < k - 1:
                    for y in els[j + 1:k]:
                        y.update(style='quote', right=0)
    return els, notes


def unit_blocks(els):
    els = [dict(b) for b in els]
    for b in els:
        if b['k'] == 'h':
            b['runs'] = regap_heading(b['runs'])
    KS.rank_headings([b for b in els if b['k'] != 'space'])
    for b in els:
        if b['k'] == 'h' and BARE.match(MARK_TAIL.sub('', plain(b['runs'])).replace('　', '').replace(' ', '')):
            b['style'] = 'secn'
    return els


# ---------------------------------------------------------------------------------------------- tables, figures
def _cell_lines(cell):
    """A table cell -> its lines (the ebook breaks long cells with <br>)."""
    lines = [[]]
    for r in BT.fix_edges(BT.fix_runs(cell)) if cell else []:
        if r['t'] == BR or r['t'] == '\n':
            lines.append([])
        else:
            lines[-1].append(r)
    return [BT.fix_edges(l) for l in lines if l] or [[]]


def _w(runs):
    return sum(2 if ord(ch) > 0x2e80 else 1 for ch in plain(runs)) / 2.0


def table_blocks(rows, head=True):
    """A small text table -> one paragraph per line of a row, cells as fixed-width inline boxes (hanging indent for the
    last cell).  A row with one cell only (a source line under the table) becomes a small paragraph after the table."""
    ncol = max(len(r) for r in rows)
    tail = []
    while rows and ncol > 1 and sum(1 for c in rows[-1] if plain(c)) == 1 and len(rows[-1]) < ncol:
        tail.insert(0, next(c for c in rows[-1] if plain(c)))
        rows = rows[:-1]
    grid = [[_cell_lines(r[j]) if j < len(r) else [[]] for j in range(ncol)] for r in rows]
    widths = [max(_w(l) for g in grid for l in g[j]) + 1.2 for j in range(ncol)]
    sizes = (3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 16, 18, 20, 22, 24, 26, 28)
    cls_of = lambda w: f'tw w{min([x for x in sizes if x >= w], default=28)}'
    used = [int(cls_of(w).split('w')[-1]) for w in widths]
    if head and len(rows) > 1 and ncol > 1 and plain(rows[0][-1]) == plain(rows[1][-1]):
        head = False                                       # the same last-column value in the first two rows: a list, not a header row
    out = []
    indent = sum(used[:-1])
    for ri, g in enumerate(grid):
        nl = max(len(c) for c in g)
        for li in range(nl):
            runs = []
            for j in range(ncol):
                cell = g[j][li] if li < len(g[j]) else []
                bold = ri == 0 and head
                if j == ncol - 1:
                    runs += [dict(x, b=1) if bold else x for x in cell]
                else:
                    runs += [dict(x, c=(x.get('c', '') + ' ' + cls_of(widths[j])).strip(), **({'b': 1} if bold else {})) for x in cell]
                    if not cell:
                        runs.append(run('\u2060', c=cls_of(widths[j])))
            out.append(dict(k='p', style='trow', runs=runs, novary=True, nomerge=True, first=-indent, left=indent + 1,
                            before=1 if ri == 0 and li == 0 else 0, after=1 if ri == len(grid) - 1 and li == nl - 1 and not tail else 0,
                            **({'keep': 1} if li < nl - 1 else {})))
    for k, cell in enumerate(tail):
        out.append(dict(k='p', style='quotel', runs=BT.fix_edges(BT.fix_runs(cell)), first=0, left=0, right=0, nomerge=True,
                        after=1 if k == len(tail) - 1 else 0))
    return out


_FACE = {}


def _em(ch, bold=False):
    """Advance of a character in the body face, in em, from the book's own font subset: Latin capitals are about 0.7 em
    wide, not half an em; CJK characters, full-width punctuation and the dashes of Chinese text one em."""
    if bold not in _FACE:
        from fontTools.ttLib import TTFont
        try:
            f = TTFont(os.path.join(style.FONT_DIR, 'SerifSC-Bold.ttf' if bold else 'SerifSC-Regular.ttf'))
            _FACE[bold] = (f.getBestCmap(), f['hmtx'].metrics, f['head'].unitsPerEm)
        except OSError:
            _FACE[bold] = ({}, {}, 1000)
    cmap, hmtx, upm = _FACE[bold]
    if ch in '—…' or ord(ch) >= 0x2e80 and ord(ch) not in cmap:
        return 1.0
    g = cmap.get(ord(ch))
    return hmtx[g][0] / upm if g in hmtx else (1.0 if ord(ch) >= 0x2e80 else 0.6)


_NO_START = set('，。、；：！？）》」』”’】〕…—·%,.;:!?)]}')       # (a line of a table cell does not start with these
_NO_END = set('（《「『“‘【〔([{')                                #  nor end with those)
_CJK = lambda ch: ord(ch) >= 0x2e80


def _can_break(t, i):
    """May a line of a table cell end before t[i]?  Between CJK characters, at spaces, never inside a Latin word."""
    a, b = t[i - 1], t[i]
    j = i
    while j < len(t) and t[j] == ' ':                            # (the spaces at a break go; what follows them opens the line)
        j += 1
    if b in _NO_START or a in _NO_END or j < len(t) and t[j] in _NO_START:
        return False
    return _CJK(a) or _CJK(b) or a == ' ' or b == ' '


def _slice_runs(runs, s, e):
    out, pos = [], 0
    for r in runs:
        n = len(r['t'])
        lo, hi = max(s, pos), min(e, pos + n)
        if lo < hi:
            out.append(dict(r, t=r['t'][lo - pos:hi - pos]))
        pos += n
    return out


def _wrap_cell(runs, width, bold=False, code=False, final=False):
    """A line of a table cell broken into lines at most `width` em wide (greedy, with the line-start / line-end rules);
    a line of code or a formula continues two em further in than it starts."""
    t = ''.join(r['t'] if not r.get('i') else '￼' for r in runs)
    if not t:
        return [runs]
    ws = [_em(c, bold) for c in t]
    lead = len(t) - len(t.lstrip('　'))
    hang = (lead + 2) * 1.0 if code else 0.0
    lines, start = [], 0
    while start < len(t):
        room = width - (hang if lines else 0.0)
        w, i, ok, opps = 0.0, start, None, []
        while i < len(t) and w + ws[i] <= room + 1e-6:
            w += ws[i]
            i += 1
            if i < len(t) and i > start and _can_break(t, i):
                ok = i
                opps.append(i)
        if i >= len(t):
            lines.append((start, len(t)))
            break
        rest = t[ok:].strip(' \u3000') if ok is not None else ''
        if final and rest and len(rest) <= 3 and all(c in '＞>)）]］}」』”’。，、；：！？…—' for c in rest):
            # what is left is punctuation only: break earlier -- after an operator of a formula ('→', '='), or at the
            # opportunity before if that keeps most of the line (only in the lines as set: the column widths stay as they were)
            fits = lambda k: sum(ws[k:]) <= width - hang + 1e-6
            ops = [k for k in range(start + 1, ok) if t[k - 1] in '→=∧∨⊃' and t[k] not in _NO_START and fits(k)]
            if ops:
                ok = ops[-1]
            elif len(opps) > 1 and opps[-2] - start >= 0.6 * (ok - start) and fits(opps[-2]):
                ok = opps[-2]
        if ok is None:                                           # one word longer than the line: after a hyphen, comma or slash,
            ok = next((k for k in range(i, start, -1) if (t[k - 1] in '-,/' or t[k] in '([')        # or before a bracket
                       and t[k] not in _NO_START and t[k - 1] not in _NO_END), None) or max(i, start + 1)
            opens = lambda k: (t[k:].lstrip(' ') or ' ')[0]
            while ok > start + 1 and ok < len(t) and (opens(ok) in _NO_START or t[ok - 1] in _NO_END):
                ok -= 1                                          # (even then no closing mark opens a line)
        lines.append((start, ok))
        start = ok
        while start < len(t) and t[start] == ' ':
            start += 1
    out = []
    for k, (a, b) in enumerate(lines):
        part = BT.fix_edges(_slice_runs(runs, a, b)) if k else _slice_runs(runs, a, b)
        if k and code and part:
            part = [dict(part[0], t='　' * int(hang)) ] + part if part[0].get('i') else [dict(part[0], t='　' * int(hang) + part[0]['t'])] + part[1:]
        out.append(part)
    return out


def _line_em(runs, bold=False):
    return sum(_em(c, bold) if not r.get('i') else 1.0 for r in runs for c in (r['t'] if not r.get('i') else 'x'))


def _col_widths(cells, nat, code, avail, pad):
    """Column widths (whole em) for a table wider than the text: columns of a few characters keep their width; for the
    others every combination of widths that fits is tried and the one giving the fewest lines in all is taken (a line
    broken in a column of code or formulas counts more than one in a column of prose; among equals the widths closest
    to the proportions of the natural widths)."""
    import itertools
    ncol = len(nat)
    fixed = [nat[j] <= 4.5 for j in range(ncol)]
    width = [math.ceil(nat[j]) if fixed[j] else 0 for j in range(ncol)]
    flex = [j for j in range(ncol) if not fixed[j]]
    room = avail - sum(width)
    if not flex:
        return width
    cache = {}

    def nlines(ri, j, w):
        key = (ri, j, w)
        if key not in cache:
            cache[key] = sum(len(_wrap_cell(l, w - (pad if j < ncol - 1 else 0.0), code=code[j])) for l in cells[ri][j]) if cells[ri][j] else 1
        return cache[key]

    def units(j):                                                # the widest piece that should not be broken
        best = 0.0
        for row in cells:
            for l in row[j]:
                t = ''.join(r['t'] for r in l if not r.get('i'))
                w = 0.0
                for i, c in enumerate(t):
                    if i and _can_break(t, i):
                        best, w = max(best, w), 0.0
                    w += _em(c)
                best = max(best, w)
        return best

    lo = [min(math.ceil(nat[j]), max(3, math.ceil(units(j) + pad))) for j in flex]
    hi = [math.ceil(nat[j]) for j in flex]
    if sum(lo) > room:                                           # no way to keep every word whole: in proportion
        tot = sum(nat[j] for j in flex)
        for j in flex:
            width[j] = max(2, int(room * nat[j] / tot))
        return width
    if len(flex) > 3:
        ranges = [range(max(l, min(h, int(room * nat[j] / sum(nat[k] for k in flex)))), h + 1) for j, l, h in zip(flex, lo, hi)]
    else:
        ranges = [range(l, h + 1) for l, h in zip(lo, hi)]
    best = None
    for combo in itertools.product(*ranges):
        if sum(combo) > room:
            continue
        total = 0.0
        for ri in range(len(cells)):
            n = [nlines(ri, j, w) for j, w in zip(flex, combo)]
            total += max(n + [1]) + sum(0.6 * (x - 1) for x, j in zip(n, flex) if code[j])
        tot_nat = sum(nat[j] for j in flex)
        skew = max(abs(w / sum(combo) - nat[j] / tot_nat) for j, w in zip(flex, combo))
        key = (round(total, 3), skew)
        if best is None or key < best[0]:
            best = (key, combo)
    for j, w in zip(flex, best[1]):
        width[j] = w
    return width


def table_blocks2(rows, spans, heads, center=True):
    """(book 16) A text table centred in the text width: cells as fixed-width inline boxes as in `table_blocks`; a row
    whose only cell spans the whole table ('*　*　*') is a centred line; only header cells (<th>) are bold.  Widths come
    from the font's own advances; a table wider than the text gets its column widths from `_col_widths` and its cells
    broken into lines (`_wrap_cell`)."""
    ncol = max(sum(sp) for sp in spans) if spans else max(len(r) for r in rows)
    full = [len(r) == 1 and (sp[0] if sp else 1) >= max(2, ncol) for r, sp in zip(rows, spans)]
    pad = 1.2
    body = [(ri, r) for ri, (r, f) in enumerate(zip(rows, full)) if not f]
    cells = [[_cell_lines(r[j]) if j < len(r) else [[]] for j in range(ncol)] for _, r in body]
    bolds = [bool(heads and heads[ri]) for ri, _ in body]
    nat = [max([_line_em(l, b) for g, b in zip(cells, bolds) for l in g[j]] or [0]) + pad for j in range(ncol)]
    while ncol > 1 and nat[-1] <= pad:                           # (an empty last column)
        ncol -= 1
        nat.pop()
        cells = [g[:ncol] for g in cells]
    def latin(j):
        t = ''.join(x['t'] for g in cells for l in g[j] for x in l if not x.get('i')).replace(' ', '').replace('　', '')
        return bool(t) and sum(1 for c in t if not _CJK(c)) >= 0.6 * len(t)
    code = [latin(j) for j in range(ncol)]
    avail = style.TEXT_W / style.FONT - 1.0
    if sum(nat) - pad <= avail:
        widths = [math.ceil(w) for w in nat]
        wrap = False
    else:
        widths = _col_widths(cells, nat, code, avail, pad)
        wrap = True
    cls_of = lambda w: f'tw w{max(2, min(34, int(w)))}'
    indent = sum(widths[:-1])
    total = indent + (widths[-1] if wrap else nat[-1] - pad)
    off = max(0.0, (avail - total) / 2) if center else 0.0
    out = []
    n = len(rows)
    gi = 0
    for ri, (r, f) in enumerate(zip(rows, full)):
        first, last = ri == 0, ri == n - 1
        if f:
            out.append(dict(k='p', style='center', runs=BT.fix_edges(BT.fix_runs(r[0])), novary=True, nomerge=True,
                            before=1 if first else 0, after=1 if last else 0))
            continue
        g, bold = cells[gi], bolds[gi]
        gi += 1
        if wrap:
            g = [[x for l in g[j] for x in (_wrap_cell(l, widths[j] - (pad if j < ncol - 1 else 0.0), bold, code[j], final=True) if l else [l])]
                 for j in range(ncol)]
        nl = max(len(c) for c in g)
        for li in range(nl):
            runs = []
            for j in range(ncol):
                cell = g[j][li] if li < len(g[j]) else []
                if j == ncol - 1:
                    runs += [dict(x, b=1) if bold else x for x in cell]
                else:
                    runs += [dict(x, c=(x.get('c', '') + ' ' + cls_of(widths[j])).strip(), **({'b': 1} if bold else {}))
                             for x in merge_runs(cell)]                  # (one box per cell: runs of one format merged)
                    if not cell:
                        runs.append(run('⁠', c=cls_of(widths[j])))
            if nl > ROW_SPLIT:                                   # (book 26) a row of many lines may break between pages,
                kp = li == 0 or nl - 3 < li < nl - 1             # two lines of it at least on either side
            else:
                kp = li < nl - 1
            kp = kp or bold and not last and li == nl - 1        # (the header row stays with the first row under it)
            out.append(dict(k='p', style='trow', runs=runs, novary=True, nomerge=True, first=-indent, left=round(off + indent + 1, 2),
                            before=1 if first and li == 0 else 0, after=1 if last and li == nl - 1 else 0,
                            **({'keep': 1} if kp else {})))
    return out


ROW_SPLIT = 8              # a table row of more lines than this may be split between pages


def fig_label(text, pat=r'^(图[^\s　]+)'):
    m = re.match(pat, text)
    return m.group(1) if m else ''


def join_images(srcs):
    """Two or more images of one table (the ebook splits it with a '(continued)' line) stacked into one image file;
    SVG pictures (the panels of one figure) into one SVG."""
    from PIL import Image
    if all(x.lower().endswith('.svg') for x in srcs):
        from lxml import etree
        name = 'join_' + '_'.join(os.path.splitext(x)[0] for x in srcs) + '.svg'
        dst = os.path.join(special.IMG_DIR, name)
        parser = etree.XMLParser(resolve_entities=False, no_network=True)
        parts = [(etree.parse(os.path.join(special.IMG_DIR, x), parser).getroot(), special.img_size(x)) for x in srcs]
        W = max(w for _, (w, _h) in parts)
        gap = max(12.0, W / 40)
        H = sum(h for _, (_w, h) in parts) + gap * (len(parts) - 1)
        root = etree.Element('{http://www.w3.org/2000/svg}svg', nsmap={None: 'http://www.w3.org/2000/svg',
                                                                      'xlink': 'http://www.w3.org/1999/xlink'})
        root.set('version', '1.1')
        root.set('width', f'{W:.3f}')
        root.set('height', f'{H:.3f}')
        root.set('viewBox', f'0 0 {W:.3f} {H:.3f}')
        y = 0.0
        for el, (w, h) in parts:                                 # each panel a nested <svg> at its own size, centred
            el.set('x', f'{(W - w) / 2:.3f}')
            el.set('y', f'{y:.3f}')
            el.set('width', f'{w:.3f}')
            el.set('height', f'{h:.3f}')
            root.append(el)
            y += h + gap
        etree.ElementTree(root).write(dst, xml_declaration=True, encoding='utf-8')
        return name
    name = 'join_' + '_'.join(re.sub(r'\D', '', x)[-5:] for x in srcs) + '.jpeg'
    dst = os.path.join(special.IMG_DIR, name)
    if not os.path.exists(dst):
        ims = []
        for x in srcs:
            im = Image.open(os.path.join(special.IMG_DIR, x)).convert('RGBA')
            bg = Image.new('RGBA', im.size, (255, 255, 255, 255))
            bg.alpha_composite(im)                               # (transparent PNGs: on white, not on black)
            ims.append(bg.convert('RGB'))
        W = max(im.width for im in ims)
        gap = max(12, W // 40)
        out = Image.new('RGB', (W, sum(im.height for im in ims) + gap * (len(ims) - 1)), 'white')
        y = 0
        for im in ims:
            out.paste(im, ((W - im.width) // 2, y))
            y += im.height + gap
        out.save(dst, quality=93)
    return name


def join_continued(C, els):
    """fig, '（续表）', fig -> one fig of the stacked images."""
    jre = C.get('join_cont')
    if not jre:
        return els
    out = []
    for e in els:
        if e['k'] == 'fig' and len(out) >= 2 and out[-1]['k'] == 'p' and re.fullmatch(jre, plain(out[-1]['runs'])) \
                and out[-2]['k'] == 'fig':
            out.pop()
            prev = out.pop()
            out.append(dict(prev, src=join_images(prev.get('parts', [prev['src']]) + [e['src']]),
                            parts=prev.get('parts', [prev['src']]) + [e['src']]))
            continue
        out.append(e)
    return out


def fig_paragraphs(C, els, fig_no):
    """Figures inside chapters -> 'see plate N' paragraphs; figures of appendices (C['inplace']) stay in the text."""
    els = join_continued(C, els)
    out = []
    i = 0
    while i < len(els):
        b = els[i]
        if b['k'] != 'fig':
            out.append(b)
            i += 1
            continue
        i += 1
        caps = []
        mode = C.get('cap_mode', 'after')                            # where the ebook puts a caption: after / before / tabfig (tables above, figures below)
        is_cap = lambda x: x['k'] == 'p' and x.get('style') == 'cap'
        above = lambda x: plain(x['runs']).startswith(('表', '（', '('))   # table titles and '(continued)' lines stand above their image
        if mode in ('before', 'tabfig'):
            while out and is_cap(out[-1]) and (mode == 'before' or above(out[-1])):
                caps.insert(0, re.sub(r'\s+', ' ', runs_text(out.pop()['runs']).replace('\u2060', '')).strip())
        while mode != 'before' and i < len(els) and is_cap(els[i]) and (mode == 'after' or not above(els[i])):
            caps.append(re.sub(r'\s+', ' ', runs_text(els[i]['runs']).replace('\u2060', '')).strip())
            i += 1
        if C.get('cap_after_re'):                                    # source / note lines right under a figure belong to it
            while i < len(els) and els[i]['k'] == 'p' and re.match(C['cap_after_re'], plain(els[i]['runs'])):
                caps.append(re.sub(r'\s+', ' ', runs_text(els[i]['runs']).replace('\u2060', '')).strip())
                i += 1
        text = '　'.join(caps)
        if b['src'] in C['inplace']:
            out.append(dict(k='fig', src=b['src']))
            for cp in caps:
                out.append(dict(k='p', style='quotel', runs=[run(cp)], first=0, left=0, right=0, nomerge=True))
            continue
        n = fig_no(b['src'], text)
        lab = fig_label(text, C.get('label_re', r'^(图[^\s　]+)'))
        runs = []
        if lab:
            runs.append(run(lab + '　'))
        runs.append(run(f'见书后插图{n}', h=f'plate-{n}', a=f'figref-{n}', c='fig'))
        out.append(dict(k='p', style='center', runs=runs, novary=True, nosplit=True, nomerge=True, before=1, after=1, plate_ref=1))
    return out


def fig_inline(C, els):
    """(book 16) Figures stay in the text: consecutive images of one figure are stacked, the caption paragraphs under
    them (title, sub-title) go with them; the result is one 'fig' element with 'caps'."""
    out = []
    i = 0
    while i < len(els):
        e = els[i]
        if e['k'] != 'fig':
            out.append(e)
            i += 1
            continue
        caps_top = []
        if out and out[-1]['k'] == 'p' and out[-1].get('style') == 'cap':
            if C.get('cap_top_re') and re.match(C['cap_top_re'], plain(out[-1]['runs'])):
                caps_top = [out.pop()]                           # (book 26) a table title above its picture: part of the figure, floats with it
            else:
                out[-1]['keep'] = 1                              # a title above the picture (表6-1) stays with it
        srcs = [e['src']]
        i += 1
        while i < len(els) and els[i]['k'] == 'fig' and els[i].get('grp') == e.get('grp') and not e.get('snap'):
            srcs.append(els[i]['src'])
            i += 1
        for g in C.get('fig_join', ()):                         # panels of one figure that the ebook puts in separate boxes
            if srcs == [g[0]]:
                while i < len(els) and els[i]['k'] == 'fig' and els[i]['src'] in g[1:]:
                    srcs.append(els[i]['src'])
                    i += 1
        caps = []
        while i < len(els) and els[i]['k'] == 'p' and els[i].get('style') == 'cap':
            caps.append(els[i])
            i += 1
        out.append(dict(k='fig', src=srcs[0] if len(srcs) == 1 else join_images(srcs), caps=caps, snap=e.get('snap'),
                        **({'caps_top': caps_top} if caps_top else {})))
    return out


FIG_MAX_H = 420.0          # pt; an in-text figure (image) is at most this high
SNAP_SCALE = 0.25          # pt per pixel of the table pictures of tools/snap.py (rendered at 4 px per pt)


def formula_scale(src, letter=8.0):
    """pt per pixel for a formula set as an image: its smallest line of letters (a band of rows with ink, at least 10 px
    high) becomes `letter` pt high; never larger than the full-width scale of the figures."""
    from PIL import Image
    import numpy as np
    im = Image.open(os.path.join(special.IMG_DIR, src)).convert('RGBA')
    bg = Image.new('RGBA', im.size, (255, 255, 255, 255))
    bg.alpha_composite(im)
    ink = (np.array(bg.convert('L')) < 140).sum(1) > 0
    bands, run_ = [], 0
    for x in list(ink) + [False]:
        if x:
            run_ += 1
        elif run_:
            bands.append(run_)
            run_ = 0
    text = [b for b in bands if b >= 10]
    return min(style.TEXT_W / 566.0, letter / min(text)) if text else style.TEXT_W / 566.0
FIG_SCALE = None           # pt per pixel of the ebook's full-width images (set on first use: text width / 566 px)


def fig_block(C, e, fmt):
    """An in-text figure: image scaled into the text width, caption lines under it; it may float to the next page."""
    global FIG_SCALE
    if FIG_SCALE is None:
        FIG_SCALE = style.TEXT_W / 566.0
    w, h = special.img_size(e['src'])
    capw = style.TEXT_W - 2 * style.FONT
    caps, fid = [], ''
    for c in e.get('caps', []):
        runs = BT.fix_edges(BT.fix_runs(c['runs']))
        if not runs:
            continue
        title = 'maintitle' in c.get('src', '')
        fid = fid or (c.get('id') if title else '')
        caps.append(('s-figcap' if title else 's-figsub', mark_runs(runs, fmt)))
    tops = [('s-figsub', mark_runs(BT.fix_edges(BT.fix_runs(c['runs'])), fmt)) for c in e.get('caps_top', [])]
    tops = [x for x in tops if x[1]]
    est = sum(math.ceil(len(plain(r)) * 9.0 / capw + 0.01) for _, r in caps + tops)
    max_h = min(FIG_MAX_H, (style.NLINES - 3) * style.LINE - 15.0 - 13.0 * est)
    if e.get('snap'):
        sc = SNAP_SCALE                                         # a picture of a table: its own size (made at SNAP_SCALE)
    elif re.match(C.get('formula_img', r'$^'), e['src']):
        sc = formula_scale(e['src'])                            # a formula set as an image: its letters about the size of the text
    elif C.get('fig_dpi'):
        sc = 72.0 / C['fig_dpi']                                # (book 18) the printed size: the scans' resolution (an SVG redrawing: its units as their pixels)
    else:
        sc = FIG_SCALE
    sc = C.get('fig_scale', {}).get(e['src'], 1.0) * sc
    sc = min(sc, style.TEXT_W / w, max_h / h)
    iw, ih = round(w * sc, 2), round(h * sc, 2)
    flt = bool(caps) and plain(caps[0][1]).startswith('图') or bool(tops) or ih > 6 * style.LINE   # numbered figures and tables, tall pictures may float
    b = dict(k='img', style='center', runs=[], src=special.img_url(e['src']), w=iw, h=ih, float=int(flt), id=fid, capw=capw,
             fig_src=e['src'])
    if e['src'] in C.get('fig_air', {}):
        b['air'] = C['fig_air'][e['src']]                       # (book 34) more air around this picture may spare a widow
    if e['src'] in C.get('fig_right', ()):
        b['align'] = 'right'                                    # (book 35) a signature above the signer's name: flush right like the name
    if caps or tops:
        b['cap'] = caps
        if tops:
            b['cap_top'] = tops                                 # (the title of a table: above the picture)
    else:
        b['cap_lines'] = []
        b['n'] = int(math.ceil((ih + 10.0) / style.LINE))
    return [b]


def image_blocks(src, max_h, width=None, max_scale=None):
    """A figure that stays in the text: an image block scaled into the text width (at most max_h pt high)."""
    w, h = special.img_size(src)
    s = min((width or style.TEXT_W) / w, max_h / h, max_scale or 1e9)
    iw, ih = w * s, h * s
    n = math.ceil(ih / style.LINE)
    return [dict(k='space', style='center', runs=[], n=1),
            dict(k='img', style='center', runs=[], src=special.img_url(src), w=round(iw, 2), h=round(ih, 2), n=n),
            dict(k='space', style='center', runs=[], n=1)]


def figure_pages(n, els, zone='front', ids=(), cap_before=False, notes=()):
    """Page modules for a part made of pictures: each picture a page of its own, fitted into the text block with its
    caption lines; the part's heading (if any) titles the first page, which then carries the bookmark and the contents line.
    `cap_before`: the caption line stands before the picture in the ebook (a page label); `ids`: anchors of the first page
    (links to the part from elsewhere in the book)."""
    title = next((plain(e['runs']) for e in els if e['k'] == 'h'), '')
    sub = []
    if notes:                                                    # (book 29) a note on the title ('参考文献[1]'): its text under the title
        title = re.sub(r'\s*[\[［]\d+[\]］]$', '', title)
        sub = [re.sub(r'^\s*[\[［]\d+[\]］]\s*', '', plain(nt['runs'])) for nt in notes]
    figs, i = [], 0
    pre = []
    while i < len(els):
        e = els[i]
        i += 1
        if cap_before and e['k'] == 'p' and e.get('style') == 'cap':
            pre.append(plain(e['runs']))
            continue
        if e['k'] != 'fig':
            continue
        lines, pre = pre, []
        while i < len(els) and els[i]['k'] == 'p' and els[i].get('style') == 'cap':
            cur = []
            for r in els[i]['runs']:
                if r['t'] in (BR, '\n'):
                    lines.append(''.join(cur).strip())
                    cur = []
                else:
                    cur.append(r['t'])
            lines.append(''.join(cur).strip())
            i += 1
        figs.append((e['src'], [re.sub(r'\s+', ' ', t) for t in lines if t]))
    mods = []
    for k, (src, lines) in enumerate(figs):
        head = title if k == 0 else ''
        sub_k = sub if k == 0 else []
        def html(bb, page, src=src, lines=lines, head=head, a=tuple(ids) if k == 0 else (), sub_k=sub_k):
            return special.figure_page_html(src, lines, head, ids=a, builder=bb, page=page, sub=sub_k)
        m = page_module(f'figpage{n}-{k}', zone, html, toc=bool(head), toc_title=head, toc_level=1, title=head or title,
                        folio=True, head=True)
        m.lines = ([head] if head else []) + sub_k + lines         # (for the text-fidelity report)
        mods.append(m)
    return mods


def plate_figs(C):
    """(fig_inline books) Figures that go to the back of the book after all, one per page: the configured ones
    (C['plate_figs']) and those that tools/bk_build.py found leaving the foot of a page blank (<scratch>/plate_figs.json)."""
    import json
    out = set(C.get('plate_figs', ()))
    try:
        out |= set(json.load(open(os.path.join(style.SCRATCH, 'plate_figs.json'), encoding='utf8')))
    except (OSError, ValueError):
        pass
    return out


def fig_plate_ref(e, fig_no):
    """(fig_inline books) A figure set at the back: in the text its title and the link 'see plate N'; the plate links back
    here and takes over the figure's anchor (the list of figures and the text's 'Figure N' links lead to the plate)."""
    caps = [(c, re.sub(r'\s+', ' ', runs_text(BT.fix_edges(BT.fix_runs(c['runs'])))).strip()) for c in e.get('caps', [])]
    caps = [(c, t) for c, t in caps if t]
    ids = [c['id'] for c, _ in caps if c.get('id')]
    n = fig_no(e['src'], '　'.join(t for _, t in caps), ids)
    runs = ([run(caps[0][1] + '　')] if caps else []) + [run(f'见书后插图{n}', h=f'plate-{n}', a=f'figref-{n}', c='fig')]
    return [dict(k='p', style='center', runs=runs, novary=True, nosplit=True, nomerge=True, before=1, after=1, plate_ref=1)]


PLATES_NOTE = '正文中的图表集中排在此处，每页一图；正文中以蓝色“见书后插图N”标示，点击可跳转，每页底部附返回链接。'
PLATES_NOTE_INLINE = ('插图都排在正文中引用它的地方；只有放在正文里会让页面底部留下空白的图移到这里，每页一图。'
                      '正文原处是图题和蓝色的“见书后插图N”，点击可跳转，每页底部附返回链接。')


def plate_modules(figs, note=PLATES_NOTE):
    if not figs:
        return []
    divider = page_module('plates', 'back', special.plate_divider_html('书后插图', note),
                          toc=True, toc_title='书后插图', toc_level=0, title='书后插图', folio=True)
    mods = [divider]
    for k, (img, cap, *ids) in enumerate(figs, 1):
        def html(bb, page, k=k, img=img, cap=cap, ids=tuple(ids[0]) if ids else ()):
            return special.plates_page_html(k, img, bb, page, cap, ids)
        m = page_module(f'plate-page{k}', 'back', html, toc=False, title=f'书后插图 {k}', folio=True, head=True)
        m.anchor = f'plate-{k}'
        m.lines = [cap]                                         # (for the text-fidelity report)
        mods.append(m)
    return mods


# ---------------------------------------------------------------------------------------------- notes
def note_table_blocks(rows):
    """A table inside a note: one small line per row under the note's text, cells as fixed-width boxes."""
    return [dict(b, style='notet', left=b['left'] + 3, before=0, after=0) for b in table_blocks(rows)]


def note_blocks(items, fmt):
    out = []
    for it in items:
        if it['k'] == 'table':
            out += note_table_blocks(it['rows'])
            continue
        if it['k'] == 'img':                               # (book 43) a table of a note, a picture: at its width at 220 dpi,
            from PIL import Image                          # at most the text block's, centred on the small grid
            iw, ih = Image.open(os.path.join(special.IMG_DIR, it['src'])).size
            w = min(style.TEXT_W, iw * 72.0 / 220)
            h = w * ih / iw
            pitch = style.TEXT_H / style.SMALL_N
            out.append(dict(k='img', style='orn', runs=[], src=special.img_url(it['src']), w=w, h=h,
                            n=math.ceil(h / pitch) + 1))
            continue
        runs = BT.fix_edges(BT.fix_runs(it['runs']))
        if not runs:
            continue
        first = runs[0]
        label = re.fullmatch(r'〔[^〕\d]{1,6}\d+〕', first['t'].strip().replace('\u2060', ''))    # (book 34: a reviser's note '〔校订注1〕', as its mark reads)
        label = label or (MARK_LABEL and re.fullmatch(r'\[(?:%s)[\dA-Z]+\]' % MARK_LABEL, first['t'].strip().replace('\u2060', '')))
        if (first.get('h') or first.get('a')) and (BT.marker_text(first['t'], fmt) or label):
            mt = _marker(first, fmt) or first['t'].strip()
            marks = [repair_link(dict(first, t=mt, s=0, c='nn'))] if not label else \
                [repair_link(dict(first, t=mt, s=0)), run('\u3000')]       # (a label wider than the number column: in the line)
            rest = [mark_runs([r], fmt)[0] if (r.get('h') or r.get('a')) and re.fullmatch(r'\[[^\]\s]{1,6}\]', r['t'].strip())
                    else r for r in runs[1:]]                        # (a mark inside a note: a note of the other series, a reviser's note)
            if rest:
                rest[0] = dict(rest[0], t=rest[0]['t'].lstrip(' \u3000'))
                if fmt == 'zhu':
                    rest[0] = dict(rest[0], t=re.sub(r'^[：:][\s\u3000]*', '', rest[0]['t']))     # '註9：text'
                rest = [r for r in rest if r['t'] or r.get('i')]
            st = 'notel' if latin_ratio(rest) > 0.4 else 'note'
            out.append(dict(k='p', style=st, runs=merge_runs(marks + rest), **({'id': it['id']} if it.get('id') else {})))
            # (the entry's own id: book 59's source notes are linked to their paragraphs, not to their labels)
        else:
            out.append(dict(k='p', style='notecap' if it.get('notecap') else 'notec', runs=runs))   # (a figure's caption: centred)
    return out


def notes_module(mid, groups, fmt, zone='body', title='注　释', toc_level=2, toc_title='注释'):
    blocks = [dict(k='h', style='h1', rank=1, runs=[run(title)], id=mid + '#top')]
    for gtitle, items in groups:
        if len(groups) > 1 and gtitle and gtitle != title:      # (the notes before the first group heading: no second title)
            blocks.append(dict(k='p', style='idxhead', runs=[run(gtitle)], nostart=False))
        blocks += note_blocks(items, fmt)
    return Mod(mid=mid, zone=zone, title=toc_title, blocks=blocks, grid='small1', toc_level=toc_level, toc_title=toc_title)


def index_module(C, n):
    """The ebook's index: letter heads, entries ('English words 中文词，12，34ff') and sub-entries (lower-case English)
    with hanging indents, in two columns of the small grid.  The ebook breaks several entries inside one paragraph with
    <br>: one block per entry.  C['index_map']: the printed page numbers are converted to pages of this PDF (exact,
    from the markers of the printed pages kept in the text: indexmap.resolve_markers)."""
    blocks, hn = [], 0
    for it in BE.items(P(n)):
        if it['k'] == 'h':
            blocks.append(dict(k='h', style='h1', rank=1, runs=[run(plain(it['runs']))], id=f'{P(n)}#top'))
            hn = len(blocks)
            continue
        if it['k'] != 'p' or not it.get('runs'):
            continue
        lines = [[]]
        for r in BT.fix_runs(_img_text(C, it['runs'])):
            if r['t'] == BR:
                lines.append([])
            else:
                lines[-1].append(r)
        for rs in lines:
            rs = [dict(r, t=r['t'].replace('\xa0', ' ')) for r in rs]
            rs = BT.fix_edges(merge_runs(rs))
            t = plain(rs)
            if not t:
                continue
            if t.startswith('（') and len(blocks) == hn:
                blocks.append(dict(k='p', style='idxnote', runs=rs, id=it['id']))     # the line under the title
                hn = len(blocks)
            elif re.fullmatch(r'[A-Z]', t):
                blocks.append(dict(k='p', style='idxhead', runs=rs, id=it['id']))
            elif t[0].islower() or t.startswith('—'):            # (a sub-entry: lower-case English, or '—term' under the entry)
                blocks.append(dict(k='p', style='indexc', runs=rs, id=it['id'], first=-1, left=2))
            else:
                blocks.append(dict(k='p', style='index', runs=rs, id=it['id']))
    imap = dict(markers=C['index_map'], series={'': []}) if C.get('index_map') else None
    title = plain(blocks[0]['runs']) if blocks and blocks[0]['k'] == 'h' else '索引'
    mod = Mod(mid=P(n), zone='back', title=title, blocks=blocks, grid='small2', header_n=hn, idxmap=imap)
    mod.top = True
    mod.unnest = True
    mod.src_parts = [n]
    return mod


def renumber(els, notes):
    """The ebooks restart note numbers in every file: number the notes of a unit 1.. in the order of their marks."""
    anchors, lead, cur = {}, [], None
    for it in notes:
        r0 = it['runs'][0] if it.get('runs') else {}
        if r0.get('a'):
            cur = anchors[r0['a']] = [it]
        elif cur is not None:
            cur.append(it)                                   # a note's further paragraphs (and tables) stay with it
        else:
            lead.append(it)
    order = {}
    for e in els:
        for r in e.get('runs') or []:
            if r.get('h') in anchors and not r.get('i') and r['h'] not in order:
                order[r['h']] = len(order) + 1
    for a in anchors:
        order.setdefault(a, len(order) + 1)                      # notes without a mark keep their place at the end
    els = [dict(e, runs=[dict(r, t=str(order[r['h']])) if r.get('h') in anchors and not r.get('i') else r for r in e['runs']])
           if e.get('runs') else e for e in els]
    out = []
    for a, (it, *more) in anchors.items():
        out.append((order[a], [dict(it, runs=[dict(it['runs'][0], t=str(order[a]))] + it['runs'][1:])] + more))
    return els, lead + [it for _, g in sorted(out, key=lambda x: x[0]) for it in g]


# ---------------------------------------------------------------------------------------------- pages
def copyright_module(n, skip=0, C=None):
    blocks = [dict(k='space', style='cip', runs=[], n=(C or {}).get('copyright_top', 4))]
    items, raw = [], []
    for k_, n_ in enumerate(_parts(n)):                          # (several parts: the CIP page and the original's rights page)
        if k_:
            raw.append(dict(k='gap'))
        raw += BE.items(P(n_))[skip if k_ == 0 else 0:]
    for it in raw:
        if it['k'] == 'table':                                  # (book 16: the publisher's lines are a table) one line per row
            for row in it['rows']:
                cells = [plain(c) for c in row if plain(c)]
                if cells:
                    items.append(dict(k='p', runs=[run('　'.join(cells))]))
        else:
            items.append(it)
    for it in items:
        if it['k'] == 'gap':
            blocks.append(dict(k='space', style='cip', runs=[], n=1))
            continue
        if it['k'] == 'img' and C and C.get('copyright_imgs') and it['src'] in C['copyright_imgs']:
            w = C['copyright_imgs'][it['src']]                    # a small picture of the page (a fund's mark), its width in pt
            from PIL import Image
            iw, ih = Image.open(os.path.join(special.IMG_DIR, it['src'])).size
            pitch = style.TEXT_H / style.SMALL_N
            blocks.append(dict(k='img', style='orn', runs=[], src=special.img_url(it['src']), w=w, h=w * ih / iw,
                               n=math.ceil(w * ih / iw / pitch) + 1))
            continue
        if it['k'] != 'p':
            continue
        runs = BT.fix_edges(BT.fix_runs(_img_text(C, it['runs']) if C else it['runs']))
        if not runs:
            continue
        t = plain(runs)
        runs = [dict(r, t=re.sub(r'(?<=[A-Z\d])-(?=\d)', '-⁠', r['t'])) for r in runs]
        if t.startswith(('图书在版编目', '版权信息')) or any(r.get('b') for r in runs) and len(t) < 8:
            runs = [dict(r, b=1) for r in runs]
            if len(blocks) > 1:
                blocks.append(dict(k='space', style='cip', runs=[], n=1))
        blocks.append(dict(k='p', style='cipj' if len(t) > 40 else 'cip', runs=runs, novary=True))
    return Mod(mid='copyright', zone='front', title='版权页', blocks=blocks, grid='small1', toc=False, head=False,
               folio=False, single=True)


def part_first_img(n):
    for it in BE.items(P(n)):
        if it['k'] == 'img':
            return it['src']
    raise KeyError(n)


def qr_html(imgs, w=130.0):
    """Publisher's QR codes of the last page (kept from the ebook): the images side by side (each w pt wide)."""
    from PIL import Image
    out = ''
    gap = 34.0
    x0 = (style.PAGE_W - len(imgs) * w - (len(imgs) - 1) * gap) / 2
    for k, name in enumerate(imgs):
        iw, ih = Image.open(os.path.join(special.IMG_DIR, name)).size
        h = w * ih / iw
        out += (f'<img src="{special.img_url(name)}" style="position:absolute;left:0;top:0;width:{w}pt;height:{h:.1f}pt;'
                f'transform:translate({x0 + k * (w + gap):.1f}pt,{style.TOP + 60 * style.SY:.1f}pt)">')
    return out


# ---------------------------------------------------------------------------------------------- book
def _parts(x):
    return list(x) if isinstance(x, (list, tuple)) else [x]


def short_right(items, max_len):
    """Short lines that are no sentences (a name, a title, 'author of …') set flush right; a blank line before the next
    paragraph of text after them."""
    out, prev = [], False
    for it in items:
        t = plain(it.get('runs') or []).strip()
        sh = it['k'] == 'p' and t and len(t) <= max_len and t[-1] not in '。！？…”' and not all(r.get('b') for r in it['runs'] if r['t'].strip())
        if it['k'] == 'p' and t and not sh and prev:
            out.append(dict(k='p', cls='', id='', runs=[], blank=1))
        out.append(dict(it, cls=(it.get('cls', '') + ' short_right').strip()) if sh else it)
        prev = bool(sh)
    return out


def part_divider(C, els):
    """A heading 'Part N' (+ sub-title lines that follow it) that becomes a page of its own: (lines, toc title, remaining elements)."""
    pr = re.compile(C.get('part_re') or PART_RE.pattern)
    if not (els and els[0]['k'] == 'h' and pr.match(plain(els[0]['runs']))):
        return None
    head = plain(regap_heading(els[0]['runs']))
    rest = els[1:]
    m = re.match(C['part_split'], head) if C.get('part_split') else None
    if not m:
        return [(1.0, head)], head, rest
    lines = [(1.0, m.group(1))]
    title = m.group(1)
    if m.group(2):
        lines.append((2.0, m.group(2)))
        title += '　' + m.group(2)
    if m.lastindex and m.lastindex >= 3 and m.group(3):
        lines.append((3.0, m.group(3)))                          # an English sub-title line (page only, not in the contents)
    sub = _cs(C, 'part_sub_cls')
    while rest and rest[0]['k'] == 'p' and set(rest[0]['src'][2:].split()) & sub:
        t_, mk = '', []                                           # (book 55: note marks inside the lines: linked on the page,
        for r in rest[0]['runs']:                                 #  a placeholder in the text until divider_html sets them)
            if r.get('s') and r.get('h') and not r.get('i'):
                t_ += f'\ue000{len(mk)}\ue001'
                mk.append((r['t'].strip(), r['h'], r.get('a', '')))
            elif not r.get('i'):
                t_ += r['t']
        lines.append((3.0, t_, mk) if mk else (3.0, t_))
        if not C.get('part_sub_notoc') and (not C.get('part_sub_toc') or re.search(C['part_sub_toc'], t_)):
            title += '　' + re.sub('\ue000\\d+\ue001', '', t_)   # (part_sub_toc: only the lines naming the part, book 55)
        rest = rest[1:]
    if C.get('part_img') and rest and rest[0]['k'] == 'fig':      # the picture of the part page (book 16)
        lines.append((98, rest[0]['src']))
        rest = rest[1:]
    if C.get('part_list') and rest and rest[0]['k'] == 'h' and re.match(C['part_list'], plain(rest[0]['runs'])):
        lines.append((95, plain(rest[0]['runs'])))                # (book 59) '精彩内容：' and the topics of the part, on its page
        rest = rest[1:]
        while rest and rest[0]['k'] == 'p':
            lines.append((94, plain(rest[0]['runs'])))
            rest = rest[1:]
    epi = _cs(C, 'part_epi_cls')                                  # the epigraph of the part, set small under the title
    if epi and rest and rest[0]['k'] == 'p' and set(rest[0]['src'][2:].split()) & epi:
        lines.append((97, ''))
        while rest and rest[0]['k'] == 'p' and set(rest[0]['src'][2:].split()) & epi:
            rs = rest[0]['runs']
            if set(rest[0]['src'][2:].split()) & _cs(C, 'part_epi_right'):
                lines.append((93, plain(rs)))                    # (books 41–58) the name under the epigraph, flush right
            elif C.get('part_epi_para'):
                mk = []
                while rs and rs[-1].get('s') and rs[-1].get('h'):   # the note mark at its end: a link on the page, the note's
                    mk.insert(0, (rs[-1]['t'].strip(), rs[-1]['h'], rs[-1].get('a', '')))   # back-link lands there
                    rs = rs[:-1]
                lines.append((96, plain(rs), mk) if mk else (96, plain(rs)))     # (96: a paragraph, justified)
            else:
                lines.append((99, plain(rs)))
            rest = rest[1:]
    return lines, title, rest


def book(b):
    global CIRC_LINK, PAGE_ANCHOR, MARK_LABEL
    C = CFG[b]
    CIRC_LINK = C.get('circ_link')
    PAGE_ANCHOR = C.get('page_anchor')
    MARK_LABEL = C.get('mark_label')
    m = meta(b)
    cover = C['cover']
    if C.get('cover_file'):                                          # a cover image supplied separately (source/covers/…) replaces the ebook's
        src = os.path.join(style.ROOT, C['cover_file'])
        cover = 'cover_custom' + os.path.splitext(src)[1]
        dst = os.path.join(special.IMG_DIR, cover)
        if not os.path.exists(dst) or os.path.getmtime(dst) < os.path.getmtime(src):
            shutil.copy(src, dst)
    mods = [page_module('cover', 'cover', special.cover_html(cover), folio=False)]
    for k_, im in enumerate(C.get('front_flaps', ())):             # the flap of the cover (the author's biography): a page image
        mods.append(page_module(f'flap{k_}', 'cover', special.cover_html(im), folio=False))
    if C['title_img']:
        mods.append(page_module('title', 'front', special.cover_html(C['title_img']), folio=False))
    else:
        mods.append(page_module('title', 'front', special.title_html(m), folio=False))
    if C.get('copyright_img'):
        mods.append(page_module('copyright', 'front', special.cover_html(C['copyright_img']), folio=False))
    elif C.get('copyright') is not None:
        mods.append(copyright_module(C['copyright'], C.get('copyright_skip', 0), C))
    fig_list = []
    plate_set = plate_figs(C) if C.get('fig_inline') else set()

    def fig_no(src, cap, ids=()):
        fig_list.append((src, cap, tuple(ids)))
        return len(fig_list)

    front, body, back = [], [], []
    pend, pend_chars = [], 0
    counter = [0]
    fmt = C['marker']

    def flush(zone_list, zone):
        nonlocal pend, pend_chars
        if pend:
            counter[0] += 1
            zone_list.append(notes_module(f'notes{counter[0]}', pend, fmt, zone=zone, title=C.get('notes_title', '注　释'),
                                          toc_title=C.get('notes_toc', '注释'), toc_level=1 if C.get('notes_end') else 2))
            pend, pend_chars = [], 0

    def gather(ns, kaitext=False):
        els, notes = [], []
        for n in _parts(ns):
            its = BE.items(P(n))
            if n in C.get('short_right', {}):                     # (book 26) the names and titles under endorsements and prefaces
                its = short_right(its, C['short_right'][n])
            e, nt = elements(C, its, kaitext=kaitext)
            if n in C.get('insert_head', {}):                     # (book 35) a part with no heading of its own: the name the ebook's contents give it
                e = [dict(k='h', lvl=1.0, runs=[run(C['insert_head'][n])], id=P(n) + '#head', src='insert_head', cls='')] + e
            els += e
            notes += nt
        return els, notes

    def add_unit(ns, zone_list, zone, els, notes, top=False, kaitext=False, toc=True, title_over=None, mid=None):
        nonlocal pend_chars
        n = _parts(ns)[0]
        if C.get('renum') and notes:
            els, notes = renumber(els, notes)
        els = fig_inline(C, els) if C.get('fig_inline') else fig_paragraphs(C, els, fig_no)
        blocks = []
        osz = C.get('orn_size', (70.0, 9.9))
        for e in unit_blocks(els):
            if e['k'] == 'fig' and C.get('fig_inline'):
                blocks += fig_plate_ref(e, fig_no) if e['src'] in plate_set else fig_block(C, e, fmt)
            elif e['k'] == 'fig':
                blocks += image_blocks(e['src'], style.TEXT_H - 11 * style.LINE, max_scale=C.get('img_max_scale'))      # leaves room for the heading above and a source line below
            elif e['k'] == 'orn':
                blocks += [dict(k='img', style='orn', runs=[], src=special.img_url(e['src']), w=osz[0], h=osz[1],
                                n=math.ceil(osz[1] / style.LINE))]
            elif e['k'] == 'table' and C.get('table2'):
                tb = table_blocks2(e['rows'], e.get('spans') or [[1] * len(r) for r in e['rows']], e.get('heads'))
                for x in tb:
                    x['nofloat'] = 1                                # (a floating figure lands before the table or on its first page)
                small = C.get('table_keep') and len(tb) <= C['table_keep']
                if small:
                    for x in tb[:-1]:
                        x['keep'] = 1                               # a small table is not split over two pages
                if blocks and blocks[-1].get('style') in ('cap', 'ck') and (small or C.get('table_head_keep')):
                    blocks[-1].update(keep=1, before=tb[0].get('before', 0), nomerge=True, nofloat=1)   # its title above it, kept with it
                    tb[0]['before'] = 0
                blocks += tb
            elif e['k'] == 'table':
                blocks += table_blocks(e['rows'], C.get('table_head', True))
            else:
                blocks.append(e)
        if len(blocks) > 1 and blocks[0].get('plate_ref') and blocks[1]['k'] == 'h':
            blocks[:2] = blocks[1::-1]                             # (a plate reference does not open a chapter: it goes under the title)
        blocks = wrap_lines(finish_blocks(blocks))
        if C.get('open_air'):                                      # the text under a chapter title may start one line lower,
            two = C['open_air'] >= 2                               # (open_air=2, 3: up to two, three lines)
            for j in range(len(blocks) - 1):                       # when that spares a page with an empty foot
                if blocks[j]['k'] == 'h' and blocks[j].get('style') == 'h1':
                    if blocks[j + 1]['k'] == 'p' and not blocks[j + 1].get('before'):
                        c1, c2 = C.get('open_air_cost', (60.0, 150.0))     # (book 39: cheaper than a paragraph's first line at a page foot)
                        blocks[j + 1]['bef_opts'] = [(0, 0.0), (1, c1), (2, c2), (3, 300.0)][:int(C['open_air']) + 1]
                    break
            for j, x in enumerate(blocks):                         # and an epigraph's '——name' may stand one line below it
                after_epi = C.get('epi_name_air') and j and blocks[j - 1].get('style') in ('kaibody', 'quote', 'verse')   # (book 34: names without '——')
                if x['k'] == 'p' and x.get('style') == 'right' and (plain(x.get('runs', [])).startswith('——') or after_epi) \
                        and not x.get('before'):
                    k_ = j
                    while after_epi and k_ + 1 < len(blocks) and blocks[k_ + 1].get('style') == 'right':
                        k_ += 1                                    # (the name's further lines: the air goes below them all)
                    nx = blocks[k_ + 1] if k_ + 1 < len(blocks) else {}
                    if not two:
                        x['bef_opts'] = [(0, 0.0), (1, 30.0)]
                    elif nx.get('k') == 'p' and nx.get('style') == 'body' and not nx.get('before') and not nx.get('bef_opts'):
                        nx['bef_opts'] = [(0, 0.0), (1, 10.0), (2, 25.0)]   # (open_air=2: the name under its quotation, the air below the pair)
        if C.get('orn_air'):                                       # (book 35) a list of entries each under a small picture: a blank
            for j, x in enumerate(blocks):                         # line before each entry, which the page breaks may drop or double
                if j and x['k'] == 'img' and x.get('style') == 'orn':
                    x['bef_opts'] = [(1, 0.0), (0, 20.0), (2, 20.0)]
        for x in blocks:
            if x['k'] in ('p', 'h') and x.get('runs'):
                x['runs'] = mark_runs(url_runs(x['runs']) if C.get('url_break') else x['runs'], fmt)
            if C.get('name_dot') and x['k'] == 'p' and x.get('runs'):
                x['runs'] = dot_runs(x['runs'])
            if C.get('sup_join') and x['k'] == 'p' and x.get('runs'):
                x['runs'] = sup_runs(x['runs'])
            if C.get('tail_join') and x['k'] == 'p' and x.get('runs'):
                x['runs'] = tail_runs(x['runs'])
        if C.get('note_plates'):                                   # (book 43) a note's table (a picture) that would leave a page
            out_ = []                                              # foot empty: at the back, a plate of its own; in the note
            for it in notes:                                       # 'see plate N', linked both ways
                if it['k'] == 'img' and it['src'] in C['note_plates']:
                    k_ = fig_no(it['src'], '', ())
                    it = dict(k='note', id='', notecap=True, runs=[run(f'（见书后插图{k_}）', h=f'plate-{k_}', a=f'figref-{k_}', c='fig')])
                out_.append(it)
            notes = out_
        if C.get('url_break'):
            notes = [dict(it, runs=url_runs(it['runs'])) for it in notes]
        if C.get('name_dot'):
            notes = [dict(it, runs=dot_runs(it['runs'])) for it in notes]
        if C.get('sup_join'):
            notes = [dict(it, runs=sup_runs(it['runs'])) for it in notes]
        if C.get('tail_join'):
            notes = [dict(it, runs=tail_runs(it['runs'])) for it in notes]
        title = next((title_text(x['runs']) for x in blocks if x['k'] == 'h'), '')     # no heading (a statement page): no bookmark
        if title_over is not None:
            title = title_over                                     # (part_intro: the part's title for the running head)
        if C.get('head_split_join') is not None:
            title = title.replace(C['head_split'], C['head_split_join'])     # (contents, bookmark, running head: one line)
        if C.get('head_split'):                                    # 'Title／Sub-title' chapter headings: the sub-title on a line of its own
            for x in blocks:
                if x['k'] == 'h' and x.get('style') == 'h1' and any(C['head_split'] in r['t'] for r in x['runs']):
                    out = []
                    for r in x['runs']:
                        parts = r['t'].split(C['head_split'])
                        for k, t in enumerate(parts):
                            if k:
                                out.append(run('\n'))
                            if t:
                                out.append(dict(r, t=t))
                    if C.get('head_split_balance'):          # each line balanced by itself ('Chapter 3' / a long title in two lines)
                        segs, cur = [], []
                        for r in out + [run('\n')]:
                            if r['t'] == '\n':
                                segs.append(cur)
                                cur = []
                            else:
                                cur.append(r)
                        out = []
                        for k, seg in enumerate(segs):
                            if k:
                                out.append(run('\n'))
                            out += normalize.balance_title(merge_runs(seg), 17.0, C.get('head_split_width', 294)) if seg else []
                    x['runs'] = out
                    x['nobalance'] = True
        keep = [x for x in blocks if x.get('nobalance')]
        saved = [x['runs'] for x in keep]
        blocks = balance_headings(blocks)
        for x, r in zip(keep, saved):
            x['runs'] = r
        for x in blocks:
            if x['k'] == 'h':
                rs = x['runs']
                for i in range(len(rs) - 1):
                    if rs[i]['t'] == '\n' and rs[i + 1].get('s'):
                        rs[i], rs[i + 1] = rs[i + 1], rs[i]
        mod = Mod(mid=mid or P(n), zone=zone, title=title, blocks=blocks, toc_level=1, toc=toc and any(x['k'] == 'h' for x in blocks))
        mod.src_part = n
        mod.src_parts = _parts(ns)
        mod.top = top
        mod.nobm = title_over is not None
        mod.unnest = zone == 'back'
        zone_list.append(mod)
        if notes:
            pend.append((title, notes))
            pend_chars += sum(len(runs_text(i['runs'])) for i in notes)

    for n, kind in C['front']:
        els, notes = gather(n, kaitext=(kind == 'kaitext'))
        if kind == 'dedication':
            lines = [(99, plain(e['runs'])) for e in els if e['k'] == 'p']
            dm = page_module('dedication' if not any(x.mid == 'dedication' for x in front) else f'dedication{n}', 'front',
                             special.divider_html(lines, grid=C.get('dedication_grid', False)), toc=False, title='献词', folio=False,
                             head=False)
            dm.lines = [t for _, t in lines]
            dm.src_parts = _parts(n)
            front.append(dm)
            continue
        if kind == 'board':                                        # (books 41–58) a series' editorial board: its title and its lines
            def _bt(rs):                                           # ('<b>主编</b> 冯隆灏': the space the ebook has between the
                out = ''                                           #  bold label and the name, which the text model drops)
                for k_, r in enumerate(rs):
                    if k_ and bool(r.get('b')) != bool(rs[k_ - 1].get('b')) and out[-1:].strip() and r['t'][:1] not in ' 　（(':
                        out += '\u3000'
                    out += r['t']
                return out
            lines = [(2.0 if e['k'] == 'h' else 99, _bt(e['runs'])) for e in els if e['k'] in ('h', 'p')]   # centred, a page
            if lines and lines[0][0] != 2.0:
                lines[0] = (2.0, lines[0][1])                      # (no heading: the first line is the title)
            bm = page_module(f'board{n}', 'front', special.divider_html(lines, snap=True), toc=False, title=lines[0][1], folio=False, head=False)
            bm.lines = [t for _, t in lines]
            bm.src_parts = _parts(n)
            front.append(bm)
            continue
        if kind == 'figure':                                       # a picture that is a page by itself (frontispiece), caption under it
            front += figure_pages(n, els)
            continue
        if kind == 'kaibody':                                      # a whole page in the ebook's Kai type: full-width Kai body text
            els = [dict(e, style='kaibody') if e['k'] == 'p' and e.get('style') in ('quote', 'body') else e for e in els]
        if kind == 'plain':                                        # (books 49–58) a preface the ebook sets in its quotation class
            els = [dict(e, style='body') if e['k'] == 'p' and e.get('style') == 'quote' else e for e in els]   # throughout: body text
        add_unit(n, front, 'front', els, notes, top=True, kaitext=(kind == 'kaitext'))
        if C.get('front_notes_each'):
            flush(front, 'front')                                  # (the notes of a preface right after it, not after the next one)
    if C.get('notes_end') != 'all':
        flush(front, 'front')                                      # (notes_end='all': the front matter's notes join the others)
    entries = []                                                   # (book 53) a part holding several chapters: one unit per
    for n in C['body']:                                            # chapter (split before its heading), each with its notes
        if isinstance(n, int) and n in C.get('split_heads', {}):
            sh_ = C['split_heads'][n]                              # (a pattern of the heading's text, or its level: book 56)
            hit = (lambda it: it['lvl'] == sh_) if isinstance(sh_, int) else (lambda it, p_=re.compile(sh_): p_.match(plain(it['runs'])))
            chunks = [[]]
            for it in BE.items(P(n)):
                if it['k'] == 'h' and hit(it) and any(x['k'] in ('p', 'h') for x in chunks[-1]):
                    chunks.append([])
                chunks[-1].append(it)
            entries += [(n, f'#u{k_}' if k_ else '', ch) for k_, ch in enumerate(chunks)]
        else:
            entries.append((n, '', None))
    for n, sfx, chunk in entries:
        els, notes = gather(n) if chunk is None else elements(C, chunk)
        plates = []
        if isinstance(n, int) and n in C.get('insert_plates', {}):                       # (book 33) a plate section bound inside a chapter: its pictures
            runs_, cur = [], []                                    # (the longest run of pictures and captions) set after the chapter,
            for k_, e in enumerate(els + [dict(k='end')]):        # a picture a page, its title on the first
                if e['k'] == 'fig' or cur and e['k'] == 'p' and e.get('style') == 'cap':
                    cur.append(k_)
                else:
                    if cur:
                        runs_.append(cur)
                    cur = []
            ks = max(runs_, key=lambda r: sum(els[k_]['k'] == 'fig' for k_ in r))
            plates = [dict(k='h', lvl=1.0, runs=[run(C['insert_plates'][n])], id=f'{P(_parts(n)[0])}#plates', src='insert_plates', cls='')]
            plates += [els[k_] for k_ in ks]
            els = [e for k_, e in enumerate(els) if k_ not in set(ks)]
        pd = part_divider(C, els)
        if pd:
            lines, title_s, els = pd
            n0 = _parts(n)[0]
            mk_out = []
            dh = special.divider_html(lines, snap=C.get('part_grid', False), marks_out=mk_out)
            if mk_out:                                             # (the epigraph's note marks: their anchors on this page)
                def dh(builder, page, _h=dh, _m=tuple(mk_out)):
                    for a_, y_ in _m:
                        builder.anchors.setdefault(a_, (page.index, y_))
                    return _h
            div = page_module(f'div{n0}{sfx}', 'body', dh, toc=True, toc_title=title_s,
                              toc_level=0, title=title_s, folio=False, head=False)
            div.part = True
            div.lines = [re.sub('\ue000\\d+\ue001', '', x[1]) for x in lines if x[0] != 98]
            div.src_parts = _parts(n)
            if not C.get('notes_end'):
                flush(body, 'body')
            body.append(div)
        pd2 = part_divider(dict(C, part_re=C['part_re2'], part_split=C.get('part_split2'), part_epi_cls=(), part_list=None), els) \
            if C.get('part_re2') else None
        if pd2:                                                    # (book 48) the parts of a part ('第二卷' > '第一部分'): a page
            lines2, title2, els = pd2                              # of their own, smaller, one level down in the contents
            lines2 = [(x[0] + 1.0, x[1]) for x in lines2]
            n0 = _parts(n)[0]
            div2 = page_module(f'div{n0}b{sfx}', 'body', special.divider_html(lines2), toc=True, toc_title=title2, toc_level=0,
                               title=title2, folio=False, head=False)
            div2.part = True
            div2.part2 = True
            div2.lines = [x[1] for x in lines2]
            div2.src_parts = [] if pd else _parts(n)
            if not C.get('notes_end') and not pd:
                flush(body, 'body')
            body.append(div2)
        if pd or pd2:
            if not els:
                if notes:                                          # (book 55) the notes of the part page's own lines
                    pend.append((title_s if pd else title2, notes))
                    pend_chars += sum(len(runs_text(i['runs'])) for i in notes)
                continue
            if C.get('part_intro') and els[0]['k'] != 'h':          # (book 40) the part's introduction after its page: not an entry of
                add_unit(n, body, 'body', els, notes, toc=False, title_over=title_s if pd else title2, mid=P(n) + sfx if sfx else None)    # its own (its sub-titles are not chapters)
                if pend_chars >= NOTE_MIN and not C.get('notes_end'):
                    flush(body, 'body')
                continue
        add_unit(n, body, 'body', els, notes, top=n in C.get('part_top', ()), mid=P(n) + sfx if sfx else None)
        if n in C.get('part_top', ()):                             # (books 50, 54…) a chapter after a part that is not inside it
            body[-1].unnest = True
        if pend_chars >= NOTE_MIN and not C.get('notes_end'):
            flush(body, 'body')
        if plates:
            body += figure_pages(f'{_parts(n)[0]}x', plates, zone='body')
    if C.get('notes_end') != 'all':
        flush(body, 'body')                                        # (notes_end: the few notes of all chapters in one module here)
    for n in C['back']:
        kind = 'text'
        if isinstance(n, tuple):
            n, kind = n
        els, notes = gather(n)
        if kind == 'figpages':                                     # pictures one to a page (a facsimile), the title on the first
            flush(back, 'back')
            if C.get('figpage_each'):                              # (one part per page, its label before the picture)
                for p_ in _parts(n):
                    e_, _ = gather(p_)
                    back += figure_pages(p_, e_, zone='back', ids=(P(p_),), cap_before=True)
            else:
                back += figure_pages(n, els, zone='back', notes=notes)
            continue
        if kind == 'notes':                                        # the ebook's own collection of notes (the translator's), in its place
            flush(back, 'back')
            title = next((plain(it['runs']) for it in BE.items(P(n)) if it['k'] == 'h'), '注释')
            groups, gcls = [], _cs(C, 'note_group_cls')            # (headings of its own between the notes: one group per part of the book)
            for it in BE.items(P(n)):
                if it['k'] == 'p' and set(it['cls'].split()) & gcls or C.get('note_group_h') and it['k'] == 'h' \
                        and (it['lvl'] > 1 or C['note_group_h'] == 'all') or C.get('note_group_re') and it['k'] == 'p' \
                        and re.match(C['note_group_re'], plain(it['runs'])):   # (book 31: <h3> headings; book 33: '第一章　…' paragraphs)
                    groups.append((_head_sub(C, [run(plain(regap_heading(it['runs'])))])[0]['t'], []))
                elif it['k'] in ('p', 'note') and it.get('runs'):
                    if not groups:                                 # (book 33: the note on the sources before the first chapter's)
                        groups.append(('' if C.get('note_group_re') else title, []))
                    runs_ = _img_text(C, it['runs'])
                    if C.get('url_break_back'):
                        runs_ = url_runs(runs_)                    # (book 59: the web addresses of the ebook's own notes part)
                    if C.get('name_dot'):
                        runs_ = dot_runs(runs_)
                    if C.get('sup_join'):
                        runs_ = sup_runs(runs_)
                    groups[-1][1].append(dict(it, k='note', runs=latin_runs(runs_, whole=False) if C.get('lat_apos') else runs_))
            nm = notes_module(f'notes_p{n}', groups, fmt, zone='back', title=C.get('endnotes_title', title),
                              toc_level=1, toc_title=C.get('endnotes_title', title))
            nm.top = True
            nm.unnest = True
            nm.src_parts = [n]
            back.append(nm)
            continue
        if kind == 'index':                                        # an index in two columns, its page numbers turned into pages of this PDF
            flush(back, 'back')
            back.append(index_module(C, n))
            continue
        if kind == 'pagelinks':                                    # a list of links to the printed pages (bare numbers, not note marks)
            els = [dict(e, runs=[dict(r, c=_cls_add(r.get('c'), 'nomark')) if r.get('h') else r for r in e['runs']])
                   if e['k'] == 'p' else e for e in els]
            if C.get('pagelinks_note'):
                k = next(i for i, e in enumerate(els) if e['k'] == 'p')
                els.insert(k + 1, dict(k='p', style='small', first=0, left=0, runs=[run(C['pagelinks_note'])], id='', src='pdf_note',
                                       nomerge=True))
        if kind == 'noindent':
            els = [dict(e, style='noindent') if e['k'] == 'p' and e.get('style') == 'body' else e for e in els]
        if kind == 'hang':                                         # a list of references set as body paragraphs: hanging indent
            els = [dict(e, style='noindent', first=-2, left=2) if e['k'] == 'p' and e.get('style') == 'body' else e for e in els]
        if kind == 'kaibody':
            els = [dict(e, style='kaibody') if e['k'] == 'p' and e.get('style') in ('quote', 'body') else e for e in els]
        add_unit(n, back, 'back', els, notes, top=True)
        if C.get('notes_end') != 'all':
            flush(back, 'back')
    if C.get('notes_end') == 'all':
        flush(back, 'back')                                        # (notes_end='all': the notes of the front matter and the text, last)
    for n in C.get('endnotes', ()):                            # notes of the whole book gathered in the last part of the ebook
        notes = [dict(it, k='note') for it in BE.items(P(n)) if it['k'] in ('p', 'note') and it.get('runs')]     # (continuation paragraphs too)
        if notes:
            nm = notes_module('notes_end', [(C['endnotes_title'], notes)], fmt, zone='back', title=C['endnotes_title'],
                              toc_level=1, toc_title=C['endnotes_title'])
            nm.top = True
            nm.unnest = True
            back.append(nm)
    plates = plate_modules(fig_list, PLATES_NOTE_INLINE if C.get('fig_inline') else PLATES_NOTE)
    allm = front + body + back + plates
    toc_bl = toc_blocks(allm, '目　錄' if C.get('tc') else '目　录', sections=C.get('toc_sections', True))
    by_mid = {m_.mid: m_ for m_ in allm}
    for x in toc_bl:                                               # (book 32: 'CO₂' in a section title keeps its subscript)
        if x.get('toc_ref') and x['toc_ref'][1] is not None:
            x['runs'] = toc_runs(by_mid[x['toc_ref'][0]].blocks[x['toc_ref'][1]]['runs'], x['h'])
    for x in toc_bl:
        if x.get('style', '').startswith('toc'):
            x['noshrink'] = True
            if C.get('toc_even'):
                x['nosplit'] = True                                # (an entry of two lines is not split over two pages)
    if C.get('toc_even'):                                          # even spacing: fixed blank lines (one before a part, and where
        zone_of = {m.mid: m.zone for m in allm}                    # the front matter, the text and the back matter begin), none else
        prev = None
        for x in toc_bl:
            if x['k'] != 'p' or not x.get('toc_ref'):
                continue
            z = zone_of.get(x['toc_ref'][0])
            if x['style'] == 'toc0':
                n_ = 1
            elif x['style'].startswith('toc1'):
                n_ = 1 if prev is not None and z != prev else (0 if not C.get('toc_sections', True) else 1)
            else:
                n_ = 0
            x['before'] = n_
            x['bef_opts'] = [(n_, 0.0)]
            x['toc_even'] = True                                   # (render: a page that ends short is not spread)
            prev = z
    toc = Mod(mid='toc', zone='front', title='目錄' if C.get('tc') else '目录', blocks=toc_bl, toc=False, head=True)
    toc.tail_min = 5
    tail = []
    if C['tail']:
        tail.append(page_module('qr', 'back', qr_html(C['tail'], C.get('tail_w', 130.0)), folio=False))
    for k_, im in enumerate(C.get('back_flaps', ())):              # the back flap, before the back cover
        tail.append(page_module(f'bflap{k_}', 'back', special.cover_html(im), folio=False))
    if C.get('backcover'):
        tail.append(page_module('backcover', 'back', special.cover_html(C['backcover']), folio=False))
    mods += [toc] + allm + tail
    if C.get('notel_vary'):                                        # (book 32: chapters of notes that are mostly references, set
        for m_ in mods:                                            #  ragged: the letter-spacing steps too, or a page cannot be filled)
            for x in getattr(m_, 'blocks', None) or ():
                if x.get('style') == 'notel':
                    x['vary'] = True
    return dict(id=f'b{b}', title=C['title'], meta=dict(m, author=C['pdf_author']), modules=mods, toc=toc, vol=b)
