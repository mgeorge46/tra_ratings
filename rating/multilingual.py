import polib

po = polib.POFile()
po.metadata = {
    'Project-Id-Version': '1.0',
    'Report-Msgid-Bugs-To': '',
    'POT-Creation-Date': '',
    'PO-Revision-Date': '',
    'Last-Translator': '',
    'Language-Team': '',
    'Language': 'lg',
    'MIME-Version': '1.0',
    'Content-Type': 'text/plain; charset=UTF-8',
    'Content-Transfer-Encoding': '8bit',
}

entry = polib.POEntry(
    msgid="Hello, world!",
    msgstr="Gyebale, ensi!",
)
po.append(entry)

po.save('locale/lg/LC_MESSAGES/django.po')
