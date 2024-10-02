import pytest


@pytest.fixture
def abe_fs(fs):
    fs.create_file("./abe/price.txt", contents="10")
    fs.create_file("./abe/valuation.txt", contents="100000")
    fs.create_file("./abe/instruments.txt", contents=("old abe,1\n" "DIA,5\n"))
    fs.create_file(
        "./abe/attributions.txt",
        contents=("sid,50\n" "jair,30\n" "ariana,20\n"),
    )
    return fs
