from guidance import guidance, select, one_or_more, zero_or_more, optional

class G():
    
    def __init__(self) -> None:
        pass
    
    @guidance(stateless=True)
    def alphaNumPunct(lm):

        return lm + select(['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z',
                    'é', 'è', 'ê', 'ë', 'à', 'â', 'ô', 'î', 'ï', 'û', 'ü', 'ç', 'æ', 'œ',
                    'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z',
                    'É', 'È', 'Ê', 'Ë', 'À', 'Â', 'Ô', 'Î', 'Ï', 'Û', 'Ü', 'Ç', 'Æ', 'Œ',
                    '0', '1', '2', '3', '4', '5', '6', '7', '8', '9', ' ', "'", ",", ".", ":", ";", "!", "?", "(", ")", "[", "]", "{", "}", "&", "-", "_", "+", "=", "*", "<", ">", "|", "@", "#", "$", "%", "^", "~", "`"])

    @guidance(stateless=True)
    def alphaNumPunctForSentence(lm):

        return lm + select(['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z',
                    'é', 'è', 'ê', 'ë', 'à', 'â', 'ô', 'î', 'ï', 'û', 'ü', 'ç', 'æ', 'œ',
                    'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z',
                    'É', 'È', 'Ê', 'Ë', 'À', 'Â', 'Ô', 'Î', 'Ï', 'Û', 'Ü', 'Ç', 'Æ', 'Œ',
                    '0', '1', '2', '3', '4', '5', '6', '7', '8', '9', ' ', "'", ",", ":", ";", "!", "?", "(", ")", "[", "]", "{", "}", "&", "-", "_", "+", "=", "*", "<", ">", "|", "@", "#", "$", "%", "^", "~", "`"])


    @guidance(stateless=True)
    def alphaNum(lm):
        return lm + select(['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z',
                    'é', 'è', 'ê', 'ë', 'à', 'â', 'ô', 'î', 'ï', 'û', 'ü', 'ç', 'æ', 'œ',
                    'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z',
                    'É', 'È', 'Ê', 'Ë', 'À', 'Â', 'Ô', 'Î', 'Ï', 'Û', 'Ü', 'Ç', 'Æ', 'Œ',
                    '0', '1', '2', '3', '4', '5', '6', '7', '8', '9'])

    @guidance(stateless=True)
    def num(lm):
        return lm + one_or_more(select(['0', '1', '2', '3', '4', '5', '6', '7', '8', '9']))

    @guidance(stateless=True)
    def float(lm):
        return lm + one_or_more(select(['0', '1', '2', '3', '4', '5', '6', '7', '8', '9','.']))

    @guidance(stateless=True)
    def bool(lm):
        return lm + select(['oui', 'non'])

    @guidance(stateless=True)
    def word(lm):
        return lm + one_or_more(G.alphaNum())

    @guidance(stateless=True)
    def sentence(lm):
        return lm + one_or_more(G.alphaNumPunctForSentence())+"."

    @guidance(stateless=True)
    def number(lm):
        return lm + one_or_more(G.num())

    @guidance(stateless=True)
    def crochet(lm):
        return lm + select(['["', '"]'])

    @guidance(stateless=True)
    def doubleQuote(lm):
        return lm +select(['"','", "','","'])

    @guidance(stateless=True)
    def element(lm,elementType):
        return lm + one_or_more(select([elementType, G.doubleQuote()]))

    @guidance(stateless=True)
    def arrayOf(lm,elementType):
        return lm + "[\"" + G.element(elementType) + G.crochet()
    
    @guidance(stateless=True)
    def elmSeparatedBy(lm,elementType,separator):
        return lm + one_or_more(select([elementType, select(separator)]))
    
    @guidance(stateless=True)
    def elmBetween(lm, elementsTypeBetween, elementType):
        return lm + "'" + elementType + "'" + select(elementsTypeBetween) + "'" +  elementType + "'"
    
    @guidance(stateless=True)
    def interdiction(lm,elementType):
        return lm + "'" + elementType + "'" + "--x" + "'" +  elementType + "'"
        
    @guidance(stateless=True)
    def relation(lm,elementType):
        return lm + select([G.implication(elementType), G.interdiction(elementType)])    