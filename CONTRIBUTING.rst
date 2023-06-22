============
Contributing
============

Contributions are welcome, and they are greatly appreciated! Every little bit
helps, and credit will always be given.

Bug reports
===========

When `reporting a bug <https://github.com/pauliacomi/pygaps/issues>`_ please include:

- Your operating system name and version.
- Any details about your local setup that might be helpful in
  troubleshooting.
- Detailed steps to reproduce the bug.

A helpful GitHub issue template is provided.

Documentation improvements
==========================

The package could always use more documentation, whether as part of the official
docs, in docstrings, or even on the web in blog posts, articles, and such. If
you think something is unclear, incomplete or should be rewritten, please submit
`an issue report <https://github.com/pauliacomi/pygaps/issues>`_ or make a pull
request.

Feature requests and feedback
=============================

The best way to send feedback is to file
`an an improvement proposal <https://github.com/pauliacomi/pygaps/issues>`_

If you are proposing a feature:

- Explain in detail how it would work.
- Keep the scope as narrow as possible, to make it easier to implement.
- And of course, remember that this project is developed in the
  spare time of the maintainers, and that code contributions are welcome :)

Development
===========

To set up `pyGAPS` for local development:

1. Fork `pyGAPS <https://github.com/pauliacomi/pygaps>`_
   (look for the "Fork" button).

2. Clone your fork locally::

    git clone https://github.com/YOURNAMEHERE/pyGAPS

3. Install the package in editable mode with its dev requirements::

    pip install -e .[dev,docs]

4. Create a branch for local development. This project uses the
   `GIT FLOW <https://www.gitkraken.com/learn/git/git-flow>`_ model::

    git checkout -b name-of-your-bugfix-or-feature

   Now you can make your changes locally.

5. When you're done making changes, run all the tests::

    pytest

6. Commit your changes and push your branch to GitHub::

    git add .
    git commit -m "Your detailed description of your changes."
    git push origin name-of-your-bugfix-or-feature

7. Submit a pull request through the GitHub website. Testing on all environments
   will be automatically performed.

Pull Request Guidelines
-----------------------

If you need some code review or feedback while you're developing the code just
make the pull request.

For merging, you should:

1. Include passing tests (run ``pytest``) [1]_.
2. Update documentation when there's new API, functionality etc.
3. Add a note to ``CHANGELOG.rst`` about the changes.
4. Add yourself to ``AUTHORS.rst``.

.. [1] If you don't have all the necessary python versions available
       locally you can rely on GitHub - it will
       `run the tests <https://github.com/pauliacomi/pyGAPS/actions>`_
       for each change you add in the pull request.

