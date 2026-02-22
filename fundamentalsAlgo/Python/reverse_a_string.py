

# Python slicing
# O(n) timee and space
# Con - it creates new object
def rev(s):
    return s[::-1]

print(rev("Hello"))

# two pointer method - best
# O(n) time and O(1) space
def rev1(s):
    s=list(s)
    l,r=0,len(s)-1
    while l<r:
        s[l],s[r]=s[r],s[l]
        l=l+1
        r=r-1
    
    return "".join(s)

print(rev1("Hello"))

# usign built in reversed method
# O(n) time and space

def rev2(s):
    return "".join(reversed(s))

print(rev2("Hello"))


# O(n) time and space
def rev3(s):
    stack=list(s)
    res=[]
    for i in stack:
        res.append(stack.pop(i))

    return ''.join(res)
    
# Reverse words in a sentence
def rev_words_in_a_sentence(s):
    temp=s.split(" ")
    temp=temp[::-1]
    out = " ".join(temp)
    print(out)

print(rev_words_in_a_sentence("Hello from the other side"))


# Reverse a String Without Affecting Special Characters
# O(n) space and O(n) time
def rev5(s):
    s = list(s)
    l, r = 0, len(s) - 1

    while l < r:
        if not s[l].isalnum():
            l += 1
        elif not s[r].isalnum():
            r -= 1
        else:
            s[l], s[r] = s[r], s[l]
            l += 1
            r -= 1

    return "".join(s)


print(rev5("a,b$c"))



# Reverse Every Word in a Sentence
# O(n) space and time
def reverse_each_word(s):
    words = s.split(" ")
    out=[]
    for i in words:
        out.append(i[::-1])

    return " ".join(out)

print(reverse_each_word("Hello from the other side"))

# Reverse Every k Characters
# IMP
def reverse_k(s,k):
    s=list(s)
    for i in range(0,len(s), 2*k):
        s[i:i+k]=reversed(s[i:i+k])
    return "".join(s)

print(reverse_k("abcdefgh",2))


# O(n) time and space
def reverse_k1(s,k):
    s=list(s)
    n=len(s)
    
    for start in range(0,n,2*k):
        left=start
        # for the cases when index goes out of bounds - we use (n-1)
        right=min(start+k-1, n-1)

        while left<right:
            s[left], s[right] = s[right], s[left]
            left += 1
            right -= 1
        
    return "".join(s)

print(reverse_k1("abcdefgh",2))
# 
#  how interviewers try to trick candidates on this
# 
# “The problem defines a pattern of reversing k characters and skipping the next k, so the window size is 2k.”


# O(n) time and space
def reverse_vowels(s):
    vowels = set("aeiouAEIOU")
    s = list(s)
    l, r = 0, len(s) - 1

    while l < r:
        if s[l] not in vowels:
            l += 1
        elif s[r] not in vowels:
            r -= 1
        else:
            s[l], s[r] = s[r], s[l]
            l += 1
            r -= 1

    return "".join(s)


def rev_linked_list(head):
    