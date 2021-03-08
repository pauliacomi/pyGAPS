============
Contributing
============

Contributions are welcome, and they are greatly appreciated! Every little bit
helps, and credit will always be given.

Bug reports
===========

When `reporting a bug <https://github.com/pauliacomi/pygaps/issues>`_ please include:

    * Your operating system name and version.
    * Any details about your local setup that might be helpful in
      troubleshooting.
    * Detailed steps to reproduce the bug.

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

* Explain in detail how it would work.
* Keep the scope as narrow as possible, to make it easier to implement.
* And of course, remember that this project is developed in the
  spare time of the maintainers, and that code contributions are welcome :)

Development
===========

To set up `pyGAPS` for local development:

1. Fork `pyGAPS <https://github.com/pauliacomi/pygaps>`_
   (look for the "Fork" button).

2. Clone your fork locally::

    git clone git@github.com:your_name_here/pygaps.git

3. Create a branch for local development::

    git checkout -b name-of-your-bugfix-or-feature

   Now you can make your changes locally.

4. When you're done making changes, run all the checks, doc builder and
   spell checker with `tox <https://tox.readthedocs.io/en/latest/install.html>`_
   one command::

    tox

   Or you could run the tests with only your own environment by running::

    python setup.py test

    # or pytest directly

    pytest

5. Commit your changes and push your branch to GitHub::

    git add .
    git commit -m "Your detailed description of your changes."
    git push origin name-of-your-bugfix-or-feature

6. Submit a pull request through the GitHub website. Testing on all environments
   will be automatically performed.

Pull Request Guidelines
-----------------------

If you need some code review or feedback while you're developing the code just
make the pull request.

For merging, you should:

1. Include passing tests (run ``tox``) [1]_.
2. Update documentation when there's new API, functionality etc.
3. Add a note to ``CHANGELOG.rst`` about the changes.
4. Add yourself to ``AUTHORS.rst``.

.. [1] If you don't have all the necessary python versions available
       locally you can rely on Travis - it will
       `run the tests <https://travis-ci.org/pauliacomi/pyGAPS/pull_requests>`_
       for each change you add in the pull request.


Tips
----

To run a subset of tests::

    tox -e envname -- pytest -k test_myfeature

To run all the test environments in *parallel* (you need to ``pip install detox``)::

    detox
