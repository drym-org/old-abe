import pytest


@pytest.fixture
def abe_fs(fs):
    fs.create_file("./abe/price.txt", contents="10")
    fs.create_file("./abe/valuation.txt", contents="100000")
    fs.create_file("./abe/instruments.txt", contents=("old abe,1/100\n" "DIA,5/100\n"))
    fs.create_file(
        "./abe/attributions.txt",
        contents=("sid,1/2\n" "jair,3/10\n" "ariana,1/5\n"),
    )
    return fs
