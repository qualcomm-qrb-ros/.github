module.exports = {
  extends: ['@commitlint/config-conventional'],
  rules: {
    "body-case": [2,"always", "sentence-case"],
    "body-leading-blank": [2, "always"],
    "type-enum": [2, "always",
        [
            "build",
            "chore",
            "ci",
            "docs",
            "feat",
            "fix",
            "perf",
            "refactor",
            "revert",
            "style",
            "test",
            "release",
        ]
    ],
  }
};
