from collections import namedtuple
from typing import List, Set, Dict, Tuple

import requests
from lxml import etree
from lxml.etree import XPath


Emoji = namedtuple('Emoji', 'char name')


def extract_character_description_from_line(line: str) -> Tuple[chr, str]:
    fields = [s.strip() for s in line.split(';')]
    char = chr(int(fields[0], 16))
    name = fields[1]
    return (char, name)


def fetch_character_descriptions() -> Dict[chr, str]:
    print('Downloading character descriptions...')

    data = requests.get(
        'https://unicode.org/Public/UNIDATA/UnicodeData.txt',
        timeout=60
    )  # type: requests.Response

    descriptions = dict()
    for line in data.content.decode(data.encoding).split('\n'):
        if line.startswith('#') or len(line) == 0:
            continue
        char, desc = extract_character_description_from_line(line)
        descriptions[char] = desc

    return descriptions


DESCRIPTIONS = fetch_character_descriptions()


def fetch_emoji_list() -> List[Emoji]:
    chars = fetch_emojis() + fetch_math_symbols()
    chars = list(set(chars)) # eliminate dupplicates
    chars = sorted(chars)
    emojis = []
    for char in chars:
        try:
            emojis.append(Emoji(char, DESCRIPTIONS[char].lower()))
        except KeyError:
            pass
    return emojis


def fetch_math_symbols() -> List[chr]:
    print('Downloading raw maths symbols...')

    data = requests.get(
        'https://unicode.org/Public/math/latest/MathClassEx-15.txt',
        timeout=60
    )  # type: requests.Response

    chars = []
    for line in data.content.decode(data.encoding).split('\n'):
        if line.startswith('#') or len(line) == 0:
            continue
        chars.extend(extract_emojis_from_line(line))

    return chars


def fetch_emojis() -> List[chr]:
    print('Downloading raw emojis...')

    data = requests.get(
        'https://unicode.org/Public/emoji/12.0/emoji-data.txt',
        timeout=60
    )  # type: requests.Response

    chars = []
    for line in data.content.decode(data.encoding).split('\n'):
        if line.startswith('#') or len(line) == 0:
            continue
        chars.extend(extract_emojis_from_line(line))

    return chars


def fetch_human_emojis() -> List[chr]:
    print('Downloading list of human emojis...')

    data = requests.get(
        'https://unicode.org/Public/emoji/12.0/emoji-data.txt',
        timeout=60
    )  # type: requests.Response

    started = False
    emojis = []
    for line in data.content.decode(data.encoding).split('\n'):
        if not started and line != '# All omitted code points have Emoji_Modifier_Base=No ':
            continue
        started = True
        if started and line == '# Total elements: 120':
            break
        if started and (line.startswith('#') or len(line) == 0):
            continue
        emojis.extend(extract_emojis_from_line(line))

    return emojis


def extract_emojis_from_line(line: str) -> List[chr]:
    emoji_range = line.split(';')[0].strip()
    try:
        (start, end) = emoji_range.split('..')
        emojis = []
        for char in range(int(start, 16), int(end, 16) + 1):
            emojis.append(chr(char))
        return emojis
    except ValueError:
        return [chr(int(emoji_range, 16))]


def fetch_annotations() -> Dict[chr, List[str]]:
    print('Downloading annotations')

    data = requests.get(
        'https://raw.githubusercontent.com/unicode-org/cldr/release-35-1/common/annotations/en.xml',
        timeout=60
    )  # type: requests.Response

    xpath = XPath('./annotations/annotation[not(@type="tts")]')
    return {element.get('cp'): element.text.split(' | ') for element in
            xpath(etree.fromstring(data.content))}


def write_file(all_emojis: List[Emoji], human_emojis: Set[chr], annotations: Dict[chr, List[str]]):
    print('Writing collected emojis to file')
    python_file = open('emojis.py', 'w')
    python_file.write('emoji_list="""')

    for entry in compile_entries(all_emojis, annotations):
        python_file.write(entry + "\n")

    python_file.write('"""\n\n')

    python_file.write('skin_tone_selectable_emojis={\'')
    python_file.write('\', \''.join(human_emojis))
    python_file.write('\'}\n')

    python_file.close()


def compile_entries(emojis: List[Emoji], annotations: Dict[chr, List[str]]) -> List[str]:
    annotated_emojis = []
    for emoji in emojis:
        if emoji.char in annotations:
            entry = f"{emoji.char} {emoji.name} <small>({', '.join(annotations[emoji.char])})</small>"
        else:
            entry = f"{emoji.char} {emoji.name}"

        annotated_emojis.append(entry)

    return annotated_emojis


if __name__ == "__main__":
    write_file(fetch_emoji_list(), fetch_human_emojis(), fetch_annotations())
