// O(V + E) time and O(V) space

function dfs(graph, node, visited) {
  if (visited.has(node)) return;

  process.stdout.write(node + " ");
  visited.add(node);

  for (const neighbor of graph[node]) {
    dfs(graph, neighbor, visited);
  }
}

const graph = {
  0: [1, 2],
  1: [3],
  2: [4, 5],
  3: [0, 6], // cycle back to 0
  4: [2], // self-cycle via 2 -> 4 -> 2
  5: [6, 7],
  6: [1], // cycle back to 1
  7: [],
};

const visited = new Set();
dfs(graph, 0, visited);
console.log();

module.exports = { dfs };
