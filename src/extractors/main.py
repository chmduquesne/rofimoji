from blockextractor import BlockExtractor
from characterfactory import CharacterFactory
from emojiextractor import EmojiExtractor
from mathcollectionextractor import MathExtractor
from nerdextractor import NerdExtractor

if __name__ == "__main__":
    character_factory = CharacterFactory()

    EmojiExtractor().extract()
    BlockExtractor(character_factory).extract()
    MathExtractor(character_factory).extract()
    NerdExtractor().extract()
