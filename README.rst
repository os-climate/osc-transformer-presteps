💬 Important

On June 26 2024, Linux Foundation announced the merger of its financial services umbrella, the Fintech Open Source Foundation (`FINOS <https://finos.org>`_), with OS-Climate, an open source community dedicated to building data technologies, modelling, and analytic tools that will drive global capital flows into climate change mitigation and resilience; OS-Climate projects are in the process of transitioning to the `FINOS governance framework <https://community.finos.org/docs/governance>`_; read more on `finos.org/press/finos-join-forces-os-open-source-climate-sustainability-esg <https://finos.org/press/finos-join-forces-os-open-source-climate-sustainability-esg>`_


=========================
OSC Transformer Pre-Steps
=========================

|osc-climate-project| |osc-climate-slack| |osc-climate-github| |pypi| |build-status| |pdm| |PyScaffold|

OS-Climate Transformer Pre-Steps Tool
=====================================

.. _notes:

This code provides you with a cli tool with the possibility to extract data from
a pdf to a json document and to create a training data set for a later usage in the
context of transformer models
to extract relevant information, but it can also be used independently.

Quick start
===========

Install via PyPi
----------------

You can simply install the package via::

    $ pip install osc-transformer-presteps

Afterwards you can use the tooling as a CLI tool by simply typing::

    $ osc-transformer-presteps

We are using typer to have a nice CLI tool here. All details and help will be shown in the CLI
tool itself and are not described here in more detail.

**Example**: Assume the folder structure is like that:

.. code-block:: text

    project/
    ├-input/
    │ ├-file_1.pdf
    │ ├-file_2.pdf
    │ └─file_3.pdf
    ├-logs/
    └─output/

Then you can now simply run (after installation of osc-transformer-presteps)
the following command to extract the data from the pdfs to json:

    $ osc-transformer-presteps extraction run-local-extraction 'input' --output-folder='output' --logs-folder='logs' --force

*Note*: Here force overcomes encryption. Please check if that is a legal action for you.

Developer space
===============

Use code directly without CLI via Github Repository
---------------------------------------------------

First clone the repository to your local environment::

    $ git clone https://github.com/os-climate/osc-transformer-presteps

We are using pdm to manage the packages and tox for a stable test framework.
Hence, first install pdm (possibly in a virtual environment) via

    $ pip install pdm

Afterwards sync you system via

    $ pdm sync

Now you have multiple demos on how to go on. See folder
[here](demo)

pdm
---

For adding new dependencies use pdm. You could add new packages via pdm add.
For example numpy via::

    $ pdm add numpy

For a very detailed description check the homepage of the pdm project:

https://pdm-project.org/en/latest/


tox
---

For running linting tools we use tox which you run outside of your virtual environment::

    $ pip install tox
    $ tox -e lint
    $ tox -e test

This will automatically apply some checks on your code and run the provided pytests. See
more details on tox on the homepage of the tox project:

https://tox.wiki/en/4.16.0/


.. |osc-climate-project| image:: https://img.shields.io/badge/OS-Climate-blue
  :alt: An OS-Climate Project
  :target: https://os-climate.org/

.. |osc-climate-slack| image:: https://img.shields.io/badge/slack-osclimate-brightgreen.svg?logo=slack
  :alt: Join OS-Climate on Slack
  :target: https://os-climate.slack.com

.. |osc-climate-github| image:: https://img.shields.io/badge/GitHub-100000?logo=github&logoColor=white
  :alt: Source code on GitHub
  :target: https://github.com/ModeSevenIndustrialSolutions/osc-data-extractor

.. |pypi| image:: https://img.shields.io/pypi/v/osc-data-extractor.svg
  :alt: PyPI package
  :target: https://pypi.org/project/osc-data-extractor/

.. |build-status| image:: https://api.cirrus-ci.com/github/os-climate/osc-data-extractor.svg?branch=main
  :alt: Built Status
  :target: https://cirrus-ci.com/github/os-climate/osc-data-extractor

.. |pdm| image:: https://img.shields.io/badge/PDM-Project-purple
  :alt: Built using PDM
  :target: https://pdm-project.org/latest/

.. |PyScaffold| image:: https://img.shields.io/badge/-PyScaffold-005CA0?logo=pyscaffold
  :alt: Project generated with PyScaffold
  :target: https://pyscaffold.org/
