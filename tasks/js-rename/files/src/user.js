function getUserName(user) {
  if (!user) return "anonymous";
  return user.nickname || `${user.first} ${user.last}`;
}

module.exports = { getUserName };
