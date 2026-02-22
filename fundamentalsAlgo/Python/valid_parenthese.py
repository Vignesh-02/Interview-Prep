

# O(n) time and space

def valid_parenthesis(s):
    bracks=[]

    mapping={')': '(', ']':'[', '}':'{' }

    for c in s:
        if c in mapping:
            if bracks and bracks[-1]==mapping[c]:
                bracks.pop()
            else:
                return False
        else:
            bracks.append(c)
    
    if not bracks:
        return True
    else:
        return False
        

out=valid_parenthesis("{{}}[]")
print(out)