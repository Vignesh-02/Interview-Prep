

# O(n) time and O(1) space
def palindrome(s):
    # s=list(s)
    l,r=0,len(s)-1
    while l <= r:
        if s[l].lower()!=s[r].lower():
            print('check')
            return "Not a Palindrome"
        l+=1
        r-=1
    return "It is a Palindrome"

out=palindrome("bubba")
print(out)