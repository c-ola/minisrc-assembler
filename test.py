from assembler import *

tokenizer = Tokenizer()

tokenizer.parse_tokens("tests/instructions.s")
print(tokenizer.tokens)
print(tokenizer.comments)
