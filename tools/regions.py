"""The Super Paper Mario releases and the main.dol each one ships.

A key names one distinct main.dol. It is the disc ID, plus `r<N>` where one ID
has several different executables (USA and Japan); that is also how Dolphin
names revision-specific settings files (`R8PE01r1.ini`), so the generated
codes/<key>.ini load for exactly the right disc.

Europe Rev 0 and Rev 1 ship byte-identical executables (they differ elsewhere
on the disc), so they share one key and one set of patches.
"""

REGIONS = {
    'R8PE01r0': {
        'id': 'R8PE01',
        'revs': (0,),
        'label': 'Super Paper Mario (USA Rev 0)',
        'title': 'Super Paper Mario',
        'region': 'USA',
        'short': 'USA',
    },
    'R8PE01r1': {
        'id': 'R8PE01',
        'revs': (1,),
        'label': 'Super Paper Mario (USA Rev 1)',
        'title': 'Super Paper Mario',
        'region': 'USA',
        'short': 'USA',
    },
    'R8PE01r2': {
        'id': 'R8PE01',
        'revs': (2,),
        'label': 'Super Paper Mario (USA Rev 2)',
        'title': 'Super Paper Mario',
        'region': 'USA',
        'short': 'USA',
    },
    'R8PP01': {
        'id': 'R8PP01',
        'revs': (0, 1),
        'label': 'Super Paper Mario (Europe Rev 0 and Rev 1)',
        'title': 'Super Paper Mario',
        'region': 'Europe',
        'short': 'EUR',
    },
    'R8PJ01r0': {
        'id': 'R8PJ01',
        'revs': (0,),
        'label': 'Super Paper Mario (Japan Rev 0)',
        'title': 'Super Paper Mario',
        'region': 'Japan',
        'short': 'JPN',
    },
    'R8PJ01r1': {
        'id': 'R8PJ01',
        'revs': (1,),
        'label': 'Super Paper Mario (Japan Rev 1)',
        'title': 'Super Paper Mario',
        'region': 'Japan',
        'short': 'JPN',
    },
    'R8PK01': {
        'id': 'R8PK01',
        'revs': (0,),
        'label': 'Super Paper Mario (Korea)',
        'title': 'Super Paper Mario',
        'region': 'Korea',
        'short': 'KOR',
    },
}

REVS = list(REGIONS.keys())
