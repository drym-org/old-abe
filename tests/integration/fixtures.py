import pytest


@pytest.fixture
def abe_fs(fs):
    fs.create_file("./abe/price.txt", contents="10")
    fs.create_file("./abe/valuation.txt", contents="100000")
    fs.create_file("./abe/instruments.txt", contents="""
        old abe,1
        DIA,5
        """)
    fs.create_file("./abe/attributions.txt", contents="""
       sid,50
       jair,30
       ariana,20
       """)
    return fs
