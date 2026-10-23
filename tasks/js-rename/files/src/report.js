const { getUserName } = require("./user");

function report(users) {
  return users.map((u) => getUserName(u)).join(", ");
}

module.exports = { report };
