/** The oldest kid, but only when the ages differ: with twins or one child there is no one to single out. */
export function codeBreaker(kids: readonly { nickname: string; age: number }[]): string | undefined {
  if (kids.length < 2) return undefined;
  const oldest = kids.reduce((a, b) => (b.age > a.age ? b : a));
  const sameAge = kids.every((k) => k.age === oldest.age);
  return sameAge ? undefined : oldest.nickname;
}
