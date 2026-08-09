class MorseConverter:
    MORSE_CODE_DICT = {
        'A': '.-', 'B': '-...', 'C': '-.-.', 'D': '-..', 'E': '.', 
        'F': '..-.', 'G': '--.', 'H': '....', 'I': '..', 'J': '.---', 
        'K': '-.-', 'L': '.-..', 'M': '--', 'N': '-.', 'O': '---', 
        'P': '.--.', 'Q': '--.-', 'R': '.-.', 'S': '...', 'T': '-', 
        'U': '..-', 'V': '...-', 'W': '.--', 'X': '-..-', 'Y': '-.--', 
        'Z': '--..', '1': '.----', '2': '..---', '3': '...--', 
        '4': '....-', '5': '.....', '6': '-....', '7': '--...', 
        '8': '---..', '9': '----.', '0': '-----', ' ': '/'
    }
    
    REVERSE_DICT = {v: k for k, v in MORSE_CODE_DICT.items()}

    @staticmethod
    def encode(text: str) -> str:
        """Converts plaintext to Morse code string."""
        text = text.upper()
        morse_chars = []
        for char in text:
            if char in MorseConverter.MORSE_CODE_DICT:
                morse_chars.append(MorseConverter.MORSE_CODE_DICT[char])
        return ' '.join(morse_chars)

    @staticmethod
    def decode(morse_str: str) -> str:
        """Converts Morse code string to plaintext."""
        # Spaces between parts of same letter, slash between words
        words = morse_str.split('/')
        decoded_words = []
        for word in words:
            chars = word.strip().split(' ')
            decoded_word = ''.join(MorseConverter.REVERSE_DICT.get(c, '') for c in chars if c)
            decoded_words.append(decoded_word)
        return ' '.join(decoded_words)
