from parser import ParserError


def fmt_pntr(line, i, message, arrow='^--- '):
    return f'{line}\n{" " * i}{arrow}{message}'


def tokenize(string):
    # state information
    block_start, in_block = None, False
    tokens, stack, prev = [], [], None

    def push_token(type, skip=None):
        tokens.append((type, ''.join(stack[:skip])))
        stack.clear()

    # loop over all the chars in the string
    # blocks are pushed as tokens
    # eg. string${eval}$string
    for i, c in enumerate(string):
        if prev == '$' and c == '{':
            if in_block:
                raise ParserError(f'Eval blocks cannot be nested.\n{fmt_pntr(fmt_pntr(string, i, "Error"), block_start, "Start")}')
            block_start, in_block = i, True
            push_token('eval', -1)
        elif in_block and prev == '}' and c == '$':
            block_start, in_block = None, False
            push_token('string', -1)
        else:
            stack.append(c)
            prev = c

    # save suffix
    if stack:
        push_token('string')
    if in_block:
        raise ParserError(f'Block was not closed.\n{fmt_pntr(fmt_pntr(string, i, "Error"), block_start, "Start")}')

    return tokens

# A -> A + B | B + A | A + B + A
# S -> A + B + A


def test_parse():
    print(tokenize('prefix${asdf}postfix'))