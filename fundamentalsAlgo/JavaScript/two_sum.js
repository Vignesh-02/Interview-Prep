function twoSum(nums, target) {
  const seen = new Map();

  for (let i = 0; i < nums.length; i += 1) {
    const diff = target - nums[i];
    if (seen.has(diff)) {
      return [seen.get(diff), i];
    }
    seen.set(nums[i], i);
  }

  return null;
}

const nums = [9, 5, 4, 3];
const target = 12;
console.log("The two sum is", twoSum(nums, target));

module.exports = { twoSum };
