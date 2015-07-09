Specchio
========

[![Build Status](https://travis-ci.org/brickgao/specchio.svg?branch=master)](https://travis-ci.org/brickgao/specchio)
[![Coverage Status](https://coveralls.io/repos/brickgao/specchio/badge.svg?branch=master)](https://coveralls.io/r/brickgao/specchio?branch=master)
[![PyPI version](https://img.shields.io/pypi/v/specchio.svg?style=flat)](https://pypi.python.org/pypi/Specchio)
[![MIT licensed](https://img.shields.io/badge/license-MIT-blue.svg)](./LICENSE)
[![Join the chat at https://gitter.im/brickgao/specchio](https://badges.gitter.im/Join%20Chat.svg)](https://gitter.im/brickgao/specchio?utm_source=badge&utm_medium=badge&utm_campaign=pr-badge&utm_content=badge)

Specchio is a tool that can help you rsync your code, it uses `.gitignore` in git to discern which file is ignored.

Install
-------
pip install specchio

Usage
-----
specchio [options] src/ user@host:dst/

General Options
-----
--init-remote: Initialize remote folder, rsync all files to remote system.

Note
---
If you want to use specchio without decrypting private keys each time, try to use `ssh-add` at first.

Why I write Specchio
-------------------
I write my code on my local system, and the code should run it on a remote system.

Once I try to solve this problem by using `git` only, I use `git add`,  `git commit` and `git push` on my local system, and then use `git pull` to pull all of the code on remote system.

It solve the problem temporarily, but it generate some temporary commit message that I don't need.

I need a tool to rsync my code and ignore file following `.gitignore`, so Specchio born.


License
-----
[MIT](http://opensource.org/licenses/MIT)

