// Python slicing equivalent
// O(n) time and space
function rev(s) {
  return s.split("").reverse().join("");
}

console.log(rev("Hello"));

// two pointer method - best
// O(n) time and O(1) extra space
function rev1(s) {
  const arr = s.split("");
  let left = 0;
  let right = arr.length - 1;
  while (left < right) {
    const temp = arr[left];
    arr[left] = arr[right];
    arr[right] = temp;
    left += 1;
    right -= 1;
  }
  return arr.join("");
}

console.log(rev1("Hello"));

// using built-in reversed method equivalent
// O(n) time and space
function rev2(s) {
  return s.split("").reverse().join("");
}

console.log(rev2("Hello"));

// O(n) time and space
function rev3(s) {
  const stack = s.split("");
  const res = [];
  while (stack.length) {
    res.push(stack.pop());
  }
  return res.join("");
}

console.log(rev3("Hello"));

// Reverse words in a sentence
function revWordsInSentence(s) {
  const temp = s.split(" ").reverse();
  const out = temp.join(" ");
  console.log(out);
}

revWordsInSentence("Hello from the other side");

// Reverse a String Without Affecting Special Characters
// O(n) time and space
function rev5(s) {
  const arr = s.split("");
  let left = 0;
  let right = arr.length - 1;

  while (left < right) {
    if (!/[a-z0-9]/i.test(arr[left])) {
      left += 1;
    } else if (!/[a-z0-9]/i.test(arr[right])) {
      right -= 1;
    } else {
      const temp = arr[left];
      arr[left] = arr[right];
      arr[right] = temp;
      left += 1;
      right -= 1;
    }
  }

  return arr.join("");
}

console.log(rev5("a,b$c"));

// Reverse Every Word in a Sentence
// O(n) time and space
function reverseEachWord(s) {
  const words = s.split(" ");
  const out = [];
  for (const word of words) {
    out.push(word.split("").reverse().join(""));
  }
  return out.join(" ");
}

console.log(reverseEachWord("Hello from the other side"));

// Reverse Every k Characters
function reverseK(s, k) {
  const arr = s.split("");
  for (let i = 0; i < arr.length; i += 2 * k) {
    const left = i;
    const right = Math.min(i + k - 1, arr.length - 1);
    let l = left;
    let r = right;
    while (l < r) {
      const temp = arr[l];
      arr[l] = arr[r];
      arr[r] = temp;
      l += 1;
      r -= 1;
    }
  }
  return arr.join("");
}

console.log(reverseK("abcdefgh", 2));

// O(n) time and space
function reverseK1(s, k) {
  const arr = s.split("");
  const n = arr.length;

  for (let start = 0; start < n; start += 2 * k) {
    let left = start;
    let right = Math.min(start + k - 1, n - 1);

    while (left < right) {
      const temp = arr[left];
      arr[left] = arr[right];
      arr[right] = temp;
      left += 1;
      right -= 1;
    }
  }

  return arr.join("");
}

console.log(reverseK1("abcdefgh", 2));

// O(n) time and space
function reverseVowels(s) {
  const vowels = new Set(["a", "e", "i", "o", "u", "A", "E", "I", "O", "U"]);
  const arr = s.split("");
  let left = 0;
  let right = arr.length - 1;

  while (left < right) {
    if (!vowels.has(arr[left])) {
      left += 1;
    } else if (!vowels.has(arr[right])) {
      right -= 1;
    } else {
      const temp = arr[left];
      arr[left] = arr[right];
      arr[right] = temp;
      left += 1;
      right -= 1;
    }
  }

  return arr.join("");
}

console.log(reverseVowels("hello world"));

module.exports = {
  rev,
  rev1,
  rev2,
  rev3,
  revWordsInSentence,
  rev5,
  reverseEachWord,
  reverseK,
  reverseK1,
  reverseVowels,
};
