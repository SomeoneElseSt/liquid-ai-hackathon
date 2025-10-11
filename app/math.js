// This function is private to this file unless we export it.
const add = (a, b) => {
  return a + b;
};

// We use module.exports to make the 'add' function available to other files.
module.exports = {
  add
};