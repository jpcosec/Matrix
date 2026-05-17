# Coding Standards

This document records the working code-organization standard for the repository. These are heuristics, not absolute laws, but they should be treated as the default design pressure when adding or refactoring code.

## Documentation

- Every file must start with a module docstring.
- Every class must have a class docstring.
- Every function must have a function docstring.

## Files and folders

- If a folder has more than 5 files, it should probably be grouped into subfolders.
- If a file has more than 80 lines, it should probably become a focused class or be split further.
- If a file has more than one class, it should probably be split into one class per file.

## Classes

- If a class has more than 2 functions, it should probably be rethought as an abstract base plus focused concrete implementations, or split into smaller collaborating classes.
- Prefer narrow classes with one explicit responsibility.
- Use typed classes, inheritance where appropriate, and dataclasses when they reduce incidental complexity.

## Functions

- If a function does more than 2 things, it should probably become 2 functions or a class.
- If a function has more than 8 lines, it should probably be split into smaller helpers.
- Prefer small internal helper functions with descriptive names over long, dense blocks of code.
- If 2 functions are effectively doing the same thing, they should probably be unified into one abstraction, or moved into a shared utility module.

## Design intent

- Favor explicit typing for arguments, return values, classes, and intermediate structures.
- Favor composition and clean interfaces over hidden coupling.
- Use class diagrams when useful to verify that responsibilities stay boxed correctly and relationships only exist where they should.
- The goal is to reduce spaghetti code by keeping each unit small, typed, documented, and structurally obvious.
