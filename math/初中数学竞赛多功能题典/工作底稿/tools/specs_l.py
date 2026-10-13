# absolute-value bars: the closing bar was set as an opening symbol, so no space
# separated it from the following sign ("|x - 5|-|2x - 3|< 1"); set as ordinary bars
E = [(r'\lvert ', '|', 'all')]
SYS = r'\left\{\begin{array}{@{}>{\displaystyle}c@{}}%s\end{array}\right.'
SPECS = [
 dict(page=104, id='5.12(1)', y=260.59, top=270, bot=252, edits=E),
 dict(page=104, id='5.12(2)', x=78.510, y=242.29, top=251, bot=233, edits=E),
 dict(page=104, id='5.13', y=82.29, top=94, bot=73, edits=E),
 dict(page=105, id='5.14', y=758.89, top=771, bot=750, edits=E),
 dict(page=105, id='5.15', y=598.89, top=611, bot=590, edits=E),
 dict(page=105, id='5.17', kind='disp', region=(220, 185, 400, 250),
      tex_old=SYS % r'x^2+2x-35>0,\\\lvert x-2\lvert <10.',
      tex_new=SYS % r'x^2+2x-35>0,\\|x-2|<10.'),
 dict(page=105, id='5.16', x=78.510, y=420.59, top=430, bot=412, edits=E),
 dict(page=106, id='5.18', y=758.89, top=771, bot=750, edits=E),
 dict(page=106, id='5.19', y=598.89, top=611, bot=590, edits=E),
 dict(page=106, id='5.20', y=438.89, top=451, bot=430, edits=E),
 dict(page=106, id='5.21', y=278.89, top=291, bot=270, edits=E),
 dict(page=106, id='5.22', y=118.79, top=131, bot=110, edits=E),
 dict(page=107, id='5.23', y=758.89, top=771, bot=750, edits=E),
 dict(page=107, id='5.24', y=598.89, top=611, bot=590, edits=E),
 dict(page=107, id='5.25', y=420.59, top=433, bot=393, edits=E),
 dict(page=108, id='5.27', x=78.510, y=740.69, top=750, bot=732, edits=E),
 dict(page=116, id='5.60', y=562.29, top=574, bot=553, edits=E),
 dict(page=117, id='5.63', y=758.89, top=771, bot=732, edits=E),
]
