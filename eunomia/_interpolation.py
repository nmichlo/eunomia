
from eunomia._nodes import InterpNode
from eunomia._util import fmt_pntr


class TokenizeError(Exception):
    pass


# ========================================================================= #
# Printing                                                                  #
# ========================================================================= #


TOKEN_STRING = 'string'
TOKEN_INTERP = 'interpolate'

TOK_BGN = '${'
TOK_END = '}'

# check the tokens
assert 1 <= len(TOK_BGN) and TOK_BGN.strip() == TOK_BGN
assert 1 <= len(TOK_END) and TOK_END.strip() == TOK_END
assert TOK_BGN != TOK_END


# ========================================================================= #
# Parsing                                                                   #
# ========================================================================= #


def _tokenize_string(string, bgn_tok=TOK_BGN, end_tok=TOK_END, strict_end=False):
    bgn_len, end_len = len(bgn_tok), len(end_tok)
    # state information
    tokens, block_start, in_block, has_interp = [], 0, False, False
    # loop over all the chars in the string
    # blocks are pushed as tokens
    for i, c in enumerate(string):
        # get the current block
        block = string[block_start:i+1]
        # 1. begin interp block
        if block[-bgn_len:] == bgn_tok:
            if in_block:
                raise TokenizeError(f'Eval blocks cannot be nested.\n{fmt_pntr(fmt_pntr(string, i, "Error"), block_start, "Start")}')
            block_start, in_block = i+1, True
            if block[:-bgn_len]:
                tokens.append((TOKEN_STRING, block[:-bgn_len]))
        # 2. end interp block
        elif block[-end_len:] == end_tok:
            if strict_end:
                if not in_block:
                    raise TokenizeError(f'Eval block ended but did not begin.\n{fmt_pntr(fmt_pntr(string, i, "Error"), block_start, "Start")}')
            has_interp = True
            block_start, in_block = i+1, False
            tokens.append((TOKEN_INTERP, block[:-end_len]))
    # save suffix
    if string[block_start:]:
        tokens.append((TOKEN_STRING, string[block_start:]))
    # Check that the interp block was closed - i will always be set if this runs
    if in_block:
        raise TokenizeError(f'Block was not closed.\n{fmt_pntr(fmt_pntr(string, i, "Error"), block_start, "Start")}')
    return tokens, has_interp


# from omegaconf: https://github.com/omry/omegaconf/blob/48b7a4ea2981c173457fd2dc8cd8bfa9680e3c74/omegaconf/_utils.py#L366
# re.finditer(key_prefix + legal_characters, string)
# key_prefix = r"\${(\w+:)?"
# legal_characters = r"([\w\.%_ \\/:,-@]*?)}"


def _replace_string(string):
    tokens, has_interp = _tokenize_string(string)
    if has_interp:
        return InterpNode(tokens)
    return string


def replace_interpolators(data):
    if isinstance(data, str):
        return _replace_string(data)
    elif isinstance(data, dict):
        return {
            k: replace_interpolators(v) for k, v in data.items()
        }
    elif isinstance(data, list):
        return [replace_interpolators(v) for v in data]
    elif isinstance(data, tuple):
        return tuple([replace_interpolators(v) for v in data])
    else:
        return data